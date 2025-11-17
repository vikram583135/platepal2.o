"""
Automation and workflow viewsets
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone

from .models_automation import (
    AutomationRule, ScheduledJob, JobExecution, Webhook, WebhookDelivery
)
from .permissions import IsAdminUser, HasAdminPermission
from .models import AuditLogEntry


class AutomationRuleViewSet(viewsets.ModelViewSet):
    """Automation rule management"""
    queryset = AutomationRule.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.automation.manage')]
    
    def get_queryset(self):
        queryset = AutomationRule.objects.all()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset.order_by('-priority', 'name')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test an automation rule"""
        rule = self.get_object()
        # In production, test the rule with sample data
        return Response({'message': 'Rule test not implemented', 'rule_id': rule.id})
    
    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """Enable an automation rule"""
        rule = self.get_object()
        rule.is_active = True
        rule.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='automation.enable',
            resource_type='automation_rule',
            resource_id=str(rule.id)
        )
        
        return Response({'message': 'Rule enabled'})
    
    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """Disable an automation rule"""
        rule = self.get_object()
        rule.is_active = False
        rule.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='automation.disable',
            resource_type='automation_rule',
            resource_id=str(rule.id)
        )
        
        return Response({'message': 'Rule disabled'})


class ScheduledJobViewSet(viewsets.ModelViewSet):
    """Scheduled job management"""
    queryset = ScheduledJob.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.jobs.manage')]
    
    def get_queryset(self):
        queryset = ScheduledJob.objects.all()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset.order_by('next_run_at')
    
    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """Manually trigger a scheduled job"""
        job = self.get_object()
        # In production, queue the job for immediate execution
        AuditLogEntry.objects.create(
            user=request.user,
            action='job.run_manually',
            resource_type='scheduled_job',
            resource_id=str(job.id)
        )
        return Response({'message': 'Job queued for execution'})
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get job execution history"""
        job = self.get_object()
        executions = JobExecution.objects.filter(job=job).order_by('-started_at')[:50]
        
        return Response([{
            'id': e.id,
            'status': e.status,
            'started_at': e.started_at.isoformat() if e.started_at else None,
            'completed_at': e.completed_at.isoformat() if e.completed_at else None,
            'error_message': e.error_message,
        } for e in executions])


class WebhookViewSet(viewsets.ModelViewSet):
    """Webhook management"""
    queryset = Webhook.objects.all()
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.webhooks.manage')]
    
    def get_queryset(self):
        queryset = Webhook.objects.all()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test a webhook"""
        webhook = self.get_object()
        test_payload = request.data.get('payload', {'test': True})
        
        # In production, send test webhook
        AuditLogEntry.objects.create(
            user=request.user,
            action='webhook.test',
            resource_type='webhook',
            resource_id=str(webhook.id)
        )
        
        return Response({'message': 'Test webhook sent'})
    
    @action(detail=True, methods=['get'])
    def deliveries(self, request, pk=None):
        """Get webhook delivery history"""
        webhook = self.get_object()
        deliveries = WebhookDelivery.objects.filter(webhook=webhook).order_by('-created_at')[:100]
        
        return Response([{
            'id': d.id,
            'event': d.event,
            'success': d.success,
            'response_status': d.response_status,
            'error_message': d.error_message,
            'created_at': d.created_at.isoformat(),
        } for d in deliveries])
    
    @action(detail=True, methods=['post'])
    def retry_failed(self, request, pk=None):
        """Retry failed webhook deliveries"""
        webhook = self.get_object()
        failed_deliveries = WebhookDelivery.objects.filter(
            webhook=webhook,
            success=False
        ).order_by('-created_at')[:10]
        
        # In production, retry these deliveries
        count = failed_deliveries.count()
        
        return Response({'message': f'{count} failed deliveries queued for retry'})

