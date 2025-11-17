"""
Serializers for admin app
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Role, Permission, RolePermission, AdminUser, APIToken,
    AdminSession, Environment, EnvironmentAccess, SSOProvider, AuditLogEntry
)

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

