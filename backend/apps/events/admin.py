"""
Admin configuration for events app
"""
from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin for Event model"""
    list_display = ['event_id', 'type', 'aggregate_type', 'aggregate_id', 'timestamp', 'sequence_number']
    list_filter = ['type', 'aggregate_type', 'timestamp']
    search_fields = ['event_id', 'type', 'aggregate_type', 'aggregate_id']
    readonly_fields = ['event_id', 'sequence_number', 'timestamp']
    ordering = ['-sequence_number']
    
    fieldsets = (
        ('Event Info', {
            'fields': ('event_id', 'type', 'version', 'sequence_number', 'timestamp')
        }),
        ('Aggregate Info', {
            'fields': ('aggregate_type', 'aggregate_id')
        }),
        ('Event Data', {
            'fields': ('payload', 'metadata')
        }),
    )

