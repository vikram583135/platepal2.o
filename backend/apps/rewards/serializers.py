"""
Serializers for rewards app
"""
from rest_framework import serializers
from .models import LoyaltyTier, RewardPoint, UserLoyalty, RewardRedemption


class LoyaltyTierSerializer(serializers.ModelSerializer):
    """Loyalty tier serializer"""
    
    class Meta:
        model = LoyaltyTier
        fields = ('id', 'name', 'level', 'min_points', 'max_points', 'benefits', 'description', 'is_active')
        read_only_fields = ('id',)


class RewardPointSerializer(serializers.ModelSerializer):
    """Reward point serializer"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = RewardPoint
        fields = ('id', 'user', 'transaction_type', 'points', 'balance_after', 'order', 'order_number',
                  'description', 'expires_at', 'created_at')
        read_only_fields = ('id', 'user', 'balance_after', 'created_at')


class UserLoyaltySerializer(serializers.ModelSerializer):
    """User loyalty serializer"""
    current_tier = LoyaltyTierSerializer(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    next_tier = serializers.SerializerMethodField()
    points_to_next_tier = serializers.SerializerMethodField()
    
    class Meta:
        model = UserLoyalty
        fields = ('id', 'user', 'user_email', 'current_tier', 'total_points', 'available_points',
                  'lifetime_points_earned', 'lifetime_points_redeemed', 'next_tier', 'points_to_next_tier')
        read_only_fields = ('id', 'user', 'total_points', 'available_points', 'lifetime_points_earned',
                           'lifetime_points_redeemed')
    
    def get_next_tier(self, obj):
        """Get next tier user can achieve"""
        if not obj.current_tier:
            # Get lowest tier
            tier = LoyaltyTier.objects.filter(is_active=True, is_deleted=False).order_by('level').first()
            return LoyaltyTierSerializer(tier).data if tier else None
        
        # Get next tier
        next_tier = LoyaltyTier.objects.filter(
            level__gt=obj.current_tier.level,
            is_active=True,
            is_deleted=False
        ).order_by('level').first()
        return LoyaltyTierSerializer(next_tier).data if next_tier else None
    
    def get_points_to_next_tier(self, obj):
        """Calculate points needed to reach next tier"""
        next_tier = None
        if not obj.current_tier:
            next_tier = LoyaltyTier.objects.filter(is_active=True, is_deleted=False).order_by('level').first()
        else:
            next_tier = LoyaltyTier.objects.filter(
                level__gt=obj.current_tier.level,
                is_active=True,
                is_deleted=False
            ).order_by('level').first()
        
        if next_tier:
            points_needed = next_tier.min_points - obj.total_points
            return max(0, points_needed)
        return None


class RewardRedemptionSerializer(serializers.ModelSerializer):
    """Reward redemption serializer"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = RewardRedemption
        fields = ('id', 'user', 'points_used', 'reward_type', 'reward_value', 'status',
                  'order', 'order_number', 'coupon_code', 'description', 'created_at')
        read_only_fields = ('id', 'user', 'status', 'coupon_code', 'created_at')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

