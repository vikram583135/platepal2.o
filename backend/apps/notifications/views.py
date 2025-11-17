"""
Views for notifications app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Notification viewset (read-only)"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        return Response({'message': 'All notifications marked as read'})
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Clear all read notifications"""
        Notification.objects.filter(
            user=request.user,
            is_read=True,
            is_deleted=False
        ).update(is_deleted=True, deleted_at=timezone.now())
        return Response({'message': 'All read notifications cleared'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notification count"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_deleted=False
        ).count()
        return Response({'count': count})
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent notifications (last 20)"""
        notifications = Notification.objects.filter(
            user=request.user,
            is_deleted=False
        ).order_by('-created_at')[:20]
        serializer = NotificationSerializer(notifications, many=True)
        return Response({'notifications': serializer.data})


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """Notification preference viewset"""
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user,
            defaults={
                'email_order_updates': True,
                'email_promotions': True,
                'email_payment_updates': True,
                'push_order_updates': True,
                'push_promotions': True,
            }
        )
        return preference
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

