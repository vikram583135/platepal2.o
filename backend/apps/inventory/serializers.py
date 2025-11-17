from rest_framework import serializers

from .models import InventoryItem, StockMovement, RecipeItem


class InventoryItemSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.SerializerMethodField()
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    linked_menu_item = serializers.CharField(source='menu_item.name', read_only=True)

    class Meta:
        model = InventoryItem
        fields = (
            'id',
            'restaurant',
            'restaurant_name',
            'menu_item',
            'linked_menu_item',
            'name',
            'sku',
            'category',
            'unit',
            'current_stock',
            'reorder_level',
            'max_capacity',
            'low_stock_threshold',
            'auto_mark_unavailable',
            'last_restocked_at',
            'notes',
            'is_low_stock',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'restaurant', 'restaurant_name', 'linked_menu_item', 'is_low_stock', 'created_at', 'updated_at')

    def get_is_low_stock(self, obj):
        return obj.is_low_stock


class StockMovementSerializer(serializers.ModelSerializer):
    inventory_item_name = serializers.CharField(source='inventory_item.name', read_only=True)

    class Meta:
        model = StockMovement
        fields = (
            'id',
            'inventory_item',
            'inventory_item_name',
            'movement_type',
            'order',
            'quantity',
            'unit_cost',
            'notes',
            'created_by',
            'created_at',
        )
        read_only_fields = ('id', 'created_at', 'created_by', 'inventory_item_name')


class RecipeItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    inventory_item_name = serializers.CharField(source='inventory_item.name', read_only=True)

    class Meta:
        model = RecipeItem
        fields = (
            'id',
            'menu_item',
            'menu_item_name',
            'inventory_item',
            'inventory_item_name',
            'quantity',
            'unit',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'menu_item_name', 'inventory_item_name')


