"""
Admin-specific models for RBAC, API tokens, sessions, and environment management
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import secrets
import uuid

User = get_user_model()


class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Role(TimestampMixin):
    """Admin roles with hierarchical permissions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(default=False)  # System roles cannot be deleted
    parent_role = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_roles')
    
    class Meta:
        db_table = 'admin_roles'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Permission(TimestampMixin):
    """Granular permissions"""
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=100, blank=True)  # e.g., 'user', 'order', 'restaurant'
    action = models.CharField(max_length=50, blank=True)  # e.g., 'view', 'edit', 'delete', 'approve'
    
    class Meta:
        db_table = 'admin_permissions'
        ordering = ['resource_type', 'action']
    
    def __str__(self):
        return f"{self.resource_type}.{self.action}" if self.resource_type else self.name


class RolePermission(TimestampMixin):
    """Many-to-many relationship between roles and permissions"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    resource_id = models.CharField(max_length=100, blank=True)  # For resource-level permissions
    
    class Meta:
        db_table = 'admin_role_permissions'
        unique_together = [['role', 'permission', 'resource_id']]
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.codename}"


class AdminUser(TimestampMixin):
    """Extended admin user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_users')
    is_active = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=255, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'admin_users'
    
    def __str__(self):
        return f"Admin: {self.user.email}"


class APIToken(TimestampMixin):
    """Scoped API tokens for automation"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    name = models.CharField(max_length=255)
    token = models.CharField(max_length=64, unique=True, db_index=True)
    token_prefix = models.CharField(max_length=8)  # First 8 chars for display
    scopes = models.JSONField(default=list)  # List of permission codenames
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    rate_limit = models.IntegerField(default=1000, validators=[MinValueValidator(1)])  # Requests per hour
    
    class Meta:
        db_table = 'admin_api_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.token_prefix}...)"
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(48)
            self.token_prefix = self.token[:8]
        super().save(*args, **kwargs)
    
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class AdminSession(TimestampMixin):
    """Admin session tracking"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_sessions')
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'admin_sessions'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"Session for {self.user.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class Environment(TimestampMixin):
    """Environment configuration (staging/prod/canary)"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_production = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=True)
    api_base_url = models.URLField(blank=True)
    database_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'admin_environments'
        ordering = ['name']
    
    def __str__(self):
        return self.display_name


class EnvironmentAccess(TimestampMixin):
    """User access to environments"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='environment_accesses')
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='accesses')
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='granted_accesses')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'admin_environment_accesses'
        unique_together = [['user', 'environment']]
    
    def __str__(self):
        return f"{self.user.email} - {self.environment.name}"


class SSOProvider(TimestampMixin):
    """SSO provider configuration"""
    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=50)  # 'SAML', 'OIDC', 'OAUTH2'
    is_active = models.BooleanField(default=True)
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    metadata_url = models.URLField(blank=True)
    sso_url = models.URLField(blank=True)
    entity_id = models.CharField(max_length=255, blank=True)
    certificate = models.TextField(blank=True)  # For SAML
    config = models.JSONField(default=dict)  # Additional provider-specific config
    
    class Meta:
        db_table = 'admin_sso_providers'
    
    def __str__(self):
        return f"{self.name} ({self.provider_type})"


class AuditLogEntry(TimestampMixin):
    """Immutable audit log for admin actions"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_log_entries')
    action = models.CharField(max_length=100)  # e.g., 'user.ban', 'order.refund'
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100)
    before_state = models.JSONField(default=dict, blank=True)
    after_state = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    environment = models.ForeignKey(Environment, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'admin_audit_log_entries'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} on {self.resource_type}:{self.resource_id} by {self.user.email if self.user else 'System'}"


class DeadLetterQueue(TimestampMixin):
    """Dead-letter queue for failed event broadcasts"""
    from apps.events.models import Event
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RETRYING = 'RETRYING', 'Retrying'
        FAILED = 'FAILED', 'Failed'
        RESOLVED = 'RESOLVED', 'Resolved'
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='dlq_entries')
    channel_group = models.CharField(max_length=255)  # e.g., 'customer_1', 'restaurant_2', 'admin'
    error_message = models.TextField()
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    failed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_dlq_entries')
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'dead_letter_queue'
        indexes = [
            models.Index(fields=['status', 'failed_at']),
            models.Index(fields=['channel_group', 'status']),
            models.Index(fields=['event']),
        ]
        ordering = ['-failed_at']
    
    def __str__(self):
        return f"DLQ Entry for event {self.event.event_id} on {self.channel_group} - {self.status}"
