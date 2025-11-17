"""
Serializers for payments app
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Payment, Refund, Wallet, WalletTransaction
from apps.orders.serializers import OrderSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer"""
    order = OrderSerializer(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Payment
        fields = ('id', 'order', 'user', 'user_email', 'payment_method', 'method_type',
                  'amount', 'currency', 'transaction_id', 'gateway_response', 'status',
                  'processed_at', 'failed_at', 'refunded_at', 'failure_reason', 'failure_code',
                  'refund_amount', 'refund_transaction_id', 'refund_reason', 'created_at')
        read_only_fields = ('id', 'transaction_id', 'gateway_response', 'status', 'processed_at',
                           'failed_at', 'refunded_at', 'created_at')


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Payment creation serializer"""
    
    class Meta:
        model = Payment
        fields = ('order_id', 'payment_method_id', 'method_type')
    
    def create(self, validated_data):
        from apps.orders.models import Order
        order_id = validated_data.pop('order_id')
        order = Order.objects.get(id=order_id)
        
        payment = Payment.objects.create(
            order=order,
            user=self.context['request'].user,
            amount=order.total_amount,
            method_type=validated_data.get('method_type', 'CARD'),
            status=Payment.Status.PROCESSING
        )
        
        # Mock payment processing
        import uuid
        payment.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        payment.status = Payment.Status.COMPLETED
        payment.processed_at = timezone.now()
        payment.save()
        
        return payment


class RefundSerializer(serializers.ModelSerializer):
    """Refund serializer"""
    payment = PaymentSerializer(read_only=True)
    order = OrderSerializer(read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Refund
        fields = ('id', 'payment', 'order', 'order_number', 'amount', 'reason', 'status',
                  'refund_transaction_id', 'processed_at', 'processed_by', 'created_at')
        read_only_fields = ('id', 'refund_transaction_id', 'processed_at', 'processed_by', 'created_at')


class WalletSerializer(serializers.ModelSerializer):
    """Wallet serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Wallet
        fields = ('id', 'user', 'user_email', 'balance', 'currency', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Wallet transaction serializer"""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = WalletTransaction
        fields = ('id', 'wallet', 'transaction_type', 'source', 'amount', 'balance_after',
                  'description', 'order', 'order_number', 'payment', 'refund',
                  'gateway_transaction_id', 'created_at')
        read_only_fields = ('id', 'wallet', 'balance_after', 'created_at')

