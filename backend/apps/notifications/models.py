from django.db import models
from apps.accounts.models import User, TimestampMixin, SoftDeleteMixin


class Notification(TimestampMixin, SoftDeleteMixin):
    """User notifications"""
    
    class NotificationType(models.TextChoices):
        ORDER_PLACED = 'ORDER_PLACED', 'Order Placed'
        ORDER_ACCEPTED = 'ORDER_ACCEPTED', 'Order Accepted'
        ORDER_READY = 'ORDER_READY', 'Order Ready'
        ORDER_OUT_FOR_DELIVERY = 'ORDER_OUT_FOR_DELIVERY', 'Out for Delivery'
        ORDER_DELIVERED = 'ORDER_DELIVERED', 'Order Delivered'
        ORDER_CANCELLED = 'ORDER_CANCELLED', 'Order Cancelled'
        PAYMENT_SUCCESS = 'PAYMENT_SUCCESS', 'Payment Successful'
        PAYMENT_FAILED = 'PAYMENT_FAILED', 'Payment Failed'
        PROMOTION = 'PROMOTION', 'Promotion'
        REVIEW_REQUEST = 'REVIEW_REQUEST', 'Review Request'
        SYSTEM = 'SYSTEM', 'System Notification'
        # Delivery rider notifications
        DELIVERY_OFFER = 'DELIVERY_OFFER', 'New Delivery Offer'
        DELIVERY_OFFER_EXPIRED = 'DELIVERY_OFFER_EXPIRED', 'Delivery Offer Expired'
        DELIVERY_CANCELLED = 'DELIVERY_CANCELLED', 'Delivery Cancelled'
        SHIFT_REMINDER = 'SHIFT_REMINDER', 'Shift Reminder'
        SURGE_ALERT = 'SURGE_ALERT', 'Surge Pricing Alert'
        EARNINGS_PAYOUT = 'EARNINGS_PAYOUT', 'Earnings Payout'
        DOCUMENT_EXPIRY = 'DOCUMENT_EXPIRY', 'Document Expiry Reminder'
        HIGH_PRIORITY_ALERT = 'HIGH_PRIORITY_ALERT', 'High Priority Alert'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict)  # Additional data (order_id, etc.)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery channels
    sent_via_email = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)
    sent_via_push = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'notifications'
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['type']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.type} - {self.user.email}"


class NotificationPreference(TimestampMixin):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email preferences
    email_order_updates = models.BooleanField(default=True)
    email_promotions = models.BooleanField(default=True)
    email_payment_updates = models.BooleanField(default=True)
    email_review_requests = models.BooleanField(default=True)
    email_system_notifications = models.BooleanField(default=True)
    
    # SMS preferences
    sms_order_updates = models.BooleanField(default=False)
    sms_promotions = models.BooleanField(default=False)
    sms_payment_updates = models.BooleanField(default=False)
    
    # Push notification preferences
    push_order_updates = models.BooleanField(default=True)
    push_promotions = models.BooleanField(default=True)
    push_payment_updates = models.BooleanField(default=True)
    push_review_requests = models.BooleanField(default=True)
    push_system_notifications = models.BooleanField(default=True)
    push_delivery_offers = models.BooleanField(default=True)
    push_surge_alerts = models.BooleanField(default=True)
    push_shift_reminders = models.BooleanField(default=True)
    
    # Sound alerts (for riders)
    sound_alerts_enabled = models.BooleanField(default=True)
    offer_sound_enabled = models.BooleanField(default=True)
    surge_sound_enabled = models.BooleanField(default=True)
    
    # Quiet hours (no notifications during these hours)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)  # e.g., 22:00
    quiet_hours_end = models.TimeField(null=True, blank=True)  # e.g., 08:00
    
    # Snooze/DND
    snooze_mode_enabled = models.BooleanField(default=False)
    snooze_until = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
