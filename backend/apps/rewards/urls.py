"""
URLs for rewards app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoyaltyTierViewSet, UserLoyaltyViewSet, RewardRedemptionViewSet

router = DefaultRouter()
router.register(r'tiers', LoyaltyTierViewSet, basename='loyalty-tier')
router.register(r'loyalty', UserLoyaltyViewSet, basename='user-loyalty')
router.register(r'redemptions', RewardRedemptionViewSet, basename='reward-redemption')

urlpatterns = [
    path('', include(router.urls)),
]

