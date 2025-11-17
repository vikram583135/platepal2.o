"""
Advanced feature models
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class FraudDetectionRule(TimestampMixin):
    """Fraud detection rules"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=50)  # 'transaction_amount', 'velocity', 'pattern', etc.
    conditions = models.JSONField(default=dict)
    action = models.CharField(max_length=50)  # 'block', 'flag', 'require_verification'
    risk_score_threshold = models.IntegerField(default=70)  # 0-100
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'fraud_detection_rules'
    
    def __str__(self):
        return self.name


class FraudFlag(TimestampMixin):
    """Fraud flags on transactions/users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    payment = models.ForeignKey('payments.Payment', on_delete=models.CASCADE, null=True, blank=True)
    risk_score = models.IntegerField()  # 0-100
    reason = models.TextField()
    rule_triggered = models.ForeignKey(FraudDetectionRule, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')  # 'PENDING', 'REVIEWED', 'FALSE_POSITIVE', 'CONFIRMED'
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_fraud_flags')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'fraud_flags'
        ordering = ['-risk_score', '-created_at']
    
    def __str__(self):
        return f"Fraud flag - Risk: {self.risk_score}"


class IPBlacklistEntry(TimestampMixin):
    """IP blacklist for fraud prevention"""
    ip_address = models.GenericIPAddressField(unique=True)
    reason = models.TextField()
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'fraud_ip_blacklist'
    
    def __str__(self):
        return f"{self.ip_address} - {self.reason}"


class Chargeback(TimestampMixin):
    """Chargeback management"""
    class Status(models.TextChoices):
        RECEIVED = 'RECEIVED', 'Received'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        EVIDENCE_SUBMITTED = 'EVIDENCE_SUBMITTED', 'Evidence Submitted'
        WON = 'WON', 'Won'
        LOST = 'LOST', 'Lost'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
    
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    payment = models.ForeignKey('payments.Payment', on_delete=models.CASCADE)
    chargeback_id = models.CharField(max_length=255, unique=True)
    reason = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.RECEIVED)
    received_date = models.DateTimeField()
    due_date = models.DateTimeField()
    evidence_bundle = models.JSONField(default=list)  # List of evidence file URLs
    notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'chargebacks'
        ordering = ['-received_date']
    
    def __str__(self):
        return f"Chargeback {self.chargeback_id} - {self.order.order_number}"


class FeatureFlag(TimestampMixin):
    """Feature flags for gradual rollouts"""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_enabled = models.BooleanField(default=False)
    rollout_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    target_audience = models.JSONField(default=dict)  # {roles: [], user_ids: [], etc.}
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'feature_flags'
    
    def __str__(self):
        return f"{self.name} - {self.rollout_percentage}%"


class FeatureFlagHistory(TimestampMixin):
    """Feature flag change history"""
    flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    before_state = models.JSONField(default=dict)
    after_state = models.JSONField(default=dict)
    reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'feature_flag_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"History for {self.flag.name}"


class SLO(TimestampMixin):
    """Service Level Objective"""
    service_name = models.CharField(max_length=100)
    metric_name = models.CharField(max_length=100)  # 'latency', 'error_rate', 'availability'
    target_value = models.FloatField()
    current_value = models.FloatField(null=True, blank=True)
    window_days = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'slos'
        unique_together = [['service_name', 'metric_name']]
    
    def __str__(self):
        return f"{self.service_name} - {self.metric_name}: {self.target_value}"

