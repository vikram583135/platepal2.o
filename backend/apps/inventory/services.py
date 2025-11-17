from decimal import Decimal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from apps.restaurants.models import RestaurantAlert
from .models import InventoryItem, RecipeItem, StockMovement


channel_layer = get_channel_layer()


def reserve_inventory_for_order(order, actor=None):
    """Deduct ingredient-level inventory when an order is kicked off"""
    if not order or not hasattr(order, 'items'):
        return

    recipe_map = _build_recipe_map(order)
    if not recipe_map:
        return

    with transaction.atomic():
        for menu_item_id, payload in recipe_map.items():
            order_items = payload['order_items']
            recipes = payload['recipes']
            total_units = sum(item.quantity for item in order_items)

            for recipe in recipes:
                required_quantity = (Decimal(str(recipe.quantity)) * Decimal(str(total_units))).quantize(Decimal('0.01'))
                inventory_item = recipe.inventory_item
                if required_quantity <= 0:
                    continue

                previous_stock = inventory_item.current_stock
                inventory_item.current_stock = max(Decimal('0.00'), inventory_item.current_stock - required_quantity)
                inventory_item.save(update_fields=['current_stock', 'updated_at'])

                StockMovement.objects.create(
                    inventory_item=inventory_item,
                    movement_type=StockMovement.MovementType.OUTBOUND,
                    order=order,
                    quantity=required_quantity,
                    created_by=actor,
                    notes=f"Auto deduction for order {order.order_number}",
                )

                if inventory_item.is_low_stock:
                    _raise_inventory_alert(order.restaurant, inventory_item, previous_stock, inventory_item.current_stock)
                    if inventory_item.auto_mark_unavailable and inventory_item.menu_item:
                        inventory_item.menu_item.is_available = False
                        inventory_item.menu_item.save(update_fields=['is_available'])


def _build_recipe_map(order):
    """Group order items + recipe definitions"""
    menu_item_ids = [item.menu_item_id for item in order.items.all() if item.menu_item_id]
    if not menu_item_ids:
        return {}

    recipes = RecipeItem.objects.filter(menu_item_id__in=menu_item_ids, is_deleted=False).select_related('inventory_item')
    if not recipes.exists():
        return {}

    map_by_menu = {}
    for order_item in order.items.all():
        if not order_item.menu_item_id:
            continue
        map_by_menu.setdefault(order_item.menu_item_id, {'order_items': [], 'recipes': []})
        map_by_menu[order_item.menu_item_id]['order_items'].append(order_item)

    for recipe in recipes:
        if recipe.menu_item_id in map_by_menu:
            map_by_menu[recipe.menu_item_id]['recipes'].append(recipe)

    return {k: v for k, v in map_by_menu.items() if v['order_items'] and v['recipes']}


def _raise_inventory_alert(restaurant, inventory_item, previous, current):
    """Create or refresh a low inventory alert"""
    if not restaurant:
        return
    alert = RestaurantAlert.objects.create(
        restaurant=restaurant,
        alert_type=RestaurantAlert.AlertType.INVENTORY_LOW,
        severity=RestaurantAlert.Severity.WARNING,
        title=f"Low stock: {inventory_item.name}",
        message=f"{inventory_item.name} dropped from {previous} to {current} {inventory_item.unit.lower()}",
        metadata={
            'inventory_item_id': inventory_item.id,
            'sku': inventory_item.sku,
            'current_stock': float(current),
            'reorder_level': float(inventory_item.reorder_level),
        },
    )
    if channel_layer:
        async_to_sync(channel_layer.group_send)(
            f'restaurant_{restaurant.id}',
            {
                'type': 'inventory_low',
                'data': {
                    'alert_id': alert.id,
                    'title': alert.title,
                    'message': alert.message,
                    'inventory_item_id': inventory_item.id,
                    'current_stock': float(current),
                    'reorder_level': float(inventory_item.reorder_level),
                },
            },
        )


