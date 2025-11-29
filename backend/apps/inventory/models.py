from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator

from apps.accounts.models import TimestampMixin, SoftDeleteMixin
from apps.restaurants.models import Restaurant, MenuItem
from apps.orders.models import Order


class InventoryItem(TimestampMixin, SoftDeleteMixin):
    """Track stock per restaurant/item"""

    class Unit(models.TextChoices):
        KILOGRAM = 'KG', 'Kilogram'
        GRAM = 'G', 'Gram'
        LITER = 'L', 'Liter'
        MILLILITER = 'ML', 'Milliliter'
        PIECE = 'PC', 'Piece'
        PACK = 'PACK', 'Pack'

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='inventory_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_links')
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=120, blank=True)
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECE)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    max_capacity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    low_stock_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    auto_mark_unavailable = models.BooleanField(default=True)
    last_auto_disabled_at = models.DateTimeField(null=True, blank=True)
    last_restocked_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'inventory_items'
        indexes = [
            models.Index(fields=['restaurant', 'name']),
            models.Index(fields=['sku']),
            models.Index(fields=['restaurant', 'is_deleted']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"

    @property
    def is_low_stock(self):
        if self.low_stock_threshold <= 0:
            return False
        return self.current_stock <= self.low_stock_threshold


class StockMovement(TimestampMixin, SoftDeleteMixin):
    """Stock adjustments"""

    class MovementType(models.TextChoices):
        INBOUND = 'INBOUND', 'Inbound'
        OUTBOUND = 'OUTBOUND', 'Outbound'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'

    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_movements')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_stock_movements')

    class Meta:
        db_table = 'inventory_movements'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['inventory_item', '-created_at']),
            models.Index(fields=['movement_type']),
        ]

    def __str__(self):
        direction = '+' if self.movement_type == self.MovementType.INBOUND else '-'
        return f"{direction}{self.quantity} {self.inventory_item.name}"


class RecipeItem(TimestampMixin, SoftDeleteMixin):
    """Tie menu items to ingredient consumption"""

    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='recipe_items')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='recipe_links')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unit = models.CharField(max_length=10, choices=InventoryItem.Unit.choices, default=InventoryItem.Unit.PIECE)

    class Meta:
        db_table = 'inventory_recipes'
        unique_together = [['menu_item', 'inventory_item']]

    def __str__(self):
        return f"{self.menu_item.name} -> {self.inventory_item.name} ({self.quantity} {self.unit})"


class InventoryAuditLog(TimestampMixin):
    """Human-readable audit entries"""

    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=120)
    metadata = models.JSONField(default=dict, blank=True)
    triggered_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_audits')

    class Meta:
        db_table = 'inventory_audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.inventory_item.name}: {self.action}"


