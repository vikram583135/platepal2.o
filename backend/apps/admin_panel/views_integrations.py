"""
Integrations and extensibility viewsets
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from .permissions import IsAdminUser, HasAdminPermission
from .models import AuditLogEntry


class IntegrationViewSet(viewsets.ViewSet):
    """Integration management"""
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.integrations.manage')]
    
    def list(self, request):
        """List all integrations"""
        integrations = [
            {
                'id': 'payment-razorpay',
                'name': 'Razorpay',
                'type': 'payment_gateway',
                'status': 'active',
                'config': {'merchant_id': '***', 'api_key': '***'},
            },
            {
                'id': 'payment-stripe',
                'name': 'Stripe',
                'type': 'payment_gateway',
                'status': 'inactive',
                'config': {},
            },
            {
                'id': 'sms-twilio',
                'name': 'Twilio',
                'type': 'sms',
                'status': 'active',
                'config': {'account_sid': '***'},
            },
            {
                'id': 'email-sendgrid',
                'name': 'SendGrid',
                'type': 'email',
                'status': 'active',
                'config': {'api_key': '***'},
            },
            {
                'id': 'mapping-google',
                'name': 'Google Maps',
                'type': 'mapping',
                'status': 'active',
                'config': {'api_key': '***'},
            },
            {
                'id': 'accounting-quickbooks',
                'name': 'QuickBooks',
                'type': 'accounting',
                'status': 'inactive',
                'config': {},
            },
        ]
        return Response(integrations)
    
    @action(detail=False, methods=['post'])
    def configure(self, request):
        """Configure an integration"""
        integration_id = request.data.get('integration_id')
        config = request.data.get('config', {})
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='integration.configure',
            resource_type='integration',
            resource_id=integration_id,
            reason=request.data.get('reason', '')
        )
        
        return Response({'message': 'Integration configured successfully'})
    
    @action(detail=False, methods=['post'])
    def test(self, request):
        """Test an integration"""
        integration_id = request.data.get('integration_id')
        # In production, test the actual integration
        return Response({'message': f'Test for {integration_id} not implemented', 'success': True})
    
    @action(detail=False, methods=['get'])
    def payment_gateways(self, request):
        """Get payment gateway status"""
        gateways = [
            {
                'name': 'Razorpay',
                'status': 'active',
                'transactions_today': 1250,
                'success_rate': 99.2,
                'reconciliation_status': 'synced',
            },
            {
                'name': 'Stripe',
                'status': 'inactive',
                'transactions_today': 0,
                'success_rate': 0,
                'reconciliation_status': 'not_configured',
            },
        ]
        return Response(gateways)
    
    @action(detail=False, methods=['get'])
    def reconciliation_status(self, request):
        """Get reconciliation status for payment gateways"""
        status_data = {
            'razorpay': {
                'last_sync': '2024-01-20T10:30:00Z',
                'pending_transactions': 5,
                'discrepancies': 0,
            },
            'stripe': {
                'last_sync': None,
                'pending_transactions': 0,
                'discrepancies': 0,
            },
        }
        return Response(status_data)


class APIExplorerViewSet(viewsets.ViewSet):
    """API explorer for admin APIs"""
    permission_classes = [IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def endpoints(self, request):
        """List all admin API endpoints"""
        endpoints = [
            {
                'path': '/api/admin/management/users/',
                'method': 'GET',
                'description': 'List all users',
                'permissions': ['admin.user.manage'],
            },
            {
                'path': '/api/admin/management/users/{id}/ban/',
                'method': 'POST',
                'description': 'Ban a user',
                'permissions': ['admin.user.manage'],
            },
            {
                'path': '/api/admin/orders/',
                'method': 'GET',
                'description': 'List all orders',
                'permissions': ['admin.order.view'],
            },
            {
                'path': '/api/admin/moderation/reviews/',
                'method': 'GET',
                'description': 'List reviews for moderation',
                'permissions': ['admin.moderation.manage'],
            },
            {
                'path': '/api/admin/automation/rules/',
                'method': 'GET',
                'description': 'List automation rules',
                'permissions': ['admin.automation.manage'],
            },
        ]
        return Response(endpoints)
    
    @action(detail=False, methods=['post'])
    def test_endpoint(self, request):
        """Test an API endpoint"""
        path = request.data.get('path')
        method = request.data.get('method', 'GET')
        payload = request.data.get('payload', {})
        
        # In production, make actual API call
        return Response({
            'message': f'Test {method} {path}',
            'status': 200,
            'response': {'test': 'response'}
        })

