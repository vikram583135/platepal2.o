from django.db import models
from apps.accounts.models import User, PaymentMethod, TimestampMixin, SoftDeleteMixin
from apps.orders.models import Order


class Payment(TimestampMixin, SoftDeleteMixin):
    """Payment transactions"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class PaymentMethodType(models.TextChoices):
        CARD = 'CARD', 'Credit/Debit Card'
        UPI = 'UPI', 'UPI'
        WALLET = 'WALLET', 'Wallet'
        CASH = 'CASH', 'Cash on Delivery'
        NET_BANKING = 'NET_BANKING', 'Net Banking'
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    method_type = models.CharField(max_length=20, choices=PaymentMethodType.choices)
    
    # Amounts
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Transaction details
    transaction_id = models.CharField(max_length=255, unique=True, blank=True)  # Gateway transaction ID
    gateway_response = models.JSONField(default=dict)  # Full gateway response
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Timestamps
    processed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # Failure details
    failure_reason = models.TextField(blank=True)
    failure_code = models.CharField(max_length=100, blank=True)
    
    # Refund details
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    refund_transaction_id = models.CharField(max_length=255, blank=True)
    refund_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payments'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id or 'N/A'} for {self.order.order_number}"


class Refund(TimestampMixin, SoftDeleteMixin):
    """Refund records"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    refund_transaction_id = models.CharField(max_length=255, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds')
    
    class Meta:
        db_table = 'refunds'
        indexes = [
            models.Index(fields=['payment']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Refund for {self.order.order_number} - {self.amount}"


class Wallet(TimestampMixin, SoftDeleteMixin):
    """User wallet for storing money"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='INR')
    
    class Meta:
        db_table = 'wallets'
        indexes = [
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"Wallet for {self.user.email} - {self.balance} {self.currency}"


class WalletTransaction(TimestampMixin):
    """Wallet transaction history"""
    
    class TransactionType(models.TextChoices):
        CREDIT = 'CREDIT', 'Credit'
        DEBIT = 'DEBIT', 'Debit'
    
    class TransactionSource(models.TextChoices):
        ADD_MONEY = 'ADD_MONEY', 'Add Money'
        ORDER_PAYMENT = 'ORDER_PAYMENT', 'Order Payment'
        REFUND = 'REFUND', 'Refund'
        CASHBACK = 'CASHBACK', 'Cashback'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    source = models.CharField(max_length=20, choices=TransactionSource.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)  # Balance after this transaction
    description = models.TextField(blank=True)
    
    # Related entities
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    refund = models.ForeignKey(Refund, on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    
    # Payment gateway details for add money
    gateway_transaction_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'wallet_transactions'
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['transaction_type', 'source']),
            models.Index(fields=['order']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} {self.amount} - {self.wallet.user.email}"


class SettlementCycle(TimestampMixin, SoftDeleteMixin):
    """Settlement cycles for restaurant payouts"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='settlements')
    cycle_start = models.DateTimeField()
    cycle_end = models.DateTimeField()
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    packaging_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee_share = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    processed_at = models.DateTimeField(null=True, blank=True)
    payout_reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'settlement_cycles'
        indexes = [
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['cycle_start', 'cycle_end']),
            models.Index(fields=['status']),
        ]
        ordering = ['-cycle_end']
    
    def __str__(self):
        return f"Settlement for {self.restaurant.name} - {self.cycle_end.date()}"


class Payout(TimestampMixin, SoftDeleteMixin):
    """Individual payout transactions to restaurant bank accounts"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        INITIATED = 'INITIATED', 'Initiated'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        REVERSED = 'REVERSED', 'Reversed'
    
    settlement = models.ForeignKey(SettlementCycle, on_delete=models.CASCADE, related_name='payouts')
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc_code = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=255, blank=True)
    account_holder_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    initiated_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    utr_number = models.CharField(max_length=100, blank=True)  # UTR for bank transfers
    failure_reason = models.TextField(blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'payouts'
        indexes = [
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['settlement']),
            models.Index(fields=['status', 'initiated_at']),
        ]
        ordering = ['-initiated_at']
    
    def __str__(self):
        return f"Payout {self.amount} to {self.restaurant.name} - {self.status}"


class ReconciliationReport(TimestampMixin, SoftDeleteMixin):
    """Reconciliation reports for financial audits"""
    
    settlement = models.ForeignKey(SettlementCycle, on_delete=models.CASCADE, related_name='reconciliation_reports')
    restaurant = models.ForeignKey('restaurants.Restaurant', on_delete=models.CASCADE, related_name='reconciliation_reports')
    report_type = models.CharField(max_length=50, default='MONTHLY')
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    total_orders = models.IntegerField(default=0)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_refunds = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discrepancies = models.JSONField(default=list, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_reports')
    file_path = models.CharField(max_length=500, blank=True)  # Path to PDF/Excel file
    
    class Meta:
        db_table = 'reconciliation_reports'
        indexes = [
            models.Index(fields=['restaurant', 'period_start', 'period_end']),
            models.Index(fields=['settlement']),
        ]
        ordering = ['-period_end']
    
    def __str__(self):
        return f"Reconciliation Report for {self.restaurant.name} - {self.period_end.date()}"