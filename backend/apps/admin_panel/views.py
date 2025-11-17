"""
Views for admin app
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import secrets

from .models import (
    Role, Permission, RolePermission, AdminUser, APIToken,
    AdminSession, Environment, EnvironmentAccess, SSOProvider, AuditLogEntry
)
from .serializers import (
    RoleSerializer, PermissionSerializer, AdminUserSerializer,
    APITokenSerializer, APITokenCreateSerializer, AdminSessionSerializer,
    EnvironmentSerializer, EnvironmentAccessSerializer, SSOProviderSerializer,
    AuditLogEntrySerializer
)
from .permissions import IsAdminUser, HasAdminPermission

User = get_user_model()


class RoleViewSet(viewsets.ModelViewSet):
    """Role management"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.role.manage')]
    
    def get_queryset(self):
        return Role.objects.all().prefetch_related('role_permissions__permission')


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """Permission listing"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def by_resource(self, request):
        """Get permissions grouped by resource type"""
        perms = Permission.objects.all().order_by('resource_type', 'action')
        grouped = {}
        for perm in perms:
            resource = perm.resource_type or 'general'
            if resource not in grouped:
                grouped[resource] = []
            grouped[resource].append(PermissionSerializer(perm).data)
        return Response(grouped)


class AdminUserViewSet(viewsets.ModelViewSet):
    """Admin user management"""
    queryset = AdminUser.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.user.manage')]
    
    def get_queryset(self):
        return AdminUser.objects.select_related('user', 'role').all()
    
    @action(detail=True, methods=['post'])
    def enable_2fa(self, request, pk=None):
        """Enable 2FA for admin user"""
        admin_user = self.get_object()
        # In production, generate TOTP secret
        secret = secrets.token_hex(16)
        admin_user.two_factor_secret = secret
        admin_user.two_factor_enabled = True
        admin_user.save()
        return Response({'secret': secret, 'qr_code_url': f'otpauth://totp/PlatePal:{admin_user.user.email}?secret={secret}'})
    
    @action(detail=True, methods=['post'])
    def disable_2fa(self, request, pk=None):
        """Disable 2FA for admin user"""
        admin_user = self.get_object()
        admin_user.two_factor_enabled = False
        admin_user.two_factor_secret = ''
        admin_user.save()
        return Response({'message': '2FA disabled'})


class APITokenViewSet(viewsets.ModelViewSet):
    """API token management"""
    serializer_class = APITokenSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return APIToken.objects.all()
        return APIToken.objects.filter(user=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return APITokenCreateSerializer
        return APITokenSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.save()
        # Return full token only on creation
        return Response({
            **APITokenSerializer(token, context={'show_full_token': True}).data,
            'message': 'Token created. Save it securely - it will not be shown again.'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def rotate(self, request, pk=None):
        """Rotate API token"""
        token = self.get_object()
        old_token = token.token
        token.token = secrets.token_urlsafe(48)
        token.token_prefix = token.token[:8]
        token.save()
        
        # Log rotation
        AuditLogEntry.objects.create(
            user=request.user,
            action='api_token.rotate',
            resource_type='api_token',
            resource_id=str(token.id),
            reason=request.data.get('reason', ''),
            metadata={'old_token_prefix': old_token[:8]}
        )
        
        return Response({
            'token': token.token,
            'token_prefix': token.token_prefix,
            'message': 'Token rotated successfully'
        })
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke API token"""
        token = self.get_object()
        token.is_active = False
        token.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='api_token.revoke',
            resource_type='api_token',
            resource_id=str(token.id),
            reason=request.data.get('reason', '')
        )
        
        return Response({'message': 'Token revoked'})


class AdminSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin session management"""
    serializer_class = AdminSessionSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return AdminSession.objects.select_related('user').all()
        return AdminSession.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """Revoke a session"""
        session = self.get_object()
        session.is_active = False
        session.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='admin_session.revoke',
            resource_type='admin_session',
            resource_id=str(session.id),
            reason=request.data.get('reason', '')
        )
        
        return Response({'message': 'Session revoked'})
    
    @action(detail=False, methods=['post'])
    def revoke_all_other(self, request):
        """Revoke all other sessions for current user"""
        current_session_key = request.session.session_key
        AdminSession.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(session_key=current_session_key).update(is_active=False)
        
        return Response({'message': 'All other sessions revoked'})


class EnvironmentViewSet(viewsets.ModelViewSet):
    """Environment management"""
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.environment.manage')]
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current environment"""
        env_name = request.headers.get('X-Environment', 'production')
        try:
            env = Environment.objects.get(name=env_name, is_active=True)
            return Response(EnvironmentSerializer(env).data)
        except Environment.DoesNotExist:
            return Response({'error': 'Environment not found'}, status=status.HTTP_404_NOT_FOUND)


class EnvironmentAccessViewSet(viewsets.ModelViewSet):
    """Environment access management"""
    queryset = EnvironmentAccess.objects.all()
    serializer_class = EnvironmentAccessSerializer
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.environment.manage')]
    
    def perform_create(self, serializer):
        serializer.save(granted_by=self.request.user)


class SSOProviderViewSet(viewsets.ModelViewSet):
    """SSO provider management"""
    queryset = SSOProvider.objects.all()
    serializer_class = SSOProviderSerializer
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.sso.manage')]
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test SSO provider connection"""
        provider = self.get_object()
        # In production, test actual SSO connection
        return Response({'message': 'Connection test not implemented', 'provider': provider.name})


class AuditLogEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log entries"""
    queryset = AuditLogEntry.objects.all()
    serializer_class = AuditLogEntrySerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = AuditLogEntry.objects.select_related('user', 'environment').all()
        
        # Filtering
        user_id = self.request.query_params.get('user_id')
        resource_type = self.request.query_params.get('resource_type')
        resource_id = self.request.query_params.get('resource_id')
        action = self.request.query_params.get('action')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        if action:
            queryset = queryset.filter(action=action)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset.order_by('-created_at')


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_audit_log(request):
    """Helper to create audit log entries"""
    AuditLogEntry.objects.create(
        user=request.user,
        action=request.data.get('action'),
        resource_type=request.data.get('resource_type'),
        resource_id=request.data.get('resource_id'),
        before_state=request.data.get('before_state', {}),
        after_state=request.data.get('after_state', {}),
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        reason=request.data.get('reason', ''),
        metadata=request.data.get('metadata', {})
    )
    return Response({'message': 'Audit log created'})

