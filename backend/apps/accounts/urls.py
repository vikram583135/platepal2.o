"""
URLs for accounts app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, UserViewSet, AddressViewSet, PaymentMethodViewSet,
    DeviceViewSet, TwoFactorAuthViewSet, SavedLocationViewSet, CookieConsentViewSet,
    BiometricAuthViewSet, UserSessionViewSet,
    send_otp, verify_otp_view, google_oauth, apple_oauth, facebook_oauth
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'two-factor-auth', TwoFactorAuthViewSet, basename='two-factor-auth')
router.register(r'saved-locations', SavedLocationViewSet, basename='saved-location')
router.register(r'cookie-consent', CookieConsentViewSet, basename='cookie-consent')
router.register(r'biometric-auth', BiometricAuthViewSet, basename='biometric-auth')
router.register(r'sessions', UserSessionViewSet, basename='user-session')

urlpatterns = [
    path('', include(router.urls)),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('otp/send/', send_otp, name='send_otp'),
    path('otp/verify/', verify_otp_view, name='verify_otp'),
    path('oauth/google/', google_oauth, name='oauth_google'),
    path('oauth/apple/', apple_oauth, name='oauth_apple'),
    path('oauth/facebook/', facebook_oauth, name='oauth_facebook'),
]

