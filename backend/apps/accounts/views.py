"""
Views for accounts app
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash
from django.core.files.storage import default_storage
from django.conf import settings
from .models import Address, PaymentMethod, OTP, Device, TwoFactorAuth, SavedLocation, CookieConsent, BiometricAuth, UserSession
from .serializers import (
    UserSerializer, UserRegistrationSerializer, AddressSerializer, PaymentMethodSerializer,
    CustomTokenObtainPairSerializer, OTPSendSerializer, OTPVerifySerializer,
    DeviceSerializer, TwoFactorAuthSerializer, SavedLocationSerializer, CookieConsentSerializer,
    BiometricAuthSerializer, UserSessionSerializer
)
from .permissions import IsOwnerOrAdmin
from .services import create_and_send_otp, verify_otp
import json
import uuid
import secrets

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom token view that uses email instead of username"""
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """User viewset"""
    queryset = User.objects.filter(is_deleted=False)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return self.queryset
        return self.queryset.filter(id=user.id)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Get current user"""
        serializer = self.get_serializer(request.user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """User registration"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify_email(self, request):
        """Email verification (mock - in production, send verification link)"""
        user = request.user
        user.is_email_verified = True
        user.save()
        return Response({'message': 'Email verified'})
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify_phone(self, request):
        """Phone verification (mock - in production, send OTP)"""
        user = request.user
        user.is_phone_verified = True
        user.save()
        return Response({'message': 'Phone verified'})
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Change user password"""
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response({'error': 'old_password and new_password are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(old_password):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        
        return Response({'message': 'Password changed successfully'})
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_profile_photo(self, request):
        """Upload profile photo"""
        user = request.user
        if 'profile_photo' not in request.FILES:
            return Response({'error': 'profile_photo is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete old photo if exists
        if user.profile_photo:
            default_storage.delete(user.profile_photo.name)
        
        user.profile_photo = request.FILES['profile_photo']
        user.save()
        
        serializer = self.get_serializer(user, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def export_data(self, request):
        """Export user data (GDPR compliance)"""
        user = request.user
        
        # Collect all user data
        from apps.orders.models import Order
        from apps.payments.models import Wallet, WalletTransaction
        from apps.notifications.models import Notification
        from apps.support.models import SupportTicket
        from apps.subscriptions.models import Subscription
        from apps.rewards.models import UserLoyalty, RewardPoint
        
        export = {
            'user': UserSerializer(user, context={'request': request}).data,
            'addresses': [AddressSerializer(addr, context={'request': request}).data for addr in user.addresses.filter(is_deleted=False)],
            'payment_methods': [PaymentMethodSerializer(pm, context={'request': request}).data for pm in user.payment_methods.filter(is_deleted=False)],
            'orders': [],  # Would serialize orders
            'wallet': None,
            'wallet_transactions': [],
            'notifications': [],
            'support_tickets': [],
            'subscriptions': [],
            'loyalty': None,
            'reward_points': [],
            'devices': [DeviceSerializer(device, context={'request': request}).data for device in Device.objects.filter(user=user, is_active=True)],
            'exported_at': timezone.now().isoformat(),
        }
        
        # In production, this would be more comprehensive and could be sent as a file
        return Response(export)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def delete_account(self, request):
        """Delete user account with data export option"""
        user = request.user
        export_data = request.data.get('export_data', False)
        
        # Export data if requested
        if export_data:
            # Use the export_data endpoint
            export_response = self.export_data(request)
            # In production, send this as a file or email before deletion
            pass
        
        # Soft delete user
        user.soft_delete()
        return Response({'message': 'Account deleted successfully'})


class AddressViewSet(viewsets.ModelViewSet):
    """Address viewset"""
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return Address.objects.filter(is_deleted=False)
        return Address.objects.filter(user=user, is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """Payment method viewset"""
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return PaymentMethod.objects.filter(is_deleted=False)
        return PaymentMethod.objects.filter(user=user, is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_otp(request):
    """Send OTP via email or SMS"""
    serializer = OTPSendSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data.get('email')
    phone = serializer.validated_data.get('phone')
    otp_type = serializer.validated_data.get('type')
    
    # Get user if authenticated
    user = request.user if request.user.is_authenticated else None
    
    try:
        otp = create_and_send_otp(email=email, phone=phone, user=user, otp_type=otp_type)
        return Response({
            'message': 'OTP sent successfully',
            'expires_at': otp.expires_at.isoformat(),
            'code': otp.code if settings.DEBUG else None  # Include code in DEBUG mode for development
        })
    except Exception as e:
        # In development, still create OTP even if sending fails
        if settings.DEBUG and (email or phone):
            try:
                from .services import generate_otp_code
                from datetime import timedelta
                code = generate_otp_code()
                expires_at = timezone.now() + timedelta(minutes=10)
                otp = OTP.objects.create(
                    user=user,
                    email=email or '',
                    phone=phone or '',
                    code=code,
                    type=otp_type,
                    expires_at=expires_at,
                )
                print(f"OTP created (email sending failed): {code} for {email or phone}")
                return Response({
                    'message': 'OTP created (email sending failed in DEBUG mode)',
                    'expires_at': otp.expires_at.isoformat(),
                    'code': code  # Include code in DEBUG mode
                })
            except Exception as inner_e:
                return Response({'error': f'Failed to create OTP: {str(inner_e)}'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp_view(request):
    """Verify OTP code"""
    serializer = OTPVerifySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data.get('email')
    phone = serializer.validated_data.get('phone')
    code = serializer.validated_data.get('code')
    otp_type = serializer.validated_data.get('type')
    
    # Get user if authenticated
    user = request.user if request.user.is_authenticated else None
    
    success, message = verify_otp(email=email, phone=phone, code=code, otp_type=otp_type, user=user)
    
    if success:
        return Response({'message': message, 'verified': True})
    else:
        return Response({'error': message, 'verified': False}, status=status.HTTP_400_BAD_REQUEST)


class DeviceViewSet(viewsets.ModelViewSet):
    """Device viewset"""
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Device.objects.filter(user=self.request.user, is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TwoFactorAuthViewSet(viewsets.ModelViewSet):
    """Two-factor authentication viewset"""
    serializer_class = TwoFactorAuthSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TwoFactorAuth.objects.filter(user=self.request.user)
    
    def get_object(self):
        obj, created = TwoFactorAuth.objects.get_or_create(user=self.request.user)
        return obj


class SavedLocationViewSet(viewsets.ModelViewSet):
    """Saved location viewset"""
    serializer_class = SavedLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SavedLocation.objects.filter(user=self.request.user, is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def google_oauth(request):
    """Google OAuth callback handler"""
    # In production, verify the token with Google
    id_token = request.data.get('id_token')
    access_token = request.data.get('access_token')
    
    if not id_token:
        return Response({'error': 'id_token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Mock Google user data (in production, decode and verify JWT)
    # For now, accept user data directly
    google_id = request.data.get('google_id')
    email = request.data.get('email')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    profile_picture = request.data.get('picture')
    
    if not google_id or not email:
        return Response({'error': 'google_id and email are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if user exists with this Google ID
        user = User.objects.filter(google_id=google_id).first()
        
        if not user:
            # Check if user exists with this email
            user = User.objects.filter(email=email).first()
            
            if user:
                # Link Google account to existing user
                user.google_id = google_id
                user.auth_provider = 'google'
                if not user.profile_photo and profile_picture:
                    # In production, download and save the image
                    pass
                user.save()
            else:
                # Create new user
                user = User.objects.create_user(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    google_id=google_id,
                    auth_provider='google',
                    is_email_verified=True,  # Google emails are verified
                )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def apple_oauth(request):
    """Apple OAuth callback handler"""
    # In production, verify the token with Apple
    identity_token = request.data.get('identity_token')
    authorization_code = request.data.get('authorization_code')
    
    if not identity_token:
        return Response({'error': 'identity_token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Mock Apple user data (in production, decode and verify JWT)
    apple_id = request.data.get('apple_id')
    email = request.data.get('email')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    
    if not apple_id:
        return Response({'error': 'apple_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if user exists with this Apple ID
        user = User.objects.filter(apple_id=apple_id).first()
        
        if not user:
            # Check if user exists with this email
            if email:
                user = User.objects.filter(email=email).first()
            
            if user:
                # Link Apple account to existing user
                user.apple_id = apple_id
                user.auth_provider = 'apple'
                user.save()
            else:
                # Create new user (email might be hidden by Apple)
                user = User.objects.create_user(
                    email=email or f'apple_{apple_id}@platepal.app',
                    first_name=first_name,
                    last_name=last_name,
                    apple_id=apple_id,
                    auth_provider='apple',
                    is_email_verified=True if email else False,
                )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def facebook_oauth(request):
    """Facebook OAuth callback handler"""
    # In production, verify the token with Facebook
    access_token = request.data.get('access_token')
    
    if not access_token:
        return Response({'error': 'access_token is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Mock Facebook user data (in production, fetch from Facebook Graph API)
    facebook_id = request.data.get('facebook_id')
    email = request.data.get('email')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    profile_picture = request.data.get('picture')
    
    if not facebook_id:
        return Response({'error': 'facebook_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if user exists with this Facebook ID
        user = User.objects.filter(facebook_id=facebook_id).first()
        
        if not user:
            # Check if user exists with this email
            if email:
                user = User.objects.filter(email=email).first()
            
            if user:
                # Link Facebook account to existing user
                user.facebook_id = facebook_id
                user.auth_provider = 'facebook'
                if not user.profile_photo and profile_picture:
                    # In production, download and save the image
                    pass
                user.save()
            else:
                # Create new user
                user = User.objects.create_user(
                    email=email or f'facebook_{facebook_id}@platepal.app',
                    first_name=first_name,
                    last_name=last_name,
                    facebook_id=facebook_id,
                    auth_provider='facebook',
                    is_email_verified=True if email else False,
                )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CookieConsentViewSet(viewsets.ModelViewSet):
    """Cookie consent viewset"""
    serializer_class = CookieConsentSerializer
    permission_classes = [permissions.AllowAny]  # Allow anonymous users
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return CookieConsent.objects.filter(user=self.request.user).order_by('-consent_date')
        # For anonymous users, filter by session_id
        session_id = self.request.session.session_key or self.request.data.get('session_id')
        if session_id:
            return CookieConsent.objects.filter(session_id=session_id).order_by('-consent_date')
        return CookieConsent.objects.none()
    
    def perform_create(self, serializer):
        # Get client IP and user agent
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = self.request.META.get('REMOTE_ADDR')
        
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        session_id = self.request.session.session_key or self.request.data.get('session_id', str(uuid.uuid4()))
        
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def current(self, request):
        """Get current cookie consent status"""
        if request.user.is_authenticated:
            consent = CookieConsent.objects.filter(user=request.user).order_by('-consent_date').first()
        else:
            session_id = request.session.session_key or request.GET.get('session_id')
            if session_id:
                consent = CookieConsent.objects.filter(session_id=session_id).order_by('-consent_date').first()
            else:
                consent = None
        
        if consent:
            serializer = self.get_serializer(consent)
            return Response(serializer.data)
        else:
            return Response({
                'consent_given': False,
                'necessary_cookies': True,
                'analytics_cookies': False,
                'marketing_cookies': False,
                'preferences_cookies': False,
            })


class BiometricAuthViewSet(viewsets.ModelViewSet):
    """Biometric authentication viewset"""
    serializer_class = BiometricAuthSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return BiometricAuth.objects.all()
        return BiometricAuth.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request):
        """Register biometric authentication"""
        from rest_framework_simplejwt.tokens import RefreshToken
        import hashlib
        
        biometric_type = request.data.get('biometric_type')
        biometric_id = request.data.get('biometric_id')
        public_key = request.data.get('public_key')
        device_id = request.data.get('device_id')
        
        if not biometric_type or not biometric_id:
            return Response({'error': 'biometric_type and biometric_id are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create device
        device = None
        if device_id:
            device, _ = Device.objects.get_or_create(
                device_id=device_id,
                user=request.user,
                defaults={
                    'device_name': request.data.get('device_name', 'Unknown Device'),
                    'device_type': request.data.get('device_type', Device.DeviceType.MOBILE_ANDROID),
                    'ip_address': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'is_trusted': True,
                }
            )
        
        # Hash public key for verification
        public_key_hash = ''
        if public_key:
            public_key_hash = hashlib.sha256(public_key.encode()).hexdigest()
        
        # Create or update biometric auth
        biometric_auth, created = BiometricAuth.objects.update_or_create(
            user=request.user,
            device=device,
            biometric_type=biometric_type,
            defaults={
                'biometric_id': biometric_id,
                'public_key_hash': public_key_hash,
                'is_enabled': True,
                'is_verified': True,
                'verified_at': timezone.now(),
            }
        )
        
        # Generate tokens
        refresh = RefreshToken.for_user(request.user)
        
        # Create session
        session = UserSession.objects.create(
            user=request.user,
            device=device,
            refresh_token_jti=refresh['jti'],
            access_token_hash=hashlib.sha256(str(refresh.access_token).encode()).hexdigest()[:255],
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            login_method='BIOMETRIC',
            biometric_auth=biometric_auth,
            status=UserSession.SessionStatus.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),  # 7 days expiry
        )
        
        serializer = self.get_serializer(biometric_auth)
        return Response({
            'biometric_auth': serializer.data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'session_id': session.id,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        """Biometric login"""
        import hashlib
        from rest_framework_simplejwt.tokens import RefreshToken
        from datetime import timedelta
        
        biometric_id = request.data.get('biometric_id')
        challenge_response = request.data.get('challenge_response')
        device_id = request.data.get('device_id')
        
        if not biometric_id:
            return Response({'error': 'biometric_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            biometric_auth = BiometricAuth.objects.get(
                biometric_id=biometric_id,
                is_enabled=True,
                is_verified=True
            )
        except BiometricAuth.DoesNotExist:
            return Response({'error': 'Biometric authentication not found or disabled'}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        user = biometric_auth.user
        
        # Verify challenge response (in production, use proper cryptographic verification)
        # For now, just check if challenge response is provided
        if challenge_response:
            # In production, verify the cryptographic challenge response
            pass
        
        # Update last used
        biometric_auth.last_used = timezone.now()
        biometric_auth.save()
        
        # Get or create device
        device = None
        if device_id:
            device, _ = Device.objects.get_or_create(
                device_id=device_id,
                user=user,
                defaults={
                    'device_name': request.data.get('device_name', 'Unknown Device'),
                    'device_type': request.data.get('device_type', Device.DeviceType.MOBILE_ANDROID),
                    'ip_address': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'is_trusted': True,
                }
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Create session
        session = UserSession.objects.create(
            user=user,
            device=device,
            refresh_token_jti=refresh['jti'],
            access_token_hash=hashlib.sha256(str(refresh.access_token).encode()).hexdigest()[:255],
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            login_method='BIOMETRIC',
            biometric_auth=biometric_auth,
            status=UserSession.SessionStatus.ACTIVE,
            expires_at=timezone.now() + timedelta(days=7),
        )
        
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'session_id': session.id,
        })
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserSessionViewSet(viewsets.ModelViewSet):
    """User session management viewset"""
    serializer_class = UserSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return UserSession.objects.all()
        return UserSession.objects.filter(user=user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def active(self, request):
        """Get active sessions"""
        active_sessions = UserSession.objects.filter(
            user=request.user,
            status=UserSession.SessionStatus.ACTIVE
        ).order_by('-last_activity')
        
        serializer = self.get_serializer(active_sessions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def revoke(self, request, pk=None):
        """Revoke a session"""
        session = self.get_object()
        
        if session.user != request.user and request.user.role != User.Role.ADMIN:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        session.revoke()
        serializer = self.get_serializer(session)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def revoke_all_other(self, request):
        """Revoke all other sessions except current"""
        from rest_framework_simplejwt.tokens import RefreshToken
        
        # Get current session JTI from refresh token if available
        refresh_token = request.data.get('refresh_token')
        current_jti = None
        
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                current_jti = token['jti']
            except Exception:
                pass
        
        # Revoke all other active sessions
        sessions_to_revoke = UserSession.objects.filter(
            user=request.user,
            status=UserSession.SessionStatus.ACTIVE
        )
        
        if current_jti:
            sessions_to_revoke = sessions_to_revoke.exclude(refresh_token_jti=current_jti)
        
        revoked_count = 0
        for session in sessions_to_revoke:
            session.revoke()
            revoked_count += 1
        
        return Response({
            'message': f'Revoked {revoked_count} session(s)',
            'revoked_count': revoked_count
        })

