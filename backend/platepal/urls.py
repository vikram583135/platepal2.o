"""
URL configuration for platepal project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from apps.accounts.health import health_check, readiness_check, liveness_check

schema_view = get_schema_view(
   openapi.Info(
      title="PlatePal API",
      default_version='v1',
      description="Food ordering platform API",
      terms_of_service="https://www.platepal.com/terms/",
      contact=openapi.Contact(email="contact@platepal.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Health check endpoints (must be before other routes)
    path('api/health/', health_check, name='health_check'),
    path('api/ready/', readiness_check, name='readiness_check'),
    path('api/live/', liveness_check, name='liveness_check'),
    
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/restaurants/', include('apps.restaurants.urls')),
    path('api/orders/', include('apps.orders.urls')),
    path('api/deliveries/', include('apps.deliveries.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/support/', include('apps.support.urls')),
    path('api/subscriptions/', include('apps.subscriptions.urls')),
    path('api/rewards/', include('apps.rewards.urls')),
    path('api/chat/', include('apps.chat.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/admin/', include('apps.admin_panel.urls')),
    path('api/events/', include('apps.events.urls')),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


