"""
Views for payments app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Payment, Refund, Wallet, WalletTransaction
from .serializers import PaymentSerializer, PaymentCreateSerializer, RefundSerializer, WalletSerializer, WalletTransactionSerializer
from apps.accounts.permissions import IsOwnerOrAdmin


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
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RefundViewSet(viewsets.ModelViewSet):
    """Refund viewset"""
    serializer_class = RefundSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Refund.objects.filter(is_deleted=False)
        return Refund.objects.filter(payment__user=user, is_deleted=False)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def process(self, request, pk=None):
        """Process refund (admin only)"""
        if request.user.role != 'ADMIN':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        refund = self.get_object()
        
        if refund.status != Refund.Status.PENDING:
            return Response({'error': 'Refund already processed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mock refund processing
        import uuid
        refund.status = Refund.Status.COMPLETED
        refund.refund_transaction_id = f"REF-{uuid.uuid4().hex[:12].upper()}"
        refund.processed_at = timezone.now()
        refund.processed_by = request.user
        refund.save()
        
        # Update payment
        refund.payment.status = Payment.Status.REFUNDED
        refund.payment.refund_amount = refund.amount
        refund.payment.refund_transaction_id = refund.refund_transaction_id
        refund.payment.refunded_at = timezone.now()
        refund.payment.save()
        
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
        order = Order.objects.get(id=order_id, user=request.user)
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
def confirm_payment(request):
    """Confirm payment after gateway processing"""
    order_id = request.data.get('order_id')
    payment_intent_id = request.data.get('payment_intent_id')
    transaction_id = request.data.get('transaction_id')
    payment_method = request.data.get('payment_method')
    
    if not order_id or not transaction_id:
        return Response({'error': 'order_id and transaction_id are required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    
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
    order.status = Order.Status.CONFIRMED
    order.save()
    
    return Response(PaymentSerializer(payment).data)


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
