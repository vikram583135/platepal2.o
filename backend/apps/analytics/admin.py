from django.contrib import admin
from .models import AnalyticsEvent


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'session_id', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('user__email', 'session_id')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

