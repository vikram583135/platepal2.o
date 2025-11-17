from django.contrib import admin
from .models import MembershipPlan, Subscription


@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'plan_type', 'price', 'currency', 'is_active', 'is_featured', 'created_at')
    list_filter = ('plan_type', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'auto_renew', 'created_at')
    list_filter = ('status', 'auto_renew', 'created_at')
    search_fields = ('user__email', 'plan__name', 'payment_transaction_id')
    readonly_fields = ('created_at', 'updated_at')

