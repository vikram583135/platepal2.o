"""
Serializers for admin app
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Role, Permission, RolePermission, AdminUser, APIToken,
    AdminSession, Environment, EnvironmentAccess, SSOProvider, AuditLogEntry
)
from .models_operations import (
    SystemHealthMetric, AlertRule, Incident, IncidentUpdate,
    RateLimitRule, IPWhitelist, IPBlacklist, MaintenanceWindow
)
from .models_automation import (
    AutomationRule, ScheduledJob, JobExecution, Webhook, WebhookDelivery
)
from .models_advanced import (
    FraudDetectionRule, FraudFlag, Chargeback, FeatureFlag, FeatureFlagHistory, SLO
)
from apps.orders.models import Review
from apps.restaurants.models import Promotion

User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'description', 'resource_type', 'action']


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'is_system', 'parent_role', 'permissions', 'permission_ids']
    
    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            for perm in permissions:
                RolePermission.objects.create(role=role, permission=perm)
        return role


class AdminUserSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = AdminUser
        fields = [
            'id', 'user', 'user_email', 'user_name', 'role', 'role_name',
            'is_active', 'last_login_ip', 'failed_login_attempts', 'locked_until',
            'two_factor_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['last_login_ip', 'failed_login_attempts', 'locked_until']


class APITokenSerializer(serializers.ModelSerializer):
    token_display = serializers.SerializerMethodField()
    
    class Meta:
        model = APIToken
        fields = [
            'id', 'name', 'token_display', 'token_prefix', 'scopes',
            'expires_at', 'last_used_at', 'last_used_ip', 'is_active',
            'rate_limit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['token_display', 'token_prefix', 'last_used_at', 'last_used_ip']
    
    def get_token_display(self, obj):
        if self.context.get('show_full_token'):
            return obj.token
        return f"{obj.token_prefix}..."


class APITokenCreateSerializer(serializers.ModelSerializer):
    token = serializers.CharField(read_only=True)
    
    class Meta:
        model = APIToken
        fields = ['id', 'name', 'scopes', 'expires_at', 'rate_limit', 'token']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AdminSessionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = AdminSession
        fields = [
            'id', 'user', 'user_email', 'session_key', 'ip_address',
            'user_agent', 'is_active', 'expires_at', 'last_activity',
            'created_at'
        ]
        read_only_fields = ['session_key', 'ip_address', 'user_agent', 'expires_at']


class EnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = [
            'id', 'name', 'display_name', 'description', 'is_production',
            'requires_approval', 'api_base_url', 'database_name', 'is_active',
            'created_at', 'updated_at'
        ]


class EnvironmentAccessSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    environment_name = serializers.CharField(source='environment.display_name', read_only=True)
    granted_by_email = serializers.EmailField(source='granted_by.email', read_only=True)
    
    class Meta:
        model = EnvironmentAccess
        fields = [
            'id', 'user', 'user_email', 'environment', 'environment_name',
            'granted_by', 'granted_by_email', 'is_active', 'created_at', 'updated_at'
        ]


class SSOProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SSOProvider
        fields = [
            'id', 'name', 'provider_type', 'is_active', 'client_id',
            'metadata_url', 'sso_url', 'entity_id', 'config', 'created_at', 'updated_at'
        ]
        read_only_fields = ['client_secret']  # Never expose secret


class AuditLogEntrySerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    environment_name = serializers.CharField(source='environment.display_name', read_only=True)
    
    class Meta:
        model = AuditLogEntry
        fields = [
            'id', 'user', 'user_email', 'action', 'resource_type', 'resource_id',
            'before_state', 'after_state', 'ip_address', 'user_agent',
            'environment', 'environment_name', 'reason', 'metadata', 'created_at'
        ]
        read_only_fields = '__all__'


# Operations serializers
class SystemHealthMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemHealthMetric
        fields = [
            'id', 'service_name', 'metric_type', 'value', 'threshold_warning',
            'threshold_critical', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = [
            'id', 'name', 'description', 'service_name', 'metric_type', 'condition',
            'threshold', 'severity', 'is_active', 'notification_channels',
            'created_at', 'updated_at'
        ]


class IncidentUpdateSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = IncidentUpdate
        fields = [
            'id', 'incident', 'user', 'user_email', 'message', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class IncidentSerializer(serializers.ModelSerializer):
    reported_by_email = serializers.EmailField(source='reported_by.email', read_only=True)
    resolved_by_email = serializers.EmailField(source='resolved_by.email', read_only=True)
    updates = IncidentUpdateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'description', 'status', 'severity', 'affected_services',
            'reported_by', 'reported_by_email', 'resolved_at', 'resolved_by',
            'resolved_by_email', 'root_cause', 'resolution', 'updates',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['reported_by', 'resolved_at', 'resolved_by', 'created_at', 'updated_at']


class RateLimitRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RateLimitRule
        fields = [
            'id', 'name', 'endpoint_pattern', 'role', 'requests_per_minute',
            'requests_per_hour', 'burst_limit', 'is_active', 'created_at', 'updated_at'
        ]


class IPWhitelistSerializer(serializers.ModelSerializer):
    added_by_email = serializers.EmailField(source='added_by.email', read_only=True)
    
    class Meta:
        model = IPWhitelist
        fields = [
            'id', 'ip_address', 'description', 'is_active', 'added_by',
            'added_by_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['added_by', 'created_at', 'updated_at']


class IPBlacklistSerializer(serializers.ModelSerializer):
    added_by_email = serializers.EmailField(source='added_by.email', read_only=True)
    
    class Meta:
        model = IPBlacklist
        fields = [
            'id', 'ip_address', 'reason', 'is_active', 'added_by',
            'added_by_email', 'expires_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['added_by', 'created_at', 'updated_at']


class MaintenanceWindowSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = MaintenanceWindow
        fields = [
            'id', 'title', 'description', 'start_time', 'end_time',
            'affected_services', 'is_active', 'user_message', 'created_by',
            'created_by_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


# Moderation serializers
class ReviewModerationSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'customer', 'customer_email', 'restaurant', 'restaurant_name',
            'order', 'order_number', 'rating', 'comment', 'is_approved',
            'is_flagged', 'flagged_reason', 'created_at', 'updated_at'
        ]


# Marketplace serializers
class PromotionSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'name', 'code', 'restaurant', 'restaurant_name', 'offer_type',
            'discount_type', 'discount_value', 'min_order_amount', 'max_discount',
            'valid_from', 'valid_until', 'max_uses', 'uses_count', 'is_active',
            'created_at', 'updated_at'
        ]


# Automation serializers
class AutomationRuleSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = AutomationRule
        fields = [
            'id', 'name', 'description', 'trigger_type', 'trigger_config',
            'conditions', 'action_type', 'action_config', 'is_active', 'priority',
            'created_by', 'created_by_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class ScheduledJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledJob
        fields = [
            'id', 'name', 'description', 'job_type', 'cron_expression', 'config',
            'is_active', 'last_run_at', 'next_run_at', 'status', 'retry_count',
            'max_retries', 'created_at', 'updated_at'
        ]
        read_only_fields = ['last_run_at', 'next_run_at', 'status', 'created_at', 'updated_at']


class JobExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobExecution
        fields = [
            'id', 'job', 'status', 'started_at', 'completed_at', 'error_message',
            'output', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = [
            'id', 'name', 'url', 'events', 'secret', 'status', 'retry_policy',
            'headers', 'is_active', 'last_triggered_at', 'failure_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['secret', 'last_triggered_at', 'failure_count', 'created_at', 'updated_at']


class WebhookDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDelivery
        fields = [
            'id', 'webhook', 'event', 'payload', 'response_status', 'response_body',
            'success', 'error_message', 'attempt_number', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# Advanced serializers
class FraudDetectionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudDetectionRule
        fields = [
            'id', 'name', 'description', 'rule_type', 'conditions', 'action',
            'risk_score_threshold', 'is_active', 'created_at', 'updated_at'
        ]


class FraudFlagSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True)
    rule_name = serializers.CharField(source='rule_triggered.name', read_only=True)
    
    class Meta:
        model = FraudFlag
        fields = [
            'id', 'user', 'user_email', 'order', 'order_number', 'payment',
            'risk_score', 'reason', 'rule_triggered', 'rule_name', 'status',
            'reviewed_by', 'reviewed_by_email', 'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reviewed_by', 'reviewed_at', 'created_at', 'updated_at']


class ChargebackSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True)
    
    class Meta:
        model = Chargeback
        fields = [
            'id', 'order', 'order_number', 'payment', 'chargeback_id', 'reason',
            'amount', 'status', 'received_date', 'due_date', 'evidence_bundle',
            'notes', 'assigned_to', 'assigned_to_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class FeatureFlagSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = FeatureFlag
        fields = [
            'id', 'name', 'description', 'is_enabled', 'rollout_percentage',
            'target_audience', 'created_by', 'created_by_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class FeatureFlagHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True)
    flag_name = serializers.CharField(source='flag.name', read_only=True)
    
    class Meta:
        model = FeatureFlagHistory
        fields = [
            'id', 'flag', 'flag_name', 'changed_by', 'changed_by_email',
            'before_state', 'after_state', 'reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SLOSerializer(serializers.ModelSerializer):
    class Meta:
        model = SLO
        fields = [
            'id', 'service_name', 'metric_name', 'target_value', 'current_value',
            'window_days', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['current_value', 'created_at', 'updated_at']

