"""
Views for subscriptions app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import timedelta
from .models import MembershipPlan, Subscription
from .serializers import MembershipPlanSerializer, SubscriptionSerializer


class MembershipPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """Membership plan viewset (read-only for customers)"""
    serializer_class = MembershipPlanSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return MembershipPlan.objects.filter(is_active=True, is_deleted=False)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class SubscriptionViewSet(viewsets.ModelViewSet):
    """Subscription viewset"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user, is_deleted=False)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def current(self, request):
        """Get current active subscription"""
        subscription = Subscription.objects.filter(
            user=request.user,
            status=Subscription.Status.ACTIVE,
            is_deleted=False
        ).first()
        
        if subscription and subscription.is_active():
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        return Response({'message': 'No active subscription'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def subscribe(self, request):
        """Subscribe to a plan"""
        plan_id = request.data.get('plan_id')
        payment_transaction_id = request.data.get('payment_transaction_id', '')
        
        if not plan_id:
            return Response({'error': 'plan_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plan = MembershipPlan.objects.get(id=plan_id, is_active=True, is_deleted=False)
        except MembershipPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Cancel existing active subscriptions
        Subscription.objects.filter(
            user=request.user,
            status=Subscription.Status.ACTIVE
        ).update(
            status=Subscription.Status.CANCELLED,
            cancelled_at=timezone.now()
        )
        
        # Calculate end date
        start_date = timezone.now()
        end_date = None
        if plan.duration_days:
            end_date = start_date + timedelta(days=plan.duration_days)
        elif plan.plan_type == MembershipPlan.PlanType.MONTHLY:
            end_date = start_date + timedelta(days=30)
        elif plan.plan_type == MembershipPlan.PlanType.YEARLY:
            end_date = start_date + timedelta(days=365)
        # LIFETIME has no end_date
        
        # Create subscription
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            start_date=start_date,
            end_date=end_date,
            payment_transaction_id=payment_transaction_id,
            auto_renew=request.data.get('auto_renew', True)
        )
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Cancel subscription"""
        subscription = self.get_object()
        
        if subscription.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        subscription.status = Subscription.Status.CANCELLED
        subscription.cancelled_at = timezone.now()
        subscription.auto_renew = False
        subscription.save()
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def renew(self, request, pk=None):
        """Renew subscription"""
        subscription = self.get_object()
        
        if subscription.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if subscription.status != Subscription.Status.EXPIRED:
            return Response({'error': 'Subscription is not expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Process payment (mock - in production, integrate with payment gateway)
        payment_transaction_id = request.data.get('payment_transaction_id', '')
        
        # Calculate new end date
        if subscription.plan.duration_days:
            new_end_date = timezone.now() + timedelta(days=subscription.plan.duration_days)
        elif subscription.plan.plan_type == MembershipPlan.PlanType.MONTHLY:
            new_end_date = timezone.now() + timedelta(days=30)
        elif subscription.plan.plan_type == MembershipPlan.PlanType.YEARLY:
            new_end_date = timezone.now() + timedelta(days=365)
        else:
            new_end_date = None
        
        subscription.status = Subscription.Status.ACTIVE
        subscription.start_date = timezone.now()
        subscription.end_date = new_end_date
        subscription.payment_transaction_id = payment_transaction_id
        subscription.save()
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

