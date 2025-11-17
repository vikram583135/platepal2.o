"""
URLs for admin app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoleViewSet, PermissionViewSet, AdminUserViewSet, APITokenViewSet,
    AdminSessionViewSet, EnvironmentViewSet, EnvironmentAccessViewSet,
    SSOProviderViewSet, AuditLogEntryViewSet, create_audit_log
)

router = DefaultRouter()
router.register(r'roles', RoleViewSet)
router.register(r'permissions', PermissionViewSet)
router.register(r'users', AdminUserViewSet)
router.register(r'api-tokens', APITokenViewSet, basename='api-tokens')
router.register(r'sessions', AdminSessionViewSet, basename='sessions')
router.register(r'environments', EnvironmentViewSet)
router.register(r'environment-accesses', EnvironmentAccessViewSet)
router.register(r'sso-providers', SSOProviderViewSet)
router.register(r'audit-logs', AuditLogEntryViewSet, basename='audit-logs')

urlpatterns = [
    path('', include(router.urls)),
    path('audit-logs/create/', create_audit_log, name='create-audit-log'),
]

