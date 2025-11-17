from decimal import Decimal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from apps.restaurants.models import RestaurantAlert
from apps.events.broadcast import EventBroadcastService
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
                    # Broadcast inventory_low event
                    EventBroadcastService.broadcast_to_restaurant(
                        restaurant_id=order.restaurant.id,
                        event_type='inventory_low',
                        aggregate_type='InventoryItem',
                        aggregate_id=str(inventory_item.id),
                        payload={
                            'inventory_item_id': inventory_item.id,
                            'name': inventory_item.name,
                            'current_stock': float(inventory_item.current_stock),
                            'reorder_level': float(inventory_item.reorder_level),
                            'unit': inventory_item.unit,
                            'menu_item_id': inventory_item.menu_item.id if inventory_item.menu_item else None,
                        },
                    )
                    
                    # If inventory runs out, mark menu item unavailable
                    if inventory_item.current_stock <= 0:
                        EventBroadcastService.broadcast_to_restaurant(
                            restaurant_id=order.restaurant.id,
                            event_type='item_sold_out',
                            aggregate_type='MenuItem',
                            aggregate_id=str(inventory_item.menu_item.id) if inventory_item.menu_item else None,
                            payload={
                                'menu_item_id': inventory_item.menu_item.id if inventory_item.menu_item else None,
                                'menu_item_name': inventory_item.menu_item.name if inventory_item.menu_item else None,
                                'inventory_item_id': inventory_item.id,
                            },
                        )
                    
                    if inventory_item.auto_mark_unavailable and inventory_item.menu_item:
                        inventory_item.menu_item.is_available = False
                        inventory_item.menu_item.save(update_fields=['is_available'])
                        
                        # Broadcast menu.updated for sold-out item
                        EventBroadcastService.broadcast_to_restaurant(
                            restaurant_id=order.restaurant.id,
                            event_type='menu.updated',
                            aggregate_type='MenuItem',
                            aggregate_id=str(inventory_item.menu_item.id),
                            payload={
                                'menu_item_id': inventory_item.menu_item.id,
                                'is_available': False,
                                'reason': 'out_of_stock',
                            },
                        )


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
    
    # Broadcast via EventBroadcastService (additional to direct channel send for backwards compatibility)
    EventBroadcastService.broadcast_to_restaurant(
        restaurant_id=restaurant.id,
        event_type='inventory_low',
        aggregate_type='InventoryItem',
        aggregate_id=str(inventory_item.id),
        payload={
            'alert_id': alert.id,
            'title': alert.title,
            'message': alert.message,
            'inventory_item_id': inventory_item.id,
            'current_stock': float(current),
            'reorder_level': float(inventory_item.reorder_level),
            'unit': inventory_item.unit,
        },
    )
    
    # Also notify admin for repeated inventory issues
    EventBroadcastService.broadcast_to_admin(
        event_type='inventory_low',
        aggregate_type='InventoryItem',
        aggregate_id=str(inventory_item.id),
        payload={
            'restaurant_id': restaurant.id,
            'restaurant_name': restaurant.name,
            'inventory_item_id': inventory_item.id,
            'inventory_item_name': inventory_item.name,
            'current_stock': float(current),
            'reorder_level': float(inventory_item.reorder_level),
        },
    )


