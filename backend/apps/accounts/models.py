from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import uuid

# Mixins
class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteMixin(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class UserManager(BaseUserManager):
    """Custom user manager"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimestampMixin, SoftDeleteMixin):
    """Custom user model"""

    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        RESTAURANT = 'RESTAURANT', 'Restaurant'
        DELIVERY = 'DELIVERY', 'Delivery'
        ADMIN = 'ADMIN', 'Admin'
        SUPPORT = 'SUPPORT', 'Support'

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    
    # Social Auth fields
    google_id = models.CharField(max_length=255, blank=True, null=True)
    apple_id = models.CharField(max_length=255, blank=True, null=True)
    facebook_id = models.CharField(max_length=255, blank=True, null=True)
    auth_provider = models.CharField(max_length=50, blank=True, null=True)  # 'email', 'google', 'apple', 'facebook'

    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name or self.email


class Address(TimestampMixin, SoftDeleteMixin):
    """User addresses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=100)  # e.g., Home, Work, Other
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'addresses'
        verbose_name_plural = 'Addresses'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.label}: {self.street}, {self.city}"


class PaymentMethod(TimestampMixin, SoftDeleteMixin):
    """User payment methods (tokenized)"""

    class PaymentMethodType(models.TextChoices):
        CARD = 'CARD', 'Credit/Debit Card'
        UPI = 'UPI', 'UPI'
        WALLET = 'WALLET', 'Wallet'
        CASH = 'CASH', 'Cash on Delivery'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    type = models.CharField(max_length=20, choices=PaymentMethodType.choices)
    provider = models.CharField(max_length=100, blank=True)  # e.g., Visa, Mastercard, Google Pay
    last_four = models.CharField(max_length=4, blank=True)  # Last four digits for cards
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    token = models.CharField(max_length=255, blank=True)  # Token from payment gateway

    class Meta:
        db_table = 'payment_methods'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_default']),
        ]

    def __str__(self):
        return f"{self.type} ({self.last_four}) for {self.user.email}"


class AuditLog(TimestampMixin):
    """Audit log for tracking important user actions"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)  # e.g., 'USER_LOGIN', 'ORDER_CREATED', 'PROFILE_UPDATED'
    resource_type = models.CharField(max_length=100)  # e.g., 'User', 'Order', 'Address'
    resource_id = models.CharField(max_length=100)  # ID of the resource
    details = models.JSONField(default=dict)  # Additional details about the action
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.email if self.user else 'Anonymous'} - {self.action} on {self.resource_type}:{self.resource_id}"


class OTP(TimestampMixin):
    """One-Time Password for verification"""

    class OTPType(models.TextChoices):
        EMAIL_VERIFICATION = 'EMAIL_VERIFICATION', 'Email Verification'
        PHONE_VERIFICATION = 'PHONE_VERIFICATION', 'Phone Verification'
        PASSWORD_RESET = 'PASSWORD_RESET', 'Password Reset'
        LOGIN = 'LOGIN', 'Login'
        TWO_FACTOR_AUTH = 'TWO_FACTOR_AUTH', 'Two-Factor Authentication'
        DELIVERY_VERIFICATION = 'DELIVERY_VERIFICATION', 'Delivery Verification'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps', null=True, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    code = models.CharField(max_length=10)
    type = models.CharField(max_length=50, choices=OTPType.choices)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)

    class Meta:
        db_table = 'otps'
        indexes = [
            models.Index(fields=['email', 'type', 'verified']),
            models.Index(fields=['phone', 'type', 'verified']),
            models.Index(fields=['user', 'type', 'verified']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"OTP for {self.email or self.phone} ({self.type})"

    def is_expired(self):
        return timezone.now() > self.expires_at


class GuestSession(TimestampMixin):
    """Temporary session for guest users"""
    session_key = models.CharField(max_length=40, unique=True)
    expires_at = models.DateTimeField()
    # Potentially store some anonymous cart data or preferences
    data = models.JSONField(default=dict)

    class Meta:
        db_table = 'guest_sessions'
        indexes = [
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Guest Session {self.session_key}"


class Device(TimestampMixin, SoftDeleteMixin):
    """User devices for security and notifications"""

    class DeviceType(models.TextChoices):
        WEB = 'WEB', 'Web Browser'
        MOBILE_ANDROID = 'MOBILE_ANDROID', 'Android App'
        MOBILE_IOS = 'MOBILE_IOS', 'iOS App'
        OTHER = 'OTHER', 'Other'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255, unique=True, blank=True, null=True)  # FCM token or unique device identifier
    device_name = models.CharField(max_length=255, blank=True)  # e.g., "My iPhone 15"
    device_type = models.CharField(max_length=20, choices=DeviceType.choices, default=DeviceType.WEB)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    last_used = models.DateTimeField(auto_now=True)
    is_trusted = models.BooleanField(default=False)  # For 2FA bypass
    is_active = models.BooleanField(default=True)  # Can be deactivated by user

    class Meta:
        db_table = 'devices'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_id']),
        ]

    def __str__(self):
        return f"{self.user.email}'s {self.device_name or self.device_type} ({self.device_id[:10] if self.device_id else 'N/A'})"


class TwoFactorAuth(TimestampMixin):
    """Two-Factor Authentication settings for a user"""

    class Method(models.TextChoices):
        NONE = 'NONE', 'None'
        OTP_APP = 'OTP_APP', 'Authenticator App'
        SMS = 'SMS', 'SMS'
        EMAIL = 'EMAIL', 'Email'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor_auth')
    is_enabled = models.BooleanField(default=False)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.NONE)
    otp_secret = models.CharField(max_length=255, blank=True, null=True)  # For authenticator apps
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'two_factor_auth'

    def __str__(self):
        return f"2FA for {self.user.email} (Enabled: {self.is_enabled})"


class SavedLocation(TimestampMixin, SoftDeleteMixin):
    """Saved locations for quick access (Home, Work, etc.)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_locations')
    label = models.CharField(max_length=100)  # e.g., Home, Work, My Cabin
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'saved_locations'
        indexes = [
            models.Index(fields=['user', 'label']),
            models.Index(fields=['user', 'is_default']),
        ]

    def __str__(self):
        return f"{self.user.email}'s saved location: {self.label}"


class CookieConsent(TimestampMixin):
    """Cookie consent tracking for GDPR compliance"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cookie_consents', null=True, blank=True)
    session_id = models.CharField(max_length=255)  # For anonymous users
    consent_given = models.BooleanField(default=False)
    consent_date = models.DateTimeField(auto_now_add=True)
    necessary_cookies = models.BooleanField(default=True)  # Always required
    analytics_cookies = models.BooleanField(default=False)
    marketing_cookies = models.BooleanField(default=False)
    preferences_cookies = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'cookie_consents'
        indexes = [
            models.Index(fields=['user', '-consent_date']),
            models.Index(fields=['session_id', '-consent_date']),
        ]
    
    def __str__(self):
        return f"Cookie consent for {self.user.email if self.user else 'Anonymous'} - {self.consent_date}"


class BiometricAuth(TimestampMixin):
    """Biometric authentication settings"""
    
    class BiometricType(models.TextChoices):
        FINGERPRINT = 'FINGERPRINT', 'Fingerprint'
        FACE_ID = 'FACE_ID', 'Face ID'
        VOICE = 'VOICE', 'Voice Recognition'
        IRIS = 'IRIS', 'Iris Scan'
        PALM = 'PALM', 'Palm Print'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='biometric_auths')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='biometric_auths', null=True, blank=True)
    biometric_type = models.CharField(max_length=20, choices=BiometricType.choices)
    biometric_id = models.CharField(max_length=255, unique=True)  # Unique identifier from device
    is_enabled = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Security
    public_key_hash = models.CharField(max_length=255, blank=True)  # Hash of public key for verification
    challenge_expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'biometric_auths'
        indexes = [
            models.Index(fields=['user', 'is_enabled']),
            models.Index(fields=['device', 'biometric_type']),
            models.Index(fields=['biometric_id']),
        ]
        unique_together = [['user', 'device', 'biometric_type']]
    
    def __str__(self):
        return f"{self.biometric_type} for {self.user.email} on {self.device.device_name if self.device else 'Unknown'}"


class UserSession(TimestampMixin):
    """User session tracking for security and management"""
    
    class SessionStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        EXPIRED = 'EXPIRED', 'Expired'
        REVOKED = 'REVOKED', 'Revoked'
        LOGGED_OUT = 'LOGGED_OUT', 'Logged Out'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, related_name='sessions', null=True, blank=True)
    
    # JWT token tracking
    refresh_token_jti = models.CharField(max_length=255, unique=True, db_index=True)  # JWT ID
    access_token_hash = models.CharField(max_length=255, blank=True)  # Hash of access token
    
    # Session details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)  # Geographic location if available
    
    # Status
    status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.ACTIVE)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    
    # Login method
    login_method = models.CharField(max_length=50, default='PASSWORD')  # PASSWORD, BIOMETRIC, 2FA, SOCIAL
    biometric_auth = models.ForeignKey(BiometricAuth, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['device', 'status']),
            models.Index(fields=['refresh_token_jti']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"Session for {self.user.email} - {self.status} ({self.device.device_name if self.device else 'Unknown'})"
    
    def revoke(self):
        """Revoke session"""
        self.status = self.SessionStatus.REVOKED
        self.revoked_at = timezone.now()
        self.save()
    
    def is_expired(self):
        """Check if session is expired"""
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = self.SessionStatus.EXPIRED
            self.save()
            return True
        return False