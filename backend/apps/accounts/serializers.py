from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from .models import User, Address, PaymentMethod, OTP, Device, TwoFactorAuth, SavedLocation, CookieConsent, BiometricAuth, UserSession


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that uses email instead of username"""
    username_field = 'email'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The parent class creates a field based on username_field, which is 'email'
        # We need to ensure the field is named 'email' not 'username'
        if 'username' in self.fields:
            self.fields['email'] = self.fields.pop('username')
    
    def validate(self, attrs):
        # Normalize email before validation to ensure case-insensitive matching
        from django.contrib.auth import get_user_model
        from rest_framework import serializers
        
        User = get_user_model()
        
        if 'email' in attrs:
            email = attrs['email']
            # Normalize email using UserManager's normalize_email method
            normalized_email = User.objects.normalize_email(email.strip())
            attrs['email'] = normalized_email
            
            # Check if user exists and is not deleted before authentication
            try:
                user = User.objects.get(email=normalized_email)
                if user.is_deleted:
                    raise serializers.ValidationError({
                        'non_field_errors': ['This account has been deleted. Please contact support.']
                    })
                if not user.is_active:
                    raise serializers.ValidationError({
                        'non_field_errors': ['This account is inactive. Please contact support.']
                    })
            except User.DoesNotExist:
                # User doesn't exist, let parent validation handle the authentication error
                pass
        
        # Call parent validation which will authenticate the user
        try:
            return super().validate(attrs)
        except serializers.ValidationError as e:
            # Preserve existing ValidationErrors but improve the message if it's an authentication error
            error_dict = e.detail
            # Check if this is an authentication error (usually in non_field_errors)
            if isinstance(error_dict, dict) and 'non_field_errors' in error_dict:
                error_msgs = error_dict['non_field_errors']
                if any('active account' in str(msg).lower() or 'authentication' in str(msg).lower() 
                       or 'credentials' in str(msg).lower() for msg in error_msgs):
                    raise serializers.ValidationError({
                        'non_field_errors': ['Invalid email or password. Please check your credentials and try again.']
                    })
            # Re-raise original ValidationError if it's not an authentication error
            raise
        except Exception as e:
            # For any other exceptions, provide a generic error message
            error_message = str(e).lower()
            if 'active account' in error_message or 'authentication' in error_message or 'credentials' in error_message:
                raise serializers.ValidationError({
                    'non_field_errors': ['Invalid email or password. Please check your credentials and try again.']
                })
            # Re-raise unexpected exceptions
            raise


class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    profile_photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'role', 
                  'is_email_verified', 'is_phone_verified', 'date_joined', 'profile_photo', 'profile_photo_url')
        read_only_fields = ('id', 'role', 'is_email_verified', 'is_phone_verified', 'date_joined', 'profile_photo_url')
    
    def get_profile_photo_url(self, obj):
        if obj.profile_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_photo.url)
            return obj.profile_photo.url
        return None


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone', 'role')
    
    def validate_password(self, value):
        """Validate password with better error messages"""
        try:
            validate_password(value)
        except Exception as e:
            # Convert Django password validation errors to user-friendly messages
            error_messages = []
            for error in e.messages:
                error_messages.append(error)
            raise serializers.ValidationError(error_messages)
        return value
    
    def validate(self, attrs):
        email = attrs.get('email')
        phone = attrs.get('phone')
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if not email and not phone:
            raise serializers.ValidationError({"email": "Either email or phone must be provided."})
        
        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        
        # Check if email or phone already exists
        if email:
            existing_user = User.objects.filter(email=email, is_deleted=False).first()
            if existing_user:
                raise serializers.ValidationError({"email": "A user with this email already exists. Please use a different email or try logging in."})
        if phone and phone.strip():
            existing_user = User.objects.filter(phone=phone, is_deleted=False).first()
            if existing_user:
                raise serializers.ValidationError({"phone": "A user with this phone number already exists."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class AddressSerializer(serializers.ModelSerializer):
    """Address serializer"""
    class Meta:
        model = Address
        fields = ('id', 'user', 'label', 'street', 'city', 'state', 'postal_code', 'country',
                  'latitude', 'longitude', 'is_default', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Payment method serializer"""
    class Meta:
        model = PaymentMethod
        fields = ('id', 'user', 'type', 'provider', 'last_four', 'is_default', 'is_active', 'token',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class OTPSendSerializer(serializers.Serializer):
    """Serializer for sending OTP"""
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)
    type = serializers.ChoiceField(choices=OTP.OTPType.choices)

    def validate(self, attrs):
        email = attrs.get('email')
        phone = attrs.get('phone')
        if not email and not phone:
            raise serializers.ValidationError("Either email or phone must be provided.")
        return attrs


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for verifying OTP"""
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False)
    code = serializers.CharField(max_length=10)
    type = serializers.ChoiceField(choices=OTP.OTPType.choices)

    def validate(self, attrs):
        email = attrs.get('email')
        phone = attrs.get('phone')
        if not email and not phone:
            raise serializers.ValidationError("Either email or phone must be provided.")
        return attrs


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for Device model"""
    class Meta:
        model = Device
        fields = ('id', 'user', 'device_id', 'device_name', 'device_type', 'ip_address',
                  'user_agent', 'last_used', 'is_trusted', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'ip_address', 'user_agent', 'last_used', 'created_at', 'updated_at')


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    """Serializer for TwoFactorAuth model"""
    class Meta:
        model = TwoFactorAuth
        fields = ('id', 'user', 'is_enabled', 'method', 'otp_secret', 'last_used', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'otp_secret', 'last_used', 'created_at', 'updated_at')
        extra_kwargs = {
            'otp_secret': {'write_only': True}  # Should not be exposed
        }


class SavedLocationSerializer(serializers.ModelSerializer):
    """Serializer for SavedLocation model"""
    class Meta:
        model = SavedLocation
        fields = ('id', 'user', 'label', 'address', 'latitude', 'longitude', 'is_default', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class CookieConsentSerializer(serializers.ModelSerializer):
    """Serializer for cookie consent"""
    class Meta:
        model = CookieConsent
        fields = ('id', 'user', 'session_id', 'consent_given', 'consent_date',
                  'necessary_cookies', 'analytics_cookies', 'marketing_cookies',
                  'preferences_cookies', 'ip_address', 'user_agent', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')


class BiometricAuthSerializer(serializers.ModelSerializer):
    """Biometric authentication serializer"""
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    
    class Meta:
        model = BiometricAuth
        fields = ('id', 'user', 'device', 'device_name', 'biometric_type', 'biometric_id',
                  'is_enabled', 'is_verified', 'verified_at', 'last_used', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'is_verified', 'verified_at', 'last_used', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserSessionSerializer(serializers.ModelSerializer):
    """User session serializer"""
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    device_type = serializers.CharField(source='device.device_type', read_only=True)
    
    class Meta:
        model = UserSession
        fields = ('id', 'user', 'device', 'device_name', 'device_type', 'refresh_token_jti',
                  'ip_address', 'user_agent', 'location', 'status', 'last_activity',
                  'expires_at', 'revoked_at', 'login_method', 'biometric_auth',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'refresh_token_jti', 'access_token_hash',
                           'status', 'revoked_at', 'created_at', 'updated_at')
