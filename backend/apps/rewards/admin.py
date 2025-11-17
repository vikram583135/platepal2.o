from django.contrib import admin
from .models import LoyaltyTier, RewardPoint, UserLoyalty, RewardRedemption


@admin.register(LoyaltyTier)
class LoyaltyTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'min_points', 'max_points', 'is_active')
    list_filter = ('is_active', 'level')
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RewardPoint)
class RewardPointAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'points', 'balance_after', 'order', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('user__email', 'order__order_number')
    readonly_fields = ('created_at',)


@admin.register(UserLoyalty)
class UserLoyaltyAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_tier', 'total_points', 'available_points', 'lifetime_points_earned')
    list_filter = ('current_tier',)
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RewardRedemption)
class RewardRedemptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'points_used', 'reward_type', 'reward_value', 'status', 'coupon_code', 'created_at')
    list_filter = ('reward_type', 'status', 'created_at')
    search_fields = ('user__email', 'coupon_code', 'order__order_number')
    readonly_fields = ('created_at',)

