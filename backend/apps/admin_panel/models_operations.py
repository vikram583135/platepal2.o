"""
System operations models
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


class SystemHealthMetric(TimestampMixin):
    """System health metrics"""
    service_name = models.CharField(max_length=100)
    metric_type = models.CharField(max_length=50)  # 'latency', 'error_rate', 'queue_size', 'cpu', 'memory'
    value = models.FloatField()
    threshold_warning = models.FloatField(null=True, blank=True)
    threshold_critical = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, default='healthy')  # 'healthy', 'warning', 'critical'
    
    class Meta:
        db_table = 'system_health_metrics'
        indexes = [
            models.Index(fields=['service_name', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.service_name} - {self.metric_type}: {self.value}"


class AlertRule(TimestampMixin):
    """Alert rules for system monitoring"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    service_name = models.CharField(max_length=100)
    metric_type = models.CharField(max_length=50)
    condition = models.CharField(max_length=20)  # 'gt', 'lt', 'eq', 'gte', 'lte'
    threshold = models.FloatField()
    severity = models.CharField(max_length=20, default='warning')  # 'info', 'warning', 'critical'
    is_active = models.BooleanField(default=True)
    notification_channels = models.JSONField(default=list)  # ['slack', 'email', 'pagerduty']
    
    class Meta:
        db_table = 'alert_rules'
    
    def __str__(self):
        return self.name


class Incident(TimestampMixin):
    """System incidents"""
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        INVESTIGATING = 'INVESTIGATING', 'Investigating'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'
    
    class Severity(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MEDIUM)
    affected_services = models.JSONField(default=list)
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_incidents')
    root_cause = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    
    class Meta:
        db_table = 'incidents'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.status}"


class IncidentUpdate(TimestampMixin):
    """Incident updates/communications"""
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name='updates')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    is_public = models.BooleanField(default=False)  # Public status update
    
    class Meta:
        db_table = 'incident_updates'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Update for {self.incident.title}"


class RateLimitRule(TimestampMixin):
    """Rate limiting rules"""
    name = models.CharField(max_length=255)
    endpoint_pattern = models.CharField(max_length=255)  # e.g., '/api/orders/*'
    role = models.CharField(max_length=50, blank=True)  # If empty, applies to all
    requests_per_minute = models.IntegerField(default=60)
    requests_per_hour = models.IntegerField(default=1000)
    burst_limit = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'rate_limit_rules'
    
    def __str__(self):
        return f"{self.name} - {self.endpoint_pattern}"


class IPWhitelist(TimestampMixin):
    """IP whitelist for high-privileged access"""
    ip_address = models.GenericIPAddressField()
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'ip_whitelist'
        unique_together = [['ip_address']]
    
    def __str__(self):
        return f"{self.ip_address} - {self.description}"


class IPBlacklist(TimestampMixin):
    """IP blacklist"""
    ip_address = models.GenericIPAddressField()
    reason = models.TextField()
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ip_blacklist'
        unique_together = [['ip_address']]
    
    def __str__(self):
        return f"{self.ip_address} - {self.reason}"


class MaintenanceWindow(TimestampMixin):
    """Scheduled maintenance windows"""
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    affected_services = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    user_message = models.TextField(blank=True)  # Message to show users
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'maintenance_windows'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_time}"

