"""
WebSocket consumers for real-time updates
"""
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings

User = get_user_model()


class BaseConsumer(AsyncJsonWebsocketConsumer):
    """Base consumer with authentication"""
    
    async def connect(self):
        """Authenticate WebSocket connection"""
        try:
            self.user = await self.authenticate()
            if not self.user or isinstance(self.user, AnonymousUser):
                # Log authentication failure but don't expose details
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"WebSocket connection rejected: Invalid or missing authentication token")
                await self.close(code=4001)  # Unauthorized
                return
            
            await self.accept()
            await self.add_to_group()
            
            # Handle since_event_id replay if provided
            query_string = self.scope.get('query_string', b'').decode()
            since_event_id = None
            if 'since_event_id=' in query_string:
                since_event_id = query_string.split('since_event_id=')[-1].split('&')[0]
            
            if since_event_id:
                await self.replay_events(since_event_id)
        except Exception as e:
            # Log error and close connection gracefully
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"WebSocket connection error: {str(e)}", exc_info=True)
            try:
                await self.close(code=1011)  # Internal error
            except:
                pass
    
    async def disconnect(self, close_code):
        """Handle disconnection"""
        await self.remove_from_group()
    
    async def authenticate(self):
        """Authenticate user from token"""
        try:
            # Get token from query string or headers
            query_string = self.scope.get('query_string', b'').decode()
            token = None
            
            if 'token=' in query_string:
                token = query_string.split('token=')[-1].split('&')[0]
            
            if not token:
                # Try to get from headers
                headers = dict(self.scope.get('headers', []))
                auth_header = headers.get(b'authorization', b'').decode()
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            if not token:
                return AnonymousUser()
            
            # Decode and validate token
            UntypedToken(token)
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get('user_id')
            
            if user_id:
                try:
                    user = await database_sync_to_async(User.objects.get)(id=user_id)
                    # Check if user is active and not deleted
                    if user.is_active and not user.is_deleted:
                        return user
                except User.DoesNotExist:
                    pass
        except (TokenError, InvalidToken) as e:
            # Token is invalid or expired
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"WebSocket authentication failed: {str(e)}")
        except Exception as e:
            # Other errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"WebSocket authentication error: {str(e)}", exc_info=True)
        
        return AnonymousUser()
    
    async def add_to_group(self):
        """Add to channel group - override in subclasses"""
        pass
    
    async def remove_from_group(self):
        """Remove from channel group - override in subclasses"""
        pass
    
    async def send_event(self, event_type, data, event_id=None):
        """Send standardized event"""
        import uuid
        from django.utils import timezone
        
        message = {
            'type': event_type,
            'data': data,
            'event_id': event_id or str(uuid.uuid4()),
            'timestamp': timezone.now().isoformat(),
            'version': '1.0'
        }
        await self.send_json(message)
    
    async def replay_events(self, since_event_id):
        """Replay events since the given event_id"""
        try:
            from apps.events.models import Event
            from apps.events.serializers import EventSerializer
            
            # Get events since the specified event_id (using timestamp comparison)
            # since_event_id can be a UUID or timestamp
            try:
                # Try to find the event by event_id to get its timestamp
                reference_event = await database_sync_to_async(Event.objects.filter(
                    event_id=since_event_id
                ).first)()
                
                if reference_event:
                    # Get events after this timestamp
                    events = await database_sync_to_async(list)(
                        Event.objects.filter(
                            timestamp__gt=reference_event.timestamp,
                            aggregate_type__in=self.get_relevant_aggregate_types()
                        ).order_by('timestamp')[:100]  # Limit to 100 most recent events
                    )
                else:
                    # If event not found, get events from last 24 hours
                    from django.utils import timezone
                    from datetime import timedelta
                    cutoff = timezone.now() - timedelta(hours=24)
                    events = await database_sync_to_async(list)(
                        Event.objects.filter(
                            timestamp__gt=cutoff,
                            aggregate_type__in=self.get_relevant_aggregate_types()
                        ).order_by('timestamp')[:100]
                    )
            except (ValueError, TypeError):
                # If since_event_id is not a valid UUID, get recent events
                from django.utils import timezone
                from datetime import timedelta
                cutoff = timezone.now() - timedelta(hours=24)
                events = await database_sync_to_async(list)(
                    Event.objects.filter(
                        timestamp__gt=cutoff,
                        aggregate_type__in=self.get_relevant_aggregate_types()
                    ).order_by('timestamp')[:100]
                )
            
            for event in events:
                serializer = EventSerializer(event)
                await self.send_event(
                    event_type=event.type,
                    data={
                        **serializer.data,
                        'payload': event.payload,
                    },
                    event_id=str(event.event_id)
                )
        except Exception as e:
            # Log error but don't fail connection
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to replay events: {str(e)}", exc_info=True)
    
    def get_relevant_aggregate_types(self):
        """Get aggregate types relevant to this consumer - override in subclasses"""
        return []


class RestaurantOrderConsumer(BaseConsumer):
    """Consumer for restaurant order updates"""
    
    async def add_to_group(self):
        restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.group_name = f'restaurant_{restaurant_id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
    
    async def remove_from_group(self):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    def get_relevant_aggregate_types(self):
        """Get aggregate types relevant to restaurant"""
        return ['Order', 'MenuItem', 'InventoryItem', 'Restaurant']
    
    # Order events
    async def order_created(self, event):
        """Send order created event"""
        await self.send_event('order.created', event['data'], event.get('event_id'))
    
    async def order_updated(self, event):
        """Send order updated event"""
        await self.send_event('order.updated', event['data'], event.get('event_id'))
    
    async def order_accepted(self, event):
        """Send order accepted event"""
        await self.send_event('order.accepted', event['data'], event.get('event_id'))
    
    async def order_rejected(self, event):
        """Send order rejected event"""
        await self.send_event('order.rejected', event['data'], event.get('event_id'))
    
    async def order_completed(self, event):
        """Send order completed event"""
        await self.send_event('order.completed', event['data'], event.get('event_id'))
    
    # Menu & inventory events
    async def menu_updated(self, event):
        """Send menu updated event"""
        await self.send_event('menu.updated', event['data'], event.get('event_id'))
    
    async def inventory_low(self, event):
        """Send inventory low alert"""
        await self.send_event('inventory_low', event['data'], event.get('event_id'))
    
    async def item_sold_out(self, event):
        """Send item sold out event"""
        await self.send_event('item_sold_out', event['data'], event.get('event_id'))
    
    # Delivery events
    async def delivery_assigned(self, event):
        """Send delivery assigned event"""
        await self.send_event('delivery.assigned', event['data'], event.get('event_id'))
    
    async def delivery_status_changed(self, event):
        """Send delivery status changed event"""
        await self.send_event('delivery.status_changed', event['data'], event.get('event_id'))
    
    async def rider_location(self, event):
        """Send rider location update"""
        await self.send_event('rider_location', event['data'], event.get('event_id'))
    
    # Alert events
    async def sla_breach(self, event):
        """Send SLA breach alert"""
        await self.send_event('sla_breach', event['data'], event.get('event_id'))
    
    async def restaurant_alert(self, event):
        """Send restaurant alert"""
        await self.send_event('restaurant_alert', event['data'], event.get('event_id'))
    
    async def restaurant_status(self, event):
        """Broadcast restaurant online/offline updates"""
        await self.send_event('restaurant_status', event['data'], event.get('event_id'))
    
    async def restaurant_high_rejection_rate(self, event):
        """Send high rejection rate alert"""
        await self.send_event('restaurant.high_rejection_rate', event['data'], event.get('event_id'))


class DeliveryConsumer(BaseConsumer):
    """Consumer for delivery rider updates"""
    
    async def add_to_group(self):
        rider_id = self.scope['url_route']['kwargs']['rider_id']
        self.group_name = f'delivery_{rider_id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
    
    async def remove_from_group(self):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    def get_relevant_aggregate_types(self):
        """Get aggregate types relevant to delivery"""
        return ['Delivery', 'DeliveryOffer', 'Order']
    
    # Job offer events
    async def job_offer(self, event):
        """Send new delivery job offer"""
        await self.send_event('job_offer', event['data'], event.get('event_id'))
    
    async def new_offer(self, event):
        """Send new delivery offer (alias for job_offer)"""
        await self.send_event('job_offer', event['data'], event.get('event_id'))
    
    async def offer_expired(self, event):
        """Send offer expiry notification"""
        await self.send_event('offer.expired', event['data'], event.get('event_id'))
    
    async def offer_accepted(self, event):
        """Send offer accepted confirmation"""
        await self.send_event('offer.accepted', event['data'], event.get('event_id'))
    
    async def offer_cancelled(self, event):
        """Send offer cancellation"""
        await self.send_event('offer.cancelled', event['data'], event.get('event_id'))
    
    # Delivery events
    async def order_assigned(self, event):
        """Send order assignment"""
        await self.send_event('delivery.assigned', event['data'], event.get('event_id'))
    
    async def delivery_assigned(self, event):
        """Send delivery assigned event"""
        await self.send_event('delivery.assigned', event['data'], event.get('event_id'))
    
    async def delivery_status_changed(self, event):
        """Send delivery status changed event"""
        await self.send_event('delivery.status_changed', event['data'], event.get('event_id'))
    
    async def order_updated(self, event):
        """Send order status update"""
        await self.send_event('order.updated', event['data'], event.get('event_id'))
    
    # Alert events
    async def surge_alert(self, event):
        """Send surge pricing alert"""
        await self.send_event('surge_alert', event['data'], event.get('event_id'))
    
    async def shift_reminder(self, event):
        """Send shift reminder"""
        await self.send_event('shift_reminder', event['data'], event.get('event_id'))
    
    async def high_priority_alert(self, event):
        """Send high priority alert"""
        await self.send_event('high_priority_alert', event['data'], event.get('event_id'))
    
    async def delivery_no_rider_available(self, event):
        """Send no rider available alert"""
        await self.send_event('delivery.no_rider_available', event['data'], event.get('event_id'))


class CustomerConsumer(BaseConsumer):
    """Consumer for customer updates"""
    
    async def add_to_group(self):
        customer_id = self.scope['url_route']['kwargs']['customer_id']
        self.group_name = f'customer_{customer_id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
    
    async def remove_from_group(self):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    def get_relevant_aggregate_types(self):
        """Get aggregate types relevant to customer"""
        return ['Order', 'Delivery', 'MenuItem', 'Payment', 'Refund', 'Promotion']
    
    # Order events
    async def order_created(self, event):
        """Send order created event"""
        await self.send_event('order.created', event['data'], event.get('event_id'))
    
    async def order_updated(self, event):
        """Send order status update"""
        await self.send_event('order.updated', event['data'], event.get('event_id'))
    
    async def order_accepted(self, event):
        """Send order accepted event"""
        await self.send_event('order.accepted', event['data'], event.get('event_id'))
    
    async def order_rejected(self, event):
        """Send order rejected event"""
        await self.send_event('order.rejected', event['data'], event.get('event_id'))
    
    async def order_completed(self, event):
        """Send order completed event"""
        await self.send_event('order.completed', event['data'], event.get('event_id'))
    
    # Delivery events
    async def rider_assigned(self, event):
        """Send rider assignment"""
        await self.send_event('delivery.assigned', event['data'], event.get('event_id'))
    
    async def delivery_assigned(self, event):
        """Send delivery assigned event"""
        await self.send_event('delivery.assigned', event['data'], event.get('event_id'))
    
    async def delivery_status_changed(self, event):
        """Send delivery status changed event"""
        await self.send_event('delivery.status_changed', event['data'], event.get('event_id'))
    
    async def rider_location(self, event):
        """Send rider location update"""
        await self.send_event('rider_location', event['data'], event.get('event_id'))
    
    # Menu events
    async def menu_updated(self, event):
        """Send menu availability update"""
        await self.send_event('menu.updated', event['data'], event.get('event_id'))
    
    async def item_sold_out(self, event):
        """Send item sold out event"""
        await self.send_event('item_sold_out', event['data'], event.get('event_id'))
    
    # Payment events
    async def payment_captured(self, event):
        """Send payment captured event"""
        await self.send_event('payment.captured', event['data'], event.get('event_id'))
    
    async def payment_failed(self, event):
        """Send payment failed event"""
        await self.send_event('payment.failed', event['data'], event.get('event_id'))
    
    async def refund_initiated(self, event):
        """Send refund initiated event"""
        await self.send_event('refund.initiated', event['data'], event.get('event_id'))
    
    async def refund_completed(self, event):
        """Send refund completed event"""
        await self.send_event('refund.completed', event['data'], event.get('event_id'))
    
    # Promotion events
    async def promo_published(self, event):
        """Send promotion published event"""
        await self.send_event('promo.published', event['data'], event.get('event_id'))


class AdminConsumer(BaseConsumer):
    """Consumer for admin updates"""
    
    async def add_to_group(self):
        self.group_name = 'admin'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
    
    async def remove_from_group(self):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    def get_relevant_aggregate_types(self):
        """Get all aggregate types for admin"""
        return ['Order', 'Delivery', 'Payment', 'Refund', 'Restaurant', 'MenuItem', 'InventoryItem', 'Payout', 'SettlementCycle', 'Fraud']
    
    # Order events
    async def order_created(self, event):
        """Send order created event"""
        await self.send_event('order.created', event['data'], event.get('event_id'))
    
    async def order_updated(self, event):
        """Send order updated event"""
        await self.send_event('order.updated', event['data'], event.get('event_id'))
    
    async def order_accepted(self, event):
        """Send order accepted event"""
        await self.send_event('order.accepted', event['data'], event.get('event_id'))
    
    async def order_rejected(self, event):
        """Send order rejected event"""
        await self.send_event('order.rejected', event['data'], event.get('event_id'))
    
    async def order_completed(self, event):
        """Send order completed event"""
        await self.send_event('order.completed', event['data'], event.get('event_id'))
    
    # Alert events
    async def system_alert(self, event):
        """Send system alert"""
        await self.send_event('system_alert', event['data'], event.get('event_id'))
    
    async def restaurant_alert(self, event):
        """Forward restaurant alert to admin"""
        await self.send_event('restaurant_alert', event['data'], event.get('event_id'))
    
    async def restaurant_high_rejection_rate(self, event):
        """Send high rejection rate alert"""
        await self.send_event('restaurant.high_rejection_rate', event['data'], event.get('event_id'))
    
    async def fraud_alert(self, event):
        """Send fraud alert"""
        await self.send_event('fraud.alert', event['data'], event.get('event_id'))
    
    async def inventory_low(self, event):
        """Send inventory low alert"""
        await self.send_event('inventory_low', event['data'], event.get('event_id'))
    
    # Payment events
    async def payment_failed(self, event):
        """Send payment failed event"""
        await self.send_event('payment.failed', event['data'], event.get('event_id'))
    
    async def payout_completed(self, event):
        """Send payout completed event"""
        await self.send_event('payout.completed', event['data'], event.get('event_id'))
    
    async def payout_failed(self, event):
        """Send payout failed event"""
        await self.send_event('payout.failed', event['data'], event.get('event_id'))
    
    # Delivery events
    async def delivery_no_rider_available(self, event):
        """Send no rider available alert"""
        await self.send_event('delivery.no_rider_available', event['data'], event.get('event_id'))


class ChatConsumer(BaseConsumer):
    """Consumer for real-time chat"""
    
    async def add_to_group(self):
        room_id = self.scope['url_route']['kwargs']['room_id']
        self.group_name = f'chat_room_{room_id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
    
    async def remove_from_group(self):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive_json(self, content):
        """Handle incoming messages"""
        message_type = content.get('type')
        
        if message_type == 'send_message':
            # Save message via database
            room_id = self.scope['url_route']['kwargs']['room_id']
            message_content = content.get('content', '')
            message_type = content.get('message_type', 'TEXT')
            
            # Create message in database
            from apps.chat.models import ChatRoom, ChatMessage
            from django.utils import timezone
            
            room = await database_sync_to_async(ChatRoom.objects.get)(id=room_id)
            
            # Check permissions
            if self.user not in [room.customer, room.restaurant, room.courier, room.support_agent]:
                await self.send_json({
                    'type': 'error',
                    'message': 'Permission denied'
                })
                return
            
            message = await database_sync_to_async(ChatMessage.objects.create)(
                room=room,
                sender=self.user,
                message_type=message_type,
                content=message_content,
            )
            
            # Update room's last message time
            room.last_message_at = timezone.now()
            await database_sync_to_async(room.save)()
            
            # Serialize message
            from apps.chat.serializers import ChatMessageSerializer
            
            # Create a simple context for serialization
            class SimpleRequest:
                def __init__(self, user):
                    self.user = user
                    self.build_absolute_uri = lambda url: url
            
            request = SimpleRequest(self.user)
            serializer = ChatMessageSerializer(message, context={'request': request})
            
            # Broadcast to all participants
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'chat_message',
                    'message': serializer.data
                }
            )
        
        elif message_type == 'typing':
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'user_name': self.user.get_full_name() or self.user.email,
                    'is_typing': content.get('is_typing', True)
                }
            )
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        await self.send_json({
            'type': 'chat_message',
            'data': event['message']
        })
    
    async def typing_indicator(self, event):
        """Send typing indicator"""
        await self.send_json({
            'type': 'typing',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'is_typing': event['is_typing']
        })