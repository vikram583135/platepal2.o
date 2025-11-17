from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_order_updates', 'push_order_updates', 'quiet_hours_enabled')
    list_filter = ('email_order_updates', 'push_order_updates', 'quiet_hours_enabled')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')

