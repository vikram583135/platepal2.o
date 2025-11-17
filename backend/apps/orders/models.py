from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.accounts.models import User, Address, TimestampMixin, SoftDeleteMixin
from apps.restaurants.models import Restaurant, MenuItem, ItemModifier, Promotion


class Order(TimestampMixin, SoftDeleteMixin):
    """Order model"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        PREPARING = 'PREPARING', 'Preparing'
        READY = 'READY', 'Ready for Pickup'
        ASSIGNED = 'ASSIGNED', 'Assigned to Rider'
        PICKED_UP = 'PICKED_UP', 'Picked Up'
        OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', 'Out for Delivery'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'
    
    class OrderType(models.TextChoices):
        DELIVERY = 'DELIVERY', 'Delivery'
        PICKUP = 'PICKUP', 'Pickup'
    
    class PriorityTag(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        RUSH = 'RUSH', 'Rush'
        VIP = 'VIP', 'VIP'
    
    # Relations
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Order details
    order_number = models.CharField(max_length=50, unique=True)  # e.g., ORD-2024-001234
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    order_type = models.CharField(max_length=20, choices=OrderType.choices, default=OrderType.DELIVERY)
    priority_tag = models.CharField(max_length=20, choices=PriorityTag.choices, default=PriorityTag.NORMAL)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Promotions
    promotion = models.ForeignKey(Promotion, on_delete=models.SET_NULL, null=True, blank=True)
    promo_code = models.CharField(max_length=50, blank=True)
    
    # Timestamps for tracking
    accepted_at = models.DateTimeField(null=True, blank=True)
    preparing_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Estimates
    estimated_preparation_time = models.IntegerField(null=True, blank=True)  # minutes
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    prep_time_override_minutes = models.IntegerField(null=True, blank=True)
    
    # Notes
    special_instructions = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    kitchen_notes = models.TextField(blank=True)
    internal_cooking_notes = models.TextField(blank=True)
    
    # Scheduled orders
    is_scheduled = models.BooleanField(default=False)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    
    # Safety features
    contactless_delivery = models.BooleanField(default=False)
    delivery_otp = models.CharField(max_length=6, blank=True)
    delivery_otp_verified = models.BooleanField(default=False)
    
    # Courier assignment
    courier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_orders', limit_choices_to={'role': 'DELIVERY'})
    courier_phone = models.CharField(max_length=20, blank=True)
    
    # Operational metadata
    combined_parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='combined_children')
    sla_breached = models.BooleanField(default=False)
    sla_breach_reason = models.CharField(max_length=255, blank=True)
    print_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'orders'
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['restaurant', 'priority_tag']),
            models.Index(fields=['order_number']),
            models.Index(fields=['created_at', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['sla_breached']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.email}"
    
    def calculate_total(self):
        """Calculate total amount"""
        # Ensure all values are Decimal to avoid type errors
        subtotal = Decimal(str(self.subtotal or 0))
        tax_amount = Decimal(str(self.tax_amount or 0))
        delivery_fee = Decimal(str(self.delivery_fee or 0))
        tip_amount = Decimal(str(self.tip_amount or 0))
        discount_amount = Decimal(str(self.discount_amount or 0))
        
        self.total_amount = (
            subtotal +
            tax_amount +
            delivery_fee +
            tip_amount -
            discount_amount
        )
        return self.total_amount


class OrderItem(TimestampMixin):
    """Order items with price snapshots"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, related_name='order_items')
    name = models.CharField(max_length=255)  # Snapshot of item name
    description = models.TextField(blank=True)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Modifiers selected (stored as JSON)
    selected_modifiers = models.JSONField(default=list)  # [{"modifier_id": 1, "name": "Extra Cheese", "price": 2.00}, ...]
    
    class Meta:
        db_table = 'order_items'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['menu_item']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculate total price including modifiers
        modifier_total = sum(
            Decimal(str(mod.get('price', 0))) for mod in self.selected_modifiers
        )
        self.total_price = (self.unit_price + modifier_total) * self.quantity
        super().save(*args, **kwargs)


class Review(TimestampMixin, SoftDeleteMixin):
    """Reviews and ratings"""
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    
    # Ratings (1-5)
    restaurant_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    food_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    delivery_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Review content
    comment = models.TextField(blank=True)
    images = models.JSONField(default=list)  # URLs to review images
    
    # Moderation
    is_approved = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    flagged_reason = models.TextField(blank=True)
    
    # Restaurant reply
    restaurant_reply = models.TextField(blank=True)
    restaurant_replied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reviews'
        indexes = [
            models.Index(fields=['restaurant', 'is_approved']),
            models.Index(fields=['customer']),
            models.Index(fields=['is_flagged']),
        ]
    
    def __str__(self):
        return f"Review for {self.restaurant.name} by {self.customer.email}"


class ItemReview(TimestampMixin, SoftDeleteMixin):
    """Individual item reviews"""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='item_reviews')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='item_reviews')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='item_reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    
    class Meta:
        db_table = 'item_reviews'
        unique_together = [['review', 'order_item']]
    
    def __str__(self):
        return f"Item review for {self.menu_item.name}"

