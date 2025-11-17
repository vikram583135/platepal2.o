from django.contrib import admin
from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'method_type', 'amount', 'status', 'transaction_id', 'created_at')
    list_filter = ('status', 'method_type', 'created_at')
    search_fields = ('order__order_number', 'transaction_id', 'user__email')
    readonly_fields = ('transaction_id', 'gateway_response', 'created_at')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment', 'amount', 'status', 'processed_at', 'processed_by')
    list_filter = ('status', 'processed_at')
    search_fields = ('order__order_number', 'payment__transaction_id')
    readonly_fields = ('refund_transaction_id', 'created_at')

