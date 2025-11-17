from decimal import Decimal

from django.db import models
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.restaurants.models import Restaurant, MenuItem
from apps.restaurants.permissions import IsRestaurantOwner
from .models import InventoryItem, StockMovement, RecipeItem
from .serializers import InventoryItemSerializer, StockMovementSerializer, RecipeItemSerializer


class InventoryItemViewSet(viewsets.ModelViewSet):
    """CRUD for inventory items per restaurant"""

    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def get_queryset(self):
        qs = InventoryItem.objects.filter(is_deleted=False).select_related('restaurant', 'menu_item')
        user = self.request.user
        if user.role == 'ADMIN':
            filtered = qs
        else:
            filtered = qs.filter(restaurant__owner=user)
        restaurant_id = self.request.query_params.get('restaurant_id') or self.request.query_params.get('restaurant')
        if restaurant_id:
            filtered = filtered.filter(restaurant_id=restaurant_id)
        return filtered

    def perform_create(self, serializer):
        restaurant = self._get_restaurant_from_request()
        serializer.save(restaurant=restaurant)

    def perform_update(self, serializer):
        instance = serializer.instance
        if self.request.user.role != 'ADMIN' and instance.restaurant.owner != self.request.user:
            raise ValidationError('You cannot modify inventory for this restaurant.')
        serializer.save()

    def _get_restaurant_from_request(self):
        restaurant_id = self.request.data.get('restaurant')
        if not restaurant_id:
            raise ValidationError('restaurant field is required.')
        qs = Restaurant.objects.filter(id=restaurant_id, is_deleted=False)
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(owner=self.request.user)
        restaurant = qs.first()
        if not restaurant:
            raise ValidationError('Restaurant not found.')
        return restaurant

    @action(detail=True, methods=['post'])
    def restock(self, request, pk=None):
        inventory_item = self.get_object()
        quantity = request.data.get('quantity')
        try:
            quantity = Decimal(str(quantity))
        except (TypeError, ValueError, ArithmeticError):
            raise ValidationError({'quantity': 'Provide a numeric quantity.'})
        if quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be greater than zero.'})
        inventory_item.current_stock += quantity
        inventory_item.last_restocked_at = timezone.now()
        inventory_item.save(update_fields=['current_stock', 'last_restocked_at', 'updated_at'])
        return Response(self.get_serializer(inventory_item).data)

    @action(detail=True, methods=['post'])
    def mark_sold_out(self, request, pk=None):
        inventory_item = self.get_object()
        if inventory_item.menu_item:
            inventory_item.menu_item.is_available = False
            inventory_item.menu_item.save(update_fields=['is_available'])
        inventory_item.current_stock = Decimal('0.00')
        inventory_item.save(update_fields=['current_stock', 'updated_at'])
        return Response(self.get_serializer(inventory_item).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        queryset = self.get_queryset()
        low_stock = queryset.filter(current_stock__lte=models.F('low_stock_threshold')).count()
        total = queryset.count()
        linked = queryset.filter(menu_item__isnull=False).count()
        return Response({
            'total_items': total,
            'low_stock_items': low_stock,
            'linked_menu_items': linked,
        })


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """Read movement history"""

    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def get_queryset(self):
        qs = StockMovement.objects.filter(is_deleted=False).select_related('inventory_item', 'order')
        user = self.request.user
        if user.role == 'ADMIN':
            return qs
        return qs.filter(inventory_item__restaurant__owner=user)


class RecipeItemViewSet(viewsets.ModelViewSet):
    """CRUD for linking ingredients to menu items"""

    serializer_class = RecipeItemSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def get_queryset(self):
        qs = RecipeItem.objects.filter(is_deleted=False).select_related('menu_item', 'inventory_item')
        user = self.request.user
        if user.role == 'ADMIN':
            return qs
        return qs.filter(menu_item__category__menu__restaurant__owner=user)

    def perform_create(self, serializer):
        menu_item = self._get_menu_item(serializer.validated_data.get('menu_item') or serializer.initial_data.get('menu_item'))
        inventory_item = self._get_inventory_item(serializer.validated_data.get('inventory_item') or serializer.initial_data.get('inventory_item'))
        serializer.save(menu_item=menu_item, inventory_item=inventory_item)

    def perform_update(self, serializer):
        menu_item = serializer.instance.menu_item
        if serializer.validated_data.get('menu_item'):
            menu_item = self._get_menu_item(serializer.validated_data['menu_item'])
        inventory_item = serializer.instance.inventory_item
        if serializer.validated_data.get('inventory_item'):
            inventory_item = self._get_inventory_item(serializer.validated_data['inventory_item'])
        serializer.save(menu_item=menu_item, inventory_item=inventory_item)

    def _get_menu_item(self, menu_item):
        if not menu_item:
            raise ValidationError('menu_item is required')
        if isinstance(menu_item, MenuItem):
            obj = menu_item
        else:
            qs = MenuItem.objects.filter(id=menu_item, is_deleted=False)
            if self.request.user.role != 'ADMIN':
                qs = qs.filter(category__menu__restaurant__owner=self.request.user)
            obj = qs.first()
        if not obj:
            raise ValidationError('Menu item not found.')
        if self.request.user.role != 'ADMIN' and obj.category.menu.restaurant.owner != self.request.user:
            raise ValidationError('You cannot modify recipes for this menu item.')
        return obj

    def _get_inventory_item(self, inventory_item):
        if not inventory_item:
            raise ValidationError('inventory_item is required')
        if isinstance(inventory_item, InventoryItem):
            obj = inventory_item
        else:
            qs = InventoryItem.objects.filter(id=inventory_item, is_deleted=False)
            if self.request.user.role != 'ADMIN':
                qs = qs.filter(restaurant__owner=self.request.user)
            obj = qs.first()
        if not obj:
            raise ValidationError('Inventory item not found.')
        if self.request.user.role != 'ADMIN':
            if obj.restaurant.owner != self.request.user:
                raise ValidationError('You cannot modify inventory for this restaurant.')
        return obj


