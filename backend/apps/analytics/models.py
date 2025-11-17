from django.db import models
from apps.accounts.models import User, TimestampMixin
from apps.restaurants.models import Restaurant
from apps.orders.models import Order


class AnalyticsEvent(TimestampMixin):
    """Analytics events tracking"""
    
    class EventType(models.TextChoices):
        PAGE_VIEW = 'PAGE_VIEW', 'Page View'
        RESTAURANT_VIEW = 'RESTAURANT_VIEW', 'Restaurant View'
        MENU_VIEW = 'MENU_VIEW', 'Menu View'
        ADD_TO_CART = 'ADD_TO_CART', 'Add to Cart'
        REMOVE_FROM_CART = 'REMOVE_FROM_CART', 'Remove from Cart'
        CHECKOUT_START = 'CHECKOUT_START', 'Checkout Started'
        ORDER_PLACED = 'ORDER_PLACED', 'Order Placed'
        SEARCH = 'SEARCH', 'Search'
        FILTER_APPLIED = 'FILTER_APPLIED', 'Filter Applied'
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_events')
    event_type = models.CharField(max_length=50, choices=EventType.choices)
    properties = models.JSONField(default=dict)  # Event properties
    session_id = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'analytics_events'
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.user or 'Anonymous'}"

