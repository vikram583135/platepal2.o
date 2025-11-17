from django.contrib import admin
from .models import SupportTicket, TicketMessage, ChatBotMessage


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'user', 'category', 'subject', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('ticket_number', 'subject', 'user__email')
    readonly_fields = ('ticket_number', 'created_at', 'updated_at')


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('ticket__ticket_number', 'message', 'user__email')
    readonly_fields = ('created_at',)


@admin.register(ChatBotMessage)
class ChatBotMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'is_from_user', 'intent', 'created_at')
    list_filter = ('is_from_user', 'intent', 'created_at')
    search_fields = ('message', 'user__email', 'session_id')
    readonly_fields = ('created_at',)

