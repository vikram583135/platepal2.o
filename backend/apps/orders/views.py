"""
Views for orders app
"""
import uuid

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from django.db.models import Avg
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Order, OrderItem, Review, ItemReview
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    ReviewSerializer,
    ItemReviewSerializer,
)
from apps.accounts.permissions import IsOwnerOrAdmin
from apps.restaurants.permissions import IsRestaurantOwner
from apps.restaurants.models import Restaurant, RestaurantAlert
from apps.restaurants.serializers import RestaurantAlertSerializer
from apps.inventory.services import reserve_inventory_for_order
from apps.events.broadcast import EventBroadcastService


channel_layer = get_channel_layer()


class OrderViewSet(viewsets.ModelViewSet):
    """Order viewset"""
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Order.objects.filter(is_deleted=False)
        elif user.role == 'RESTAURANT':
            return Order.objects.filter(restaurant__owner=user, is_deleted=False)
        elif user.role == 'DELIVERY':
            return Order.objects.filter(delivery__rider=user, is_deleted=False)
        else:  # CUSTOMER
            return Order.objects.filter(customer=user, is_deleted=False)
    
    @transaction.atomic
    def perform_create(self, serializer):
        try:
            # Customer is set in serializer.create() from context
            order = serializer.save()
            
            # Create order.created event and broadcast
            order_data = OrderSerializer(order, context={'request': self.request}).data
            EventBroadcastService.broadcast_to_multiple(
                event_type='order.created',
                aggregate_type='Order',
                aggregate_id=str(order.id),
                payload=order_data,
                customer_id=order.customer.id,
                restaurant_id=order.restaurant.id,
                include_admin=True,
                metadata={
                    'user_id': self.request.user.id if self.request.user.is_authenticated else None,
                    'user_role': self.request.user.role if self.request.user.is_authenticated else None,
                }
            )
            
            # Also broadcast to restaurant branch channel if applicable
            if hasattr(order.restaurant, 'branches'):
                for branch in order.restaurant.branches.all():
                    EventBroadcastService.broadcast(
                        event_type='order.created',
                        aggregate_type='Order',
                        aggregate_id=str(order.id),
                        payload=order_data,
                        channels=[f'restaurant_{branch.id}'] if branch.id != order.restaurant.id else [],
                        metadata={'branch_id': branch.id}
                    )
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Order creation error: {str(e)}")
            print(traceback.format_exc())
            # Re-raise to let DRF handle it properly
            raise

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    def queue(self, request):
        """Return grouped order queues for restaurant dashboard"""
        queryset = self._filter_restaurant_queryset(request)
        status_groups = {
            'new': [Order.Status.PENDING],
            'accepted': [Order.Status.ACCEPTED],
            'preparing': [Order.Status.PREPARING],
            'ready': [Order.Status.READY],
            'assigned': [Order.Status.ASSIGNED],
            'out_for_delivery': [Order.Status.PICKED_UP, Order.Status.OUT_FOR_DELIVERY],
            'completed': [Order.Status.DELIVERED],
            'cancelled': [Order.Status.CANCELLED],
        }
        payload = {}
        for label, statuses in status_groups.items():
            orders = queryset.filter(status__in=statuses).order_by('created_at')
            payload[label] = OrderSerializer(
                orders,
                many=True,
                context={'request': request, 'include_internal': True}
            ).data
        payload['metrics'] = self._queue_metrics(queryset)
        return Response(payload)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    def realtime_feed(self, request):
        """KPI + timers for live dashboard"""
        queryset = self._filter_restaurant_queryset(request)
        restaurant = self._get_restaurant_instance(request, queryset)
        latest_orders = queryset.order_by('-created_at')[:8]
        preparing_orders = queryset.filter(status=Order.Status.PREPARING).order_by('created_at')[:8]
        feed = {
            'latest_orders': OrderSerializer(
                latest_orders,
                many=True,
                context={'request': request, 'include_internal': True}
            ).data,
            'preparing_timers': self._build_timer_payload(preparing_orders),
            'sla_watchlist': self._sla_watchlist(queryset),
        }
        if restaurant:
            alerts = RestaurantAlert.objects.filter(
                restaurant=restaurant,
                is_deleted=False
            ).order_by('-created_at')[:5]
            feed['alerts'] = RestaurantAlertSerializer(alerts, many=True).data
        return Response(feed)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    def kds_board(self, request):
        """Data for Kitchen Display System views"""
        queryset = self._filter_restaurant_queryset(request)
        board = {
            'new': self._build_kds_payload(queryset.filter(status=Order.Status.PENDING)),
            'preparing': self._build_kds_payload(queryset.filter(status=Order.Status.PREPARING)),
            'ready': self._build_kds_payload(queryset.filter(status=Order.Status.READY)),
            'completed': self._build_kds_payload(queryset.filter(status=Order.Status.DELIVERED).order_by('-delivered_at')[:20]),
        }
        return Response(board)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    @transaction.atomic
    def accept(self, request, pk=None):
        """Restaurant accepts order"""
        order = self.get_object()
        
        if order.status != Order.Status.PENDING:
            return Response({'error': 'Order cannot be accepted'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = Order.Status.ACCEPTED
        order.accepted_at = timezone.now()
        order.save()
        
        # Create order.accepted event and broadcast
        order_data = OrderSerializer(order, context={'request': request, 'include_internal': True}).data
        EventBroadcastService.broadcast_to_multiple(
            event_type='order.accepted',
            aggregate_type='Order',
            aggregate_id=str(order.id),
            payload=order_data,
            customer_id=order.customer.id,
            restaurant_id=order.restaurant.id,
            include_admin=True,
            metadata={
                'user_id': request.user.id,
                'accepted_at': order.accepted_at.isoformat(),
            }
        )
        
        self.evaluate_sla(order)
        
        # Trigger automatic rider assignment
        try:
            from apps.deliveries.services_assignment import RiderAssignmentService
            delivery = RiderAssignmentService.assign_rider_to_order(order)
            if delivery:
                logger.info(f"Rider assignment triggered for order {order.id}")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to trigger rider assignment for order {order.id}: {str(e)}")
        
        return Response(order_data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    @transaction.atomic
    def decline(self, request, pk=None):
        """Restaurant declines order"""
        order = self.get_object()
        
        if order.status != Order.Status.PENDING:
            return Response({'error': 'Order cannot be declined'}, status=status.HTTP_400_BAD_REQUEST)
        
        cancellation_reason = request.data.get('reason', 'Restaurant declined')
        order.status = Order.Status.CANCELLED
        order.cancellation_reason = cancellation_reason
        order.cancelled_at = timezone.now()
        order.save()
        
        # Auto-refund if payment was made
        from apps.payments.models import Payment, Refund
        from apps.payments.views import process_refund
        refund_processed = False
        if hasattr(order, 'payment') and order.payment.status == Payment.Status.COMPLETED:
            try:
                # Process refund
                refund = Refund.objects.create(
                    payment=order.payment,
                    order=order,
                    amount=order.total_amount,
                    reason=f"Order rejected by restaurant: {cancellation_reason}",
                    status=Refund.Status.PROCESSING,
                    processed_by=request.user
                )
                # Auto-process refund (in production, integrate with payment gateway)
                refund.status = Refund.Status.COMPLETED
                refund.refund_transaction_id = f"REF-{uuid.uuid4().hex[:12].upper()}"
                refund.processed_at = timezone.now()
                refund.save()
                refund_processed = True
            except Exception as e:
                # Log error but continue
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to process refund for order {order.id}: {str(e)}")
        
        # Create order.rejected event and broadcast
        order_data = OrderSerializer(order, context={'request': request}).data
        EventBroadcastService.broadcast_to_multiple(
            event_type='order.rejected',
            aggregate_type='Order',
            aggregate_id=str(order.id),
            payload={
                **order_data,
                'rejection_reason': cancellation_reason,
                'refund_processed': refund_processed,
            },
            customer_id=order.customer.id,
            restaurant_id=order.restaurant.id,
            include_admin=True,
            metadata={
                'user_id': request.user.id,
                'rejection_reason': cancellation_reason,
                'refund_processed': refund_processed,
            }
        )
        
        # Track rejection rate for admin alerts (if high rejection rate)
        from apps.restaurants.models import RestaurantAlert
        from datetime import timedelta
        recent_rejections = Order.objects.filter(
            restaurant=order.restaurant,
            status=Order.Status.CANCELLED,
            cancellation_reason__icontains='declined',
            cancelled_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        if recent_rejections >= 5:  # Alert if 5+ rejections in 24h
            EventBroadcastService.broadcast_to_admin(
                event_type='restaurant.high_rejection_rate',
                aggregate_type='Restaurant',
                aggregate_id=str(order.restaurant.id),
                payload={
                    'restaurant_id': order.restaurant.id,
                    'restaurant_name': order.restaurant.name,
                    'rejection_count': recent_rejections,
                    'period_hours': 24,
                }
            )
        
        return Response(order_data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    def start_preparing(self, request, pk=None):
        """Restaurant starts preparing order"""
        order = self.get_object()
        
        if order.status != Order.Status.ACCEPTED:
            return Response({'error': 'Order must be accepted first'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = Order.Status.PREPARING
        order.preparing_at = timezone.now()
        order.save()
        
        reserve_inventory_for_order(order, actor=request.user)
        self.broadcast_order_updated(order)
        self.evaluate_sla(order)
        return Response(OrderSerializer(order, context={'request': request, 'include_internal': True}).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    @transaction.atomic
    def mark_ready(self, request, pk=None):
        """Restaurant marks order as ready"""
        order = self.get_object()
        
        if order.status != Order.Status.PREPARING:
            return Response({'error': 'Order must be preparing'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = Order.Status.READY
        order.ready_at = timezone.now()
        order.save()
        
        self.broadcast_order_updated(order, event_type='order.updated', include_internal=True)
        self.evaluate_sla(order)
        return Response(OrderSerializer(order, context={'request': request, 'include_internal': True}).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    @transaction.atomic
    def mark_assigned(self, request, pk=None):
        """Mark order as assigned to delivery"""
        order = self.get_object()
        if order.status not in [Order.Status.READY, Order.Status.PREPARING]:
            return Response({'error': 'Order must be ready or preparing to assign'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.ASSIGNED
        order.save(update_fields=['status', 'updated_at'])
        self.broadcast_order_updated(order, event_type='order.updated', include_internal=True)
        self.evaluate_sla(order)
        return Response(OrderSerializer(order, context={'request': request, 'include_internal': True}).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    @transaction.atomic
    def mark_picked_up(self, request, pk=None):
        """Mark order as picked up by courier"""
        order = self.get_object()
        if order.status not in [Order.Status.READY, Order.Status.ASSIGNED]:
            return Response({'error': 'Order must be ready or assigned before pickup'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.PICKED_UP
        order.picked_up_at = timezone.now()
        order.save(update_fields=['status', 'picked_up_at'])
        self.broadcast_order_updated(order, event_type='order.updated', include_internal=True)
        return Response(OrderSerializer(order, context={'request': request, 'include_internal': True}).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    @transaction.atomic
    def mark_completed(self, request, pk=None):
        """Mark order as delivered/completed"""
        order = self.get_object()
        if order.status not in [Order.Status.OUT_FOR_DELIVERY, Order.Status.PICKED_UP, Order.Status.READY]:
            return Response({'error': 'Order must be out for delivery or picked up'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.Status.DELIVERED
        order.delivered_at = timezone.now()
        order.actual_delivery_time = order.delivered_at
        order.save(update_fields=['status', 'delivered_at', 'actual_delivery_time'])
        
        # Create order.completed event
        order_data = OrderSerializer(order, context={'request': request, 'include_internal': True}).data
        self.broadcast_order_updated(order, event_type='order.completed', include_internal=True)
        
        # Capture payment if deferred (workflow 5)
        from apps.payments.models import Payment
        if hasattr(order, 'payment') and order.payment.status == Payment.Status.PENDING:
            # Capture deferred payment
            try:
                payment = order.payment
                payment.status = Payment.Status.COMPLETED
                payment.processed_at = timezone.now()
                if not payment.transaction_id:
                    payment.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
                payment.save()
                
                # Broadcast payment.captured event
                EventBroadcastService.broadcast_to_multiple(
                    event_type='payment.captured',
                    aggregate_type='Payment',
                    aggregate_id=str(payment.id),
                    payload={'payment_id': payment.id, 'order_id': order.id},
                    customer_id=order.customer.id,
                    restaurant_id=order.restaurant.id,
                    include_admin=True,
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to capture payment for order {order.id}: {str(e)}")
        
        return Response(order_data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    def update_prep_time(self, request, pk=None):
        """Override preparation time for SLA tracking"""
        order = self.get_object()
        minutes = request.data.get('minutes')
        try:
            minutes = int(minutes)
        except (TypeError, ValueError):
            return Response({'error': 'minutes must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
        order.prep_time_override_minutes = minutes
        order.estimated_preparation_time = minutes
        order.save(update_fields=['prep_time_override_minutes', 'estimated_preparation_time'])
        self.broadcast_order_updated(order)
        self.evaluate_sla(order)
        return Response(OrderSerializer(order, context={'request': request, 'include_internal': True}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    def add_kitchen_note(self, request, pk=None):
        """Add kitchen/internal cooking notes"""
        order = self.get_object()
        kitchen_note = request.data.get('note', '').strip()
        internal_note = request.data.get('internal_note', '').strip()
        if kitchen_note:
            order.kitchen_notes = kitchen_note
        if internal_note:
            order.internal_cooking_notes = internal_note
        order.save(update_fields=['kitchen_notes', 'internal_cooking_notes'])
        self.broadcast_order_updated(order)
        return Response(OrderSerializer(order, context={'request': request, 'include_internal': True}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    def mark_priority(self, request, pk=None):
        """Toggle order priority (RUSH/VIP)"""
        order = self.get_object()
        priority = request.data.get('priority_tag', Order.PriorityTag.NORMAL)
        if priority not in Order.PriorityTag.values:
            return Response({'error': 'Invalid priority_tag'}, status=status.HTTP_400_BAD_REQUEST)
        order.priority_tag = priority
        order.save(update_fields=['priority_tag'])
        self.broadcast_order_updated(order)
        if priority != Order.PriorityTag.NORMAL:
            self.create_restaurant_alert(
                order,
                alert_type=RestaurantAlert.AlertType.SYSTEM,
                severity=RestaurantAlert.Severity.WARNING,
                title=f"{priority.title()} order #{order.order_number}",
                message='Order flagged for priority handling',
                metadata={'order_id': order.id, 'priority': priority},
            )
        return Response(OrderSerializer(order, context={'request': request, 'include_internal': True}).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    def combine_with(self, request, pk=None):
        """Combine orders going to the same address"""
        order = self.get_object()
        target_id = request.data.get('target_order_id')
        if not target_id:
            return Response({'error': 'target_order_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            target_order = Order.objects.get(
                id=target_id,
                restaurant=order.restaurant,
                is_deleted=False
            )
        except Order.DoesNotExist:
            return Response({'error': 'Target order not found for this restaurant'}, status=status.HTTP_404_NOT_FOUND)
        if target_order.id == order.id:
            return Response({'error': 'Cannot combine order with itself'}, status=status.HTTP_400_BAD_REQUEST)
        if order.delivery_address_id != target_order.delivery_address_id:
            return Response({'error': 'Orders must share the same delivery address'}, status=status.HTTP_400_BAD_REQUEST)
        order.combined_parent = target_order
        order.save(update_fields=['combined_parent'])
        self.broadcast_order_updated(order)
        self.broadcast_order_updated(target_order)
        return Response({
            'source_order': OrderSerializer(order, context={'request': request, 'include_internal': True}).data,
            'target_order': OrderSerializer(target_order, context={'request': request, 'include_internal': True}).data,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsRestaurantOwner])
    def print_docket(self, request, pk=None):
        """Increment print count when docket printed"""
        order = self.get_object()
        order.print_count += 1
        order.save(update_fields=['print_count'])
        self.broadcast_order_updated(order)
        return Response(OrderSerializer(order, context={'request': request, 'include_internal': True}).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def cancel(self, request, pk=None):
        """Cancel order and initiate refund if paid"""
        order = self.get_object()
        
        if order.customer != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if order.status in [Order.Status.DELIVERED, Order.Status.CANCELLED]:
            return Response({'error': 'Order cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        
        cancellation_reason = request.data.get('reason', '').strip()
        if not cancellation_reason:
            return Response({'error': 'Cancellation reason is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = Order.Status.CANCELLED
        order.cancellation_reason = cancellation_reason
        order.cancelled_at = timezone.now()
        order.save()
        
        # Auto-refund if payment was made
        from apps.payments.models import Payment
        if hasattr(order, 'payment') and order.payment.status == Payment.Status.COMPLETED:
            from apps.payments.models import Refund
            refund = Refund.objects.create(
                payment=order.payment,
                order=order,
                amount=order.total_amount,
                reason=f"Order cancellation: {cancellation_reason}",
                status=Refund.Status.PROCESSING
            )
            
            # Auto-process refund (in production, integrate with payment gateway)
            refund.status = Refund.Status.COMPLETED
            refund.refund_transaction_id = f"REF-{uuid.uuid4().hex[:12].upper()}"
            refund.processed_at = timezone.now()
            refund.save()
            
            # Update payment
            order.payment.status = Payment.Status.REFUNDED
            order.payment.refund_amount = refund.amount
            order.payment.refund_transaction_id = refund.refund_transaction_id
            order.payment.refunded_at = timezone.now()
            order.payment.save()
            
            # Credit to wallet if applicable
            if order.payment.method_type == Payment.PaymentMethodType.WALLET:
                from apps.payments.models import Wallet, WalletTransaction
                wallet, _ = Wallet.objects.get_or_create(
                    user=order.customer,
                    defaults={'balance': 0.00, 'currency': 'INR'}
                )
                from decimal import Decimal
                wallet.balance += Decimal(str(refund.amount))
                wallet.save()
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type=WalletTransaction.TransactionType.CREDIT,
                    source=WalletTransaction.TransactionSource.REFUND,
                    amount=Decimal(str(refund.amount)),
                    balance_after=wallet.balance,
                    description=f'Refund for cancelled order {order.order_number}',
                    refund=refund,
                    order=order
                )
        
        # Broadcast order cancellation
        self.broadcast_order_updated(order)
        
        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data)
    
    def broadcast_order_updated(self, order, event_type='order.updated', include_internal=False):
        """Broadcast order updated event using EventBroadcastService"""
        order_data = self._serialize_order(order, include_internal=include_internal)
        EventBroadcastService.broadcast_to_multiple(
            event_type=event_type,
            aggregate_type='Order',
            aggregate_id=str(order.id),
            payload=order_data,
            customer_id=order.customer.id,
            restaurant_id=order.restaurant.id,
            include_admin=True,
        )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def courier(self, request, pk=None):
        """Get courier details for order"""
        order = self.get_object()
        
        # Check permission
        if order.customer != request.user and request.user.role not in ['ADMIN', 'RESTAURANT']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if not order.courier:
            return Response({'error': 'No courier assigned yet'}, status=status.HTTP_404_NOT_FOUND)
        
        courier_data = {
            'id': order.courier.id,
            'name': f"{order.courier.first_name} {order.courier.last_name}".strip(),
            'phone': order.courier_phone or order.courier.phone,
            'rating': getattr(order.courier, 'delivery_rating', 4.5),  # Mock rating
        }
        
        return Response(courier_data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def eta(self, request, pk=None):
        """Get estimated delivery time"""
        order = self.get_object()
        
        if order.customer != request.user and request.user.role not in ['ADMIN', 'RESTAURANT']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        from datetime import timedelta
        
        # Calculate ETA based on order status
        if order.status == Order.Status.DELIVERED:
            eta_minutes = 0
            estimated_time = order.delivered_at
        elif order.status in [Order.Status.OUT_FOR_DELIVERY, Order.Status.PICKED_UP]:
            # Estimate remaining time (mock - in production, use real-time location)
            eta_minutes = 15  # Mock 15 minutes remaining
            estimated_time = timezone.now() + timedelta(minutes=eta_minutes)
        elif order.status == Order.Status.READY:
            eta_minutes = 20  # Estimated time from ready to delivery
            estimated_time = timezone.now() + timedelta(minutes=eta_minutes)
        elif order.status == Order.Status.PREPARING:
            # Preparation time + delivery time
            prep_time = order.estimated_preparation_time or 20
            delivery_time = order.restaurant.delivery_time_minutes or 30
            eta_minutes = prep_time + delivery_time
            estimated_time = timezone.now() + timedelta(minutes=eta_minutes)
        else:
            eta_minutes = order.restaurant.delivery_time_minutes or 30
            estimated_time = timezone.now() + timedelta(minutes=eta_minutes)
        
        return Response({
            'eta_minutes': eta_minutes,
            'estimated_time': estimated_time.isoformat() if estimated_time else None,
            'status': order.status,
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def generate_delivery_otp(self, request, pk=None):
        """Generate OTP for delivery verification"""
        order = self.get_object()
        
        if order.customer != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        import random
        otp = str(random.randint(100000, 999999))
        order.delivery_otp = otp
        order.save()
        
        # In production, send OTP via SMS
        return Response({
            'message': 'OTP generated successfully',
            'otp': otp,  # In production, don't return OTP in response
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def verify_delivery_otp(self, request, pk=None):
        """Verify delivery OTP"""
        order = self.get_object()
        otp = request.data.get('otp')
        
        if order.customer != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if not otp:
            return Response({'error': 'OTP is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if order.delivery_otp == otp:
            order.delivery_otp_verified = True
            order.save()
            return Response({'message': 'OTP verified successfully', 'verified': True})
        else:
            return Response({'error': 'Invalid OTP', 'verified': False}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def timeline(self, request, pk=None):
        """Get order timeline"""
        order = self.get_object()
        
        if order.customer != request.user and request.user.role not in ['ADMIN', 'RESTAURANT']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        timeline = []
        
        timeline.append({
            'status': 'PENDING',
            'label': 'Order Placed',
            'timestamp': order.created_at.isoformat(),
            'completed': True,
        })
        
        if order.accepted_at:
            timeline.append({
                'status': 'ACCEPTED',
                'label': 'Order Accepted',
                'timestamp': order.accepted_at.isoformat(),
                'completed': True,
            })
        
        if order.preparing_at:
            timeline.append({
                'status': 'PREPARING',
                'label': 'Preparing Your Order',
                'timestamp': order.preparing_at.isoformat(),
                'completed': order.status in [Order.Status.READY, Order.Status.ASSIGNED, Order.Status.PICKED_UP, Order.Status.OUT_FOR_DELIVERY, Order.Status.DELIVERED],
            })
        
        if order.ready_at:
            timeline.append({
                'status': 'READY',
                'label': 'Ready for Pickup',
                'timestamp': order.ready_at.isoformat(),
                'completed': order.status in [Order.Status.ASSIGNED, Order.Status.PICKED_UP, Order.Status.OUT_FOR_DELIVERY, Order.Status.DELIVERED],
            })
        
        if order.picked_up_at:
            timeline.append({
                'status': 'PICKED_UP',
                'label': 'Picked Up by Courier',
                'timestamp': order.picked_up_at.isoformat(),
                'completed': True,
            })
        
        if order.status == Order.Status.OUT_FOR_DELIVERY:
            timeline.append({
                'status': 'OUT_FOR_DELIVERY',
                'label': 'Out for Delivery',
                'timestamp': timezone.now().isoformat(),
                'completed': False,
            })
        
        if order.delivered_at:
            timeline.append({
                'status': 'DELIVERED',
                'label': 'Delivered',
                'timestamp': order.delivered_at.isoformat(),
                'completed': True,
            })
        
        return Response({'timeline': timeline})
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def invoice(self, request, pk=None):
        """Generate invoice PDF"""
        order = self.get_object()
        
        if order.customer != request.user and request.user.role not in ['ADMIN', 'RESTAURANT']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # In production, use reportlab to generate PDF
        # For now, return invoice data as JSON
        invoice_data = {
            'order_number': order.order_number,
            'date': order.created_at.isoformat(),
            'customer': {
                'name': f"{order.customer.first_name} {order.customer.last_name}".strip(),
                'email': order.customer.email,
                'phone': order.customer.phone,
            },
            'restaurant': {
                'name': order.restaurant.name,
                'address': order.restaurant.address,
                'phone': order.restaurant.phone,
            },
            'items': [
                {
                    'name': item.name,
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'total_price': str(item.total_price),
                }
                for item in order.items.all()
            ],
            'subtotal': str(order.subtotal),
            'tax_amount': str(order.tax_amount),
            'delivery_fee': str(order.delivery_fee),
            'tip_amount': str(order.tip_amount),
            'discount_amount': str(order.discount_amount),
            'total_amount': str(order.total_amount),
            'payment_method': order.payment.method_type if hasattr(order, 'payment') else 'CASH',
            'transaction_id': order.payment.transaction_id if hasattr(order, 'payment') and order.payment.transaction_id else None,
        }
        
        return Response(invoice_data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def repeat(self, request, pk=None):
        """Repeat a previous order"""
        original_order = self.get_object()
        
        if original_order.customer != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Create new order with same items
        new_order = Order.objects.create(
            customer=request.user,
            restaurant=original_order.restaurant,
            delivery_address=original_order.delivery_address,
            order_number=f"ORD-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            order_type=original_order.order_type,
            subtotal=original_order.subtotal,
            tax_amount=original_order.tax_amount,
            delivery_fee=original_order.delivery_fee,
            tip_amount=original_order.tip_amount,
            discount_amount=0,  # Reset discount
            total_amount=original_order.subtotal + original_order.tax_amount + original_order.delivery_fee + original_order.tip_amount,
            contactless_delivery=original_order.contactless_delivery,
        )
        
        # Copy order items
        for original_item in original_order.items.all():
            OrderItem.objects.create(
                order=new_order,
                menu_item=original_item.menu_item,
                name=original_item.name,
                description=original_item.description,
                quantity=original_item.quantity,
                unit_price=original_item.unit_price,
                selected_modifiers=original_item.selected_modifiers,
            )
        
        serializer = OrderSerializer(new_order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def transaction(self, request, pk=None):
        """Get transaction details"""
        order = self.get_object()
        
        if order.customer != request.user and request.user.role not in ['ADMIN', 'RESTAURANT']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        if not hasattr(order, 'payment'):
            return Response({'error': 'No payment found for this order'}, status=status.HTTP_404_NOT_FOUND)
        
        payment = order.payment
        transaction_data = {
            'transaction_id': payment.transaction_id,
            'payment_method': payment.method_type,
            'amount': str(payment.amount),
            'currency': payment.currency,
            'status': payment.status,
            'processed_at': payment.processed_at.isoformat() if payment.processed_at else None,
            'gateway_response': payment.gateway_response,
            'refund_amount': str(payment.refund_amount) if payment.refund_amount else None,
            'refund_transaction_id': payment.refund_transaction_id if payment.refund_transaction_id else None,
            'refunded_at': payment.refunded_at.isoformat() if payment.refunded_at else None,
        }
        
        return Response(transaction_data)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _filter_restaurant_queryset(self, request):
        queryset = self.get_queryset()
        restaurant_id = request.query_params.get('restaurant_id')
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        return queryset

    def _get_restaurant_instance(self, request, queryset):
        restaurant_id = request.query_params.get('restaurant_id') or request.data.get('restaurant_id')
        if request.user.role == 'ADMIN':
            if not restaurant_id:
                return None
            return Restaurant.objects.filter(id=restaurant_id).first()
        owner_restaurants = request.user.restaurants.all().order_by('id')
        if restaurant_id:
            return owner_restaurants.filter(id=restaurant_id).first()
        if queryset:
            first_order = queryset.first()
            if first_order:
                return first_order.restaurant
        return owner_restaurants.first()

    def _queue_metrics(self, queryset):
        today = timezone.now().date()
        metrics = {
            'pending': queryset.filter(status=Order.Status.PENDING).count(),
            'preparing': queryset.filter(status=Order.Status.PREPARING).count(),
            'ready': queryset.filter(status=Order.Status.READY).count(),
            'out_for_delivery': queryset.filter(status__in=[Order.Status.PICKED_UP, Order.Status.OUT_FOR_DELIVERY]).count(),
            'completed_today': queryset.filter(status=Order.Status.DELIVERED, delivered_at__date=today).count(),
            'today_orders': queryset.filter(created_at__date=today).count(),
        }
        metrics['avg_prep_time'] = self._average_prep_time_minutes(queryset)
        return metrics

    def _average_prep_time_minutes(self, queryset):
        durations = []
        recent = queryset.filter(preparing_at__isnull=False, ready_at__isnull=False).order_by('-ready_at')[:25]
        for order in recent:
            durations.append((order.ready_at - order.preparing_at).total_seconds() / 60)
        if not durations:
            return 0
        return round(sum(durations) / len(durations), 1)

    def _build_timer_payload(self, orders):
        payload = []
        now_time = timezone.now()
        for order in orders:
            start = order.preparing_at or order.accepted_at or order.created_at
            if not start:
                continue
            elapsed = (now_time - start).total_seconds() / 60
            payload.append({
                'order_id': order.id,
                'status': order.status,
                'elapsed_minutes': round(elapsed, 1),
                'priority_tag': order.priority_tag,
            })
        return payload

    def _build_kds_payload(self, orders):
        now_time = timezone.now()
        serialized = []
        orders = orders.select_related('customer').prefetch_related('items')
        for order in orders[:20]:
            start = order.preparing_at or order.accepted_at or order.created_at
            elapsed = ((now_time - start).total_seconds() / 60) if start else 0
            serialized.append({
                'order_id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'priority_tag': order.priority_tag,
                'elapsed_minutes': round(max(elapsed, 0), 1),
                'special_instructions': order.special_instructions,
                'customer_name': order.customer.get_short_name() if order.customer else '',
                'items': [
                    {
                        'id': item.id,
                        'name': item.name, 
                        'quantity': item.quantity,
                        'selected_modifiers': item.selected_modifiers
                    }
                    for item in order.items.all()
                ],
            })
        return serialized

    def _sla_watchlist(self, queryset):
        watchlist = []
        statuses = [Order.Status.ACCEPTED, Order.Status.PREPARING, Order.Status.READY]
        now_time = timezone.now()
        for order in queryset.filter(status__in=statuses).order_by('created_at'):
            reference = order.preparing_at or order.accepted_at or order.created_at
            if not reference:
                continue
            threshold = self._sla_threshold(order)
            elapsed = (now_time - reference).total_seconds() / 60
            remaining = threshold - elapsed
            if remaining <= 5:
                watchlist.append({
                    'order_id': order.id,
                    'status': order.status,
                    'priority_tag': order.priority_tag,
                    'remaining_minutes': round(max(remaining, 0), 1),
                    'elapsed_minutes': round(elapsed, 1),
                })
        return watchlist[:10]

    def _sla_threshold(self, order):
        settings = getattr(order.restaurant, 'settings', None)
        return getattr(settings, 'sla_threshold_minutes', 35)

    def evaluate_sla(self, order):
        reference = order.preparing_at or order.accepted_at or order.created_at
        if not reference:
            return
        threshold = self._sla_threshold(order)
        elapsed = (timezone.now() - reference).total_seconds() / 60
        breached = elapsed > threshold
        if breached and not order.sla_breached:
            order.sla_breached = True
            order.sla_breach_reason = f"SLA exceeded by {int(elapsed - threshold)} mins"
            order.save(update_fields=['sla_breached', 'sla_breach_reason'])
            alert = self.create_restaurant_alert(
                order,
                alert_type=RestaurantAlert.AlertType.SLA_BREACH,
                severity=RestaurantAlert.Severity.CRITICAL,
                title=f"SLA breach for order #{order.order_number}",
                message=order.sla_breach_reason,
                metadata={'order_id': order.id, 'elapsed_minutes': round(elapsed, 1)},
            )
            self.broadcast_order_updated(order, event_type='sla_breach')
        elif not breached and order.sla_breached:
            order.sla_breached = False
            order.sla_breach_reason = ''
            order.save(update_fields=['sla_breached', 'sla_breach_reason'])

    def create_restaurant_alert(self, order, alert_type, severity, title, message, metadata=None):
        alert = RestaurantAlert.objects.create(
            restaurant=order.restaurant,
            order=order,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            metadata=metadata or {},
        )
        self.broadcast_alert(alert)
        return alert

    def broadcast_alert(self, alert):
        payload = RestaurantAlertSerializer(alert).data
        self._send_to_group(f'restaurant_{alert.restaurant_id}', 'restaurant_alert', payload)
        self._send_to_group('admin', 'restaurant_alert', payload)

    def _serialize_order(self, order, include_internal=False):
        request = getattr(self, 'request', None)
        serializer = OrderSerializer(
            order,
            context={'request': request, 'include_internal': include_internal}
        )
        return serializer.data

    def _send_to_group(self, group_name, event_type, data):
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': event_type,
                'data': data,
                'event_id': str(uuid.uuid4()),
            }
        )


class ReviewViewSet(viewsets.ModelViewSet):
    """Review viewset"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        restaurant_id = self.request.query_params.get('restaurant_id')
        order_id = self.request.query_params.get('order_id')
        
        queryset = Review.objects.filter(is_deleted=False)
        
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id, is_approved=True)
        elif order_id:
            queryset = queryset.filter(order_id=order_id)
        else:
            # Default: show user's reviews or all approved reviews
            if self.request.user.role == 'RESTAURANT':
                queryset = queryset.filter(restaurant__owner=self.request.user, is_approved=True)
            elif self.request.user.role != 'ADMIN':
                queryset = queryset.filter(customer=self.request.user)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_images(self, request, pk=None):
        """Upload review images"""
        review = self.get_object()
        
        if review.customer != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        images = request.FILES.getlist('images')
        if not images:
            return Response({'error': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        image_urls = []
        for image in images:
            # In production, upload to S3/Cloudinary
            from django.core.files.storage import default_storage
            filename = default_storage.save(f'reviews/{review.id}/{image.name}', image)
            url = default_storage.url(filename)
            image_urls.append(request.build_absolute_uri(url))
        
        review.images = review.images + image_urls if review.images else image_urls
        review.save()
        
        return Response({'images': image_urls})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reply(self, request, pk=None):
        """Restaurant reply to review"""
        review = self.get_object()
        
        # Check if user is restaurant owner
        if review.restaurant.owner != request.user and request.user.role != 'ADMIN':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        reply_text = request.data.get('reply', '').strip()
        if not reply_text:
            return Response({'error': 'Reply text is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        review.restaurant_reply = reply_text
        review.restaurant_replied_at = timezone.now()
        review.save()
        
        serializer = self.get_serializer(review)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def flag(self, request, pk=None):
        """Flag inappropriate review"""
        review = self.get_object()
        
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'error': 'Flag reason is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        review.is_flagged = True
        review.flagged_reason = reason
        review.save()
        
        # In production, notify admins
        return Response({'message': 'Review flagged for moderation'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        """Approve review (admin/restaurant only)"""
        if request.user.role not in ['ADMIN', 'RESTAURANT']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        review = self.get_object()
        review.is_approved = True
        review.is_flagged = False
        review.save()
        
        serializer = self.get_serializer(review)
        return Response(serializer.data)


class ItemReviewViewSet(viewsets.ModelViewSet):
    """Item review viewset"""
    serializer_class = ItemReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ItemReview.objects.filter(is_deleted=False)

