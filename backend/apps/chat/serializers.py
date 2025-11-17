"""
Serializers for chat app
"""
from rest_framework import serializers
from .models import ChatRoom, ChatMessage, ChatTemplate, MaskedCall
from apps.accounts.serializers import UserSerializer


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    sender_photo = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = ('id', 'room', 'sender', 'sender_name', 'sender_email', 'sender_photo',
                  'message_type', 'content', 'image_url', 'file_url', 'is_read', 'read_at', 'created_at')
        read_only_fields = ('id', 'sender', 'is_read', 'read_at', 'created_at')
    
    def get_sender_photo(self, obj):
        if obj.sender.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.sender.profile_photo.url)
            return obj.sender.profile_photo.url
        return None


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for chat rooms"""
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.get_full_name', read_only=True)
    restaurant_phone = serializers.CharField(source='restaurant.phone', read_only=True)
    courier_name = serializers.CharField(source='courier.get_full_name', read_only=True)
    courier_phone = serializers.CharField(source='courier.phone', read_only=True)
    support_agent_name = serializers.CharField(source='support_agent.get_full_name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ('id', 'room_type', 'order', 'order_number',
                  'customer', 'customer_name', 'customer_phone',
                  'restaurant', 'restaurant_name', 'restaurant_phone',
                  'courier', 'courier_name', 'courier_phone',
                  'support_agent', 'support_agent_name',
                  'is_active', 'last_message_at',
                  'last_message', 'unread_count', 'created_at')
        read_only_fields = ('id', 'last_message_at', 'created_at')
    
    def get_last_message(self, obj):
        last_msg = obj.messages.filter(is_deleted=False).order_by('-created_at').first()
        if last_msg:
            return ChatMessageSerializer(last_msg, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(is_deleted=False, is_read=False).exclude(sender=request.user).count()
        return 0


class ChatTemplateSerializer(serializers.ModelSerializer):
    """Chat template serializer"""
    
    class Meta:
        model = ChatTemplate
        fields = ('id', 'category', 'title', 'message', 'is_auto_template',
                  'auto_trigger', 'usage_count', 'display_order', 'created_at', 'updated_at')
        read_only_fields = ('id', 'usage_count', 'created_at', 'updated_at')


class MaskedCallSerializer(serializers.ModelSerializer):
    """Masked call serializer"""
    caller_email = serializers.EmailField(source='caller.email', read_only=True)
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = MaskedCall
        fields = ('id', 'caller', 'caller_email', 'recipient', 'recipient_email',
                  'order', 'order_number', 'call_type', 'caller_masked_number',
                  'recipient_masked_number', 'started_at', 'ended_at', 'duration_seconds',
                  'status', 'provider_call_id', 'provider_data', 'created_at', 'updated_at')
        read_only_fields = ('id', 'caller', 'recipient', 'started_at', 'ended_at',
                           'duration_seconds', 'status', 'created_at', 'updated_at')

