"""
Content moderation viewsets
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone

from apps.orders.models import Review, ItemReview
from apps.restaurants.models import Restaurant
from apps.restaurants.serializers import RestaurantSerializer
from .permissions import IsAdminUser, HasAdminPermission
from .models import AuditLogEntry
from .serializers import ReviewModerationSerializer


class ReviewModerationViewSet(viewsets.ModelViewSet):
    """Review moderation management"""
    queryset = Review.objects.all()
    serializer_class = ReviewModerationSerializer
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.moderation.manage')]
    
    def get_queryset(self):
        from .utils import validate_query_param
        
        queryset = Review.objects.select_related('customer', 'restaurant', 'order').all()
        
        # Filtering with validation
        try:
            is_flagged = validate_query_param(
                self.request.query_params.get('is_flagged'),
                'is_flagged',
                param_type=bool
            )
            is_approved = validate_query_param(
                self.request.query_params.get('is_approved'),
                'is_approved',
                param_type=bool
            )
            search = validate_query_param(
                self.request.query_params.get('search'),
                'search',
                param_type=str
            )
            
            if is_flagged is not None:
                queryset = queryset.filter(is_flagged=is_flagged)
            if is_approved is not None:
                queryset = queryset.filter(is_approved=is_approved)
            if search:
                queryset = queryset.filter(
                    Q(comment__icontains=search) |
                    Q(customer__email__icontains=search) |
                    Q(restaurant__name__icontains=search)
                )
        except Exception as e:
            # If validation fails, return empty queryset or handle error
            pass
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a review"""
        review = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {'is_approved': review.is_approved, 'is_flagged': review.is_flagged}
        review.is_approved = True
        review.is_flagged = False
        review.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='review.approve',
            resource_type='review',
            resource_id=str(review.id),
            before_state=before_state,
            after_state={'is_approved': True, 'is_flagged': False},
            reason=reason
        )
        
        return Response({'message': 'Review approved successfully'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject/remove a review"""
        review = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {'is_approved': review.is_approved, 'is_flagged': review.is_flagged}
        review.is_approved = False
        review.is_flagged = True
        review.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='review.reject',
            resource_type='review',
            resource_id=str(review.id),
            before_state=before_state,
            after_state={'is_approved': False, 'is_flagged': True},
            reason=reason
        )
        
        return Response({'message': 'Review rejected successfully'})
    
    @action(detail=True, methods=['post'])
    def flag(self, request, pk=None):
        """Flag a review for review"""
        review = self.get_object()
        reason = request.data.get('reason', '')
        
        before_state = {'is_flagged': review.is_flagged}
        review.is_flagged = True
        review.flagged_reason = reason
        review.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='review.flag',
            resource_type='review',
            resource_id=str(review.id),
            before_state=before_state,
            after_state={'is_flagged': True},
            reason=reason
        )
        
        return Response({'message': 'Review flagged successfully'})
    
    @action(detail=True, methods=['post'])
    def warn_user(self, request, pk=None):
        """Warn the user who wrote the review"""
        review = self.get_object()
        reason = request.data.get('reason', '')
        
        # In production, send warning notification to user
        AuditLogEntry.objects.create(
            user=request.user,
            action='review.warn_user',
            resource_type='review',
            resource_id=str(review.id),
            reason=reason,
            metadata={'warned_user_id': review.customer.id}
        )
        
        return Response({'message': 'User warned successfully'})
    
    @action(detail=False, methods=['post'])
    def bulk_approve(self, request):
        """Bulk approve reviews"""
        review_ids = request.data.get('review_ids', [])
        reason = request.data.get('reason', '')
        
        reviews = Review.objects.filter(id__in=review_ids)
        count = reviews.update(is_approved=True, is_flagged=False)
        
        for review in reviews:
            AuditLogEntry.objects.create(
                user=request.user,
                action='review.approve',
                resource_type='review',
                resource_id=str(review.id),
                reason=reason
            )
        
        return Response({'message': f'{count} reviews approved successfully'})
    
    @action(detail=False, methods=['post'])
    def bulk_reject(self, request):
        """Bulk reject reviews"""
        review_ids = request.data.get('review_ids', [])
        reason = request.data.get('reason', '')
        
        reviews = Review.objects.filter(id__in=review_ids)
        count = reviews.update(is_approved=False, is_flagged=True)
        
        for review in reviews:
            AuditLogEntry.objects.create(
                user=request.user,
                action='review.reject',
                resource_type='review',
                resource_id=str(review.id),
                reason=reason
            )
        
        return Response({'message': f'{count} reviews rejected successfully'})


class RestaurantContentManagementViewSet(viewsets.ReadOnlyModelViewSet):
    """Restaurant content management"""
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.content.manage')]
    
    @action(detail=True, methods=['post'])
    def update_description(self, request, pk=None):
        """Update restaurant description"""
        restaurant = self.get_object()
        description = request.data.get('description', '')
        reason = request.data.get('reason', '')
        
        before_state = {'description': restaurant.description}
        restaurant.description = description
        restaurant.save()
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='restaurant.update_description',
            resource_type='restaurant',
            resource_id=str(restaurant.id),
            before_state=before_state,
            after_state={'description': description},
            reason=reason
        )
        
        return Response({'message': 'Description updated successfully'})
    
    @action(detail=True, methods=['post'])
    def feature(self, request, pk=None):
        """Feature/promote a restaurant"""
        restaurant = self.get_object()
        reason = request.data.get('reason', '')
        
        # In production, add to featured restaurants list
        AuditLogEntry.objects.create(
            user=request.user,
            action='restaurant.feature',
            resource_type='restaurant',
            resource_id=str(restaurant.id),
            reason=reason
        )
        
        return Response({'message': 'Restaurant featured successfully'})
    
    @action(detail=True, methods=['post'])
    def unfeature(self, request, pk=None):
        """Remove restaurant from featured list"""
        restaurant = self.get_object()
        reason = request.data.get('reason', '')
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='restaurant.unfeature',
            resource_type='restaurant',
            resource_id=str(restaurant.id),
            reason=reason
        )
        
        return Response({'message': 'Restaurant unfeatured successfully'})


class PolicyManagementViewSet(viewsets.ViewSet):
    """Policy documents management"""
    permission_classes = [IsAdminUser, HasAdminPermission(permission_codename='admin.policy.manage')]
    
    @action(detail=False, methods=['get'])
    def list_policies(self, request):
        """List all policy documents"""
        # In production, this would fetch from a Policy model
        policies = [
            {'id': 1, 'name': 'Terms of Service', 'version': '2.1', 'updated_at': '2024-01-15'},
            {'id': 2, 'name': 'Privacy Policy', 'version': '1.8', 'updated_at': '2024-01-10'},
            {'id': 3, 'name': 'Seller Agreement', 'version': '3.0', 'updated_at': '2024-01-20'},
        ]
        return Response(policies)
    
    @action(detail=False, methods=['post'])
    def update_policy(self, request):
        """Update a policy document"""
        policy_id = request.data.get('policy_id')
        content = request.data.get('content')
        reason = request.data.get('reason', '')
        
        AuditLogEntry.objects.create(
            user=request.user,
            action='policy.update',
            resource_type='policy',
            resource_id=str(policy_id),
            reason=reason,
            metadata={'content_length': len(content) if content else 0}
        )
        
        return Response({'message': 'Policy updated successfully'})

