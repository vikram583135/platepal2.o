from django.contrib import admin
from .models import Order, OrderItem, Review, ItemReview


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('name', 'unit_price', 'total_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'restaurant', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'order_type', 'is_scheduled', 'created_at')
    search_fields = ('order_number', 'customer__email', 'restaurant__name')
    readonly_fields = ('order_number', 'subtotal', 'tax_amount', 'delivery_fee', 'total_amount', 'created_at')
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'quantity', 'unit_price', 'total_price')
    list_filter = ('order__status',)
    search_fields = ('order__order_number', 'name')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'customer', 'restaurant_rating', 'food_rating', 'is_approved', 'is_flagged', 'created_at')
    list_filter = ('is_approved', 'is_flagged', 'restaurant_rating', 'created_at')
    search_fields = ('restaurant__name', 'customer__email', 'comment')
    readonly_fields = ('order', 'customer', 'restaurant', 'created_at')


@admin.register(ItemReview)
class ItemReviewAdmin(admin.ModelAdmin):
    list_display = ('menu_item', 'review', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('menu_item__name', 'review__customer__email')

