"""
Serializers for payments app
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Payment, Refund, Wallet, WalletTransaction, SettlementCycle, Payout
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
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user is None or getattr(order, 'customer', None) != user:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'order_id': 'Not authorized to create payment for this order'})
        
        payment = Payment.objects.create(
            order=order,
            user=user,
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


class SettlementCycleSerializer(serializers.ModelSerializer):
    """Settlement cycle serializer"""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_id = serializers.IntegerField(source='restaurant.id', read_only=True)
    
    class Meta:
        model = SettlementCycle
        fields = ('id', 'restaurant', 'restaurant_id', 'restaurant_name', 'cycle_start', 'cycle_end',
                  'total_sales', 'commission_amount', 'packaging_fee', 'delivery_fee_share',
                  'tax_amount', 'net_payout', 'status', 'processed_at', 'payout_reference',
                  'notes', 'created_at', 'updated_at')
        read_only_fields = ('id', 'restaurant', 'created_at', 'updated_at')


class PayoutSerializer(serializers.ModelSerializer):
    """Payout serializer"""
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_id = serializers.IntegerField(source='restaurant.id', read_only=True)
    settlement_cycle_end = serializers.DateTimeField(source='settlement.cycle_end', read_only=True)
    settlement_id = serializers.IntegerField(source='settlement.id', read_only=True)
    
    class Meta:
        model = Payout
        fields = ('id', 'settlement', 'settlement_id', 'settlement_cycle_end', 'restaurant',
                  'restaurant_id', 'restaurant_name', 'amount', 'bank_account_number',
                  'bank_ifsc_code', 'bank_name', 'account_holder_name', 'status',
                  'initiated_at', 'processed_at', 'utr_number', 'failure_reason',
                  'gateway_response', 'created_at', 'updated_at')
        read_only_fields = ('id', 'settlement', 'restaurant', 'created_at', 'updated_at')
