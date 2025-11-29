"""
URLs for payments app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet, RefundViewSet, WalletViewSet,
    SettlementCycleViewSet, PayoutViewSet,
    create_payment_intent, confirm_payment
)

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'refunds', RefundViewSet, basename='refund')
router.register(r'wallet', WalletViewSet, basename='wallet')
router.register(r'settlements', SettlementCycleViewSet, basename='settlement')
router.register(r'payouts', PayoutViewSet, basename='payout')

urlpatterns = [
    path('', include(router.urls)),
    path('create_payment_intent/', create_payment_intent, name='create_payment_intent'),
    path('confirm_payment/', confirm_payment, name='confirm_payment'),
]

