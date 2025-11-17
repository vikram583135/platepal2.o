"""
Admin for chat app
"""
from django.contrib import admin
from .models import ChatRoom, ChatMessage, ChatTemplate, MaskedCall


@admin.register(ChatTemplate)
class ChatTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_auto_template', 'auto_trigger', 'usage_count', 'display_order')
    list_filter = ('category', 'is_auto_template')
    search_fields = ('title', 'message')
    ordering = ('category', 'display_order')


@admin.register(MaskedCall)
class MaskedCallAdmin(admin.ModelAdmin):
    list_display = ('call_type', 'caller', 'recipient', 'caller_masked_number', 'recipient_masked_number', 'status', 'started_at', 'duration_seconds')
    list_filter = ('call_type', 'status', 'started_at')
    search_fields = ('caller__email', 'recipient__email', 'caller_masked_number', 'recipient_masked_number')
    date_hierarchy = 'started_at'


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'room_type', 'customer', 'restaurant', 'courier', 'order', 'is_active', 'last_message_at', 'created_at')
    list_filter = ('room_type', 'is_active', 'created_at')
    search_fields = ('customer__email', 'restaurant__email', 'courier__email', 'order__order_number')
    raw_id_fields = ('customer', 'restaurant', 'courier', 'support_agent', 'order')
    readonly_fields = ('created_at', 'updated_at', 'last_message_at')
    date_hierarchy = 'created_at'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'message_type', 'content', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'created_at')
    search_fields = ('content', 'sender__email', 'room__id')
    raw_id_fields = ('room', 'sender')
    readonly_fields = ('created_at', 'updated_at', 'read_at')
    date_hierarchy = 'created_at'

