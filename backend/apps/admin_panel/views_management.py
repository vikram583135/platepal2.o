"""
Management viewsets for admin operations on users, restaurants, orders, etc.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta

from apps.orders.models import Order
from apps.restaurants.models import Restaurant
from apps.payments.models import Wallet, WalletTransaction
from apps.accounts.models import Address, PaymentMethod, Device
from .permissions import IsAdminUser, HasAdminPermission
from .models import AuditLogEntry, Environment

User = get_user_model()


class UserManagementViewSet(viewsets.ModelViewSet):
    """Admin user management operations"""
    queryset = User.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.user.manage')]
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # Filtering
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')
        search = self.request.query_params.get('search')
        
        if role:
            queryset = queryset.filter(role=role)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        return queryset.select_related().order_by('-date_joined')
    
    @action(detail=True, methods=['post'])
    def ban(self, request, pk=None):
        """Ban a user"""
        user = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {'is_active': user.is_active}
        user.is_active = False
        user.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='user.ban',
            resource_type='user',
            resource_id=str(user.id),
            before_state=before_state,
            after_state={'is_active': False},
            reason=reason,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'User banned successfully'})
    
    @action(detail=True, methods=['post'])
    def unban(self, request, pk=None):
        """Unban a user"""
        user = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {'is_active': user.is_active}
        user.is_active = True
        user.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='user.unban',
            resource_type='user',
            resource_id=str(user.id),
            before_state=before_state,
            after_state={'is_active': True},
            reason=reason,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'User unbanned successfully'})
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Force password reset for a user"""
        user = self.get_object()
        reason = request.data.get('reason', '')
        
        # In production, send password reset email
        # For now, just log the action
        AuditLogEntry.objects.create(
            user=request.user,
            action='user.reset_password',
            resource_type='user',
            resource_id=str(user.id),
            reason=reason,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Password reset initiated'})
    
    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Get full user profile"""
        user = self.get_object()
        
        # Get related data
        orders = Order.objects.filter(customer=user).order_by('-created_at')[:10]
        wallet = Wallet.objects.filter(user=user).first()
        wallet_transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:20] if wallet else []
        addresses = Address.objects.filter(user=user, is_deleted=False)
        payment_methods = PaymentMethod.objects.filter(user=user, is_deleted=False)
        devices = Device.objects.filter(user=user, is_active=True)
        
        from apps.orders.serializers import OrderSerializer
        from apps.payments.serializers import WalletSerializer, WalletTransactionSerializer
        from apps.accounts.serializers import AddressSerializer, PaymentMethodSerializer, DeviceSerializer
        
        return Response({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'role': user.role,
                'is_active': user.is_active,
                'is_email_verified': user.is_email_verified,
                'is_phone_verified': user.is_phone_verified,
                'date_joined': user.date_joined,
            },
            'orders': OrderSerializer(orders, many=True).data,
            'wallet': WalletSerializer(wallet).data if wallet else None,
            'wallet_transactions': WalletTransactionSerializer(wallet_transactions, many=True).data,
            'addresses': AddressSerializer(addresses, many=True).data,
            'payment_methods': PaymentMethodSerializer(payment_methods, many=True).data,
            'devices': DeviceSerializer(devices, many=True).data,
        })
    
    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """Get user activity log"""
        user = self.get_object()
        
        audit_logs = AuditLogEntry.objects.filter(
            Q(user=user) | Q(resource_type='user', resource_id=str(user.id))
        ).order_by('-created_at')[:50]
        
        from .serializers import AuditLogEntrySerializer
        return Response(AuditLogEntrySerializer(audit_logs, many=True).data)
    
    @action(detail=False, methods=['post'])
    def bulk_ban(self, request):
        """Bulk ban users"""
        user_ids = request.data.get('user_ids', [])
        reason = request.data.get('reason', '')
        
        users = User.objects.filter(id__in=user_ids)
        count = users.update(is_active=False)
        
        # Create audit logs
        for user in users:
            AuditLogEntry.objects.create(
                user=request.user,
                action='user.ban',
                resource_type='user',
                resource_id=str(user.id),
                before_state={'is_active': True},
                after_state={'is_active': False},
                reason=reason,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        return Response({'message': f'{count} users banned successfully'})
    
    @action(detail=False, methods=['post'])
    def bulk_unban(self, request):
        """Bulk unban users"""
        user_ids = request.data.get('user_ids', [])
        reason = request.data.get('reason', '')
        
        users = User.objects.filter(id__in=user_ids)
        count = users.update(is_active=True)
        
        # Create audit logs
        for user in users:
            AuditLogEntry.objects.create(
                user=request.user,
                action='user.unban',
                resource_type='user',
                resource_id=str(user.id),
                before_state={'is_active': False},
                after_state={'is_active': True},
                reason=reason,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        return Response({'message': f'{count} users unbanned successfully'})


class RestaurantManagementViewSet(viewsets.ReadOnlyModelViewSet):
    """Restaurant management for admin"""
    queryset = Restaurant.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.restaurant.manage')]
    
    def get_queryset(self):
        queryset = Restaurant.objects.select_related('owner').all()
        
        # Filtering
        status = self.request.query_params.get('status')
        search = self.request.query_params.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(owner__email__icontains=search) |
                Q(city__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        """Suspend a restaurant"""
        restaurant = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {'status': restaurant.status}
        restaurant.status = Restaurant.Status.SUSPENDED
        restaurant.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='restaurant.suspend',
            resource_type='restaurant',
            resource_id=str(restaurant.id),
            before_state=before_state,
            after_state={'status': restaurant.status},
            reason=reason
        )
        
        return Response({'message': 'Restaurant suspended successfully'})
    
    @action(detail=True, methods=['post'])
    def approve_kyc(self, request, pk=None):
        """Approve restaurant KYC"""
        restaurant = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {'kyc_verified': restaurant.kyc_verified}
        restaurant.kyc_verified = True
        restaurant.kyc_verified_at = timezone.now()
        restaurant.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='restaurant.kyc.approve',
            resource_type='restaurant',
            resource_id=str(restaurant.id),
            before_state=before_state,
            after_state={'kyc_verified': True},
            reason=reason
        )
        
        return Response({'message': 'KYC approved successfully'})


class DeliveryManagementViewSet(viewsets.ReadOnlyModelViewSet):
    """Delivery partner management for admin"""
    queryset = User.objects.filter(role=User.Role.DELIVERY)
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.delivery.manage')]
    
    def get_queryset(self):
        queryset = User.objects.filter(role=User.Role.DELIVERY)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset.order_by('-date_joined')

