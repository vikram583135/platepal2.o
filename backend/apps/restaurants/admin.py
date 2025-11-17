from django.contrib import admin
from .models import (
    Restaurant,
    Menu,
    MenuCategory,
    MenuItem,
    ItemModifier,
    Promotion,
    SearchHistory,
    PopularSearch,
    RestaurantSettings,
    RestaurantBranch,
    ManagerProfile,
    RestaurantDocument,
    DocumentReviewLog,
    RestaurantAlert,
)


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'cuisine_type', 'status', 'rating', 'city', 'kyc_verified')
    list_filter = ('status', 'cuisine_type', 'kyc_verified', 'accepts_delivery', 'accepts_pickup')
    search_fields = ('name', 'owner__email', 'city', 'address')
    readonly_fields = ('rating', 'total_ratings')


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'name', 'is_active', 'available_from', 'available_until')
    list_filter = ('is_active',)
    search_fields = ('restaurant__name', 'name')


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('menu', 'name', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'menu__name')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'rating', 'is_featured')
    list_filter = ('is_available', 'is_vegetarian', 'is_vegan', 'is_spicy', 'is_featured')
    search_fields = ('name', 'description', 'category__name')
    readonly_fields = ('rating', 'total_ratings')


@admin.register(ItemModifier)
class ItemModifierAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu_item', 'type', 'price', 'is_required', 'is_available')
    list_filter = ('type', 'is_required', 'is_available')
    search_fields = ('name', 'menu_item__name')


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'restaurant', 'discount_type', 'discount_value', 'is_active', 'valid_until')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_until')
    search_fields = ('name', 'code', 'restaurant__name')
    filter_horizontal = ('applicable_items', 'applicable_categories')


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'search_type', 'created_at')
    list_filter = ('search_type', 'created_at')
    search_fields = ('query', 'user__email')
    readonly_fields = ('created_at',)


@admin.register(PopularSearch)
class PopularSearchAdmin(admin.ModelAdmin):
    list_display = ('query', 'search_count', 'last_searched', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('query',)
    readonly_fields = ('created_at',)


@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'is_online', 'auto_accept_orders', 'default_prep_time_minutes')
    list_filter = ('is_online', 'auto_accept_orders')
    search_fields = ('restaurant__name',)


@admin.register(RestaurantBranch)
class RestaurantBranchAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'name', 'branch_type', 'city', 'is_primary', 'service_radius_km')
    list_filter = ('branch_type', 'city', 'is_primary')
    search_fields = ('name', 'restaurant__name', 'city')


@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'first_name', 'role', 'email', 'is_primary')
    list_filter = ('role', 'is_primary')
    search_fields = ('first_name', 'last_name', 'email', 'restaurant__name')


@admin.register(RestaurantDocument)
class RestaurantDocumentAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'document_type', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('document_type', 'status')
    search_fields = ('restaurant__name', 'document_number')
    readonly_fields = ('submitted_at', 'reviewed_at')


@admin.register(DocumentReviewLog)
class DocumentReviewLogAdmin(admin.ModelAdmin):
    list_display = ('document', 'reviewer', 'status_before', 'status_after', 'created_at')
    list_filter = ('status_after', 'created_at')
    search_fields = ('document__restaurant__name', 'reviewer__email')


@admin.register(RestaurantAlert)
class RestaurantAlertAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'alert_type', 'severity', 'title', 'is_read', 'created_at')
    list_filter = ('alert_type', 'severity', 'is_read')
    search_fields = ('restaurant__name', 'title', 'message')

