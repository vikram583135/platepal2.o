"""
Rider Assignment Service
Handles automatic rider assignment when order is accepted
"""
import logging
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Delivery, DeliveryOffer, RiderLocation, RiderShift, RiderSettings
from .services import (
    find_nearby_riders,
    create_delivery_offer,
    calculate_distance,
    calculate_earnings_breakdown,
    calculate_surge_multiplier,
    check_auto_accept_rules
)
from apps.accounts.models import User
from apps.orders.models import Order
from apps.events.broadcast import EventBroadcastService

logger = logging.getLogger(__name__)


class RiderAssignmentService:
    """Service for automatically assigning riders to deliveries"""
    
    @staticmethod
    @transaction.atomic
    def assign_rider_to_order(order: Order, radius_km: int = 5, max_riders: int = 10) -> Optional[Delivery]:
        """
        Automatically assign a rider to an order when it's accepted.
        Creates delivery offers for candidate riders.
        
        Args:
            order: Order object
            radius_km: Search radius in kilometers (default: 5 km)
            max_riders: Maximum number of riders to offer to (default: 10)
        
        Returns:
            Delivery object if assigned, None otherwise
        """
        # Create or get delivery object
        delivery, created = Delivery.objects.get_or_create(
            order=order,
            defaults={
                'pickup_address': order.restaurant.address,
                'pickup_latitude': order.restaurant.latitude,
                'pickup_longitude': order.restaurant.longitude,
                'delivery_address': order.delivery_address,
                'delivery_latitude': order.delivery_address.latitude if order.delivery_address else None,
                'delivery_longitude': order.delivery_address.longitude if order.delivery_address else None,
                'status': Delivery.Status.PENDING,
            }
        )
        
        if not order.delivery_address or not order.delivery_address.latitude or not order.delivery_address.longitude:
            logger.warning(f"Order {order.id} missing delivery address coordinates")
            return None
        
        # Find nearby riders
        pickup_lat = float(order.restaurant.latitude or 0)
        pickup_lng = float(order.restaurant.longitude or 0)
        
        if not pickup_lat or not pickup_lng:
            logger.warning(f"Order {order.id} restaurant missing coordinates")
            return None
        
        nearby_riders_list = find_nearby_riders(
            delivery_lat=pickup_lat,
            delivery_lng=pickup_lng,
            radius_km=radius_km,
            max_riders=max_riders
        )
        
        if not nearby_riders_list:
            logger.info(f"No nearby riders found for order {order.id}")
            # Escalate: expand radius or increase incentive
            return RiderAssignmentService._escalate_assignment(delivery, order, radius_km * 2)
        
        # Calculate surge multiplier
        surge_multiplier = calculate_surge_multiplier(pickup_lat, pickup_lng, radius_km)
        
        # Calculate distance and earnings
        delivery_distance = calculate_distance(
            pickup_lat,
            pickup_lng,
            float(order.delivery_address.latitude),
            float(order.delivery_address.longitude)
        )
        
        earnings_breakdown = calculate_earnings_breakdown(
            base_fee=Decimal('5.00'),  # Default base fee
            distance_km=delivery_distance,
            time_minutes=30,  # Estimated time
            surge_multiplier=surge_multiplier,
            tip=order.tip_amount or Decimal('0.00')
        )
        
        estimated_earnings = Decimal(str(earnings_breakdown['total_earnings']))
        
        # Sort riders by distance and rating
        nearby_riders_list.sort(key=lambda x: x['distance_km'])
        
        # Create offers for top candidates
        offers_created = 0
        for rider_info in nearby_riders_list[:max_riders]:
            rider = rider_info['rider']
            
            # Check if rider is available (active shift, no active delivery)
            active_shift = RiderShift.objects.filter(
                rider=rider,
                status__in=[RiderShift.Status.ACTIVE]
            ).first()
            
            if not active_shift:
                continue  # Skip riders without active shifts
            
            active_delivery = Delivery.objects.filter(
                rider=rider,
                status__in=[Delivery.Status.ACCEPTED, Delivery.Status.PICKED_UP, Delivery.Status.IN_TRANSIT]
            ).first()
            
            if active_delivery:
                continue  # Skip riders with active deliveries
            
            # Check auto-accept rules
            offer = create_delivery_offer(
                delivery=delivery,
                rider=rider,
                estimated_earnings=estimated_earnings,
                distance_km=delivery_distance,
                expires_in_minutes=5  # 5 minute expiry
            )
            
            # Update offer with surge info
            if surge_multiplier > 1.0:
                offer.is_surge = True
                offer.surge_multiplier = surge_multiplier
                offer.save()
            
            # Check auto-accept
            if check_auto_accept_rules(rider, offer):
                # Auto-accept the offer
                try:
                    offer.status = DeliveryOffer.Status.ACCEPTED
                    offer.accepted_at = timezone.now()
                    offer.save()
                    
                    delivery.rider = rider
                    delivery.status = Delivery.Status.ACCEPTED
                    delivery.save()
                    
                    order.status = Order.Status.ASSIGNED
                    order.courier = rider
                    order.save()
                    
                    # Broadcast assignment
                    delivery_data = {'id': delivery.id, 'order_id': order.id, 'rider_id': rider.id}
                    EventBroadcastService.broadcast_to_multiple(
                        event_type='delivery.assigned',
                        aggregate_type='Delivery',
                        aggregate_id=str(delivery.id),
                        payload=delivery_data,
                        customer_id=order.customer.id,
                        restaurant_id=order.restaurant.id,
                        rider_id=rider.id,
                        include_admin=True,
                    )
                    
                    logger.info(f"Auto-assigned rider {rider.id} to order {order.id}")
                    return delivery
                except Exception as e:
                    logger.error(f"Failed to auto-accept offer {offer.id}: {str(e)}")
            
            # Broadcast job_offer to rider via WebSocket
            EventBroadcastService.broadcast_to_rider(
                rider_id=rider.id,
                event_type='job_offer',
                aggregate_type='DeliveryOffer',
                aggregate_id=str(offer.id),
                payload={
                    'offer_id': offer.id,
                    'delivery_id': delivery.id,
                    'order_id': order.id,
                    'estimated_earnings': float(estimated_earnings),
                    'distance_km': float(delivery_distance),
                    'expires_at': offer.expires_at.isoformat(),
                    'time_remaining_seconds': int((offer.expires_at - timezone.now()).total_seconds()),
                    'is_surge': offer.is_surge,
                    'surge_multiplier': float(surge_multiplier) if offer.is_surge else 1.0,
                }
            )
            
            offers_created += 1
        
        if offers_created == 0:
            # No riders available, escalate
            return RiderAssignmentService._escalate_assignment(delivery, order, radius_km * 2)
        
        logger.info(f"Created {offers_created} delivery offers for order {order.id}")
        return delivery
    
    @staticmethod
    def _escalate_assignment(delivery: Delivery, order: Order, expanded_radius: int) -> Optional[Delivery]:
        """
        Escalate rider assignment: expand radius, increase incentive, or fallback to manual.
        
        Args:
            delivery: Delivery object
            order: Order object
            expanded_radius: Expanded search radius
        
        Returns:
            Delivery if assigned, None otherwise
        """
        # Try with expanded radius
        if expanded_radius <= 20:  # Max 20 km radius
            logger.info(f"Escalating assignment for order {order.id} with radius {expanded_radius}km")
            return RiderAssignmentService.assign_rider_to_order(
                order=order,
                radius_km=expanded_radius,
                max_riders=15  # More riders
            )
        
        # If still no riders, mark for admin manual assignment
        logger.warning(f"No riders available for order {order.id} after escalation")
        EventBroadcastService.broadcast_to_admin(
            event_type='delivery.no_rider_available',
            aggregate_type='Delivery',
            aggregate_id=str(delivery.id),
            payload={
                'delivery_id': delivery.id,
                'order_id': order.id,
                'order_number': order.order_number,
                'restaurant_id': order.restaurant.id,
                'message': 'No riders available after escalation, requires manual assignment',
            }
        )
        
        # Mark order as failed if timeout (e.g., after 30 minutes)
        # This would be handled by a Celery task in production
        return None

