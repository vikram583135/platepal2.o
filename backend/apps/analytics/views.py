"""
Views for analytics app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import AnalyticsEvent
from apps.orders.models import Order
from apps.restaurants.models import Restaurant


class AnalyticsViewSet(viewsets.ViewSet):
    """Analytics viewset"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get dashboard analytics (admin only)"""
        if request.user.role != 'ADMIN':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Time ranges
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Orders
        total_orders = Order.objects.filter(is_deleted=False).count()
        orders_today = Order.objects.filter(created_at__date=today, is_deleted=False).count()
        orders_week = Order.objects.filter(created_at__gte=week_ago, is_deleted=False).count()
        
        # Revenue
        revenue_today = Order.objects.filter(
            created_at__date=today,
            is_deleted=False,
            status=Order.Status.DELIVERED
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_week = Order.objects.filter(
            created_at__gte=week_ago,
            is_deleted=False,
            status=Order.Status.DELIVERED
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Restaurants
        total_restaurants = Restaurant.objects.filter(is_deleted=False).count()
        active_restaurants = Restaurant.objects.filter(
            is_deleted=False,
            status=Restaurant.Status.ACTIVE
        ).count()
        
        return Response({
            'orders': {
                'total': total_orders,
                'today': orders_today,
                'week': orders_week,
            },
            'revenue': {
                'today': float(revenue_today),
                'week': float(revenue_week),
            },
            'restaurants': {
                'total': total_restaurants,
                'active': active_restaurants,
            }
        })
    
    @action(detail=False, methods=['post'], permission_classes=[])
    def track_event(self, request):
        """Track analytics event"""
        event_type = request.data.get('event_type')
        properties = request.data.get('properties', {})
        
        if not event_type:
            return Response({'error': 'event_type required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user if request.user.is_authenticated else None
        
        AnalyticsEvent.objects.create(
            user=user,
            event_type=event_type,
            properties=properties,
            session_id=request.data.get('session_id', ''),
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        return Response({'message': 'Event tracked'})
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

