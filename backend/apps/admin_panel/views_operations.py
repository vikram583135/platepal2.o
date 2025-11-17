"""
System operations viewsets
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta

from .models_operations import (
    SystemHealthMetric, AlertRule, Incident, IncidentUpdate,
    RateLimitRule, IPWhitelist, IPBlacklist, MaintenanceWindow
)
from .permissions import IsAdminUser, HasAdminPermission
from .models import AuditLogEntry


class SystemHealthViewSet(viewsets.ViewSet):
    """System health monitoring"""
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.system.view')]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get system health dashboard data"""
        # Get latest metrics for each service
        services = SystemHealthMetric.objects.values('service_name').distinct()
        
        health_data = {}
        for service in services:
            service_name = service['service_name']
            latest_metrics = SystemHealthMetric.objects.filter(
                service_name=service_name
            ).order_by('-created_at')[:10]
            
            health_data[service_name] = {
                'status': 'healthy',
                'metrics': {}
            }
            
            for metric in latest_metrics:
                if metric.status == 'critical':
                    health_data[service_name]['status'] = 'critical'
                elif metric.status == 'warning' and health_data[service_name]['status'] == 'healthy':
                    health_data[service_name]['status'] = 'warning'
                
                if metric.metric_type not in health_data[service_name]['metrics']:
                    health_data[service_name]['metrics'][metric.metric_type] = {
                        'current': metric.value,
                        'status': metric.status,
                        'threshold_warning': metric.threshold_warning,
                        'threshold_critical': metric.threshold_critical,
                    }
        
        return Response(health_data)
    
    @action(detail=False, methods=['get'])
    def metrics(self, request):
        """Get metrics for a specific service"""
        service_name = request.query_params.get('service')
        metric_type = request.query_params.get('metric_type')
        hours = int(request.query_params.get('hours', 24))
        
        since = timezone.now() - timedelta(hours=hours)
        queryset = SystemHealthMetric.objects.filter(created_at__gte=since)
        
        if service_name:
            queryset = queryset.filter(service_name=service_name)
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        metrics = queryset.order_by('created_at')
        
        return Response([{
            'timestamp': m.created_at.isoformat(),
            'value': m.value,
            'status': m.status,
        } for m in metrics])


class AlertRuleViewSet(viewsets.ModelViewSet):
    """Alert rule management"""
    queryset = AlertRule.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.alerts.manage')]
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test an alert rule"""
        rule = self.get_object()
        # In production, test the alert rule
        return Response({'message': 'Alert rule test not implemented'})


class IncidentViewSet(viewsets.ModelViewSet):
    """Incident management"""
    queryset = Incident.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.incidents.manage')]
    
    def get_queryset(self):
        queryset = Incident.objects.select_related('reported_by', 'resolved_by').all()
        
        status = self.request.query_params.get('status')
        severity = self.request.query_params.get('severity')
        
        if status:
            queryset = queryset.filter(status=status)
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update incident status"""
        incident = self.get_object()
        new_status = request.data.get('status')
        message = request.data.get('message', '')
        
        if new_status not in [s[0] for s in Incident.Status.choices]:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        before_state = {'status': incident.status}
        incident.status = new_status
        
        if new_status == Incident.Status.RESOLVED:
            incident.resolved_at = timezone.now()
            incident.resolved_by = request.user
        
        incident.save()
        
        # Create update
        IncidentUpdate.objects.create(
            incident=incident,
            user=request.user,
            message=message or f"Status changed to {new_status}",
            is_public=request.data.get('is_public', False)
        )
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='incident.update_status',
            resource_type='incident',
            resource_id=str(incident.id),
            before_state=before_state,
            after_state={'status': new_status},
            reason=message
        )
        
        return Response({'message': 'Incident status updated'})
    
    @action(detail=True, methods=['post'])
    def add_update(self, request, pk=None):
        """Add an update to an incident"""
        incident = self.get_object()
        message = request.data.get('message', '')
        is_public = request.data.get('is_public', False)
        
        update = IncidentUpdate.objects.create(
            incident=incident,
            user=request.user,
            message=message,
            is_public=is_public
        )
        
        return Response({'message': 'Update added', 'id': update.id})


class RateLimitRuleViewSet(viewsets.ModelViewSet):
    """Rate limit rule management"""
    queryset = RateLimitRule.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.ratelimit.manage')]


class IPWhitelistViewSet(viewsets.ModelViewSet):
    """IP whitelist management"""
    queryset = IPWhitelist.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.security.manage')]


class IPBlacklistViewSet(viewsets.ModelViewSet):
    """IP blacklist management"""
    queryset = IPBlacklist.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.security.manage')]


class MaintenanceWindowViewSet(viewsets.ModelViewSet):
    """Maintenance window management"""
    queryset = MaintenanceWindow.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.maintenance.manage')]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

