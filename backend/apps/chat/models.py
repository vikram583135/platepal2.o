"""
Chat models for in-app messaging
"""
from django.db import models
from apps.accounts.models import User, TimestampMixin, SoftDeleteMixin
from apps.orders.models import Order


class ChatRoom(TimestampMixin, SoftDeleteMixin):
    """Chat room for conversations"""
    
    class RoomType(models.TextChoices):
        ORDER = 'ORDER', 'Order Chat'
        RESTAURANT = 'RESTAURANT', 'Restaurant Support'
        COURIER = 'COURIER', 'Courier Chat'
        SUPPORT = 'SUPPORT', 'Customer Support'
        RIDER_CUSTOMER = 'RIDER_CUSTOMER', 'Rider-Customer Chat'
        RIDER_RESTAURANT = 'RIDER_RESTAURANT', 'Rider-Restaurant Chat'
        DISPATCH = 'DISPATCH', 'Dispatch Chat'
    
    room_type = models.CharField(max_length=20, choices=RoomType.choices)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='chat_rooms', null=True, blank=True)
    
    # Participants
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_chat_rooms', limit_choices_to={'role': 'CUSTOMER'})
    restaurant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restaurant_chat_rooms', null=True, blank=True, limit_choices_to={'role': 'RESTAURANT'})
    courier = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courier_chat_rooms', null=True, blank=True, limit_choices_to={'role': 'DELIVERY'})
    support_agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_chat_rooms', null=True, blank=True, limit_choices_to={'role__in': ['ADMIN', 'SUPPORT']})
    
    # Status
    is_active = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'chat_rooms'
        indexes = [
            models.Index(fields=['customer', 'is_active']),
            models.Index(fields=['order', 'room_type']),
            models.Index(fields=['last_message_at']),
        ]
        unique_together = [
            ['order', 'room_type'],  # One room per order per type
        ]
    
    def __str__(self):
        if self.order:
            return f"Chat for Order {self.order.order_number} ({self.room_type})"
        return f"Chat {self.room_type} - {self.customer.email}"


class ChatMessage(TimestampMixin, SoftDeleteMixin):
    """Individual chat messages"""
    
    class MessageType(models.TextChoices):
        TEXT = 'TEXT', 'Text'
        IMAGE = 'IMAGE', 'Image'
        FILE = 'FILE', 'File'
        SYSTEM = 'SYSTEM', 'System Message'
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_chat_messages')
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    file_url = models.URLField(blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'chat_messages'
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['is_read']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.email} in {self.room}"


class ChatTemplate(TimestampMixin, SoftDeleteMixin):
    """Chat message templates for quick replies"""
    
    class TemplateCategory(models.TextChoices):
        RIDER_CUSTOMER = 'RIDER_CUSTOMER', 'Rider-Customer'
        RIDER_RESTAURANT = 'RIDER_RESTAURANT', 'Rider-Restaurant'
        DISPATCH = 'DISPATCH', 'Dispatch'
        GENERAL = 'GENERAL', 'General'
    
    category = models.CharField(max_length=50, choices=TemplateCategory.choices)
    title = models.CharField(max_length=255)  # Short title for quick selection
    message = models.TextField()  # Template message
    
    # Auto-templates (system generated)
    is_auto_template = models.BooleanField(default=False)  # True for auto-generated templates
    auto_trigger = models.CharField(max_length=50, blank=True)  # When to auto-suggest (e.g., 'REACHED_PICKUP')
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    
    # Order
    display_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'chat_templates'
        indexes = [
            models.Index(fields=['category', 'display_order']),
            models.Index(fields=['is_auto_template', 'auto_trigger']),
        ]
        ordering = ['category', 'display_order']
    
    def __str__(self):
        return f"{self.category} - {self.title}"


class MaskedCall(TimestampMixin):
    """Masked phone call tracking for rider-customer/restaurant communication"""
    
    class CallType(models.TextChoices):
        RIDER_CUSTOMER = 'RIDER_CUSTOMER', 'Rider-Customer'
        RIDER_RESTAURANT = 'RIDER_RESTAURANT', 'Rider-Restaurant'
        DISPATCH_RIDER = 'DISPATCH_RIDER', 'Dispatch-Rider'
    
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='masked_calls_made')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='masked_calls_received', null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='masked_calls', null=True, blank=True)
    
    call_type = models.CharField(max_length=50, choices=CallType.choices)
    
    # Masked numbers
    caller_masked_number = models.CharField(max_length=20)
    recipient_masked_number = models.CharField(max_length=20)
    
    # Call details
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, default='INITIATED')  # INITIATED, CONNECTED, ENDED, FAILED
    
    # Provider details (if using external service like Twilio)
    provider_call_id = models.CharField(max_length=100, blank=True)
    provider_data = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'masked_calls'
        indexes = [
            models.Index(fields=['caller', '-started_at']),
            models.Index(fields=['recipient', '-started_at']),
            models.Index(fields=['order', 'call_type']),
            models.Index(fields=['started_at']),
        ]
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Masked call {self.call_type} - {self.caller.email} to {self.recipient.email if self.recipient else 'Unknown'}"


