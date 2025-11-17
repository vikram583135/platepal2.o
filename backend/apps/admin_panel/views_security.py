"""
Security, compliance and privacy viewsets
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
import json

from apps.accounts.models import User, Address, PaymentMethod
from apps.orders.models import Order
from apps.payments.models import Wallet, WalletTransaction
from .permissions import IsAdminUser, HasAdminPermission
from .models import AuditLogEntry

User = get_user_model()


class GDPRViewSet(viewsets.ViewSet):
    """GDPR compliance workflows"""
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.gdpr.manage')]
    
    @action(detail=False, methods=['post'])
    def export_user_data(self, request):
        """Export all user data (GDPR)"""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Collect all user data
        export_data = {
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'date_joined': user.date_joined.isoformat(),
            },
            'addresses': list(Address.objects.filter(user=user, is_deleted=False).values()),
            'payment_methods': list(PaymentMethod.objects.filter(user=user, is_deleted=False).values('type', 'provider', 'last_four', 'is_default')),
            'orders': list(Order.objects.filter(customer=user, is_deleted=False).values('order_number', 'status', 'total_amount', 'created_at')),
            'wallet': None,
            'wallet_transactions': [],
        }
        
        wallet = Wallet.objects.filter(user=user).first()
        if wallet:
            export_data['wallet'] = {
                'balance': str(wallet.balance),
                'currency': wallet.currency,
            }
            export_data['wallet_transactions'] = list(
                WalletTransaction.objects.filter(wallet=wallet).values(
                    'transaction_type', 'source', 'amount', 'description', 'created_at'
                )
            )
        
        # Log export
        AuditLogEntry.objects.create(
            user=request.user,
            action='gdpr.export_data',
            resource_type='user',
            resource_id=str(user.id),
            reason=request.data.get('reason', 'GDPR data export request')
        )
        
        return Response(export_data)
    
    @action(detail=False, methods=['post'])
    def delete_user_data(self, request):
        """Delete user data (GDPR right to be forgotten)"""
        user_id = request.data.get('user_id')
        reason = request.data.get('reason', '')
        
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Soft delete user and related data
        user.soft_delete()
        Address.objects.filter(user=user).update(is_deleted=True)
        PaymentMethod.objects.filter(user=user).update(is_deleted=True)
        
        # Log deletion
        AuditLogEntry.objects.create(
            user=request.user,
            action='gdpr.delete_data',
            resource_type='user',
            resource_id=str(user.id),
            reason=reason or 'GDPR right to be forgotten'
        )
        
        return Response({'message': 'User data deleted successfully'})
    
    @action(detail=False, methods=['get'])
    def data_requests(self, request):
        """List pending GDPR data requests"""
        # In production, this would query a DataRequest model
        requests = AuditLogEntry.objects.filter(
            action__in=['gdpr.export_data', 'gdpr.delete_data'],
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).order_by('-created_at')[:50]
        
        from .serializers import AuditLogEntrySerializer
        return Response(AuditLogEntrySerializer(requests, many=True).data)


class PIIMaskingViewSet(viewsets.ViewSet):
    """PII masking utilities"""
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.pii.manage')]
    
    @action(detail=False, methods=['post'])
    def mask_user_data(self, request):
        """Mask PII in user data"""
        user_id = request.data.get('user_id')
        fields = request.data.get('fields', ['email', 'phone'])
        
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        masked_data = {}
        if 'email' in fields:
            masked_data['email'] = self._mask_email(user.email)
        if 'phone' in fields:
            masked_data['phone'] = self._mask_phone(user.phone) if user.phone else None
        if 'name' in fields:
            masked_data['first_name'] = self._mask_string(user.first_name)
            masked_data['last_name'] = self._mask_string(user.last_name)
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='pii.mask',
            resource_type='user',
            resource_id=str(user.id),
            reason=request.data.get('reason', 'PII masking request')
        )
        
        return Response(masked_data)
    
    def _mask_email(self, email):
        """Mask email address"""
        if not email:
            return None
        parts = email.split('@')
        if len(parts) != 2:
            return email
        username = parts[0]
        domain = parts[1]
        if len(username) <= 2:
            masked_username = '*' * len(username)
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        return f"{masked_username}@{domain}"
    
    def _mask_phone(self, phone):
        """Mask phone number"""
        if not phone:
            return None
        if len(phone) <= 4:
            return '*' * len(phone)
        return phone[:2] + '*' * (len(phone) - 4) + phone[-2:]
    
    def _mask_string(self, s):
        """Mask string"""
        if not s:
            return None
        if len(s) <= 2:
            return '*' * len(s)
        return s[0] + '*' * (len(s) - 2) + s[-1]


class ConsentManagementViewSet(viewsets.ViewSet):
    """Consent management"""
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.consent.manage')]
    
    @action(detail=False, methods=['get'])
    def user_consents(self, request):
        """Get user consent status"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.accounts.models import CookieConsent
        consents = CookieConsent.objects.filter(user_id=user_id).order_by('-consent_date')
        
        return Response([{
            'id': c.id,
            'consent_given': c.consent_given,
            'analytics_cookies': c.analytics_cookies,
            'marketing_cookies': c.marketing_cookies,
            'consent_date': c.consent_date.isoformat(),
        } for c in consents])
    
    @action(detail=False, methods=['post'])
    def revoke_consent(self, request):
        """Revoke user consent"""
        user_id = request.data.get('user_id')
        consent_type = request.data.get('consent_type')  # 'analytics', 'marketing', 'all'
        
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from apps.accounts.models import CookieConsent
        # In production, create a new consent record with revoked status
        AuditLogEntry.objects.create(
            user=request.user,
            action='consent.revoke',
            resource_type='user',
            resource_id=str(user_id),
            reason=request.data.get('reason', '')
        )
        
        return Response({'message': 'Consent revoked successfully'})

