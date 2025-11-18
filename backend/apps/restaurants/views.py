"""
Views for restaurants app
"""
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import ValidationError, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg, F
from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from .models import (
    Restaurant,
    Menu,
    MenuCategory,
    MenuItem,
    ItemModifier,
    Promotion,
    SearchHistory,
    PopularSearch,
    RestaurantSettings,
    RestaurantBranch,
    ManagerProfile,
    RestaurantDocument,
    DocumentReviewLog,
    RestaurantAlert,
)
from .serializers import (
    RestaurantSerializer,
    RestaurantListSerializer,
    RestaurantSignupSerializer,
    MenuSerializer,
    MenuCategorySerializer,
    MenuItemSerializer,
    ItemModifierSerializer,
    PromotionSerializer,
    RestaurantSettingsSerializer,
    RestaurantBranchSerializer,
    ManagerProfileSerializer,
    RestaurantDocumentSerializer,
    DocumentReviewLogSerializer,
    RestaurantAlertSerializer,
    RestaurantSettingsUpdateSerializer,
)
from .permissions import IsRestaurantOwner
from apps.accounts.permissions import IsOwnerOrAdmin
from apps.orders.models import Order, Review
from apps.orders.serializers import OrderSerializer
from apps.inventory.models import InventoryItem
from apps.payments.models import Payment


class RestaurantSignupView(APIView):
    """OTP-driven signup flow for restaurant owners"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RestaurantSignupSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        return Response(payload, status=status.HTTP_201_CREATED)


class RestaurantViewSet(viewsets.ModelViewSet):
    """Restaurant viewset"""

    queryset = Restaurant.objects.filter(is_deleted=False)
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'cuisine_type',
        'restaurant_type',
        'city',
        'status',
        'onboarding_status',
        'is_pure_veg',
        'is_halal',
    ]
    search_fields = ['name', 'description', 'city', 'address', 'billing_city']
    ordering_fields = ['rating', 'delivery_time_minutes', 'created_at', 'name', 'cost_for_two', 'hygiene_rating']
    ordering = ['-rating']

    def get_queryset(self):
        queryset = (
            Restaurant.objects.filter(is_deleted=False)
            .select_related('owner', 'settings')
            .prefetch_related(
                'menus__categories__items',
                'branches',
                'managers',
                'documents',
                'alerts',
                'promotions',
            )
        )
        action = getattr(self, 'action', None)
        if action == 'list':
            return queryset.filter(status=Restaurant.Status.ACTIVE)
        user = self.request.user
        if not user.is_authenticated:
            return queryset.filter(status=Restaurant.Status.ACTIVE)
        if user.role == 'ADMIN':
            return queryset
        if user.role == 'RESTAURANT':
            return queryset.filter(owner=user)
        return queryset.filter(status=Restaurant.Status.ACTIVE)
    
    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        search_query = self.request.query_params.get('search', '')
        
        # Enhanced search: also search in menu items
        if search_query:
            # Search in restaurants
            restaurant_ids = list(queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(cuisine_type__icontains=search_query)
            ).values_list('id', flat=True))
            
            # Search in menu items
            menu_item_restaurant_ids = MenuItem.objects.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            ).values_list('category__menu__restaurant_id', flat=True).distinct()
            
            # Combine results
            all_restaurant_ids = list(set(list(restaurant_ids) + list(menu_item_restaurant_ids)))
            queryset = queryset.filter(id__in=all_restaurant_ids)
        
        # Apply filters
        # Multiple cuisines (comma-separated)
        cuisines = self.request.query_params.get('cuisines', '')
        if cuisines:
            cuisine_list = [c.strip() for c in cuisines.split(',') if c.strip()]
            if cuisine_list:
                queryset = queryset.filter(
                    Q(cuisine_type__in=cuisine_list) | Q(cuisine_types__overlap=cuisine_list)
                )
        
        # Rating range
        min_rating = self.request.query_params.get('min_rating')
        max_rating = self.request.query_params.get('max_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        if max_rating:
            queryset = queryset.filter(rating__lte=max_rating)
        
        # Delivery time range
        max_delivery_time = self.request.query_params.get('max_delivery_time')
        if max_delivery_time:
            queryset = queryset.filter(delivery_time_minutes__lte=max_delivery_time)
        
        # Veg/Non-Veg filter
        veg_only = self.request.query_params.get('veg_only')
        if veg_only == 'true':
            # Filter restaurants that have vegetarian items
            veg_restaurant_ids = MenuItem.objects.filter(
                is_vegetarian=True,
                is_deleted=False,
                is_available=True
            ).values_list('category__menu__restaurant_id', flat=True).distinct()
            queryset = queryset.filter(id__in=veg_restaurant_ids)
        
        # Pure veg filter
        pure_veg = self.request.query_params.get('pure_veg')
        if pure_veg == 'true':
            queryset = queryset.filter(is_pure_veg=True)
        
        # Offers filter
        has_offers = self.request.query_params.get('has_offers')
        if has_offers == 'true':
            # Restaurants with active promotions
            restaurant_ids_with_offers = Promotion.objects.filter(
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now(),
                is_deleted=False
            ).values_list('restaurant_id', flat=True).distinct()
            queryset = queryset.filter(Q(id__in=restaurant_ids_with_offers) | Q(has_offers=True))
        
        # Cost for two range
        min_cost = self.request.query_params.get('min_cost')
        max_cost = self.request.query_params.get('max_cost')
        if min_cost:
            queryset = queryset.filter(cost_for_two__gte=min_cost)
        if max_cost:
            queryset = queryset.filter(cost_for_two__lte=max_cost)
        
        # Hygiene rating
        min_hygiene = self.request.query_params.get('min_hygiene')
        if min_hygiene:
            queryset = queryset.filter(hygiene_rating__gte=min_hygiene)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RestaurantListSerializer
        return RestaurantSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [AllowAny()]
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def menu(self, request, pk=None):
        """Get restaurant menu"""
        restaurant = self.get_object()
        menus = restaurant.menus.filter(is_active=True, is_deleted=False)
        serializer = MenuSerializer(menus, many=True)
        return Response(serializer.data)


class RestaurantSettingsViewSet(viewsets.ModelViewSet):
    """Manage restaurant operational settings"""

    serializer_class = RestaurantSettingsSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def get_queryset(self):
        qs = RestaurantSettings.objects.filter(is_deleted=False).select_related('restaurant', 'restaurant__owner')
        user = self.request.user
        if user.role == 'ADMIN':
            return qs
        return qs.filter(restaurant__owner=user)

    def perform_create(self, serializer):
        restaurant = self._get_restaurant_from_request()
        if RestaurantSettings.objects.filter(restaurant=restaurant, is_deleted=False).exists():
            raise ValidationError('Settings already exist for this restaurant.')
        serializer.save(restaurant=restaurant)

    def perform_update(self, serializer):
        restaurant = serializer.instance.restaurant
        if self.request.user.role != 'ADMIN' and restaurant.owner != self.request.user:
            raise ValidationError('You cannot modify settings for this restaurant.')
        serializer.save()

    def _get_restaurant_from_request(self):
        restaurant_id = self.request.data.get('restaurant')
        if not restaurant_id:
            raise ValidationError('restaurant field is required.')
        qs = Restaurant.objects.filter(id=restaurant_id, is_deleted=False)
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(owner=self.request.user)
        return get_object_or_404(qs, id=restaurant_id)


class RestaurantBranchViewSet(viewsets.ModelViewSet):
    """CRUD for restaurant branches"""

    serializer_class = RestaurantBranchSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def get_queryset(self):
        qs = RestaurantBranch.objects.filter(is_deleted=False).select_related('restaurant', 'restaurant__owner')
        user = self.request.user
        if user.role == 'ADMIN':
            return qs
        return qs.filter(restaurant__owner=user)

    def perform_create(self, serializer):
        restaurant = self._get_restaurant_from_request()
        serializer.save(restaurant=restaurant)
        if not restaurant.is_multi_branch:
            restaurant.is_multi_branch = True
            restaurant.save(update_fields=['is_multi_branch'])

    def perform_update(self, serializer):
        restaurant = serializer.instance.restaurant
        if self.request.user.role != 'ADMIN' and restaurant.owner != self.request.user:
            raise ValidationError('You cannot modify this branch.')
        serializer.save()

    def _get_restaurant_from_request(self):
        restaurant_id = self.request.data.get('restaurant')
        if not restaurant_id:
            raise ValidationError('restaurant field is required.')
        qs = Restaurant.objects.filter(id=restaurant_id, is_deleted=False)
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(owner=self.request.user)
        return get_object_or_404(qs, id=restaurant_id)


class ManagerProfileViewSet(viewsets.ModelViewSet):
    """Manage restaurant managers/staff"""

    serializer_class = ManagerProfileSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def get_queryset(self):
        qs = ManagerProfile.objects.filter(is_deleted=False).select_related('restaurant', 'restaurant__owner', 'user')
        user = self.request.user
        if user.role == 'ADMIN':
            return qs
        return qs.filter(restaurant__owner=user)

    def perform_create(self, serializer):
        restaurant = self._get_restaurant_from_request()
        if serializer.validated_data.get('is_primary'):
            ManagerProfile.objects.filter(restaurant=restaurant, is_primary=True).update(is_primary=False)
        serializer.save(restaurant=restaurant)

    def perform_update(self, serializer):
        restaurant = serializer.instance.restaurant
        if self.request.user.role != 'ADMIN' and restaurant.owner != self.request.user:
            raise ValidationError('You cannot modify this manager profile.')
        if self.request.data.get('is_primary'):
            ManagerProfile.objects.filter(restaurant=restaurant, is_primary=True).exclude(id=serializer.instance.id).update(is_primary=False)
        serializer.save()

    def _get_restaurant_from_request(self):
        restaurant_id = self.request.data.get('restaurant')
        if not restaurant_id:
            raise ValidationError('restaurant field is required.')
        qs = Restaurant.objects.filter(id=restaurant_id, is_deleted=False)
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(owner=self.request.user)
        return get_object_or_404(qs, id=restaurant_id)


class RestaurantDocumentViewSet(viewsets.ModelViewSet):
    """Upload and track KYC documents during onboarding"""

    serializer_class = RestaurantDocumentSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        qs = RestaurantDocument.objects.filter(is_deleted=False).select_related('restaurant', 'branch', 'restaurant__owner')
        user = self.request.user
        if user.role == 'ADMIN':
            return qs
        return qs.filter(restaurant__owner=user)

    def perform_create(self, serializer):
        restaurant = self._get_restaurant_from_request()
        branch = self._get_branch_from_request(optional=True)
        serializer.save(restaurant=restaurant, branch=branch)

    def perform_update(self, serializer):
        document = serializer.instance
        if self.request.user.role != 'ADMIN' and document.restaurant.owner != self.request.user:
            raise ValidationError('You cannot modify this document.')
        serializer.save()

    def _get_restaurant_from_request(self):
        restaurant_id = self.request.data.get('restaurant')
        if not restaurant_id:
            raise ValidationError('restaurant field is required.')
        qs = Restaurant.objects.filter(id=restaurant_id, is_deleted=False)
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(owner=self.request.user)
        return get_object_or_404(qs, id=restaurant_id)

    def _get_branch_from_request(self, optional=False):
        branch_id = self.request.data.get('branch')
        if not branch_id:
            if optional:
                return None
            raise ValidationError('branch field is required.')
        qs = RestaurantBranch.objects.filter(id=branch_id, is_deleted=False)
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(restaurant__owner=self.request.user)
        return get_object_or_404(qs, id=branch_id)

    @action(detail=True, methods=['post'])
    def resubmit(self, request, pk=None):
        document = self.get_object()
        if request.user.role != 'ADMIN' and document.restaurant.owner != request.user:
            raise ValidationError('You cannot resubmit this document.')
        document.status = RestaurantDocument.DocumentStatus.PENDING
        document.needs_reupload = False
        document.rejection_reason = ''
        document.submitted_at = timezone.now()
        document.save(update_fields=['status', 'needs_reupload', 'rejection_reason', 'submitted_at'])
        return Response(self.get_serializer(document).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def review(self, request, pk=None):
        document = self.get_object()
        if request.user.role != 'ADMIN':
            raise ValidationError('Only admins can review documents.')
        new_status = request.data.get('status')
        if new_status not in dict(RestaurantDocument.DocumentStatus.choices):
            raise ValidationError('Invalid status.')
        previous_status = document.status
        document.status = new_status
        document.reviewed_at = timezone.now()
        document.rejection_reason = request.data.get('rejection_reason', '')
        document.needs_reupload = document.status == RestaurantDocument.DocumentStatus.REJECTED
        document.save(update_fields=['status', 'reviewed_at', 'rejection_reason', 'needs_reupload'])
        DocumentReviewLog.objects.create(
            document=document,
            reviewer=request.user,
            status_before=previous_status,
            status_after=document.status,
            notes=request.data.get('notes', ''),
        )
        return Response(self.get_serializer(document).data)


class RestaurantAlertViewSet(viewsets.ModelViewSet):
    """Surface actionable alerts to restaurant dashboard"""

    serializer_class = RestaurantAlertSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        qs = RestaurantAlert.objects.filter(is_deleted=False).select_related('restaurant', 'order')
        user = self.request.user
        if user.role == 'ADMIN':
            return qs
        return qs.filter(restaurant__owner=user)

    def perform_create(self, serializer):
        restaurant = self._get_restaurant_from_request()
        serializer.save(restaurant=restaurant)

    def _get_restaurant_from_request(self):
        restaurant_id = self.request.data.get('restaurant')
        if not restaurant_id:
            raise ValidationError('restaurant field is required.')
        qs = Restaurant.objects.filter(id=restaurant_id, is_deleted=False)
        if self.request.user.role != 'ADMIN':
            qs = qs.filter(owner=self.request.user)
        return get_object_or_404(qs, id=restaurant_id)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        alert = self.get_object()
        if alert.is_read:
            return Response(self.get_serializer(alert).data)
        alert.is_read = True
        alert.read_at = timezone.now()
        alert.save(update_fields=['is_read', 'read_at'])
        return Response(self.get_serializer(alert).data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        alert = self.get_object()
        alert.resolved_at = timezone.now()
        alert.is_read = True
        alert.read_at = alert.read_at or timezone.now()
        alert.save(update_fields=['resolved_at', 'is_read', 'read_at'])
        return Response(self.get_serializer(alert).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        queryset = self.get_queryset().filter(is_read=False)
        updated = queryset.update(is_read=True, read_at=timezone.now())
        return Response({'updated': updated})


class RestaurantDashboardView(APIView):
    """Aggregate KPIs for the restaurant dashboard"""

    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def get(self, request):
        restaurant = self._get_restaurant(request)
        payload = self._build_metrics(restaurant)
        return Response(payload)

    def _build_metrics(self, restaurant):
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        orders = Order.objects.filter(restaurant=restaurant, is_deleted=False)
        orders_today = orders.filter(created_at__date=today)

        sales_today = orders_today.filter(status=Order.Status.DELIVERED).aggregate(total=Sum('total_amount'))['total'] or 0
        avg_order_value = orders_today.aggregate(avg=Avg('total_amount'))['avg'] or 0
        ongoing = orders.filter(status__in=[
            Order.Status.ACCEPTED,
            Order.Status.PREPARING,
            Order.Status.READY,
            Order.Status.ASSIGNED,
            Order.Status.PICKED_UP,
            Order.Status.OUT_FOR_DELIVERY,
        ]).count()

        ratings = Review.objects.filter(restaurant=restaurant).aggregate(
            avg=Avg('restaurant_rating'),
            total=Count('id'),
        )

        low_stock = InventoryItem.objects.filter(
            restaurant=restaurant,
            is_deleted=False,
            current_stock__lte=F('low_stock_threshold'),
        ).count()

        payments = Payment.objects.filter(
            order__restaurant=restaurant,
            status=Payment.Status.COMPLETED,
        )
        payouts_week = payments.filter(processed_at__gte=week_ago).aggregate(total=Sum('amount'))['total'] or 0

        settings = getattr(restaurant, 'settings', None)
        return {
            'restaurant': {
                'id': restaurant.id,
                'name': restaurant.name,
                'city': restaurant.city,
                'is_online': settings.is_online if settings else False,
                'sla_threshold': settings.sla_threshold_minutes if settings else restaurant.delivery_time_minutes,
            },
            'orders': {
                'today': orders_today.count(),
                'ongoing': ongoing,
                'cancelled_today': orders_today.filter(status=Order.Status.CANCELLED).count(),
                'latest': OrderSerializer(
                    orders.order_by('-created_at')[:5],
                    many=True,
                    context={'request': self.request, 'include_internal': True},
                ).data,
            },
            'sales': {
                'sales_today': float(sales_today),
                'avg_order_value': float(avg_order_value),
                'payout_last_7_days': float(payouts_week),
            },
            'ratings': {
                'current_rating': float(ratings['avg'] or restaurant.rating or 0),
                'total_reviews': ratings['total'] or restaurant.total_ratings,
            },
            'inventory': {
                'low_stock_items': low_stock,
            },
            'alerts': {
                'unread': restaurant.alerts.filter(is_deleted=False, is_read=False).count(),
                'latest': RestaurantAlertSerializer(
                    restaurant.alerts.filter(is_deleted=False).order_by('-created_at')[:5],
                    many=True,
                ).data,
            },
        }

    def _get_restaurant(self, request):
        restaurant_id = request.query_params.get('restaurant_id')
        qs = Restaurant.objects.filter(is_deleted=False).select_related('settings')
        if request.user.role != 'ADMIN':
            qs = qs.filter(owner=request.user)
        
        if restaurant_id:
            # Convert restaurant_id to integer with proper error handling
            try:
                restaurant_id = int(restaurant_id)
            except (ValueError, TypeError):
                # Invalid restaurant_id format, fall back to first restaurant
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Invalid restaurant_id format received: {restaurant_id}. Falling back to first restaurant.')
                restaurant = qs.first()
                if not restaurant:
                    raise ValidationError({
                        'error': 'No restaurants linked to this account.',
                        'details': {'detail': 'Please complete restaurant onboarding first.'}
                    })
                return restaurant
            
            # Check if restaurant exists in the filtered queryset (i.e., belongs to user)
            try:
                restaurant = qs.get(id=restaurant_id)
                return restaurant
            except Restaurant.DoesNotExist:
                # Restaurant doesn't exist or doesn't belong to user
                # Silently fall back to user's first restaurant instead of throwing error
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Restaurant {restaurant_id} not found or not owned by user {request.user.id}. Falling back to first restaurant.')
                restaurant = qs.first()
                if not restaurant:
                    raise ValidationError({
                        'error': 'No restaurants linked to this account.',
                        'details': {'detail': 'Please complete restaurant onboarding first.'}
                    })
                return restaurant
        
        # If no restaurant_id provided, get the first restaurant
        restaurant = qs.first()
        if not restaurant:
            raise ValidationError({
                'error': 'No restaurants linked to this account.',
                'details': {'detail': 'Please complete restaurant onboarding first.'}
            })
        return restaurant


class RestaurantOnlineStatusView(APIView):
    """Toggle online/offline state from dashboard"""

    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def post(self, request):
        restaurant = self._get_restaurant(request)
        desired_state = request.data.get('is_online')
        if desired_state is None:
            raise ValidationError({'is_online': 'Provide a boolean value.'})
        desired_state = bool(desired_state)
        settings, _ = RestaurantSettings.objects.get_or_create(restaurant=restaurant)
        settings.is_online = desired_state
        settings.save(update_fields=['is_online'])
        self._broadcast_status(restaurant, settings.is_online)
        return Response({'is_online': settings.is_online})

    def _get_restaurant(self, request):
        restaurant_id = request.data.get('restaurant_id') or request.query_params.get('restaurant_id')
        qs = Restaurant.objects.filter(is_deleted=False).select_related('settings')
        if request.user.role != 'ADMIN':
            qs = qs.filter(owner=request.user)
        if restaurant_id:
            try:
                restaurant_id = int(restaurant_id)
            except (ValueError, TypeError):
                # Invalid restaurant_id format, fall back to first restaurant
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Invalid restaurant_id format received: {restaurant_id}. Falling back to first restaurant.')
                restaurant = qs.first()
                if not restaurant:
                    raise ValidationError('No restaurants linked to this account.')
                return restaurant
            try:
                return qs.get(id=restaurant_id)
            except Restaurant.DoesNotExist:
                # Restaurant doesn't exist or doesn't belong to user, fall back to first restaurant
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Restaurant {restaurant_id} not found or not owned by user {request.user.id}. Falling back to first restaurant.')
                restaurant = qs.first()
                if not restaurant:
                    raise ValidationError('No restaurants linked to this account.')
                return restaurant
        restaurant = qs.first()
        if not restaurant:
            raise ValidationError('No restaurants linked to this account.')
        return restaurant
    
    def _broadcast_status(self, restaurant, is_online):
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        payload = {
            'restaurant_id': restaurant.id,
            'is_online': is_online,
            'updated_at': timezone.now().isoformat(),
        }
        async_to_sync(channel_layer.group_send)(
            f'restaurant_{restaurant.id}',
            {
                'type': 'restaurant_status',
                'data': payload,
            }
        )


class RestaurantOnboardingViewSet(viewsets.ViewSet):
    """Wizard-like onboarding API for restaurants"""

    permission_classes = [IsAuthenticated, IsRestaurantOwner]

    def list(self, request):
        restaurant = self._get_restaurant(request)
        payload = self._serialize_onboarding(request, restaurant)
        payload['progress'] = self._calculate_progress(restaurant)
        return Response(payload)

    def create(self, request):
        serializer = RestaurantSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        restaurant = serializer.save(status=Restaurant.Status.PENDING, onboarding_status=Restaurant.OnboardingStatus.IN_PROGRESS)
        RestaurantSettings.objects.get_or_create(restaurant=restaurant)
        payload = self._serialize_onboarding(request, restaurant)
        payload['progress'] = self._calculate_progress(restaurant)
        return Response(payload, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def basic_profile(self, request):
        restaurant = self._get_restaurant(request)
        serializer = RestaurantSerializer(
            restaurant,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(onboarding_status=Restaurant.OnboardingStatus.IN_PROGRESS)
        payload = self._serialize_onboarding(request, restaurant)
        payload['progress'] = self._calculate_progress(restaurant)
        return Response(payload)

    @action(detail=False, methods=['post'])
    def location(self, request):
        restaurant = self._get_restaurant(request)
        fields = ['address', 'city', 'state', 'postal_code', 'country', 'latitude', 'longitude', 'delivery_radius_km', 'billing_address', 'billing_city', 'billing_state', 'billing_postal_code', 'billing_country']
        data = {field: request.data.get(field) for field in fields if field in request.data}
        serializer = RestaurantSerializer(restaurant, data=data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(onboarding_status=Restaurant.OnboardingStatus.IN_PROGRESS)
        payload = self._serialize_onboarding(request, restaurant)
        payload['progress'] = self._calculate_progress(restaurant)
        return Response(payload)

    @action(detail=False, methods=['post'])
    def operations(self, request):
        """Update prep time / SLA / delivery radius settings during onboarding"""
        restaurant = self._get_restaurant(request)
        settings, _ = RestaurantSettings.objects.get_or_create(restaurant=restaurant)
        serializer = RestaurantSettingsUpdateSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        payload = self._serialize_onboarding(request, restaurant)
        payload['progress'] = self._calculate_progress(restaurant)
        return Response(payload)

    @action(detail=False, methods=['post'])
    def submit(self, request):
        restaurant = self._get_restaurant(request)
        restaurant.onboarding_status = Restaurant.OnboardingStatus.SUBMITTED
        restaurant.status = Restaurant.Status.PENDING
        restaurant.save(update_fields=['onboarding_status', 'status'])
        payload = self._serialize_onboarding(request, restaurant)
        payload['progress'] = self._calculate_progress(restaurant)
        return Response(payload)

    def _get_restaurant(self, request):
        restaurant_id = request.data.get('restaurant_id') or request.query_params.get('restaurant_id')
        qs = Restaurant.objects.filter(owner=request.user, is_deleted=False)
        if restaurant_id:
            return get_object_or_404(qs, id=restaurant_id)
        restaurant = qs.first()
        if not restaurant:
            raise ValidationError('No restaurant found. Please create one first.')
        return restaurant

    def _serialize_onboarding(self, request, restaurant):
        settings = getattr(restaurant, 'settings', None)
        return {
            'restaurant': RestaurantSerializer(restaurant, context={'request': request}).data,
            'settings': RestaurantSettingsSerializer(settings).data if settings else None,
            'branches': RestaurantBranchSerializer(restaurant.branches.filter(is_deleted=False), many=True).data,
            'managers': ManagerProfileSerializer(restaurant.managers.filter(is_deleted=False), many=True).data,
            'documents': RestaurantDocumentSerializer(restaurant.documents.filter(is_deleted=False), many=True).data,
        }

    def _calculate_progress(self, restaurant):
        steps = {
            'profile': bool(restaurant.name and restaurant.phone and restaurant.cuisine_type),
            'location': bool(restaurant.address and restaurant.city and restaurant.delivery_radius_km),
            'documents': restaurant.documents.filter(status=RestaurantDocument.DocumentStatus.APPROVED).exists(),
            'managers': restaurant.managers.filter(is_deleted=False).exists(),
        }
        completed = len([s for s in steps.values() if s])
        percentage = int((completed / len(steps)) * 100) if steps else 0
        return {'steps': steps, 'percentage': percentage}
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def menu_search(self, request, pk=None):
        """Search within restaurant menu"""
        restaurant = self.get_object()
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({'items': []})
        
        # Search in menu items
        items = MenuItem.objects.filter(
            category__menu__restaurant=restaurant,
            category__menu__is_active=True,
            category__menu__is_deleted=False,
            is_deleted=False,
        ).filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:20]
        
        serializer = MenuItemSerializer(items, many=True)
        return Response({'items': serializer.data})
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def bestsellers(self, request, pk=None):
        """Get bestseller items"""
        restaurant = self.get_object()
        
        # Get items ordered by rating and total_ratings
        items = MenuItem.objects.filter(
            category__menu__restaurant=restaurant,
            category__menu__is_active=True,
            category__menu__is_deleted=False,
            is_deleted=False,
            is_available=True,
        ).order_by('-rating', '-total_ratings')[:10]
        
        serializer = MenuItemSerializer(items, many=True)
        return Response({'items': serializer.data})
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def recommendations(self, request, pk=None):
        """Get recommended items (basic implementation - can be enhanced with ML)"""
        restaurant = self.get_object()
        
        # Basic recommendation: featured items + high-rated items
        featured = MenuItem.objects.filter(
            category__menu__restaurant=restaurant,
            category__menu__is_active=True,
            category__menu__is_deleted=False,
            is_deleted=False,
            is_available=True,
            is_featured=True,
        )[:5]
        
        high_rated = MenuItem.objects.filter(
            category__menu__restaurant=restaurant,
            category__menu__is_active=True,
            category__menu__is_deleted=False,
            is_deleted=False,
            is_available=True,
            rating__gte=4.0,
        ).exclude(id__in=[f.id for f in featured]).order_by('-rating')[:5]
        
        items = list(featured) + list(high_rated)
        serializer = MenuItemSerializer(items, many=True)
        return Response({'items': serializer.data})
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def nearby(self, request):
        """Get nearby restaurants (mock - in production, use PostGIS)"""
        lat = request.query_params.get('latitude')
        lon = request.query_params.get('longitude')
        radius = request.query_params.get('radius', 10)  # km
        
        if not lat or not lon:
            return Response({'error': 'latitude and longitude required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Simple distance calculation (Haversine would be better)
        restaurants = self.queryset.all()
        # In production, use PostGIS ST_DWithin for efficient geo queries
        serializer = RestaurantListSerializer(restaurants[:20], many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def serviceability(self, request, pk=None):
        """Check if restaurant can deliver to a location"""
        restaurant = self.get_object()
        lat = request.query_params.get('latitude')
        lon = request.query_params.get('longitude')
        
        if not lat or not lon:
            return Response({'error': 'latitude and longitude required'}, status=status.HTTP_400_BAD_REQUEST)
        
        from math import radians, cos, sin, asin, sqrt
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return Response({'error': 'Invalid coordinates'}, status=status.HTTP_400_BAD_REQUEST)

        # Haversine calculation (approx)
        def haversine(lat1, lon1, lat2, lon2):
            r = 6371  # km
            d_lat = radians(lat2 - lat1)
            d_lon = radians(lon2 - lon1)
            a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
            c = 2 * asin(sqrt(a))
            return r * c

        customer_distance = haversine(float(restaurant.latitude), float(restaurant.longitude), lat, lon)
        delivery_radius = float(restaurant.delivery_radius_km or 5)
        can_deliver = customer_distance <= delivery_radius
        estimated_time = restaurant.delivery_time_minutes + (5 if not can_deliver else 0)
        
        return Response({
            'can_deliver': can_deliver,
            'estimated_delivery_time': estimated_time,
            'delivery_fee': float(restaurant.delivery_fee),
            'distance_km': round(customer_distance, 2),
            'max_radius_km': delivery_radius,
        })


class MenuViewSet(viewsets.ModelViewSet):
    """Menu viewset"""
    serializer_class = MenuSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Menu.objects.filter(is_deleted=False)
        return Menu.objects.filter(restaurant__owner=user, is_deleted=False)


class MenuCategoryViewSet(viewsets.ModelViewSet):
    """Menu category viewset"""
    serializer_class = MenuCategorySerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    
    def get_queryset(self):
        menu_id = self.request.query_params.get('menu')
        if menu_id:
            return MenuCategory.objects.filter(menu_id=menu_id, is_deleted=False)
        return MenuCategory.objects.filter(is_deleted=False)


class MenuItemViewSet(viewsets.ModelViewSet):
    """Menu item viewset"""
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_available', 'is_vegetarian', 'is_vegan']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        category_id = self.request.query_params.get('category')
        if category_id:
            return MenuItem.objects.filter(category_id=category_id, is_deleted=False)
        return MenuItem.objects.filter(is_deleted=False)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsRestaurantOwner()]
        return [AllowAny()]
    
    @transaction.atomic
    def perform_create(self, serializer):
        menu_item = serializer.save()
        self._broadcast_menu_updated(menu_item)
    
    @transaction.atomic
    def perform_update(self, serializer):
        menu_item = serializer.save()
        self._broadcast_menu_updated(menu_item)
    
    def _broadcast_menu_updated(self, menu_item):
        """Broadcast menu.updated event"""
        from apps.events.broadcast import EventBroadcastService
        from apps.restaurants.serializers import MenuItemSerializer
        
        menu_data = MenuItemSerializer(menu_item, context={'request': self.request}).data
        restaurant = menu_item.restaurant
        
        # Broadcast to restaurant channel
        EventBroadcastService.broadcast_to_restaurant(
            restaurant_id=restaurant.id,
            event_type='menu.updated',
            aggregate_type='MenuItem',
            aggregate_id=str(menu_item.id),
            payload=menu_data,
        )
        
        # Broadcast to subscribed customers (in production, maintain customer subscriptions)
        # For now, broadcast to all customers (would be optimized in production)
        # EventBroadcastService.broadcast_to_customer() would be called for subscribed customers


class ItemModifierViewSet(viewsets.ModelViewSet):
    """Item modifier viewset"""
    serializer_class = ItemModifierSerializer
    permission_classes = [IsAuthenticated, IsRestaurantOwner]
    
    def get_queryset(self):
        item_id = self.request.query_params.get('item')
        if item_id:
            return ItemModifier.objects.filter(menu_item_id=item_id, is_deleted=False)
        return ItemModifier.objects.filter(is_deleted=False)


class PromotionViewSet(viewsets.ModelViewSet):
    """Promotion viewset"""
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        restaurant_id = self.request.query_params.get('restaurant')
        
        if user.role == 'ADMIN':
            return Promotion.objects.filter(is_deleted=False)
        elif user.role == 'RESTAURANT':
            return Promotion.objects.filter(restaurant__owner=user, is_deleted=False)
        else:
            # Customers see active promotions
            return Promotion.objects.filter(is_active=True, is_deleted=False)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def validate(self, request):
        """Validate promotion code"""
        code = request.data.get('code', '').strip()
        restaurant_id = request.data.get('restaurant_id')
        order_amount = request.data.get('order_amount', 0)
        
        if not code:
            return Response({'valid': False, 'message': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            promotion = Promotion.objects.get(code=code, is_active=True, is_deleted=False)
            
            # Check validity
            from django.utils import timezone
            if promotion.valid_from > timezone.now() or promotion.valid_until < timezone.now():
                return Response({'valid': False, 'message': 'Promotion expired'})
            
            # Check restaurant applicability
            if promotion.restaurant and restaurant_id and promotion.restaurant.id != restaurant_id:
                return Response({'valid': False, 'message': 'This offer is not applicable for this restaurant'})
            
            # Check minimum order amount
            if order_amount < promotion.minimum_order_amount:
                return Response({
                    'valid': False,
                    'message': f'Minimum order amount of {promotion.minimum_order_amount} required'
                })
            
            # Check usage limits
            if promotion.max_uses and promotion.uses_count >= promotion.max_uses:
                return Response({'valid': False, 'message': 'This offer has reached maximum uses'})
            
            # Check user usage limit
            if request.user.is_authenticated:
                from apps.orders.models import Order
                user_uses = Order.objects.filter(
                    customer=request.user,
                    promotion=promotion,
                    is_deleted=False
                ).count()
                if user_uses >= promotion.max_uses_per_user:
                    return Response({'valid': False, 'message': 'You have already used this offer'})
            
            return Response({
                'valid': True,
                'promotion': PromotionSerializer(promotion, context={'request': request}).data
            })
        except Promotion.DoesNotExist:
            return Response({'valid': False, 'message': 'Invalid code'})
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def available(self, request):
        """Get available offers for user"""
        restaurant_id = request.query_params.get('restaurant_id')
        order_amount = float(request.query_params.get('order_amount', 0))
        payment_method = request.query_params.get('payment_method', '')
        
        from django.utils import timezone
        now = timezone.now()
        
        # Base query for active promotions
        queryset = Promotion.objects.filter(
            is_active=True,
            is_deleted=False,
            valid_from__lte=now,
            valid_until__gte=now,
        )
        
        # Filter by restaurant if provided
        if restaurant_id:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(restaurant_id=restaurant_id) | Q(restaurant__isnull=True)
            )
        else:
            # Platform offers only
            queryset = queryset.filter(restaurant__isnull=True)
        
        # Filter by minimum order amount
        queryset = queryset.filter(minimum_order_amount__lte=order_amount)
        
        # Filter by payment method for bank/UPI offers
        if payment_method:
            if payment_method in ['CARD', 'NET_BANKING']:
                # Show bank offers
                bank_offers = queryset.filter(offer_type=Promotion.OfferType.BANK)
                if payment_method == 'NET_BANKING':
                    # Filter by applicable banks (mock - in production, get from payment gateway)
                    pass
            elif payment_method == 'UPI':
                # Show UPI offers
                queryset = queryset.filter(offer_type=Promotion.OfferType.UPI)
        
        # Order by priority
        queryset = queryset.order_by('-priority', '-created_at')
        
        serializer = PromotionSerializer(queryset[:20], many=True, context={'request': request})
        return Response({'offers': serializer.data})


@api_view(['POST'])
@permission_classes([AllowAny])
def detect_location(request):
    """Detect location from coordinates (reverse geocoding)"""
    lat = request.data.get('latitude')
    lon = request.data.get('longitude')
    
    if not lat or not lon:
        return Response({'error': 'latitude and longitude required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # In production, use a geocoding service (Google Maps, OpenStreetMap, etc.)
    # For now, return mock data
    return Response({
        'address': '123 Main Street',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'postal_code': '400001',
        'country': 'India',
        'latitude': float(lat),
        'longitude': float(lon),
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions(request):
    """Get search suggestions based on query"""
    query = request.query_params.get('q', '').strip()
    
    if not query or len(query) < 2:
        return Response({'suggestions': []})
    
    suggestions = []
    
    # Restaurant name suggestions
    restaurants = Restaurant.objects.filter(
        name__icontains=query,
        is_deleted=False,
        status=Restaurant.Status.ACTIVE
    )[:5]
    suggestions.extend([{'type': 'restaurant', 'text': r.name, 'id': r.id} for r in restaurants])
    
    # Dish name suggestions
    dishes = MenuItem.objects.filter(
        name__icontains=query,
        is_deleted=False,
        is_available=True
    )[:5]
    suggestions.extend([{'type': 'dish', 'text': d.name, 'id': d.id, 'restaurant': d.restaurant.name} for d in dishes])
    
    # Cuisine suggestions
    cuisines = Restaurant.CuisineType.choices
    matching_cuisines = [c[1] for c in cuisines if query.lower() in c[1].lower()][:3]
    suggestions.extend([{'type': 'cuisine', 'text': c} for c in matching_cuisines])
    
    return Response({'suggestions': suggestions[:10]})


@api_view(['GET'])
@permission_classes([AllowAny])
def popular_searches(request):
    """Get popular searches"""
    # Get top 10 popular searches
    popular = PopularSearch.objects.all()[:10]
    return Response({
        'searches': [{'query': p.query, 'count': p.search_count} for p in popular]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_searches(request):
    """Get user's recent searches"""
    user = request.user
    recent = SearchHistory.objects.filter(user=user).order_by('-created_at')[:10]
    return Response({
        'searches': [{'query': s.query, 'type': s.search_type, 'created_at': s.created_at} for s in recent]
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def save_search(request):
    """Save a search query"""
    query = request.data.get('query', '').strip()
    search_type = request.data.get('type', 'general')
    
    if not query:
        return Response({'error': 'query is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Save to user's search history if authenticated
    user = request.user if request.user.is_authenticated else None
    if user:
        SearchHistory.objects.create(user=user, query=query, search_type=search_type)
    
    # Update popular searches
    popular, created = PopularSearch.objects.get_or_create(query=query)
    if not created:
        popular.search_count += 1
        popular.last_searched = timezone.now()
        popular.save()
    
    return Response({'message': 'Search saved'})


@api_view(['GET'])
@permission_classes([AllowAny])
def advanced_search(request):
    """Advanced search with dish name, ingredient, semantic search"""
    query = request.query_params.get('q', '').strip()
    search_type = request.query_params.get('type', 'all')  # all, restaurant, dish, ingredient
    
    if not query:
        return Response({'error': 'query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    results = {
        'restaurants': [],
        'dishes': [],
        'ingredients': [],
    }
    
    # Search restaurants
    if search_type in ['all', 'restaurant']:
        restaurants = Restaurant.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(cuisine_type__icontains=query),
            is_deleted=False,
            status=Restaurant.Status.ACTIVE
        )[:20]
        results['restaurants'] = RestaurantListSerializer(restaurants, many=True).data
    
    # Search dishes
    if search_type in ['all', 'dish']:
        dishes = MenuItem.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query),
            is_deleted=False,
            is_available=True
        ).select_related('category__menu__restaurant')[:20]
        results['dishes'] = MenuItemSerializer(dishes, many=True).data
    
    # Search ingredients (in description - basic implementation)
    if search_type in ['all', 'ingredient']:
        # In production, use proper ingredient extraction/NLP
        ingredient_dishes = MenuItem.objects.filter(
            description__icontains=query,
            is_deleted=False,
            is_available=True
        ).select_related('category__menu__restaurant')[:10]
        results['ingredients'] = MenuItemSerializer(ingredient_dishes, many=True).data
    
    # Save search
    save_search(request._request if hasattr(request, '_request') else request)
    
    return Response(results)


@api_view(['GET'])
@permission_classes([AllowAny])
def trending_dishes(request):
    """Get trending dishes based on order frequency and ratings"""
    limit = int(request.query_params.get('limit', 20))
    
    from django.db.models import Count, Q
    from datetime import timedelta
    from django.utils import timezone
    
    # Get dishes ordered in last 30 days, ordered by order count and rating
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    from apps.orders.models import OrderItem
    
    trending = MenuItem.objects.filter(
        is_deleted=False,
        is_available=True,
        order_items__order__created_at__gte=thirty_days_ago,
        order_items__order__is_deleted=False
    ).annotate(
        order_count=Count('order_items', filter=Q(order_items__order__created_at__gte=thirty_days_ago))
    ).filter(
        order_count__gt=0
    ).order_by('-order_count', '-rating')[:limit]
    
    serializer = MenuItemSerializer(trending, many=True, context={'request': request})
    return Response({'dishes': serializer.data})

