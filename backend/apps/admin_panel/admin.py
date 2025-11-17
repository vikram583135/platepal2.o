from django.contrib import admin
from .models import (
    Role, Permission, RolePermission, AdminUser, APIToken,
    AdminSession, Environment, EnvironmentAccess, SSOProvider, AuditLogEntry
)
from .models_operations import (
    SystemHealthMetric, AlertRule, Incident, IncidentUpdate,
    RateLimitRule, IPWhitelist, IPBlacklist, MaintenanceWindow
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_system', 'parent_role', 'created_at')
    list_filter = ('is_system', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'resource_type', 'action')
    list_filter = ('resource_type', 'action')
    search_fields = ('name', 'codename', 'description')


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'two_factor_enabled', 'last_login_ip')
    list_filter = ('is_active', 'two_factor_enabled', 'role')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'token_prefix', 'is_active', 'expires_at', 'last_used_at')
    list_filter = ('is_active', 'expires_at')
    search_fields = ('name', 'user__email', 'token_prefix')
    readonly_fields = ('token', 'token_prefix', 'last_used_at', 'last_used_ip')


@admin.register(AdminSession)
class AdminSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'is_active', 'expires_at', 'last_activity')
    list_filter = ('is_active', 'expires_at')
    search_fields = ('user__email', 'session_key', 'ip_address')


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'is_production', 'requires_approval', 'is_active')
    list_filter = ('is_production', 'requires_approval', 'is_active')


@admin.register(SSOProvider)
class SSOProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider_type', 'is_active')
    list_filter = ('provider_type', 'is_active')


@admin.register(AuditLogEntry)
class AuditLogEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'resource_type', 'resource_id', 'created_at')
    list_filter = ('action', 'resource_type', 'created_at')
    search_fields = ('user__email', 'action', 'resource_type', 'resource_id')
    readonly_fields = ('user', 'action', 'resource_type', 'resource_id', 'before_state', 'after_state', 'ip_address', 'user_agent', 'environment', 'reason', 'metadata', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'severity', 'reported_by', 'created_at')
    list_filter = ('status', 'severity', 'created_at')
    search_fields = ('title', 'description')


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_name', 'metric_type', 'severity', 'is_active')
    list_filter = ('severity', 'is_active', 'service_name')


@admin.register(RateLimitRule)
class RateLimitRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'endpoint_pattern', 'role', 'requests_per_minute', 'is_active')
    list_filter = ('is_active', 'role')


from .models_advanced import (
    FraudDetectionRule, FraudFlag, Chargeback, FeatureFlag, SLO
)

@admin.register(FraudDetectionRule)
class FraudDetectionRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'action', 'risk_score_threshold', 'is_active')
    list_filter = ('rule_type', 'is_active')


@admin.register(FraudFlag)
class FraudFlagAdmin(admin.ModelAdmin):
    list_display = ('user', 'order', 'risk_score', 'status', 'created_at')
    list_filter = ('status', 'risk_score', 'created_at')


@admin.register(Chargeback)
class ChargebackAdmin(admin.ModelAdmin):
    list_display = ('chargeback_id', 'order', 'amount', 'status', 'received_date')
    list_filter = ('status', 'received_date')


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_enabled', 'rollout_percentage', 'created_at')
    list_filter = ('is_enabled',)


@admin.register(SLO)
class SLOAdmin(admin.ModelAdmin):
    list_display = ('service_name', 'metric_name', 'target_value', 'current_value', 'is_active')
    list_filter = ('service_name', 'is_active')

