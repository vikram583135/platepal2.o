"""
URLs for subscriptions app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MembershipPlanViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'plans', MembershipPlanViewSet, basename='membership-plan')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]

