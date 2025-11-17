from django.db import models
from apps.accounts.models import User, TimestampMixin, SoftDeleteMixin


class MembershipPlan(TimestampMixin, SoftDeleteMixin):
    """Membership plans (Premium, Gold, etc.)"""
    
    class PlanType(models.TextChoices):
        MONTHLY = 'MONTHLY', 'Monthly'
        YEARLY = 'YEARLY', 'Yearly'
        LIFETIME = 'LIFETIME', 'Lifetime'
    
    name = models.CharField(max_length=100)  # Premium, Gold, etc.
    plan_type = models.CharField(max_length=20, choices=PlanType.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    
    # Benefits
    benefits = models.JSONField(default=dict)  # {
    #   'free_delivery': True,
    #   'discount_percentage': 10,
    #   'priority_support': True,
    #   'exclusive_offers': True,
    #   'cashback_percentage': 5,
    #   'max_free_deliveries_per_month': 20,
    # }
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Validity
    duration_days = models.IntegerField(null=True, blank=True)  # null = lifetime
    
    class Meta:
        db_table = 'membership_plans'
        indexes = [
            models.Index(fields=['plan_type', 'is_active']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.plan_type}"


class Subscription(TimestampMixin, SoftDeleteMixin):
    """User subscriptions"""
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'
        PENDING = 'PENDING', 'Pending'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(MembershipPlan, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Payment
    payment_transaction_id = models.CharField(max_length=255, blank=True)
    auto_renew = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'subscriptions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'end_date']),
            models.Index(fields=['auto_renew']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"
    
    def is_active(self):
        from django.utils import timezone
        return (
            self.status == Subscription.Status.ACTIVE and
            (self.end_date is None or self.end_date > timezone.now())
        )

