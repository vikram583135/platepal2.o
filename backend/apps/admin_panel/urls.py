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
from .views_management import (
    UserManagementViewSet, RestaurantManagementViewSet, DeliveryManagementViewSet
)
from .views_moderation import (
    ReviewModerationViewSet, RestaurantContentManagementViewSet, PolicyManagementViewSet
)
from .views_marketplace import (
    CatalogManagementViewSet, CampaignManagementViewSet
)
from .views_operations import (
    SystemHealthViewSet, AlertRuleViewSet, IncidentViewSet,
    RateLimitRuleViewSet, IPWhitelistViewSet, IPBlacklistViewSet,
    MaintenanceWindowViewSet
)
from .views_security import (
    GDPRViewSet, PIIMaskingViewSet, ConsentManagementViewSet
)
from .views_automation import (
    AutomationRuleViewSet, ScheduledJobViewSet, WebhookViewSet
)
from .views_integrations import (
    IntegrationViewSet, APIExplorerViewSet
)
from .views_advanced import (
    FraudDetectionViewSet, ChargebackViewSet, FeatureFlagViewSet, SLOViewSet
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

# Management endpoints
router.register(r'management/users', UserManagementViewSet, basename='management-users')
router.register(r'management/restaurants', RestaurantManagementViewSet, basename='management-restaurants')
router.register(r'management/delivery', DeliveryManagementViewSet, basename='management-delivery')

# Moderation endpoints
router.register(r'moderation/reviews', ReviewModerationViewSet, basename='moderation-reviews')
router.register(r'content/restaurants', RestaurantContentManagementViewSet, basename='content-restaurants')
router.register(r'policies', PolicyManagementViewSet, basename='policies')

# Marketplace endpoints
router.register(r'catalog', CatalogManagementViewSet, basename='catalog')
router.register(r'campaigns', CampaignManagementViewSet, basename='campaigns')

# System operations endpoints
router.register(r'system/health', SystemHealthViewSet, basename='system-health')
router.register(r'system/alerts', AlertRuleViewSet, basename='alerts')
router.register(r'system/incidents', IncidentViewSet, basename='incidents')
router.register(r'system/rate-limits', RateLimitRuleViewSet, basename='rate-limits')
router.register(r'system/ip-whitelist', IPWhitelistViewSet, basename='ip-whitelist')
router.register(r'system/ip-blacklist', IPBlacklistViewSet, basename='ip-blacklist')
router.register(r'system/maintenance', MaintenanceWindowViewSet, basename='maintenance')

# Security & Compliance endpoints
router.register(r'security/gdpr', GDPRViewSet, basename='gdpr')
router.register(r'security/pii', PIIMaskingViewSet, basename='pii')
router.register(r'security/consent', ConsentManagementViewSet, basename='consent')

# Automation endpoints
router.register(r'automation/rules', AutomationRuleViewSet, basename='automation-rules')
router.register(r'automation/jobs', ScheduledJobViewSet, basename='scheduled-jobs')
router.register(r'automation/webhooks', WebhookViewSet, basename='webhooks')

# Integrations endpoints
router.register(r'integrations', IntegrationViewSet, basename='integrations')
router.register(r'api-explorer', APIExplorerViewSet, basename='api-explorer')

# Advanced features endpoints
router.register(r'fraud', FraudDetectionViewSet, basename='fraud')
router.register(r'chargebacks', ChargebackViewSet, basename='chargebacks')
router.register(r'feature-flags', FeatureFlagViewSet, basename='feature-flags')
router.register(r'slos', SLOViewSet, basename='slos')

urlpatterns = [
    path('', include(router.urls)),
    path('audit-logs/create/', create_audit_log, name='create-audit-log'),
]

