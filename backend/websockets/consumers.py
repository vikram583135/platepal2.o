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
        self.user = await self.authenticate()
        if not self.user or isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        await self.accept()
        await self.add_to_group()
    
    async def disconnect(self, close_code):
        """Handle disconnection"""
        await self.remove_from_group()
    
    async def authenticate(self):
        """Authenticate user from token"""
        try:
            # Get token from query string or headers
            token = self.scope.get('query_string', b'').decode().split('token=')[-1].split('&')[0]
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
                return await database_sync_to_async(User.objects.get)(id=user_id)
        except (TokenError, InvalidToken, User.DoesNotExist, Exception):
            pass
        
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
    
    async def order_created(self, event):
        """Send order created event"""
        await self.send_event('order_created', event['data'], event.get('event_id'))
    
    async def order_updated(self, event):
        """Send order updated event"""
        await self.send_event('order_updated', event['data'], event.get('event_id'))
    
    async def menu_updated(self, event):
        """Send menu updated event"""
        await self.send_event('menu_updated', event['data'], event.get('event_id'))
    
    async def inventory_low(self, event):
        """Send inventory low alert"""
        await self.send_event('inventory_low', event['data'], event.get('event_id'))
    
    async def sla_breach(self, event):
        """Send SLA breach alert"""
        await self.send_event('sla_breach', event['data'], event.get('event_id'))
    
    async def restaurant_alert(self, event):
        """Send restaurant alert"""
        await self.send_event('restaurant_alert', event['data'], event.get('event_id'))
    
    async def restaurant_status(self, event):
        """Broadcast restaurant online/offline updates"""
        await self.send_event('restaurant_status', event['data'], event.get('event_id'))


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
    
    async def order_assigned(self, event):
        """Send order assignment"""
        await self.send_event('order_assigned', event['data'], event.get('event_id'))
    
    async def order_updated(self, event):
        """Send order status update"""
        await self.send_event('order_updated', event['data'], event.get('event_id'))
    
    async def new_offer(self, event):
        """Send new delivery offer"""
        await self.send_event('new_offer', event['data'], event.get('event_id'))
    
    async def offer_expired(self, event):
        """Send offer expiry notification"""
        await self.send_event('offer_expired', event['data'], event.get('event_id'))
    
    async def offer_accepted(self, event):
        """Send offer accepted confirmation"""
        await self.send_event('offer_accepted', event['data'], event.get('event_id'))
    
    async def offer_cancelled(self, event):
        """Send offer cancellation"""
        await self.send_event('offer_cancelled', event['data'], event.get('event_id'))
    
    async def surge_alert(self, event):
        """Send surge pricing alert"""
        await self.send_event('surge_alert', event['data'], event.get('event_id'))
    
    async def shift_reminder(self, event):
        """Send shift reminder"""
        await self.send_event('shift_reminder', event['data'], event.get('event_id'))
    
    async def high_priority_alert(self, event):
        """Send high priority alert"""
        await self.send_event('high_priority_alert', event['data'], event.get('event_id'))


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
    
    async def order_updated(self, event):
        """Send order status update"""
        await self.send_event('order_updated', event['data'], event.get('event_id'))
    
    async def rider_assigned(self, event):
        """Send rider assignment"""
        await self.send_event('rider_assigned', event['data'], event.get('event_id'))
    
    async def rider_location(self, event):
        """Send rider location update"""
        await self.send_event('rider_location', event['data'], event.get('event_id'))
    
    async def menu_updated(self, event):
        """Send menu availability update"""
        await self.send_event('menu_updated', event['data'], event.get('event_id'))


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
    
    async def order_created(self, event):
        """Send order created event"""
        await self.send_event('order_created', event['data'], event.get('event_id'))
    
    async def order_updated(self, event):
        """Send order updated event"""
        await self.send_event('order_updated', event['data'], event.get('event_id'))
    
    async def system_alert(self, event):
        """Send system alert"""
        await self.send_event('system_alert', event['data'], event.get('event_id'))
    
    async def restaurant_alert(self, event):
        """Forward restaurant alert to admin"""
        await self.send_event('restaurant_alert', event['data'], event.get('event_id'))


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