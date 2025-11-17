"""
Automation and workflow models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AutomationRule(TimestampMixin):
    """Automation rules for workflow automation"""
    class TriggerType(models.TextChoices):
        EVENT = 'EVENT', 'Event'
        METRIC = 'METRIC', 'Metric'
        SCHEDULE = 'SCHEDULE', 'Schedule'
        WEBHOOK = 'WEBHOOK', 'Webhook'
    
    class ActionType(models.TextChoices):
        SEND_NOTIFICATION = 'SEND_NOTIFICATION', 'Send Notification'
        CREATE_TICKET = 'CREATE_TICKET', 'Create Ticket'
        REFUND = 'REFUND', 'Issue Refund'
        SUSPEND_PARTNER = 'SUSPEND_PARTNER', 'Suspend Partner'
        UPDATE_STATUS = 'UPDATE_STATUS', 'Update Status'
        WEBHOOK = 'WEBHOOK', 'Trigger Webhook'
        EMAIL = 'EMAIL', 'Send Email'
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trigger_type = models.CharField(max_length=20, choices=TriggerType.choices)
    trigger_config = models.JSONField(default=dict)  # Event name, metric thresholds, etc.
    conditions = models.JSONField(default=list)  # List of condition objects
    action_type = models.CharField(max_length=30, choices=ActionType.choices)
    action_config = models.JSONField(default=dict)  # Action-specific configuration
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'automation_rules'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return self.name


class ScheduledJob(TimestampMixin):
    """Scheduled jobs (cron-like)"""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    job_type = models.CharField(max_length=100)  # 'settlement_run', 'data_sync', 'report', etc.
    cron_expression = models.CharField(max_length=100)  # e.g., '0 2 * * *' (daily at 2 AM)
    config = models.JSONField(default=dict)  # Job-specific configuration
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    next_run_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    class Meta:
        db_table = 'scheduled_jobs'
        ordering = ['next_run_at']
    
    def __str__(self):
        return self.name


class JobExecution(TimestampMixin):
    """Job execution history"""
    job = models.ForeignKey(ScheduledJob, on_delete=models.CASCADE, related_name='executions')
    status = models.CharField(max_length=20, default='PENDING')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    output = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'job_executions'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.job.name} - {self.started_at}"


class Webhook(TimestampMixin):
    """Webhook configuration"""
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        FAILING = 'FAILING', 'Failing'
    
    name = models.CharField(max_length=255)
    url = models.URLField()
    events = models.JSONField(default=list)  # List of events to trigger on
    secret = models.CharField(max_length=255, blank=True)  # For signature verification
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    retry_policy = models.JSONField(default=dict)  # {max_retries: 3, backoff: 'exponential'}
    headers = models.JSONField(default=dict)  # Custom headers
    is_active = models.BooleanField(default=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'webhooks'
    
    def __str__(self):
        return f"{self.name} - {self.url}"


class WebhookDelivery(TimestampMixin):
    """Webhook delivery attempts"""
    webhook = models.ForeignKey(Webhook, on_delete=models.CASCADE, related_name='deliveries')
    event = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    attempt_number = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'webhook_deliveries'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.webhook.name} - {self.event} - {self.created_at}"

