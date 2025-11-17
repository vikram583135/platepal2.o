"""
Advanced features viewsets
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models_advanced import (
    FraudDetectionRule, FraudFlag, Chargeback, FeatureFlag, FeatureFlagHistory, SLO
)
from .permissions import IsAdminUser, HasAdminPermission
from .models import AuditLogEntry


class FraudDetectionViewSet(viewsets.ViewSet):
    """Fraud detection management"""
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.fraud.manage')]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get fraud detection dashboard"""
        today = timezone.now().date()
        
        flags_today = FraudFlag.objects.filter(created_at__date=today).count()
        high_risk_flags = FraudFlag.objects.filter(risk_score__gte=80, status='PENDING').count()
        confirmed_fraud = FraudFlag.objects.filter(status='CONFIRMED', created_at__date=today).count()
        
        return Response({
            'flags_today': flags_today,
            'high_risk_pending': high_risk_flags,
            'confirmed_fraud_today': confirmed_fraud,
        })
    
    @action(detail=False, methods=['get'])
    def flags(self, request):
        """Get fraud flags"""
        queryset = FraudFlag.objects.select_related('user', 'order', 'payment', 'rule_triggered').all()
        
        status_filter = request.query_params.get('status')
        min_risk = request.query_params.get('min_risk')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if min_risk:
            queryset = queryset.filter(risk_score__gte=int(min_risk))
        
        flags = queryset.order_by('-risk_score', '-created_at')[:100]
        
        return Response([{
            'id': f.id,
            'user_id': f.user.id if f.user else None,
            'order_id': f.order.id if f.order else None,
            'risk_score': f.risk_score,
            'reason': f.reason,
            'status': f.status,
            'created_at': f.created_at.isoformat(),
        } for f in flags])
    
    @action(detail=False, methods=['post'])
    def review_flag(self, request):
        """Review a fraud flag"""
        flag_id = request.data.get('flag_id')
        status = request.data.get('status')  # 'FALSE_POSITIVE', 'CONFIRMED'
        notes = request.data.get('notes', '')
        
        try:
            flag = FraudFlag.objects.get(id=flag_id)
        except FraudFlag.DoesNotExist:
            return Response({'error': 'Flag not found'}, status=status.HTTP_404_NOT_FOUND)
        
        flag.status = status
        flag.reviewed_by = request.user
        flag.reviewed_at = timezone.now()
        flag.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='fraud.flag.review',
            resource_type='fraud_flag',
            resource_id=str(flag.id),
            reason=notes
        )
        
        return Response({'message': 'Flag reviewed successfully'})


class ChargebackViewSet(viewsets.ModelViewSet):
    """Chargeback management"""
    queryset = Chargeback.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.chargeback.manage')]
    
    def get_queryset(self):
        queryset = Chargeback.objects.select_related('order', 'payment', 'assigned_to').all()
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-received_date')
    
    @action(detail=True, methods=['post'])
    def submit_evidence(self, request, pk=None):
        """Submit evidence for chargeback"""
        chargeback = self.get_object()
        evidence_urls = request.data.get('evidence_urls', [])
        
        chargeback.evidence_bundle = evidence_urls
        chargeback.status = Chargeback.Status.EVIDENCE_SUBMITTED
        chargeback.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='chargeback.submit_evidence',
            resource_type='chargeback',
            resource_id=str(chargeback.id),
            reason=request.data.get('notes', '')
        )
        
        return Response({'message': 'Evidence submitted successfully'})
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update chargeback status"""
        chargeback = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in [s[0] for s in Chargeback.Status.choices]:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        before_state = {'status': chargeback.status}
        chargeback.status = new_status
        chargeback.notes = notes
        chargeback.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='chargeback.update_status',
            resource_type='chargeback',
            resource_id=str(chargeback.id),
            before_state=before_state,
            after_state={'status': new_status},
            reason=notes
        )
        
        return Response({'message': 'Status updated successfully'})


class FeatureFlagViewSet(viewsets.ModelViewSet):
    """Feature flag management"""
    queryset = FeatureFlag.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.feature_flags.manage')]
    
    def perform_create(self, serializer):
        flag = serializer.save(created_by=self.request.user)
        
        FeatureFlagHistory.objects.create(
            flag=flag,
            changed_by=self.request.user,
            before_state={},
            after_state={
                'is_enabled': flag.is_enabled,
                'rollout_percentage': flag.rollout_percentage,
            },
            reason='Feature flag created'
        )
    
    def perform_update(self, serializer):
        flag = self.get_object()
        before_state = {
            'is_enabled': flag.is_enabled,
            'rollout_percentage': flag.rollout_percentage,
        }
        
        flag = serializer.save()
        
        after_state = {
            'is_enabled': flag.is_enabled,
            'rollout_percentage': flag.rollout_percentage,
        }
        
        FeatureFlagHistory.objects.create(
            flag=flag,
            changed_by=self.request.user,
            before_state=before_state,
            after_state=after_state,
            reason=self.request.data.get('reason', '')
        )
        
        AuditLogEntry.objects.create(
            user=self.request.user,
            action='feature_flag.update',
            resource_type='feature_flag',
            resource_id=str(flag.id),
            before_state=before_state,
            after_state=after_state,
            reason=self.request.data.get('reason', '')
        )
    
    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """Rollback feature flag"""
        flag = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {
            'is_enabled': flag.is_enabled,
            'rollout_percentage': flag.rollout_percentage,
        }
        
        flag.is_enabled = False
        flag.rollout_percentage = 0
        flag.save()
        
        FeatureFlagHistory.objects.create(
            flag=flag,
            changed_by=request.user,
            before_state=before_state,
            after_state={'is_enabled': False, 'rollout_percentage': 0},
            reason=reason or 'Rollback'
        )
        
        return Response({'message': 'Feature flag rolled back'})


class SLOViewSet(viewsets.ModelViewSet):
    """SLO management"""
    queryset = SLO.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.slo.manage')]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get SLO dashboard"""
        slos = SLO.objects.filter(is_active=True)
        
        dashboard_data = []
        for slo in slos:
            # In production, calculate current value from metrics
            compliance = (slo.current_value or 0) <= slo.target_value if slo.current_value else None
            
            dashboard_data.append({
                'id': slo.id,
                'service_name': slo.service_name,
                'metric_name': slo.metric_name,
                'target_value': slo.target_value,
                'current_value': slo.current_value,
                'compliant': compliance,
            })
        
        return Response(dashboard_data)

