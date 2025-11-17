"""
Centralized Event Broadcasting Service
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Event
from .services import EventService

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


class EventBroadcastService:
    """
    Centralized service for broadcasting events via WebSocket channels.
    Ensures events are persisted in the event store and broadcast to relevant channels.
    """
    
    @staticmethod
    @transaction.atomic
    def broadcast(
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Dict[str, Any],
        channels: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        version: str = '1.0'
    ) -> Event:
        """
        Create an event in the event store and broadcast it to WebSocket channels.
        
        Args:
            event_type: Type of event (e.g., 'order.created', 'payment.captured')
            aggregate_type: Type of aggregate (e.g., 'Order', 'Payment')
            aggregate_id: ID of the aggregate instance
            payload: Event payload data
            channels: List of channel group names to broadcast to (e.g., ['customer_1', 'restaurant_2', 'admin'])
            metadata: Optional metadata (user, IP, request ID, etc.)
            version: Event schema version
        
        Returns:
            Created Event instance
        """
        # Create event in event store (within transaction)
        event = EventService.create_event(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            metadata=metadata or {},
            version=version
        )
        
        # Broadcast to channels (outside transaction for async)
        if channels:
            try:
                EventBroadcastService._send_to_channels(
                    event_type=event_type,
                    event_id=str(event.event_id),
                    channels=channels,
                    data={
                        'event_id': str(event.event_id),
                        'type': event_type,
                        'version': version,
                        'timestamp': event.timestamp.isoformat(),
                        'aggregate_type': aggregate_type,
                        'aggregate_id': str(aggregate_id),
                        'payload': payload
                    }
                )
            except Exception as e:
                # Log error but don't fail the transaction
                logger.error(f"Failed to broadcast event {event.event_id}: {str(e)}", exc_info=True)
                
                # Schedule retry for failed broadcasts
                from .tasks import retry_event_broadcast
                for channel in channels:
                    try:
                        retry_event_broadcast.delay(str(event.event_id), channel)
                    except Exception as retry_error:
                        logger.error(f"Failed to schedule retry for event {event.event_id}: {str(retry_error)}")
        
        return event
    
    @staticmethod
    def _send_to_channels(event_type: str, event_id: str, channels: List[str], data: Dict[str, Any]):
        """
        Send event to multiple channel groups.
        
        Args:
            event_type: Type of event (for handler routing)
            event_id: Unique event ID
            channels: List of channel group names
            data: Event data to send
        """
        if not channel_layer:
            logger.warning("Channel layer not configured, skipping broadcast")
            return
        
        # Normalize event type for channel handler (e.g., 'order.created' -> 'order_created')
        handler_type = event_type.replace('.', '_')
        
        for channel_group in channels:
            try:
                async_to_sync(channel_layer.group_send)(
                    channel_group,
                    {
                        'type': handler_type,
                        'data': data,
                        'event_id': event_id,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send to channel {channel_group}: {str(e)}", exc_info=True)
                
                # Schedule retry for failed channel
                try:
                    from .tasks import retry_event_broadcast
                    retry_event_broadcast.delay(event_id, channel_group)
                except Exception as retry_error:
                    logger.error(f"Failed to schedule retry for channel {channel_group}: {str(retry_error)}")
                    # Fallback: send to DLQ if retry scheduling fails
                    try:
                        from .tasks import send_to_dlq
                        send_to_dlq.delay(event_id, channel_group, str(e))
                    except Exception as dlq_error:
                        logger.error(f"Failed to send to DLQ: {str(dlq_error)}")
    
    @staticmethod
    def broadcast_to_customer(customer_id: int, event_type: str, aggregate_type: str, 
                               aggregate_id: str, payload: Dict[str, Any], **kwargs) -> Event:
        """Broadcast event to a specific customer"""
        return EventBroadcastService.broadcast(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            channels=[f'customer_{customer_id}'],
            **kwargs
        )
    
    @staticmethod
    def broadcast_to_restaurant(restaurant_id: int, event_type: str, aggregate_type: str,
                                aggregate_id: str, payload: Dict[str, Any], **kwargs) -> Event:
        """Broadcast event to a specific restaurant"""
        return EventBroadcastService.broadcast(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            channels=[f'restaurant_{restaurant_id}'],
            **kwargs
        )
    
    @staticmethod
    def broadcast_to_rider(rider_id: int, event_type: str, aggregate_type: str,
                           aggregate_id: str, payload: Dict[str, Any], **kwargs) -> Event:
        """Broadcast event to a specific rider"""
        return EventBroadcastService.broadcast(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            channels=[f'delivery_{rider_id}'],
            **kwargs
        )
    
    @staticmethod
    def broadcast_to_admin(event_type: str, aggregate_type: str, aggregate_id: str,
                          payload: Dict[str, Any], **kwargs) -> Event:
        """Broadcast event to admin channel"""
        return EventBroadcastService.broadcast(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            channels=['admin'],
            **kwargs
        )
    
    @staticmethod
    def broadcast_to_multiple(
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Dict[str, Any],
        customer_id: Optional[int] = None,
        restaurant_id: Optional[int] = None,
        rider_id: Optional[int] = None,
        include_admin: bool = False,
        **kwargs
    ) -> Event:
        """
        Broadcast event to multiple channels based on provided IDs.
        
        Args:
            event_type: Type of event
            aggregate_type: Type of aggregate
            aggregate_id: ID of aggregate
            payload: Event payload
            customer_id: Optional customer ID
            restaurant_id: Optional restaurant ID
            rider_id: Optional rider ID
            include_admin: Whether to include admin channel
            **kwargs: Additional arguments for broadcast()
        
        Returns:
            Created Event instance
        """
        channels = []
        if customer_id:
            channels.append(f'customer_{customer_id}')
        if restaurant_id:
            channels.append(f'restaurant_{restaurant_id}')
        if rider_id:
            channels.append(f'delivery_{rider_id}')
        if include_admin:
            channels.append('admin')
        
        return EventBroadcastService.broadcast(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            channels=channels,
            **kwargs
        )

