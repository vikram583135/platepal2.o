"""
Minimal test settings for PlatePal backend
This configuration includes only core apps to avoid circular dependencies
"""
from .settings import *

# Override INSTALLED_APPS with minimal set for testing
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps (required)
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',
    
    # All PlatePal apps (they have interdependencies)
    'apps.accounts',
    'apps.restaurants',
    'apps.orders',
    'apps.deliveries',
    'apps.payments',
    'apps.notifications',
    'apps.support',
    'apps.subscriptions',
    'apps.rewards',
    'apps.chat',
    'apps.analytics',
    'apps.inventory',
    'apps.admin_panel',
    'apps.events',
]

# Use simple middleware for tests
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Use Postgres test database (required for ArrayField and other Postgres-specific features)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_platepal',
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default='postgres'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
        'TEST': {
            'NAME': 'test_platepal',
        }
    }
}

# Disable migrations for faster test setup
# Comment this out if you need to test migrations
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = {}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Disable Celery during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use simple email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable debug toolbar and other dev tools
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: False,
}
