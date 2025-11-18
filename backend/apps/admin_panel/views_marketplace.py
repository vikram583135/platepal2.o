"""
Marketplace and catalog management viewsets
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone

from apps.restaurants.models import MenuCategory, MenuItem, Promotion, Restaurant
from .permissions import IsAdminUser, HasAdminPermission
from .models import AuditLogEntry
from .serializers import PromotionSerializer


class CatalogManagementViewSet(viewsets.ViewSet):
    """Catalog and taxonomy management"""
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.catalog.manage')]
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """List all menu categories"""
        categories = MenuCategory.objects.select_related('menu__restaurant').all()
        
        search = request.query_params.get('search')
        if search:
            categories = categories.filter(name__icontains=search)
        
        # Group by restaurant
        grouped = {}
        for cat in categories:
            restaurant_name = cat.menu.restaurant.name
            if restaurant_name not in grouped:
                grouped[restaurant_name] = []
            grouped[restaurant_name].append({
                'id': cat.id,
                'name': cat.name,
                'menu': cat.menu.name,
                'is_active': cat.is_active,
            })
        
        return Response(grouped)
    
    @action(detail=False, methods=['post'])
    def create_category(self, request):
        """Create a new category"""
        menu_id = request.data.get('menu_id')
        name = request.data.get('name')
        
        from apps.restaurants.models import Menu
        try:
            menu = Menu.objects.get(id=menu_id)
            category = MenuCategory.objects.create(
                menu=menu,
                name=name,
                is_active=True
            )
            
            AuditLogEntry.objects.create(
                user=request.user,
                action='catalog.category.create',
                resource_type='menu_category',
                resource_id=str(category.id),
                reason=request.data.get('reason', '')
            )
            
            return Response({'message': 'Category created successfully', 'id': category.id})
        except Menu.DoesNotExist:
            return Response({'error': 'Menu not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def featured_listings(self, request):
        """Get featured restaurant listings"""
        featured = Restaurant.objects.filter(
            is_deleted=False,
            status=Restaurant.Status.ACTIVE
        ).order_by('-rating')[:20]
        
        from apps.restaurants.serializers import RestaurantSerializer
        return Response(RestaurantSerializer(featured, many=True).data)
    
    @action(detail=False, methods=['post'])
    def set_featured(self, request):
        """Set restaurants as featured"""
        restaurant_ids = request.data.get('restaurant_ids', [])
        reason = request.data.get('reason', '')
        
        restaurants = Restaurant.objects.filter(id__in=restaurant_ids)
        
        for restaurant in restaurants:
            AuditLogEntry.objects.create(
                user=request.user,
                action='catalog.featured.set',
                resource_type='restaurant',
                resource_id=str(restaurant.id),
                reason=reason
            )
        
        return Response({'message': f'{restaurants.count()} restaurants featured'})


class CampaignManagementViewSet(viewsets.ModelViewSet):
    """Campaign management"""
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.campaign.manage')]
    
    def get_queryset(self):
        queryset = Promotion.objects.select_related('restaurant').all()
        
        search = self.request.query_params.get('search')
        is_active = self.request.query_params.get('is_active')
        offer_type = self.request.query_params.get('offer_type')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if offer_type:
            queryset = queryset.filter(offer_type=offer_type)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a merchant campaign"""
        promotion = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {'is_active': promotion.is_active}
        promotion.is_active = True
        promotion.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='campaign.approve',
            resource_type='promotion',
            resource_id=str(promotion.id),
            before_state=before_state,
            after_state={'is_active': True},
            reason=reason
        )
        
        return Response({'message': 'Campaign approved successfully'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a merchant campaign"""
        promotion = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {'is_active': promotion.is_active}
        promotion.is_active = False
        promotion.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='campaign.reject',
            resource_type='promotion',
            resource_id=str(promotion.id),
            before_state=before_state,
            after_state={'is_active': False},
            reason=reason
        )
        
        return Response({'message': 'Campaign rejected successfully'})
    
    @action(detail=False, methods=['post'])
    def create_platform_campaign(self, request):
        """Create a platform-wide campaign"""
        from apps.restaurants.serializers import PromotionSerializer
        
        data = request.data.copy()
        data['offer_type'] = 'PLATFORM'
        data['restaurant'] = None  # Platform campaigns don't belong to a restaurant
        
        serializer = PromotionSerializer(data=data)
        if serializer.is_valid():
            promotion = serializer.save()
            
            AuditLogEntry.objects.create(
                user=request.user,
                action='campaign.create_platform',
                resource_type='promotion',
                resource_id=str(promotion.id),
                reason=request.data.get('reason', '')
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get campaign performance metrics"""
        promotion = self.get_object()
        
        # In production, calculate actual metrics
        metrics = {
            'total_uses': promotion.uses_count,
            'max_uses': promotion.max_uses,
            'usage_percentage': (promotion.uses_count / promotion.max_uses * 100) if promotion.max_uses else 0,
            'total_discount_given': 0,  # Would calculate from orders
            'estimated_revenue_impact': 0,
        }
        
        return Response(metrics)

