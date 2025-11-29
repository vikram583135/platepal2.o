"""
Event Service for persisting and retrieving events
"""
import uuid
from typing import Dict, Any, Optional, List
from django.db import transaction
from django.utils import timezone
from .models import Event


class EventService:
    """Service for managing events in the event store"""
    
    @staticmethod
    @transaction.atomic
    def create_event(
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        version: str = '1.0'
    ) -> Event:
        """
        Create and persist an event in the event store.
        
        Args:
            event_type: Type of event (e.g., 'order.created')
            aggregate_type: Type of aggregate (e.g., 'Order')
            aggregate_id: ID of the aggregate instance
            payload: Event payload data
            metadata: Optional metadata (user, IP, etc.)
            version: Event schema version
        
        Returns:
            Created Event instance
        """
        # Ensure payload is JSON serializable
        import json
        from django.core.serializers.json import DjangoJSONEncoder
        
        if payload:
            payload = json.loads(json.dumps(payload, cls=DjangoJSONEncoder))
            
        event = Event.objects.create(
            event_id=uuid.uuid4(),
            type=event_type,
            version=version,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            payload=payload or {},
            metadata=metadata or {},
            timestamp=timezone.now()
        )
        return event
    
    @staticmethod
    def get_events_by_aggregate(
        aggregate_type: str,
        aggregate_id: str,
        since_event_id: Optional[str] = None
    ) -> List[Event]:
        """
        Get all events for a specific aggregate.
        
        Args:
            aggregate_type: Type of aggregate
            aggregate_id: ID of the aggregate
            since_event_id: Optional event ID to get events after this one
        
        Returns:
            List of Event instances
        """
        queryset = Event.objects.filter(
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id)
        ).order_by('sequence_number')
        
        if since_event_id:
            try:
                since_event = Event.objects.get(event_id=since_event_id)
                queryset = queryset.filter(sequence_number__gt=since_event.sequence_number)
            except Event.DoesNotExist:
                pass
        
        return list(queryset)
    
    @staticmethod
    def get_events_by_type(
        event_type: str,
        since_event_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get events by type.
        
        Args:
            event_type: Type of event
            since_event_id: Optional event ID to get events after this one
            limit: Optional limit on number of events
        
        Returns:
            List of Event instances
        """
        queryset = Event.objects.filter(type=event_type).order_by('sequence_number')
        
        if since_event_id:
            try:
                since_event = Event.objects.get(event_id=since_event_id)
                queryset = queryset.filter(sequence_number__gt=since_event.sequence_number)
            except Event.DoesNotExist:
                pass
        
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    @staticmethod
    def get_events_since(
        since_event_id: str,
        limit: Optional[int] = 1000
    ) -> List[Event]:
        """
        Get events after a specific event ID (for replay).
        
        Args:
            since_event_id: Event ID to start from
            limit: Maximum number of events to return
        
        Returns:
            List of Event instances
        """
        try:
            since_event = Event.objects.get(event_id=since_event_id)
            queryset = Event.objects.filter(
                sequence_number__gt=since_event.sequence_number
            ).order_by('sequence_number')[:limit]
            return list(queryset)
        except Event.DoesNotExist:
            # If event not found, return recent events
            return list(Event.objects.order_by('-sequence_number')[:limit or 100])
    
    @staticmethod
    def get_latest_event_for_aggregate(
        aggregate_type: str,
        aggregate_id: str
    ) -> Optional[Event]:
        """
        Get the latest event for an aggregate.
        
        Args:
            aggregate_type: Type of aggregate
            aggregate_id: ID of the aggregate
        
        Returns:
            Latest Event instance or None
        """
        try:
            return Event.objects.filter(
                aggregate_type=aggregate_type,
                aggregate_id=str(aggregate_id)
            ).order_by('-sequence_number').first()
        except Event.DoesNotExist:
            return None

