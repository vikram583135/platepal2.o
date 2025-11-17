"""
Views for deliveries app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import (
    Delivery, RiderLocation, RiderEarnings, DeliveryDocument,
    RiderProfile, RiderBankDetail, RiderOnboarding, RiderBackgroundCheck, RiderReferral,
    RiderShift, DeliveryOffer, RiderWallet, RiderWalletTransaction,
    RiderRating, RiderDispute, EmergencyContact, AutoAcceptRule,
    Fleet, FleetRider, RiderAgreement, OfflineAction, TripLog, RiderSettings
)
from .serializers import (
    DeliverySerializer, RiderLocationSerializer, RiderEarningsSerializer, DeliveryDocumentSerializer,
    RiderProfileSerializer, RiderBankDetailSerializer, RiderOnboardingSerializer,
    RiderBackgroundCheckSerializer, RiderReferralSerializer, RiderShiftSerializer,
    DeliveryOfferSerializer, RiderWalletSerializer, RiderWalletTransactionSerializer,
    RiderRatingSerializer, RiderDisputeSerializer, EmergencyContactSerializer,
    AutoAcceptRuleSerializer, FleetSerializer, FleetRiderSerializer, RiderAgreementSerializer,
    OfflineActionSerializer, TripLogSerializer, RiderSettingsSerializer
)
from apps.accounts.permissions import IsOwnerOrAdmin
from apps.accounts.models import User
from apps.orders.models import Order

channel_layer = get_channel_layer()


class DeliveryViewSet(viewsets.ModelViewSet):
    """Delivery viewset"""
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Delivery.objects.filter(is_deleted=False)
        elif user.role == 'DELIVERY':
            return Delivery.objects.filter(rider=user, is_deleted=False)
        else:
            return Delivery.objects.filter(order__customer=user, is_deleted=False)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def assign(self, request, pk=None):
        """Assign delivery to rider (admin or auto-assign)"""
        delivery = self.get_object()
        rider_id = request.data.get('rider_id')
        
        if request.user.role != 'ADMIN' and not rider_id:
            rider_id = request.user.id  # Rider self-assigning
        
        if delivery.status != Delivery.Status.PENDING:
            return Response({'error': 'Delivery already assigned'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rider = User.objects.get(id=rider_id, role=User.Role.DELIVERY)
            delivery.rider = rider
            delivery.status = Delivery.Status.ASSIGNED
            delivery.save()
            
            # Broadcast to rider
            self.broadcast_to_rider(rider.id, 'order_assigned', DeliverySerializer(delivery).data)
            
            return Response(DeliverySerializer(delivery).data)
        except User.DoesNotExist:
            return Response({'error': 'Rider not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def accept(self, request, pk=None):
        """Rider accepts delivery"""
        delivery = self.get_object()
        
        if delivery.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if delivery.status != Delivery.Status.ASSIGNED:
            return Response({'error': 'Delivery not assigned'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery.status = Delivery.Status.ACCEPTED
        delivery.save()
        
        # Update order status
        delivery.order.status = Order.Status.ASSIGNED
        delivery.order.save()
        
        self.broadcast_order_update(delivery.order)
        return Response(DeliverySerializer(delivery).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reject(self, request, pk=None):
        """Rider rejects delivery"""
        delivery = self.get_object()
        
        if delivery.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        delivery.status = Delivery.Status.REJECTED
        delivery.rider = None
        delivery.save()
        
        return Response(DeliverySerializer(delivery).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def arrive_at_pickup(self, request, pk=None):
        """Rider arrives at pickup location"""
        delivery = self.get_object()
        
        if delivery.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if delivery.status != Delivery.Status.ACCEPTED:
            return Response({'error': 'Delivery not accepted yet'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery.status = Delivery.Status.ARRIVED_AT_PICKUP
        delivery.save()
        
        self.broadcast_order_update(delivery.order)
        return Response(DeliverySerializer(delivery).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pickup(self, request, pk=None):
        """Rider picks up order"""
        delivery = self.get_object()
        
        if delivery.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if delivery.status not in [Delivery.Status.ACCEPTED, Delivery.Status.ARRIVED_AT_PICKUP]:
            return Response({'error': 'Cannot pick up at this stage'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery.status = Delivery.Status.PICKED_UP
        delivery.actual_pickup_time = timezone.now()
        
        # Update status to IN_TRANSIT
        delivery.status = Delivery.Status.IN_TRANSIT
        delivery.save()
        
        delivery.order.status = Order.Status.PICKED_UP
        delivery.order.picked_up_at = timezone.now()
        delivery.order.save()
        
        self.broadcast_order_update(delivery.order)
        return Response(DeliverySerializer(delivery).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pause(self, request, pk=None):
        """Pause trip"""
        delivery = self.get_object()
        
        if delivery.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if delivery.status not in [Delivery.Status.ACCEPTED, Delivery.Status.PICKED_UP, Delivery.Status.IN_TRANSIT]:
            return Response({'error': 'Cannot pause trip at this stage'}, status=status.HTTP_400_BAD_REQUEST)
        
        if delivery.is_paused:
            return Response({'error': 'Trip is already paused'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery.is_paused = True
        delivery.paused_at = timezone.now()
        delivery.pause_reason = request.data.get('reason', 'Short break')
        delivery.save()
        
        return Response(DeliverySerializer(delivery).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def resume(self, request, pk=None):
        """Resume trip"""
        delivery = self.get_object()
        
        if delivery.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if not delivery.is_paused:
            return Response({'error': 'Trip is not paused'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery.is_paused = False
        delivery.resumed_at = timezone.now()
        delivery.save()
        
        return Response(DeliverySerializer(delivery).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        """Rider completes delivery"""
        delivery = self.get_object()
        
        if delivery.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if delivery.status not in [Delivery.Status.IN_TRANSIT, Delivery.Status.PICKED_UP]:
            return Response({'error': 'Cannot complete delivery at this stage'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check contactless delivery OTP if required
        if delivery.is_contactless and delivery.delivery_otp:
            otp = request.data.get('otp')
            if not otp or otp != delivery.delivery_otp:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery.status = Delivery.Status.DELIVERED
        delivery.actual_delivery_time = timezone.now()
        
        # Save delivery photo if provided
        if 'delivery_photo' in request.FILES:
            delivery.delivery_photo = request.FILES['delivery_photo']
        
        # Save signature if provided
        if 'signature_image' in request.FILES:
            delivery.signature_image = request.FILES['signature_image']
        
        delivery.save()
        
        delivery.order.status = Order.Status.DELIVERED
        delivery.order.delivered_at = timezone.now()
        delivery.order.save()
        
        # Award reward points when order is delivered
        self.award_reward_points(delivery.order)
        
        self.broadcast_order_update(delivery.order)
        return Response(DeliverySerializer(delivery).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unable_to_deliver(self, request, pk=None):
        """Mark delivery as unable to deliver"""
        delivery = self.get_object()
        
        if delivery.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if delivery.status not in [Delivery.Status.IN_TRANSIT, Delivery.Status.PICKED_UP]:
            return Response({'error': 'Cannot mark as unable to deliver at this stage'}, status=status.HTTP_400_BAD_REQUEST)
        
        reason = request.data.get('reason', '')
        reason_code = request.data.get('code', 'OTHER')
        
        if not reason:
            return Response({'error': 'Reason is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery.status = Delivery.Status.FAILED
        delivery.unable_to_deliver_reason = reason
        delivery.unable_to_deliver_code = reason_code
        
        # Save photo if provided
        if 'photo' in request.FILES:
            delivery.unable_to_deliver_photo = request.FILES['photo']
        
        delivery.save()
        
        # Update order status
        delivery.order.status = Order.Status.CANCELLED
        delivery.order.cancellation_reason = reason
        delivery.order.cancelled_at = timezone.now()
        delivery.order.save()
        
        self.broadcast_order_update(delivery.order)
        return Response(DeliverySerializer(delivery).data)
    
    def award_reward_points(self, order):
        """Award reward points for completed order"""
        try:
            from apps.rewards.models import UserLoyalty, RewardPoint
            from django.utils import timezone
            from datetime import timedelta
            
            # Get or create user loyalty
            loyalty, created = UserLoyalty.objects.get_or_create(
                user=order.customer,
                defaults={'total_points': 0, 'available_points': 0}
            )
            
            # Calculate points (1% of order value, minimum 10 points)
            from decimal import Decimal
            points_earned = max(10, int(float(order.total_amount) * 0.01))
            
            # Check if user has active subscription for bonus
            from apps.subscriptions.models import Subscription
            subscription = Subscription.objects.filter(
                user=order.customer,
                status=Subscription.Status.ACTIVE
            ).first()
            
            if subscription and subscription.is_active():
                # Apply points multiplier from subscription benefits
                multiplier = subscription.plan.benefits.get('points_multiplier', 1.0)
                points_earned = int(points_earned * multiplier)
            
            # Update loyalty
            loyalty.total_points += points_earned
            loyalty.available_points += points_earned
            loyalty.lifetime_points_earned += points_earned
            loyalty.save()
            
            # Update tier
            loyalty.update_tier()
            
            # Create reward point transaction
            RewardPoint.objects.create(
                user=order.customer,
                transaction_type=RewardPoint.TransactionType.EARNED,
                points=points_earned,
                balance_after=loyalty.available_points,
                order=order,
                description=f"Earned {points_earned} points for order {order.order_number}",
                expires_at=timezone.now() + timedelta(days=365)  # Points expire after 1 year
            )
        except Exception as e:
            # Log error but don't fail order
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to award reward points for order {order.id}: {str(e)}")
    
    def broadcast_to_rider(self, rider_id, event_type, data):
        """Broadcast event to rider"""
        import uuid
        async_to_sync(channel_layer.group_send)(
            f'delivery_{rider_id}',
            {
                'type': event_type,
                'data': data,
                'event_id': str(uuid.uuid4()),
            }
        )
    
    def broadcast_order_update(self, order):
        """Broadcast order update to customer"""
        import uuid
        from apps.orders.serializers import OrderSerializer
        event_data = OrderSerializer(order).data
        
        async_to_sync(channel_layer.group_send)(
            f'customer_{order.customer.id}',
            {
                'type': 'order_updated',
                'data': event_data,
                'event_id': str(uuid.uuid4()),
            }
        )


class RiderLocationViewSet(viewsets.ModelViewSet):
    """Rider location viewset"""
    serializer_class = RiderLocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderLocation.objects.all()
        return RiderLocation.objects.filter(rider=user)
    
    def perform_create(self, serializer):
        from decimal import Decimal
        import math
        
        location = serializer.save(rider=self.request.user)
        
        # Get rider settings for location mode
        settings, _ = RiderSettings.objects.get_or_create(rider=self.request.user)
        location.location_mode = settings.location_mode
        location.save()
        
        # Determine if rider is moving (based on speed)
        is_moving = False
        if location.speed:
            is_moving = float(location.speed) > 0.5  # More than 0.5 m/s
        
        location.is_moving = is_moving
        location.save()
        
        # Check geo-fencing for active deliveries
        active_deliveries = Delivery.objects.filter(
            rider=self.request.user,
            status__in=[Delivery.Status.ACCEPTED, Delivery.Status.ARRIVED_AT_PICKUP, Delivery.Status.PICKED_UP, Delivery.Status.IN_TRANSIT]
        )
        
        for delivery in active_deliveries:
            # Check pickup zone
            if delivery.pickup_latitude and delivery.pickup_longitude:
                distance = self.calculate_distance(
                    float(location.latitude),
                    float(location.longitude),
                    float(delivery.pickup_latitude),
                    float(delivery.pickup_longitude)
                )
                
                # Pickup zone radius: 100 meters
                if distance <= 0.1:  # 100 meters in km
                    if not location.near_pickup_zone:
                        location.near_pickup_zone = True
                        location.pickup_zone_entered_at = timezone.now()
                        location.save()
                        
                        # Auto-update delivery status if accepted
                        if delivery.status == Delivery.Status.ACCEPTED:
                            delivery.status = Delivery.Status.ARRIVED_AT_PICKUP
                            delivery.save()
                            self.broadcast_order_update(delivery.order)
            
            # Check drop zone
            if delivery.delivery_latitude and delivery.delivery_longitude:
                distance = self.calculate_distance(
                    float(location.latitude),
                    float(location.longitude),
                    float(delivery.delivery_latitude),
                    float(delivery.delivery_longitude)
                )
                
                # Drop zone radius: 100 meters
                if distance <= 0.1:  # 100 meters in km
                    if not location.near_drop_zone:
                        location.near_drop_zone = True
                        location.drop_zone_entered_at = timezone.now()
                        location.save()
        
        # Broadcast location update
        for delivery in active_deliveries:
            import uuid
            async_to_sync(channel_layer.group_send)(
                f'customer_{delivery.order.customer.id}',
                {
                    'type': 'rider_location',
                    'data': {
                        'delivery_id': delivery.id,
                        'order_id': delivery.order.id,
                        'location': {
                            'latitude': float(location.latitude),
                            'longitude': float(location.longitude),
                            'heading': float(location.heading) if location.heading else None,
                            'speed': float(location.speed) if location.speed else None,
                        }
                    },
                    'event_id': str(uuid.uuid4()),
                }
            )
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in kilometers using Haversine formula"""
        import math
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2) * math.sin(dlat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon/2) * math.sin(dlon/2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance


class RiderEarningsViewSet(viewsets.ReadOnlyModelViewSet):
    """Rider earnings viewset (read-only)"""
    serializer_class = RiderEarningsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderEarnings.objects.all()
        return RiderEarnings.objects.filter(rider=user)


class DeliveryDocumentViewSet(viewsets.ModelViewSet):
    """Delivery document viewset"""
    serializer_class = DeliveryDocumentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return DeliveryDocument.objects.filter(is_deleted=False)
        return DeliveryDocument.objects.filter(rider=user, is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(rider=self.request.user)


class RiderProfileViewSet(viewsets.ModelViewSet):
    """Rider profile viewset"""
    serializer_class = RiderProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderProfile.objects.filter(is_deleted=False)
        return RiderProfile.objects.filter(rider=user, is_deleted=False)
    
    def perform_create(self, serializer):
        profile = serializer.save(rider=self.request.user)
        # Recalculate completion percentage
        profile.profile_completion_percentage = profile.calculate_completion_percentage()
        profile.save()
    
    def perform_update(self, serializer):
        profile = serializer.save()
        # Recalculate completion percentage
        profile.profile_completion_percentage = profile.calculate_completion_percentage()
        profile.save()


class RiderBankDetailViewSet(viewsets.ModelViewSet):
    """Rider bank detail viewset"""
    serializer_class = RiderBankDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderBankDetail.objects.filter(is_deleted=False)
        return RiderBankDetail.objects.filter(rider=user, is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(rider=self.request.user)


class RiderOnboardingViewSet(viewsets.ModelViewSet):
    """Rider onboarding viewset"""
    serializer_class = RiderOnboardingSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderOnboarding.objects.all()
        return RiderOnboarding.objects.filter(rider=user)
    
    def get_object(self):
        if self.action == 'retrieve' and not self.kwargs.get('pk'):
            # Get or create onboarding for current rider
            onboarding, created = RiderOnboarding.objects.get_or_create(
                rider=self.request.user,
                defaults={'status': RiderOnboarding.OnboardingStatus.NOT_STARTED}
            )
            return onboarding
        return super().get_object()
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get current onboarding status"""
        onboarding, created = RiderOnboarding.objects.get_or_create(
            rider=request.user,
            defaults={'status': RiderOnboarding.OnboardingStatus.NOT_STARTED}
        )
        serializer = self.get_serializer(onboarding)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start onboarding process"""
        onboarding, created = RiderOnboarding.objects.get_or_create(
            rider=request.user,
            defaults={'status': RiderOnboarding.OnboardingStatus.IN_PROGRESS}
        )
        if not created and onboarding.status == RiderOnboarding.OnboardingStatus.NOT_STARTED:
            onboarding.status = RiderOnboarding.OnboardingStatus.IN_PROGRESS
            onboarding.started_at = timezone.now()
            onboarding.save()
        serializer = self.get_serializer(onboarding)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def submit(self, request):
        """Submit onboarding for verification"""
        try:
            onboarding = RiderOnboarding.objects.get(rider=request.user)
        except RiderOnboarding.DoesNotExist:
            return Response({'error': 'Onboarding not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if onboarding.status != RiderOnboarding.OnboardingStatus.IN_PROGRESS:
            return Response({'error': 'Onboarding already submitted'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if all required items are completed
        if not all([
            onboarding.phone_verified,
            onboarding.email_verified,
            onboarding.profile_completed,
            onboarding.documents_uploaded,
            onboarding.bank_details_added,
            onboarding.agreement_signed,
        ]):
            return Response({'error': 'Please complete all required steps'}, status=status.HTTP_400_BAD_REQUEST)
        
        onboarding.status = RiderOnboarding.OnboardingStatus.PENDING_VERIFICATION
        onboarding.completed_at = timezone.now()
        onboarding.save()
        
        serializer = self.get_serializer(onboarding)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def use_referral_code(self, request):
        """Apply referral code"""
        referral_code = request.data.get('referral_code')
        if not referral_code:
            return Response({'error': 'Referral code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            referral = RiderReferral.objects.get(
                referral_code=referral_code,
                status=RiderReferral.Status.PENDING
            )
        except RiderReferral.DoesNotExist:
            return Response({'error': 'Invalid referral code'}, status=status.HTTP_404_NOT_FOUND)
        
        onboarding, created = RiderOnboarding.objects.get_or_create(
            rider=request.user,
            defaults={'status': RiderOnboarding.OnboardingStatus.IN_PROGRESS}
        )
        
        if onboarding.referral_code_used:
            return Response({'error': 'Referral code already used'}, status=status.HTTP_400_BAD_REQUEST)
        
        onboarding.referral_code_used = referral_code
        onboarding.save()
        
        # Link referral to user when they complete onboarding
        referral.referred_user = request.user
        referral.status = RiderReferral.Status.COMPLETED
        referral.completed_at = timezone.now()
        referral.save()
        
        serializer = self.get_serializer(onboarding)
        return Response(serializer.data)


class RiderBackgroundCheckViewSet(viewsets.ReadOnlyModelViewSet):
    """Rider background check viewset (read-only for riders)"""
    serializer_class = RiderBackgroundCheckSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderBackgroundCheck.objects.filter(is_deleted=False)
        return RiderBackgroundCheck.objects.filter(rider=user, is_deleted=False)


class RiderReferralViewSet(viewsets.ModelViewSet):
    """Rider referral viewset"""
    serializer_class = RiderReferralSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderReferral.objects.all()
        return RiderReferral.objects.filter(referrer=user)
    
    @action(detail=False, methods=['get'])
    def my_code(self, request):
        """Get or generate referral code for current rider"""
        import secrets
        referral, created = RiderReferral.objects.get_or_create(
            referrer=request.user,
            defaults={
                'referral_code': secrets.token_urlsafe(8).upper()[:10],
                'status': RiderReferral.Status.PENDING
            }
        )
        serializer = self.get_serializer(referral)
        return Response(serializer.data)


class RiderShiftViewSet(viewsets.ModelViewSet):
    """Rider shift viewset"""
    serializer_class = RiderShiftSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderShift.objects.all()
        return RiderShift.objects.filter(rider=user)
    
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new shift"""
        # Check if rider has an active shift
        active_shift = RiderShift.objects.filter(
            rider=request.user,
            status__in=[RiderShift.Status.SCHEDULED, RiderShift.Status.ACTIVE, RiderShift.Status.PAUSED]
        ).first()
        
        if active_shift:
            if active_shift.status == RiderShift.Status.PAUSED:
                # Resume paused shift
                active_shift.status = RiderShift.Status.ACTIVE
                active_shift.save()
                serializer = self.get_serializer(active_shift)
                return Response(serializer.data)
            return Response({'error': 'You already have an active shift'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new shift
        shift = RiderShift.objects.create(
            rider=request.user,
            status=RiderShift.Status.ACTIVE,
            actual_start=timezone.now()
        )
        serializer = self.get_serializer(shift)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop current shift"""
        shift = self.get_object()
        if shift.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if shift.status not in [RiderShift.Status.ACTIVE, RiderShift.Status.PAUSED]:
            return Response({'error': 'Shift is not active'}, status=status.HTTP_400_BAD_REQUEST)
        
        shift.status = RiderShift.Status.COMPLETED
        shift.actual_end = timezone.now()
        
        # Calculate time online
        if shift.actual_start:
            duration = shift.actual_end - shift.actual_start
            shift.time_online_minutes = int(duration.total_seconds() / 60)
        
        shift.save()
        serializer = self.get_serializer(shift)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause current shift"""
        shift = self.get_object()
        if shift.rider != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if shift.status != RiderShift.Status.ACTIVE:
            return Response({'error': 'Shift is not active'}, status=status.HTTP_400_BAD_REQUEST)
        
        shift.status = RiderShift.Status.PAUSED
        shift.save()
        serializer = self.get_serializer(shift)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active shift"""
        shift = RiderShift.objects.filter(
            rider=request.user,
            status__in=[RiderShift.Status.ACTIVE, RiderShift.Status.PAUSED]
        ).first()
        
        if shift:
            serializer = self.get_serializer(shift)
            return Response(serializer.data)
        return Response({'error': 'No active shift'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get shift summary statistics"""
        from django.db.models import Sum, Count
        from datetime import datetime, timedelta
        
        today = timezone.now().date()
        
        # Today's shift
        today_shift = RiderShift.objects.filter(
            rider=request.user,
            actual_start__date=today
        ).first()
        
        # Today's statistics
        today_stats = RiderShift.objects.filter(
            rider=request.user,
            actual_start__date=today,
            status=RiderShift.Status.COMPLETED
        ).aggregate(
            total_earnings=Sum('earnings_total'),
            total_deliveries=Sum('deliveries_completed'),
            total_time_online=Sum('time_online_minutes')
        )
        
        # Acceptance rate (from deliveries)
        total_offers = DeliveryOffer.objects.filter(
            rider=request.user,
            status__in=[DeliveryOffer.Status.ACCEPTED, DeliveryOffer.Status.DECLINED]
        ).count()
        accepted_offers = DeliveryOffer.objects.filter(
            rider=request.user,
            status=DeliveryOffer.Status.ACCEPTED
        ).count()
        
        acceptance_rate = (accepted_offers / total_offers * 100) if total_offers > 0 else 0
        
        return Response({
            'today_shift': self.get_serializer(today_shift).data if today_shift else None,
            'today_earnings': float(today_stats['total_earnings'] or 0),
            'today_deliveries': today_stats['total_deliveries'] or 0,
            'today_time_online_minutes': today_stats['total_time_online'] or 0,
            'acceptance_rate': round(acceptance_rate, 2),
        })


class DeliveryOfferViewSet(viewsets.ModelViewSet):
    """Delivery offer viewset"""
    serializer_class = DeliveryOfferSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return DeliveryOffer.objects.all()
        return DeliveryOffer.objects.filter(rider=user)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Get nearby job offers"""
        from django.db.models import Q
        from datetime import timedelta
        from .services import calculate_surge_multiplier, find_nearby_riders
        
        # Get rider's current location (latest)
        latest_location = RiderLocation.objects.filter(
            rider=request.user
        ).order_by('-created_at').first()
        
        if not latest_location:
            return Response({'error': 'Please enable location services'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get active offers that haven't been sent to this rider or are pending
        offers = DeliveryOffer.objects.filter(
            Q(status=DeliveryOffer.Status.PENDING) | 
            (Q(status=DeliveryOffer.Status.SENT) & (Q(rider__isnull=True) | Q(rider=request.user))),
            expires_at__gt=timezone.now()
        ).select_related('delivery', 'delivery__order').order_by('-priority', '-created_at')
        
        # Enhance offers with surge pricing and distance calculation
        enhanced_offers = []
        rider_lat = float(latest_location.latitude)
        rider_lng = float(latest_location.longitude)
        
        for offer in offers[:20]:  # Limit to 20 offers
            if offer.delivery.pickup_latitude and offer.delivery.pickup_longitude:
                # Calculate surge multiplier for offer area
                surge_multiplier = calculate_surge_multiplier(
                    float(offer.delivery.pickup_latitude),
                    float(offer.delivery.pickup_longitude)
                )
                
                # Update offer if surge detected
                if surge_multiplier > 1.0 and not offer.is_surge:
                    offer.is_surge = True
                    offer.surge_multiplier = surge_multiplier
                    offer.estimated_earnings *= Decimal(str(surge_multiplier))
                    offer.save()
            
            enhanced_offers.append(offer)
        
        serializer = self.get_serializer(enhanced_offers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a delivery offer"""
        offer = self.get_object()
        
        # Check if offer is valid
        if offer.status != DeliveryOffer.Status.SENT or offer.rider != request.user:
            return Response({'error': 'Invalid offer'}, status=status.HTTP_400_BAD_REQUEST)
        
        if offer.is_expired():
            offer.status = DeliveryOffer.Status.EXPIRED
            offer.save()
            return Response({'error': 'Offer has expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if rider already has an accepted offer
        active_delivery = Delivery.objects.filter(
            rider=request.user,
            status__in=[Delivery.Status.ACCEPTED, Delivery.Status.PICKED_UP, Delivery.Status.IN_TRANSIT]
        ).first()
        
        if active_delivery:
            return Response({'error': 'You already have an active delivery'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Accept the offer
        offer.status = DeliveryOffer.Status.ACCEPTED
        offer.accepted_at = timezone.now()
        offer.save()
        
        # Assign delivery to rider
        delivery = offer.delivery
        delivery.rider = request.user
        delivery.status = Delivery.Status.ACCEPTED
        delivery.save()
        
        # Update order status
        delivery.order.status = Order.Status.ASSIGNED
        delivery.order.save()
        
        # Broadcast update
        self.broadcast_to_rider(request.user.id, 'offer_accepted', DeliverySerializer(delivery).data)
        
        serializer = self.get_serializer(offer)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline a delivery offer"""
        offer = self.get_object()
        
        if offer.status != DeliveryOffer.Status.SENT or offer.rider != request.user:
            return Response({'error': 'Invalid offer'}, status=status.HTTP_400_BAD_REQUEST)
        
        decline_reason = request.data.get('reason', '')
        decline_code = request.data.get('code', 'OTHER')
        
        offer.status = DeliveryOffer.Status.DECLINED
        offer.declined_at = timezone.now()
        offer.decline_reason = decline_reason
        offer.decline_code = decline_code
        offer.save()
        
        serializer = self.get_serializer(offer)
        return Response(serializer.data)
    
    def broadcast_to_rider(self, rider_id, event_type, data):
        """Broadcast event to rider"""
        import uuid
        async_to_sync(channel_layer.group_send)(
            f'delivery_{rider_id}',
            {
                'type': event_type,
                'data': data,
                'event_id': str(uuid.uuid4()),
            }
        )


class RiderWalletViewSet(viewsets.ReadOnlyModelViewSet):
    """Rider wallet viewset"""
    serializer_class = RiderWalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderWallet.objects.filter(is_deleted=False)
        return RiderWallet.objects.filter(rider=user, is_deleted=False)
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """Get current rider's wallet"""
        wallet, created = RiderWallet.objects.get_or_create(
            rider=request.user,
            defaults={'balance': 0, 'currency': 'USD'}
        )
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get wallet transactions"""
        wallet, created = RiderWallet.objects.get_or_create(
            rider=request.user,
            defaults={'balance': 0, 'currency': 'USD'}
        )
        transactions = RiderWalletTransaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')[:50]
        serializer = RiderWalletTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def instant_payout(self, request):
        """Initiate instant payout"""
        wallet, created = RiderWallet.objects.get_or_create(
            rider=request.user,
            defaults={'balance': 0, 'currency': 'USD'}
        )
        
        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
        
        if amount <= 0:
            return Response({'error': 'Amount must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)
        
        if amount > wallet.balance:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Instant payout fee (example: 2% or minimum $1)
        fee_percentage = Decimal('0.02')  # 2%
        min_fee = Decimal('1.00')
        fee = max(amount * fee_percentage, min_fee)
        payout_amount = amount - fee
        
        # Check bank details
        try:
            bank_detail = RiderBankDetail.objects.get(rider=request.user, is_verified=True)
        except RiderBankDetail.DoesNotExist:
            return Response({'error': 'Bank details not verified'}, status=status.HTTP_400_BAD_REQUEST)
        
        # In production, integrate with payout gateway (Stripe, PayPal, etc.)
        # For now, simulate instant payout
        
        # Deduct from wallet
        wallet.balance -= amount
        wallet.save()
        
        # Create wallet transaction
        transaction = RiderWalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=RiderWalletTransaction.TransactionType.DEBIT,
            source=RiderWalletTransaction.TransactionSource.PAYOUT,
            amount=amount,
            balance_after=wallet.balance,
            description=f"Instant payout of ${amount} (Fee: ${fee})"
        )
        
        return Response({
            'message': 'Instant payout initiated',
            'amount': float(amount),
            'fee': float(fee),
            'payout_amount': float(payout_amount),
            'transaction_id': transaction.id,
            'estimated_arrival': 'Within 1 business day',
            'note': 'In production, this would be processed via payment gateway'
        })
    
    @action(detail=False, methods=['get'])
    def earnings_breakdown(self, request):
        """Get earnings breakdown for period"""
        from django.db.models import Sum
        from datetime import timedelta
        
        period = request.query_params.get('period', 'week')  # day, week, month
        
        if period == 'day':
            start_date = timezone.now().date()
        elif period == 'week':
            start_date = timezone.now().date() - timedelta(days=7)
        elif period == 'month':
            start_date = timezone.now().date() - timedelta(days=30)
        else:
            start_date = timezone.now().date() - timedelta(days=7)
        
        # Get earnings from completed deliveries
        deliveries = Delivery.objects.filter(
            rider=request.user,
            status=Delivery.Status.DELIVERED,
            actual_delivery_time__date__gte=start_date
        )
        
        breakdown = deliveries.aggregate(
            total_earnings=Sum('total_earnings'),
            total_base_fee=Sum('base_fee'),
            total_distance_fee=Sum('distance_fee'),
            total_tip=Sum('tip_amount'),
            total_deliveries=deliveries.count()
        )
        
        return Response({
            'period': period,
            'start_date': start_date.isoformat(),
            'breakdown': {
                'total_earnings': float(breakdown['total_earnings'] or 0),
                'base_fee': float(breakdown['total_base_fee'] or 0),
                'distance_fee': float(breakdown['total_distance_fee'] or 0),
                'tips': float(breakdown['total_tip'] or 0),
                'total_deliveries': breakdown['total_deliveries'] or 0,
            }
        })


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """Emergency contact viewset"""
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return EmergencyContact.objects.filter(is_deleted=False)
        return EmergencyContact.objects.filter(rider=user, is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(rider=self.request.user)


class AutoAcceptRuleViewSet(viewsets.ModelViewSet):
    """Auto-accept rule viewset"""
    serializer_class = AutoAcceptRuleSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return AutoAcceptRule.objects.filter(is_deleted=False)
        return AutoAcceptRule.objects.filter(rider=user, is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(rider=self.request.user)


class RiderRatingViewSet(viewsets.ReadOnlyModelViewSet):
    """Rider rating viewset (read-only for riders)"""
    serializer_class = RiderRatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderRating.objects.all()
        return RiderRating.objects.filter(rider=user)


class RiderDisputeViewSet(viewsets.ModelViewSet):
    """Rider dispute viewset"""
    serializer_class = RiderDisputeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderDispute.objects.filter(is_deleted=False)
        return RiderDispute.objects.filter(rider=user, is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(rider=self.request.user)


class RiderAgreementViewSet(viewsets.ModelViewSet):
    """Rider agreement viewset"""
    serializer_class = RiderAgreementSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderAgreement.objects.all()
        return RiderAgreement.objects.filter(rider=user)
    
    @action(detail=False, methods=['post'])
    def accept(self, request):
        """Accept rider agreement"""
        agreement_version = request.data.get('agreement_version')
        agreement_text = request.data.get('agreement_text')
        
        if not agreement_version or not agreement_text:
            return Response({'error': 'Agreement version and text are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get client IP and user agent
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        agreement = RiderAgreement.objects.create(
            rider=request.user,
            agreement_version=agreement_version,
            agreement_text=agreement_text,
            agreed_at=timezone.now(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Update onboarding
        onboarding, created = RiderOnboarding.objects.get_or_create(
            rider=request.user,
            defaults={'status': RiderOnboarding.OnboardingStatus.IN_PROGRESS}
        )
        onboarding.agreement_signed = True
        onboarding.save()
        
        serializer = self.get_serializer(agreement)
        return Response(serializer.data)


class FleetViewSet(viewsets.ModelViewSet):
    """Fleet viewset"""
    serializer_class = FleetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Fleet.objects.filter(is_deleted=False)
        # Fleet managers can see their fleets
        return Fleet.objects.filter(manager=user, is_deleted=False)
    
    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Get fleet dashboard data"""
        fleet = self.get_object()
        
        # Check permissions
        if request.user.role != 'ADMIN' and fleet.manager != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get active riders
        active_riders = FleetRider.objects.filter(
            fleet=fleet,
            is_active=True
        ).select_related('rider')
        
        # Get rider assignments (deliveries)
        rider_ids = [fr.rider.id for fr in active_riders]
        active_deliveries = Delivery.objects.filter(
            rider_id__in=rider_ids,
            status__in=[Delivery.Status.ACCEPTED, Delivery.Status.PICKED_UP, Delivery.Status.IN_TRANSIT]
        )
        
        # Get live locations
        from django.db.models import Max
        latest_locations = RiderLocation.objects.filter(
            rider_id__in=rider_ids
        ).values('rider').annotate(
            latest_created=Max('created_at')
        )
        
        return Response({
            'fleet': FleetSerializer(fleet).data,
            'active_riders_count': active_riders.count(),
            'active_deliveries_count': active_deliveries.count(),
            'riders': [FleetRiderSerializer(fr).data for fr in active_riders],
        })


class FleetRiderViewSet(viewsets.ModelViewSet):
    """Fleet rider viewset"""
    serializer_class = FleetRiderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return FleetRider.objects.all()
        # Fleet managers can see their fleet riders
        return FleetRider.objects.filter(fleet__manager=user)
    
    @action(detail=True, methods=['post'])
    def replace_for_delivery(self, request, pk=None):
        """Replace rider for a specific delivery"""
        fleet_rider = self.get_object()
        delivery_id = request.data.get('delivery_id')
        new_rider_id = request.data.get('new_rider_id')
        
        if not delivery_id or not new_rider_id:
            return Response({'error': 'delivery_id and new_rider_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            delivery = Delivery.objects.get(id=delivery_id)
            new_rider = User.objects.get(id=new_rider_id, role=User.Role.DELIVERY)
        except (Delivery.DoesNotExist, User.DoesNotExist):
            return Response({'error': 'Delivery or rider not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if delivery is assigned to the old rider
        if delivery.rider != fleet_rider.rider:
            return Response({'error': 'Delivery not assigned to this rider'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Replace rider
        old_rider = delivery.rider
        delivery.rider = new_rider
        delivery.save()
        
        return Response({
            'message': f'Delivery reassigned from {old_rider.email} to {new_rider.email}',
            'delivery': DeliverySerializer(delivery).data
        })


class OfflineActionViewSet(viewsets.ModelViewSet):
    """Offline action viewset"""
    serializer_class = OfflineActionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return OfflineAction.objects.all()
        return OfflineAction.objects.filter(rider=user)
    
    def perform_create(self, serializer):
        serializer.save(rider=self.request.user)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending offline actions"""
        pending_actions = OfflineAction.objects.filter(
            rider=request.user,
            status=OfflineAction.Status.PENDING
        ).order_by('created_at')
        serializer = self.get_serializer(pending_actions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """Sync offline actions"""
        pending_actions = OfflineAction.objects.filter(
            rider=request.user,
            status=OfflineAction.Status.PENDING
        ).order_by('created_at')
        
        synced_count = 0
        failed_count = 0
        
        for action in pending_actions:
            try:
                # Process action based on type
                if action.action_type == OfflineAction.ActionType.ACCEPT_OFFER:
                    # Handle accept offer action
                    offer_id = action.action_data.get('offer_id')
                    if offer_id:
                        try:
                            offer = DeliveryOffer.objects.get(id=offer_id, rider=request.user)
                            # Accept the offer (simplified - would need full logic)
                            pass
                        except DeliveryOffer.DoesNotExist:
                            action.status = OfflineAction.Status.FAILED
                            action.sync_error = 'Offer not found'
                            action.save()
                            failed_count += 1
                            continue
                
                action.status = OfflineAction.Status.COMPLETED
                action.synced_at = timezone.now()
                action.save()
                synced_count += 1
            except Exception as e:
                action.retry_count += 1
                if action.retry_count >= action.max_retries:
                    action.status = OfflineAction.Status.FAILED
                    action.sync_error = str(e)
                else:
                    # Calculate next retry time (exponential backoff)
                    from datetime import timedelta
                    import math
                    delay_seconds = math.pow(2, action.retry_count) * 60  # 2^retry_count minutes
                    action.next_retry_at = timezone.now() + timedelta(seconds=delay_seconds)
                action.save()
                failed_count += 1
        
        return Response({
            'synced_count': synced_count,
            'failed_count': failed_count,
            'message': f'Synced {synced_count} actions, {failed_count} failed'
        })


class TripLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Trip log viewset (read-only)"""
    serializer_class = TripLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return TripLog.objects.all()
        return TripLog.objects.filter(rider=user)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get trip analytics"""
        from django.db.models import Sum, Count, Avg
        from datetime import timedelta
        
        user = request.user
        period = request.query_params.get('period', 'week')  # day, week, month
        
        if period == 'day':
            start_date = timezone.now().date()
        elif period == 'week':
            start_date = timezone.now().date() - timedelta(days=7)
        elif period == 'month':
            start_date = timezone.now().date() - timedelta(days=30)
        else:
            start_date = timezone.now().date() - timedelta(days=7)
        
        trip_logs = TripLog.objects.filter(
            rider=user,
            trip_started_at__date__gte=start_date
        )
        
        analytics = trip_logs.aggregate(
            total_trips=Count('id'),
            total_distance=Sum('total_distance_km'),
            total_time=Sum('total_time_minutes'),
            total_earnings=Sum('total_earnings'),
            avg_distance=Avg('total_distance_km'),
            avg_time=Avg('total_time_minutes'),
            avg_earnings=Avg('total_earnings')
        )
        
        return Response({
            'period': period,
            'start_date': start_date.isoformat(),
            'analytics': {
                'total_trips': analytics['total_trips'] or 0,
                'total_distance_km': float(analytics['total_distance'] or 0),
                'total_time_minutes': analytics['total_time'] or 0,
                'total_earnings': float(analytics['total_earnings'] or 0),
                'avg_distance_km': float(analytics['avg_distance'] or 0),
                'avg_time_minutes': analytics['avg_time'] or 0,
                'avg_earnings': float(analytics['avg_earnings'] or 0),
            }
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export trip logs as CSV"""
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        trip_logs = TripLog.objects.filter(rider=user)
        
        if start_date:
            trip_logs = trip_logs.filter(trip_started_at__date__gte=start_date)
        if end_date:
            trip_logs = trip_logs.filter(trip_started_at__date__lte=end_date)
        
        trip_logs = trip_logs.order_by('-trip_started_at')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="trip_logs_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Trip Date', 'Order Number', 'Distance (km)', 'Time (min)',
            'Base Fee', 'Distance Fee', 'Time Fee', 'Tip', 'Total Earnings'
        ])
        
        for log in trip_logs:
            writer.writerow([
                log.trip_started_at.strftime('%Y-%m-%d %H:%M:%S'),
                log.delivery.order.order_number,
                log.total_distance_km,
                log.total_time_minutes,
                log.base_fee,
                log.distance_fee,
                log.time_fee,
                log.tip_amount,
                log.total_earnings
            ])
        
        return response


class RiderSettingsViewSet(viewsets.ModelViewSet):
    """Rider settings viewset"""
    serializer_class = RiderSettingsSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return RiderSettings.objects.all()
        return RiderSettings.objects.filter(rider=user)
    
    def get_object(self):
        if self.action == 'retrieve' and not self.kwargs.get('pk'):
            # Get or create settings for current rider
            settings, created = RiderSettings.objects.get_or_create(
                rider=self.request.user
            )
            return settings
        return super().get_object()
    
    def perform_create(self, serializer):
        serializer.save(rider=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_settings(self, request):
        """Get current rider's settings"""
        settings, created = RiderSettings.objects.get_or_create(
            rider=request.user
        )
        serializer = self.get_serializer(settings)
        return Response(serializer.data)

