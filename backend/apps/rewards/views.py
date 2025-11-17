"""
Views for rewards app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import LoyaltyTier, RewardPoint, UserLoyalty, RewardRedemption
from .serializers import (
    LoyaltyTierSerializer, RewardPointSerializer, UserLoyaltySerializer, RewardRedemptionSerializer
)


class LoyaltyTierViewSet(viewsets.ReadOnlyModelViewSet):
    """Loyalty tier viewset"""
    serializer_class = LoyaltyTierSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return LoyaltyTier.objects.filter(is_active=True, is_deleted=False).order_by('level')


class UserLoyaltyViewSet(viewsets.ReadOnlyModelViewSet):
    """User loyalty viewset"""
    serializer_class = UserLoyaltySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserLoyalty.objects.filter(user=self.request.user)
    
    def get_object(self):
        loyalty, created = UserLoyalty.objects.get_or_create(
            user=self.request.user,
            defaults={'total_points': 0, 'available_points': 0}
        )
        return loyalty
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def balance(self, request):
        """Get current points balance"""
        loyalty, created = UserLoyalty.objects.get_or_create(
            user=request.user,
            defaults={'total_points': 0, 'available_points': 0}
        )
        
        # Update tier
        loyalty.update_tier()
        
        serializer = self.get_serializer(loyalty)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def history(self, request):
        """Get reward points history"""
        points = RewardPoint.objects.filter(user=request.user).order_by('-created_at')[:50]
        serializer = RewardPointSerializer(points, many=True)
        return Response({'transactions': serializer.data})


class RewardRedemptionViewSet(viewsets.ModelViewSet):
    """Reward redemption viewset"""
    serializer_class = RewardRedemptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RewardRedemption.objects.filter(user=self.request.user, is_deleted=False)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def redeem(self, request):
        """Redeem points for reward"""
        reward_type = request.data.get('reward_type')  # DISCOUNT, CASHBACK, FREE_DELIVERY
        points_to_redeem = int(request.data.get('points', 0))
        order_id = request.data.get('order_id')
        
        if not reward_type or points_to_redeem <= 0:
            return Response({'error': 'reward_type and points are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user loyalty
        loyalty, created = UserLoyalty.objects.get_or_create(
            user=request.user,
            defaults={'total_points': 0, 'available_points': 0}
        )
        
        if loyalty.available_points < points_to_redeem:
            return Response({'error': 'Insufficient points'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate reward value (1 point = 0.01 currency unit, or custom logic)
        reward_value = Decimal(str(points_to_redeem)) * Decimal('0.01')
        
        # Create redemption
        redemption = RewardRedemption.objects.create(
            user=request.user,
            points_used=points_to_redeem,
            reward_type=reward_type,
            reward_value=reward_value,
            status=RewardRedemption.Status.PROCESSED,
            order_id=order_id if order_id else None,
            description=f"Redeemed {points_to_redeem} points for {reward_type}"
        )
        
        # Deduct points
        loyalty.available_points -= points_to_redeem
        loyalty.lifetime_points_redeemed += points_to_redeem
        loyalty.save()
        
        # Create reward point transaction
        RewardPoint.objects.create(
            user=request.user,
            transaction_type=RewardPoint.TransactionType.REDEEMED,
            points=-points_to_redeem,
            balance_after=loyalty.available_points,
            order_id=order_id if order_id else None,
            description=f"Redeemed {points_to_redeem} points for {reward_type}"
        )
        
        # Generate coupon code if discount
        if reward_type == 'DISCOUNT':
            import uuid
            redemption.coupon_code = f"REWARD-{uuid.uuid4().hex[:8].upper()}"
            redemption.save()
        
        serializer = self.get_serializer(redemption)
        return Response(serializer.data)

