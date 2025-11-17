from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, PaymentMethod, AuditLog, OTP, GuestSession, Device, TwoFactorAuth, SavedLocation, CookieConsent, BiometricAuth, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_email_verified', 'date_joined')
    list_filter = ('role', 'is_active', 'is_email_verified', 'is_staff', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('PlatePal Info', {'fields': ('role', 'phone', 'is_email_verified', 'is_phone_verified')}),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'city', 'state', 'is_default', 'created_at')
    list_filter = ('country', 'is_default', 'created_at')
    search_fields = ('user__email', 'street', 'city', 'state')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'provider', 'last_four', 'is_default', 'is_active')
    list_filter = ('type', 'is_default', 'is_active')
    search_fields = ('user__email', 'provider')


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone', 'code', 'type', 'verified', 'expires_at', 'created_at')
    list_filter = ('type', 'verified', 'created_at')
    search_fields = ('email', 'phone', 'code')
    readonly_fields = ('code', 'created_at', 'updated_at')


@admin.register(GuestSession)
class GuestSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'expires_at', 'created_at')
    list_filter = ('expires_at', 'created_at')
    search_fields = ('session_key',)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_name', 'device_type', 'is_trusted', 'is_active', 'last_used')
    list_filter = ('device_type', 'is_trusted', 'is_active')
    search_fields = ('user__email', 'device_name', 'device_id')


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_enabled', 'last_used', 'created_at')
    list_filter = ('is_enabled', 'created_at')
    search_fields = ('user__email',)


@admin.register(SavedLocation)
class SavedLocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'address', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('user__email', 'label', 'address')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'resource_type', 'resource_id', 'ip_address', 'created_at')
    list_filter = ('action', 'resource_type', 'created_at')
    search_fields = ('user__email', 'resource_type', 'resource_id')
    readonly_fields = ('user', 'action', 'resource_type', 'resource_id', 'details', 'ip_address', 'user_agent', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(CookieConsent)
class CookieConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'consent_given', 'consent_date', 'analytics_cookies', 'marketing_cookies')
    list_filter = ('consent_given', 'analytics_cookies', 'marketing_cookies', 'consent_date')
    search_fields = ('user__email', 'session_id', 'ip_address')
    readonly_fields = ('consent_date', 'ip_address', 'user_agent')


@admin.register(BiometricAuth)
class BiometricAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'biometric_type', 'get_device_name', 'is_enabled', 'is_verified', 'last_used', 'created_at')
    list_filter = ('biometric_type', 'is_enabled', 'is_verified', 'created_at')
    search_fields = ('user__email', 'biometric_id', 'device__device_name')
    readonly_fields = ('verified_at', 'last_used', 'created_at', 'updated_at')
    
    def get_device_name(self, obj):
        return obj.device.device_name if obj.device else 'N/A'
    get_device_name.short_description = 'Device'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_device_name', 'ip_address', 'status', 'login_method', 'last_activity', 'expires_at')
    list_filter = ('status', 'login_method', 'created_at')
    search_fields = ('user__email', 'refresh_token_jti', 'ip_address', 'device__device_name')
    readonly_fields = ('refresh_token_jti', 'access_token_hash', 'revoked_at', 'created_at', 'updated_at')
    date_hierarchy = 'last_activity'
    
    def get_device_name(self, obj):
        return obj.device.device_name if obj.device else 'N/A'
    get_device_name.short_description = 'Device'

