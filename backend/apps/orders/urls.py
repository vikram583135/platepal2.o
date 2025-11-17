"""
URLs for orders app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, ReviewViewSet, ItemReviewViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'item-reviews', ItemReviewViewSet, basename='item-review')

urlpatterns = [
    path('', include(router.urls)),
]

