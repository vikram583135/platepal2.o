from django.db import models
from apps.accounts.models import User, TimestampMixin, SoftDeleteMixin


class SupportTicket(TimestampMixin, SoftDeleteMixin):
    """Customer support tickets"""
    
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'
    
    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        URGENT = 'URGENT', 'Urgent'
    
    class Category(models.TextChoices):
        ORDER_ISSUE = 'ORDER_ISSUE', 'Order Issue'
        PAYMENT_ISSUE = 'PAYMENT_ISSUE', 'Payment Issue'
        DELIVERY_ISSUE = 'DELIVERY_ISSUE', 'Delivery Issue'
        REFUND_REQUEST = 'REFUND_REQUEST', 'Refund Request'
        ACCOUNT_ISSUE = 'ACCOUNT_ISSUE', 'Account Issue'
        TECHNICAL_ISSUE = 'TECHNICAL_ISSUE', 'Technical Issue'
        FEEDBACK = 'FEEDBACK', 'Feedback'
        OTHER = 'OTHER', 'Other'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_tickets')
    ticket_number = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, choices=Category.choices)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    
    # Related entities
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', limit_choices_to={'role': 'ADMIN'})
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_tickets', limit_choices_to={'role': 'ADMIN'})
    
    class Meta:
        db_table = 'support_tickets'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['ticket_number']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.subject}"


class TicketMessage(TimestampMixin):
    """Messages in support tickets"""
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_messages')
    message = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal notes (not visible to customer)
    attachments = models.JSONField(default=list)  # URLs to attached files
    
    class Meta:
        db_table = 'ticket_messages'
        indexes = [
            models.Index(fields=['ticket', '-created_at']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message in {self.ticket.ticket_number}"


class ChatBotMessage(TimestampMixin):
    """Chatbot conversation history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chatbot_messages', null=True, blank=True)
    session_id = models.CharField(max_length=255)  # For guest users
    message = models.TextField()
    is_from_user = models.BooleanField(default=True)
    intent = models.CharField(max_length=100, blank=True)  # Detected intent
    confidence = models.FloatField(null=True, blank=True)  # Confidence score
    
    class Meta:
        db_table = 'chatbot_messages'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_id', '-created_at']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"Chat message from {self.user.email if self.user else 'Guest'}"

