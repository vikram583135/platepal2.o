from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import InventoryItemViewSet, StockMovementViewSet, RecipeItemViewSet


router = DefaultRouter()
router.register(r'items', InventoryItemViewSet, basename='inventory-item')
router.register(r'movements', StockMovementViewSet, basename='inventory-movement')
router.register(r'recipes', RecipeItemViewSet, basename='inventory-recipe')

urlpatterns = [
    path('', include(router.urls)),
]


