from django.contrib import admin

from .models import InventoryItem, StockMovement, RecipeItem, InventoryAuditLog


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'sku', 'current_stock', 'reorder_level', 'is_deleted')
    list_filter = ('restaurant', 'is_deleted', 'category')
    search_fields = ('name', 'sku', 'restaurant__name')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('inventory_item', 'movement_type', 'quantity', 'order', 'created_at')
    list_filter = ('movement_type',)
    search_fields = ('inventory_item__name', 'order__order_number')


@admin.register(RecipeItem)
class RecipeItemAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'inventory_item', 'quantity', 'unit')
    search_fields = ('menu_item__name', 'inventory_item__name')


@admin.register(InventoryAuditLog)
class InventoryAuditLogAdmin(admin.ModelAdmin):
    list_display = ('inventory_item', 'action', 'created_at')
    search_fields = ('inventory_item__name', 'action')


