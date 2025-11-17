from django.apps import AppConfig


class DeliveriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.deliveries'
    
    def ready(self):
        """Import advanced features when app is ready"""
        try:
            import apps.deliveries.models_advanced  # noqa: F401
        except ImportError:
            pass  # Advanced features not available
    verbose_name = 'Deliveries'

