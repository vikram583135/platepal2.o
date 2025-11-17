"""
Views for chat app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import ChatRoom, ChatMessage, ChatTemplate, MaskedCall
from .serializers import ChatRoomSerializer, ChatMessageSerializer, ChatTemplateSerializer, MaskedCallSerializer
from apps.orders.models import Order
from apps.deliveries.services import mask_phone_number
from apps.accounts.models import User


class ChatRoomViewSet(viewsets.ModelViewSet):
    """Chat room viewset"""
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Customers see their own rooms
        if user.role == 'CUSTOMER':
            return ChatRoom.objects.filter(
                customer=user,
                is_active=True,
                is_deleted=False
            ).order_by('-last_message_at', '-created_at')
        
        # Restaurants see rooms for their orders
        elif user.role == 'RESTAURANT':
            return ChatRoom.objects.filter(
                restaurant=user,
                is_active=True,
                is_deleted=False
            ).order_by('-last_message_at', '-created_at')
        
        # Couriers see rooms for their deliveries
        elif user.role == 'DELIVERY':
            return ChatRoom.objects.filter(
                courier=user,
                is_active=True,
                is_deleted=False
            ).order_by('-last_message_at', '-created_at')
        
        # Support/Admin see all rooms
        elif user.role in ['ADMIN', 'SUPPORT']:
            return ChatRoom.objects.filter(
                is_active=True,
                is_deleted=False
            ).order_by('-last_message_at', '-created_at')
        
        return ChatRoom.objects.none()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_or_get(self, request):
        """Create or get chat room for order"""
        order_id = request.data.get('order_id')
        room_type = request.data.get('room_type', ChatRoom.RoomType.ORDER)
        
        if not order_id:
            return Response({'error': 'Order ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order = Order.objects.get(id=order_id, is_deleted=False)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions
        if request.user.role == 'CUSTOMER' and order.customer != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'RESTAURANT' and order.restaurant.owner != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'DELIVERY' and order.courier != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get or create room
        room, created = ChatRoom.objects.get_or_create(
            order=order,
            room_type=room_type,
            defaults={
                'customer': order.customer,
                'restaurant': order.restaurant.owner if order.restaurant else None,
                'courier': order.courier,
                'is_active': True,
            }
        )
        
        serializer = self.get_serializer(room)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_support_room(self, request):
        """Create support chat room"""
        if request.user.role != 'CUSTOMER':
            return Response({'error': 'Only customers can create support rooms'}, status=status.HTTP_403_FORBIDDEN)
        
        room = ChatRoom.objects.create(
            room_type=ChatRoom.RoomType.SUPPORT,
            customer=request.user,
            is_active=True,
        )
        
        serializer = self.get_serializer(room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_read(self, request, pk=None):
        """Mark all messages in room as read"""
        room = self.get_object()
        
        # Check permissions
        if request.user not in [room.customer, room.restaurant, room.courier, room.support_agent]:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        ChatMessage.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=request.user).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({'message': 'Messages marked as read'})


class ChatMessageViewSet(viewsets.ModelViewSet):
    """Chat message viewset"""
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        room_id = self.request.query_params.get('room_id')
        if room_id:
            return ChatMessage.objects.filter(
                room_id=room_id,
                is_deleted=False
            ).order_by('created_at')
        return ChatMessage.objects.none()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        room = serializer.validated_data['room']
        
        # Check permissions
        if self.request.user not in [room.customer, room.restaurant, room.courier, room.support_agent]:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not have permission to send messages in this room')
        
        message = serializer.save(sender=self.request.user)
        
        # Update room's last message time
        room.last_message_at = timezone.now()
        room.save()
        
        # Broadcast message via WebSocket
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_room_{room.id}',
            {
                'type': 'chat_message',
                'message': ChatMessageSerializer(message, context={'request': self.request}).data
            }
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        
        if message.sender == request.user:
            return Response({'message': 'Cannot mark own message as read'})
        
        message.is_read = True
        message.read_at = timezone.now()
        message.save()
        
        return Response(ChatMessageSerializer(message, context={'request': request}).data)


class ChatTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """Chat template viewset (read-only for riders, full access for admins)"""
    serializer_class = ChatTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        category = self.request.query_params.get('category')
        
        queryset = ChatTemplate.objects.filter(is_deleted=False)
        
        if category:
            queryset = queryset.filter(category=category)
        
        if user.role == 'ADMIN':
            return queryset
        else:
            # Riders can see templates for their role
            if user.role == 'DELIVERY':
                return queryset.filter(category__in=[
                    ChatTemplate.TemplateCategory.RIDER_CUSTOMER,
                    ChatTemplate.TemplateCategory.RIDER_RESTAURANT,
                    ChatTemplate.TemplateCategory.DISPATCH,
                    ChatTemplate.TemplateCategory.GENERAL
                ])
            elif user.role == 'RESTAURANT':
                return queryset.filter(category__in=[
                    ChatTemplate.TemplateCategory.RIDER_RESTAURANT,
                    ChatTemplate.TemplateCategory.GENERAL
                ])
            elif user.role == 'CUSTOMER':
                return queryset.filter(category__in=[
                    ChatTemplate.TemplateCategory.RIDER_CUSTOMER,
                    ChatTemplate.TemplateCategory.GENERAL
                ])
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Mark template as used (increment usage count)"""
        template = self.get_object()
        template.usage_count += 1
        template.save()
        serializer = self.get_serializer(template)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def for_trigger(self, request):
        """Get templates for a specific auto-trigger"""
        trigger = request.query_params.get('trigger')
        if not trigger:
            return Response({'error': 'trigger parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        templates = ChatTemplate.objects.filter(
            is_auto_template=True,
            auto_trigger=trigger,
            is_deleted=False
        ).order_by('display_order')
        
        serializer = self.get_serializer(templates, many=True)
        return Response(serializer.data)


class MaskedCallViewSet(viewsets.ModelViewSet):
    """Masked call viewset"""
    serializer_class = MaskedCallSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return MaskedCall.objects.all()
        return MaskedCall.objects.filter(
            Q(caller=user) | Q(recipient=user)
        )
    
    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate a masked call"""
        from apps.deliveries.services import mask_phone_number
        
        call_type = request.data.get('call_type')
        recipient_id = request.data.get('recipient_id')
        order_id = request.data.get('order_id')
        
        if not call_type or not recipient_id:
            return Response({'error': 'call_type and recipient_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            recipient = User.objects.get(id=recipient_id)
        except User.DoesNotExist:
            return Response({'error': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        order = None
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Mask phone numbers
        caller_masked = mask_phone_number(request.user.phone) if request.user.phone else "***-***-****"
        recipient_masked = mask_phone_number(recipient.phone) if recipient.phone else "***-***-****"
        
        # Create masked call record
        masked_call = MaskedCall.objects.create(
            caller=request.user,
            recipient=recipient,
            order=order,
            call_type=call_type,
            caller_masked_number=caller_masked,
            recipient_masked_number=recipient_masked,
            status='INITIATED',
            started_at=timezone.now()
        )
        
        # In production, integrate with phone service provider (Twilio, etc.)
        # For now, return the masked numbers
        serializer = self.get_serializer(masked_call)
        return Response({
            'masked_call': serializer.data,
            'caller_masked_number': caller_masked,
            'recipient_masked_number': recipient_masked,
            'message': 'Use these masked numbers to make the call via external service'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """End a masked call"""
        masked_call = self.get_object()
        
        if masked_call.caller != request.user and masked_call.recipient != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        masked_call.status = 'ENDED'
        masked_call.ended_at = timezone.now()
        
        if masked_call.started_at:
            duration = masked_call.ended_at - masked_call.started_at
            masked_call.duration_seconds = int(duration.total_seconds())
        
        masked_call.save()
        
        serializer = self.get_serializer(masked_call)
        return Response(serializer.data)

