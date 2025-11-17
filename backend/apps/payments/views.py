"""
Views for payments app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from .models import Payment, Refund, Wallet, WalletTransaction, SettlementCycle, Payout
from .serializers import PaymentSerializer, PaymentCreateSerializer, RefundSerializer, WalletSerializer, WalletTransactionSerializer
from apps.accounts.permissions import IsOwnerOrAdmin
from apps.events.broadcast import EventBroadcastService
import logging

logger = logging.getLogger(__name__)


class PaymentViewSet(viewsets.ModelViewSet):
    """Payment viewset"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Payment.objects.filter(is_deleted=False)
        return Payment.objects.filter(user=user, is_deleted=False)
    
    @transaction.atomic
    def perform_create(self, serializer):
        payment = serializer.save(user=self.request.user)
        
        # Create payment.captured or payment.failed event based on status
        if payment.status == Payment.Status.COMPLETED:
            EventBroadcastService.broadcast_to_multiple(
                event_type='payment.captured',
                aggregate_type='Payment',
                aggregate_id=str(payment.id),
                payload=PaymentSerializer(payment).data,
                customer_id=payment.user.id,
                restaurant_id=payment.order.restaurant.id,
                include_admin=True,
            )
        elif payment.status == Payment.Status.FAILED:
            EventBroadcastService.broadcast_to_admin(
                event_type='payment.failed',
                aggregate_type='Payment',
                aggregate_id=str(payment.id),
                payload={
                    **PaymentSerializer(payment).data,
                    'failure_reason': payment.failure_reason,
                    'failure_code': payment.failure_code,
                }
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    @transaction.atomic
    def capture(self, request, pk=None):
        """Capture payment (for deferred payments)"""
        payment = self.get_object()
        
        if payment.status != Payment.Status.PENDING:
            return Response({'error': 'Payment cannot be captured'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mock capture - in production, integrate with payment gateway
        import uuid
        payment.status = Payment.Status.COMPLETED
        payment.transaction_id = payment.transaction_id or f"TXN-{uuid.uuid4().hex[:12].upper()}"
        payment.processed_at = timezone.now()
        payment.save()
        
        # Broadcast payment.captured event
        EventBroadcastService.broadcast_to_multiple(
            event_type='payment.captured',
            aggregate_type='Payment',
            aggregate_id=str(payment.id),
            payload=PaymentSerializer(payment).data,
            customer_id=payment.user.id,
            restaurant_id=payment.order.restaurant.id,
            include_admin=True,
        )
        
        return Response(PaymentSerializer(payment).data)


class RefundViewSet(viewsets.ModelViewSet):
    """Refund viewset"""
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Refund.objects.filter(is_deleted=False)
        return Refund.objects.filter(payment__user=user, is_deleted=False)
    
    @transaction.atomic
    def perform_create(self, serializer):
        """Create refund and emit refund.initiated event"""
        refund = serializer.save()
        
        # Create refund.initiated event
        EventBroadcastService.broadcast_to_multiple(
            event_type='refund.initiated',
            aggregate_type='Refund',
            aggregate_id=str(refund.id),
            payload=RefundSerializer(refund).data,
            customer_id=refund.payment.user.id,
            restaurant_id=refund.order.restaurant.id if hasattr(refund, 'order') else None,
            include_admin=True,
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    @transaction.atomic
    def process(self, request, pk=None):
        """Process refund (admin only)"""
        if request.user.role != 'ADMIN':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        refund = self.get_object()
        
        if refund.status not in [Refund.Status.PENDING, Refund.Status.PROCESSING]:
            return Response({'error': 'Refund already processed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mock refund processing - in production, integrate with payment gateway
        import uuid
        refund.status = Refund.Status.COMPLETED
        refund.refund_transaction_id = refund.refund_transaction_id or f"REF-{uuid.uuid4().hex[:12].upper()}"
        refund.processed_at = timezone.now()
        refund.processed_by = request.user
        refund.save()
        
        # Update payment
        refund.payment.status = Payment.Status.REFUNDED
        refund.payment.refund_amount = refund.amount
        refund.payment.refund_transaction_id = refund.refund_transaction_id
        refund.payment.refunded_at = timezone.now()
        refund.payment.save()
        
        # Update wallet if applicable
        if refund.payment.method_type == Payment.PaymentMethodType.WALLET:
            wallet, _ = Wallet.objects.get_or_create(
                user=refund.payment.user,
                defaults={'balance': 0.00, 'currency': 'INR'}
            )
            from decimal import Decimal
            wallet.balance += Decimal(str(refund.amount))
            wallet.save()
            
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=WalletTransaction.TransactionType.CREDIT,
                source=WalletTransaction.TransactionSource.REFUND,
                amount=Decimal(str(refund.amount)),
                balance_after=wallet.balance,
                description=f'Refund for order {refund.order.order_number if hasattr(refund, "order") else ""}',
                refund=refund,
            )
        
        # Broadcast refund.completed event
        EventBroadcastService.broadcast_to_multiple(
            event_type='refund.completed',
            aggregate_type='Refund',
            aggregate_id=str(refund.id),
            payload=RefundSerializer(refund).data,
            customer_id=refund.payment.user.id,
            restaurant_id=refund.order.restaurant.id if hasattr(refund, 'order') else None,
            include_admin=True,
        )
        
        return Response(RefundSerializer(refund).data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def timeline(self, request, pk=None):
        """Get refund timeline"""
        refund = self.get_object()
        
        if refund.payment.user != request.user and request.user.role != 'ADMIN':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        timeline = []
        
        # Refund requested
        timeline.append({
            'status': 'REQUESTED',
            'label': 'Refund Requested',
            'timestamp': refund.created_at.isoformat(),
            'completed': True,
        })
        
        # Processing
        if refund.status == Refund.Status.PROCESSING:
            timeline.append({
                'status': 'PROCESSING',
                'label': 'Processing Refund',
                'timestamp': timezone.now().isoformat(),
                'completed': False,
            })
        elif refund.status in [Refund.Status.COMPLETED, Refund.Status.FAILED]:
            timeline.append({
                'status': 'PROCESSING',
                'label': 'Processing Refund',
                'timestamp': refund.created_at.isoformat(),
                'completed': True,
            })
        
        # Completed or Failed
        if refund.status == Refund.Status.COMPLETED:
            timeline.append({
                'status': 'COMPLETED',
                'label': 'Refund Completed',
                'timestamp': refund.processed_at.isoformat() if refund.processed_at else timezone.now().isoformat(),
                'completed': True,
            })
        elif refund.status == Refund.Status.FAILED:
            timeline.append({
                'status': 'FAILED',
                'label': 'Refund Failed',
                'timestamp': timezone.now().isoformat(),
                'completed': True,
            })
        
        return Response({'timeline': timeline})


from rest_framework.decorators import api_view
from apps.orders.models import Order
import uuid


@api_view(['POST'])
def create_payment_intent(request):
    """Create payment intent for gateway integration"""
    order_id = request.data.get('order_id')
    payment_method = request.data.get('payment_method')  # CARD, UPI, WALLET, CASH, NET_BANKING
    amount = request.data.get('amount')
    
    if not order_id or not payment_method or not amount:
        return Response({'error': 'order_id, payment_method, and amount are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Create payment intent (mock - in production, integrate with Razorpay/Stripe)
    payment_intent_id = f"pi_{uuid.uuid4().hex[:24]}"
    
    # Mock gateway response
    gateway_response = {
        'payment_intent_id': payment_intent_id,
        'client_secret': f"secret_{uuid.uuid4().hex[:32]}",
        'status': 'requires_payment_method',
    }
    
    # For UPI, return UPI details
    if payment_method == 'UPI':
        gateway_response['upi_id'] = f"platepal@{request.data.get('upi_provider', 'paytm')}"
        gateway_response['qr_code'] = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={gateway_response['upi_id']}"
    
    return Response(gateway_response)


@api_view(['POST'])
@transaction.atomic
def confirm_payment(request):
    """Confirm payment after gateway processing"""
    from apps.orders.models import Order
    
    order_id = request.data.get('order_id')
    payment_intent_id = request.data.get('payment_intent_id')
    transaction_id = request.data.get('transaction_id')
    payment_method = request.data.get('payment_method')
    payment_status = request.data.get('status', 'completed')  # 'completed' or 'failed'
    failure_reason = request.data.get('failure_reason', '')
    failure_code = request.data.get('failure_code', '')
    
    if not order_id:
        return Response({'error': 'order_id is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Handle payment failure
    if payment_status == 'failed':
        # Create or update payment with failed status
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'user': request.user,
                'method_type': payment_method or Payment.PaymentMethodType.CASH,
                'amount': order.total_amount,
                'transaction_id': transaction_id or f"TXN-FAIL-{uuid.uuid4().hex[:12].upper()}",
                'status': Payment.Status.FAILED,
                'failure_reason': failure_reason or 'Payment failed',
                'failure_code': failure_code or 'GATEWAY_ERROR',
            }
        )
        
        if not created:
            payment.status = Payment.Status.FAILED
            payment.failure_reason = failure_reason or 'Payment failed'
            payment.failure_code = failure_code or 'GATEWAY_ERROR'
            if transaction_id:
                payment.transaction_id = transaction_id
            payment.save()
        
        # Broadcast payment.failed event
        EventBroadcastService.broadcast_to_multiple(
            event_type='payment.failed',
            aggregate_type='Payment',
            aggregate_id=str(payment.id),
            payload={
                **PaymentSerializer(payment).data,
                'failure_reason': payment.failure_reason,
                'failure_code': payment.failure_code,
            },
            customer_id=payment.user.id,
            restaurant_id=order.restaurant.id,
            include_admin=True,
        )
        
        # Optionally cancel order if payment fails
        # order.status = Order.Status.CANCELLED
        # order.cancellation_reason = f"Payment failed: {failure_reason}"
        # order.cancelled_at = timezone.now()
        # order.save()
        
        return Response({
            'status': 'failed',
            'payment': PaymentSerializer(payment).data,
            'message': failure_reason or 'Payment failed'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle successful payment
    if not transaction_id:
        return Response({'error': 'transaction_id is required for successful payment'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    # Create or update payment
    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={
            'user': request.user,
            'method_type': payment_method or Payment.PaymentMethodType.CASH,
            'amount': order.total_amount,
            'transaction_id': transaction_id,
            'status': Payment.Status.COMPLETED,
            'processed_at': timezone.now(),
        }
    )
    
    if not created:
        payment.status = Payment.Status.COMPLETED
        payment.transaction_id = transaction_id
        payment.processed_at = timezone.now()
        payment.save()
    
    # Update order status
    if order.status == Order.Status.PENDING:
        order.status = Order.Status.CONFIRMED
        order.save()
    
    # Broadcast payment.captured event
    EventBroadcastService.broadcast_to_multiple(
        event_type='payment.captured',
        aggregate_type='Payment',
        aggregate_id=str(payment.id),
        payload=PaymentSerializer(payment).data,
        customer_id=payment.user.id,
        restaurant_id=order.restaurant.id,
        include_admin=True,
    )
    
    return Response({
        'status': 'completed',
        'payment': PaymentSerializer(payment).data
    })


class WalletViewSet(viewsets.ModelViewSet):
    """Wallet viewset"""
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user, is_deleted=False)
    
    def get_object(self):
        wallet, created = Wallet.objects.get_or_create(
            user=self.request.user,
            defaults={'balance': 0.00, 'currency': 'INR'}
        )
        return wallet
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def balance(self, request):
        """Get wallet balance"""
        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': 0.00, 'currency': 'INR'}
        )
        return Response({
            'balance': str(wallet.balance),
            'currency': wallet.currency
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def add_money(self, request):
        """Add money to wallet"""
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'CARD')
        
        if not amount or float(amount) <= 0:
            return Response({'error': 'Valid amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': 0.00, 'currency': 'INR'}
        )
        
        # In production, process payment through gateway first
        # For now, directly add to wallet
        import uuid
        from decimal import Decimal
        
        amount_decimal = Decimal(str(amount))
        wallet.balance += amount_decimal
        wallet.save()
        
        # Create transaction record
        transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=WalletTransaction.TransactionType.CREDIT,
            source=WalletTransaction.TransactionSource.ADD_MONEY,
            amount=amount_decimal,
            balance_after=wallet.balance,
            description=f'Added {amount} {wallet.currency} to wallet',
            gateway_transaction_id=f"TXN_{uuid.uuid4().hex[:12].upper()}"
        )
        
        return Response({
            'message': 'Money added successfully',
            'balance': str(wallet.balance),
            'transaction': WalletTransactionSerializer(transaction).data
        })
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def history(self, request):
        """Get wallet transaction history"""
        wallet, created = Wallet.objects.get_or_create(
            user=request.user,
            defaults={'balance': 0.00, 'currency': 'INR'}
        )
        
        transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:50]
        serializer = WalletTransactionSerializer(transactions, many=True)
        return Response({'transactions': serializer.data})
