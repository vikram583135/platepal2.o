"""
Serializers for support app
"""
from rest_framework import serializers
from .models import SupportTicket, TicketMessage, ChatBotMessage


class TicketMessageSerializer(serializers.ModelSerializer):
    """Ticket message serializer"""
    user_name = serializers.SerializerMethodField()
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = TicketMessage
        fields = ('id', 'ticket', 'user', 'user_name', 'user_email', 'message', 'is_internal',
                  'attachments', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class SupportTicketSerializer(serializers.ModelSerializer):
    """Support ticket serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = ('id', 'ticket_number', 'user', 'user_email', 'user_name', 'category', 'subject',
                  'description', 'status', 'priority', 'order', 'order_number', 'assigned_to',
                  'assigned_to_email', 'resolved_at', 'resolved_by', 'messages', 'created_at', 'updated_at')
        read_only_fields = ('id', 'ticket_number', 'user', 'assigned_to', 'resolved_at', 'resolved_by',
                           'created_at', 'updated_at')
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # Generate ticket number
        import uuid
        from datetime import datetime
        ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        validated_data['ticket_number'] = ticket_number
        
        return super().create(validated_data)


class ChatBotMessageSerializer(serializers.ModelSerializer):
    """Chatbot message serializer"""
    
    class Meta:
        model = ChatBotMessage
        fields = ('id', 'user', 'session_id', 'message', 'is_from_user', 'intent', 'confidence', 'created_at')
        read_only_fields = ('id', 'created_at')

