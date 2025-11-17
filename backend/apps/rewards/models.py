from django.db import models
from apps.accounts.models import User, TimestampMixin, SoftDeleteMixin
from apps.orders.models import Order


class LoyaltyTier(TimestampMixin, SoftDeleteMixin):
    """Loyalty program tiers (Bronze, Silver, Gold, Platinum)"""
    name = models.CharField(max_length=50)  # Bronze, Silver, Gold, Platinum
    level = models.IntegerField(unique=True)  # 1, 2, 3, 4
    min_points = models.IntegerField()  # Minimum points required
    max_points = models.IntegerField(null=True, blank=True)  # null = unlimited
    
    # Benefits
    benefits = models.JSONField(default=dict)  # {
    #   'points_multiplier': 1.5,
    #   'discount_percentage': 5,
    #   'free_delivery_threshold': 0,
    #   'priority_support': True,
    # }
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'loyalty_tiers'
        ordering = ['level']
    
    def __str__(self):
        return f"{self.name} (Level {self.level})"


class RewardPoint(TimestampMixin):
    """Reward points transactions"""
    
    class TransactionType(models.TextChoices):
        EARNED = 'EARNED', 'Earned'
        REDEEMED = 'REDEEMED', 'Redeemed'
        EXPIRED = 'EXPIRED', 'Expired'
        ADJUSTED = 'ADJUSTED', 'Adjusted'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reward_points')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    points = models.IntegerField()  # Positive for earned, negative for redeemed
    balance_after = models.IntegerField()  # Points balance after this transaction
    
    # Related entities
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='reward_points')
    description = models.TextField(blank=True)
    
    # Expiry
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reward_points'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} {abs(self.points)} points - {self.user.email}"


class UserLoyalty(TimestampMixin):
    """User loyalty status and points"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    current_tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    total_points = models.IntegerField(default=0)
    available_points = models.IntegerField(default=0)  # Points not expired
    lifetime_points_earned = models.IntegerField(default=0)
    lifetime_points_redeemed = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'user_loyalty'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['current_tier']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.current_tier.name if self.current_tier else 'No Tier'} - {self.available_points} points"
    
    def update_tier(self):
        """Update user's tier based on total points"""
        if self.total_points == 0:
            self.current_tier = None
            self.save()
            return
        
        # Find appropriate tier
        tier = LoyaltyTier.objects.filter(
            min_points__lte=self.total_points,
            is_active=True,
            is_deleted=False
        ).order_by('-level').first()
        
        if tier and (tier.max_points is None or self.total_points <= tier.max_points):
            if self.current_tier != tier:
                self.current_tier = tier
                self.save()
                return tier
        elif not tier:
            # No tier found, set to lowest tier if exists
            lowest_tier = LoyaltyTier.objects.filter(is_active=True, is_deleted=False).order_by('level').first()
            if lowest_tier:
                self.current_tier = lowest_tier
                self.save()
        
        return None


class RewardRedemption(TimestampMixin, SoftDeleteMixin):
    """Reward point redemptions"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSED = 'PROCESSED', 'Processed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reward_redemptions')
    points_used = models.IntegerField()
    reward_type = models.CharField(max_length=50)  # DISCOUNT, CASHBACK, FREE_DELIVERY, etc.
    reward_value = models.DecimalField(max_digits=10, decimal_places=2)  # Discount amount, cashback, etc.
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Related entities
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='reward_redemptions')
    coupon_code = models.CharField(max_length=50, blank=True)  # Generated coupon code if applicable
    
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'reward_redemptions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['coupon_code']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.points_used} points - {self.reward_type}"

