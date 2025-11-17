"""
Services for deliveries app - Business logic and helper functions
"""
import math
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from .models import (
    Delivery, DeliveryOffer, RiderLocation, RiderSettings,
    OfflineAction, AutoAcceptRule, TripLog
)
from apps.accounts.models import User
from apps.orders.models import Order


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two points in kilometers using Haversine formula
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance


def calculate_eta(distance_km, avg_speed_kmh=30):
    """
    Calculate estimated time of arrival based on distance
    
    Args:
        distance_km: Distance in kilometers
        avg_speed_kmh: Average speed in km/h (default: 30 km/h)
    
    Returns:
        Estimated time in minutes
    """
    if distance_km <= 0 or avg_speed_kmh <= 0:
        return 0
    
    time_hours = distance_km / avg_speed_kmh
    time_minutes = int(time_hours * 60)
    
    return time_minutes


def generate_navigation_deep_link(pickup_lat, pickup_lng, drop_lat, drop_lng, nav_app='GOOGLE_MAPS'):
    """
    Generate navigation deep link based on preferred app
    
    Args:
        pickup_lat, pickup_lng: Pickup coordinates
        drop_lat, drop_lng: Drop coordinates
        nav_app: Navigation app preference ('GOOGLE_MAPS', 'WAZE', 'APPLE_MAPS')
    
    Returns:
        Deep link URL string
    """
    if nav_app == 'GOOGLE_MAPS':
        return f"https://www.google.com/maps/dir/?api=1&origin={pickup_lat},{pickup_lng}&destination={drop_lat},{drop_lng}&travelmode=driving"
    elif nav_app == 'WAZE':
        return f"https://waze.com/ul?ll={pickup_lat},{pickup_lng}&navigate=yes"
    elif nav_app == 'APPLE_MAPS':
        return f"http://maps.apple.com/?daddr={drop_lat},{drop_lng}&saddr={pickup_lat},{pickup_lng}"
    else:
        # Default to Google Maps
        return f"https://www.google.com/maps/dir/?api=1&origin={pickup_lat},{pickup_lng}&destination={drop_lat},{drop_lng}&travelmode=driving"


def calculate_earnings_breakdown(base_fee, distance_km, time_minutes, surge_multiplier=1.0, tip=0.0):
    """
    Calculate earnings breakdown for a delivery
    
    Args:
        base_fee: Base delivery fee
        distance_km: Distance in kilometers
        time_minutes: Time taken in minutes
        surge_multiplier: Surge pricing multiplier (default: 1.0)
        tip: Tip amount (default: 0.0)
    
    Returns:
        Dictionary with earnings breakdown
    """
    # Distance fee calculation (example: $1 per km)
    distance_fee = Decimal(str(distance_km)) * Decimal('1.0')
    
    # Time fee calculation (example: $0.10 per minute)
    time_fee = Decimal(str(time_minutes)) * Decimal('0.10')
    
    # Apply surge multiplier to base and distance fees
    base_fee_with_surge = Decimal(str(base_fee)) * Decimal(str(surge_multiplier))
    distance_fee_with_surge = distance_fee * Decimal(str(surge_multiplier))
    
    # Total earnings
    total_earnings = base_fee_with_surge + distance_fee_with_surge + time_fee + Decimal(str(tip))
    
    return {
        'base_fee': float(base_fee_with_surge),
        'distance_fee': float(distance_fee_with_surge),
        'time_fee': float(time_fee),
        'surge_multiplier': float(surge_multiplier),
        'tip_amount': float(tip),
        'total_earnings': float(total_earnings)
    }


def find_nearby_riders(delivery_lat, delivery_lng, radius_km=5, max_riders=10):
    """
    Find nearby riders for a delivery
    
    Args:
        delivery_lat, delivery_lng: Delivery location coordinates
        radius_km: Search radius in kilometers (default: 5 km)
        max_riders: Maximum number of riders to return (default: 10)
    
    Returns:
        QuerySet of nearby riders
    """
    # Get active riders with recent locations
    recent_time = timezone.now() - timedelta(minutes=10)  # Within last 10 minutes
    recent_locations = RiderLocation.objects.filter(
        created_at__gte=recent_time
    ).select_related('rider').distinct('rider')
    
    nearby_riders = []
    for location in recent_locations:
        if location.latitude and location.longitude:
            distance = calculate_distance(
                float(location.latitude),
                float(location.longitude),
                delivery_lat,
                delivery_lng
            )
            
            if distance <= radius_km:
                nearby_riders.append({
                    'rider': location.rider,
                    'distance_km': distance,
                    'latitude': float(location.latitude),
                    'longitude': float(location.longitude)
                })
    
    # Sort by distance and return top riders
    nearby_riders.sort(key=lambda x: x['distance_km'])
    return nearby_riders[:max_riders]


def create_delivery_offer(delivery, rider, estimated_earnings, distance_km, expires_in_minutes=5):
    """
    Create a delivery offer for a rider
    
    Args:
        delivery: Delivery object
        rider: Rider user object
        estimated_earnings: Estimated earnings for the delivery
        distance_km: Distance in kilometers
        expires_in_minutes: Offer expiry time in minutes (default: 5 minutes)
    
    Returns:
        DeliveryOffer object
    """
    from .models import DeliveryOffer
    
    expires_at = timezone.now() + timedelta(minutes=expires_in_minutes)
    
    # Calculate estimated times
    avg_speed_kmh = 30  # Default average speed
    estimated_travel_time = calculate_eta(distance_km, avg_speed_kmh)
    
    estimated_pickup_time = timezone.now() + timedelta(minutes=estimated_travel_time // 2)
    estimated_drop_time = timezone.now() + timedelta(minutes=estimated_travel_time)
    
    offer = DeliveryOffer.objects.create(
        delivery=delivery,
        rider=rider,
        estimated_earnings=estimated_earnings,
        distance_km=distance_km,
        estimated_pickup_time=estimated_pickup_time,
        estimated_drop_time=estimated_drop_time,
        expires_at=expires_at,
        status=DeliveryOffer.Status.SENT,
        sent_at=timezone.now()
    )
    
    # Send notification to rider
    send_delivery_offer_notification(rider, offer)
    
    return offer


def send_delivery_offer_notification(rider, offer):
    """
    Send notification to rider about new delivery offer
    
    Args:
        rider: Rider user object
        offer: DeliveryOffer object
    """
    try:
        from apps.notifications.models import Notification, NotificationPreference
        
        # Check rider's notification preferences
        prefs, created = NotificationPreference.objects.get_or_create(user=rider)
        
        # Check snooze mode
        if prefs.snooze_mode_enabled and prefs.snooze_until:
            if timezone.now() < prefs.snooze_until:
                return  # Don't send if snooze is active
        
        # Check quiet hours
        if prefs.quiet_hours_enabled and prefs.quiet_hours_start and prefs.quiet_hours_end:
            current_time = timezone.now().time()
            if prefs.quiet_hours_start <= prefs.quiet_hours_end:
                if prefs.quiet_hours_start <= current_time <= prefs.quiet_hours_end:
                    return  # Don't send during quiet hours
            else:  # Quiet hours span midnight
                if current_time >= prefs.quiet_hours_start or current_time <= prefs.quiet_hours_end:
                    return  # Don't send during quiet hours
        
        if not prefs.push_delivery_offers:
            return  # Rider has disabled delivery offer notifications
        
        # Create notification
        notification = Notification.objects.create(
            user=rider,
            type=Notification.NotificationType.DELIVERY_OFFER,
            title=f"New Delivery Offer - ${offer.estimated_earnings:.2f}",
            message=f"Delivery offer for ${offer.estimated_earnings:.2f}, {offer.distance_km:.1f} km away",
            data={
                'offer_id': offer.id,
                'delivery_id': offer.delivery.id,
                'estimated_earnings': float(offer.estimated_earnings),
                'distance_km': float(offer.distance_km),
                'expires_at': offer.expires_at.isoformat(),
            },
            sent_via_push=True
        )
        
        # Broadcast via WebSocket if rider is online
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        import uuid
        
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'delivery_{rider.id}',
                {
                    'type': 'new_offer',
                    'data': {
                        'offer_id': offer.id,
                        'delivery_id': offer.delivery.id,
                        'estimated_earnings': float(offer.estimated_earnings),
                        'distance_km': float(offer.distance_km),
                        'expires_at': offer.expires_at.isoformat(),
                        'time_remaining_seconds': int((offer.expires_at - timezone.now()).total_seconds()),
                    },
                    'event_id': str(uuid.uuid4()),
                }
            )
    except Exception as e:
        # Log error but don't fail
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send delivery offer notification: {str(e)}")


def check_auto_accept_rules(rider, offer):
    """
    Check if offer matches rider's auto-accept rules
    
    Args:
        rider: Rider user object
        offer: DeliveryOffer object
    
    Returns:
        True if offer matches auto-accept rules, False otherwise
    """
    try:
        auto_rules = AutoAcceptRule.objects.filter(
            rider=rider,
            is_enabled=True
        ).order_by('-priority')
        
        for rule in auto_rules:
            if rule.matches_offer(offer):
                return True
        
        return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to check auto-accept rules: {str(e)}")
        return False


def optimize_route(deliveries):
    """
    Optimize route for multiple deliveries (simplified TSP algorithm)
    
    Args:
        deliveries: List of Delivery objects
    
    Returns:
        Ordered list of deliveries for optimal route
    """
    if not deliveries or len(deliveries) <= 1:
        return deliveries
    
    # Simple nearest neighbor algorithm
    optimized = []
    remaining = list(deliveries)
    
    # Start from first delivery's pickup location
    if remaining:
        current = remaining.pop(0)
        optimized.append(current)
        
        current_lat = float(current.pickup_latitude) if current.pickup_latitude else 0
        current_lng = float(current.pickup_longitude) if current.pickup_longitude else 0
    
    # Find nearest remaining delivery
    while remaining:
        nearest = None
        nearest_distance = float('inf')
        nearest_index = -1
        
        for i, delivery in enumerate(remaining):
            if delivery.pickup_latitude and delivery.pickup_longitude:
                distance = calculate_distance(
                    current_lat,
                    current_lng,
                    float(delivery.pickup_latitude),
                    float(delivery.pickup_longitude)
                )
                
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest = delivery
                    nearest_index = i
        
        if nearest:
            optimized.append(nearest)
            remaining.pop(nearest_index)
            current_lat = float(nearest.pickup_latitude)
            current_lng = float(nearest.pickup_longitude)
        else:
            break
    
    return optimized


def calculate_surge_multiplier(area_lat, area_lng, radius_km=5):
    """
    Calculate surge multiplier based on demand in area
    
    Args:
        area_lat, area_lng: Area center coordinates
        radius_km: Search radius in kilometers
    
    Returns:
        Surge multiplier (1.0 = no surge, higher = surge pricing)
    """
    try:
        # Count pending deliveries in area (demand)
        recent_time = timezone.now() - timedelta(minutes=30)
        pending_deliveries = Delivery.objects.filter(
            status=Delivery.Status.PENDING,
            created_at__gte=recent_time,
            pickup_latitude__isnull=False,
            pickup_longitude__isnull=False
        )
        
        demand_count = 0
        for delivery in pending_deliveries:
            distance = calculate_distance(
                area_lat,
                area_lng,
                float(delivery.pickup_latitude),
                float(delivery.pickup_longitude)
            )
            if distance <= radius_km:
                demand_count += 1
        
        # Count available riders in area (supply)
        available_riders = RiderLocation.objects.filter(
            created_at__gte=recent_time,
            latitude__isnull=False,
            longitude__isnull=False
        ).select_related('rider').distinct('rider')
        
        supply_count = 0
        for location in available_riders:
            distance = calculate_distance(
                area_lat,
                area_lng,
                float(location.latitude),
                float(location.longitude)
            )
            if distance <= radius_km:
                supply_count += 1
        
        # Calculate surge based on demand/supply ratio
        if supply_count == 0:
            return 2.0  # High surge if no riders available
        elif demand_count == 0:
            return 1.0  # No surge if no demand
        
        ratio = demand_count / supply_count
        
        # Surge multiplier formula: 1.0 + (ratio * 0.5), capped at 3.0
        surge = min(3.0, 1.0 + (ratio * 0.5))
        
        return round(surge, 2)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to calculate surge multiplier: {str(e)}")
        return 1.0


def queue_offline_action(rider, action_type, action_data, resource_id=None):
    """
    Queue an action to be synced when rider comes back online
    
    Args:
        rider: Rider user object
        action_type: ActionType enum value
        action_data: Dictionary with action payload
        resource_id: ID of the resource (optional)
    
    Returns:
        OfflineAction object
    """
    from .models import OfflineAction
    
    action = OfflineAction.objects.create(
        rider=rider,
        action_type=action_type,
        status=OfflineAction.Status.PENDING,
        action_data=action_data,
        resource_id=resource_id or ''
    )
    
    return action


def create_trip_log(delivery, rider, trip_started_at, trip_ended_at=None):
    """
    Create a trip log entry for analytics
    
    Args:
        delivery: Delivery object
        rider: Rider user object
        trip_started_at: Trip start datetime
        trip_ended_at: Trip end datetime (optional)
    
    Returns:
        TripLog object
    """
    from .models import TripLog
    
    # Calculate distance if locations available
    total_distance = 0.0
    if delivery.pickup_latitude and delivery.pickup_longitude and \
       delivery.delivery_latitude and delivery.delivery_longitude:
        total_distance = calculate_distance(
            float(delivery.pickup_latitude),
            float(delivery.pickup_longitude),
            float(delivery.delivery_latitude),
            float(delivery.delivery_longitude)
        )
    
    # Calculate time
    if trip_ended_at:
        duration = trip_ended_at - trip_started_at
        total_time_minutes = int(duration.total_seconds() / 60)
    else:
        total_time_minutes = 0
    
    # Get earnings breakdown
    earnings_breakdown = calculate_earnings_breakdown(
        base_fee=delivery.base_fee,
        distance_km=total_distance,
        time_minutes=total_time_minutes,
        surge_multiplier=1.0,  # Would need to get from offer
        tip=delivery.tip_amount
    )
    
    trip_log = TripLog.objects.create(
        rider=rider,
        delivery=delivery,
        total_distance_km=total_distance,
        total_time_minutes=total_time_minutes,
        trip_started_at=trip_started_at,
        trip_ended_at=trip_ended_at,
        base_fee=earnings_breakdown['base_fee'],
        distance_fee=earnings_breakdown['distance_fee'],
        time_fee=earnings_breakdown['time_fee'],
        surge_multiplier=earnings_breakdown['surge_multiplier'],
        tip_amount=earnings_breakdown['tip_amount'],
        total_earnings=earnings_breakdown['total_earnings']
    )
    
    return trip_log


def mask_phone_number(phone_number):
    """
    Mask phone number for privacy (show only last 4 digits)
    
    Args:
        phone_number: Phone number string
    
    Returns:
        Masked phone number string (e.g., "***-***-1234")
    """
    if not phone_number or len(phone_number) < 4:
        return "***-***-****"
    
    last_four = phone_number[-4:]
    masked = "***-***-" + last_four
    
    return masked


def get_adaptive_location_interval(rider_location, rider_settings):
    """
    Get adaptive location update interval based on movement and battery
    
    Args:
        rider_location: RiderLocation object
        rider_settings: RiderSettings object
    
    Returns:
        Interval in seconds
    """
    base_interval_moving = rider_settings.location_update_interval_moving
    base_interval_idle = rider_settings.location_update_interval_idle
    
    # Adjust based on battery level
    if rider_location.battery_level:
        if rider_location.battery_level < 20:
            # Low battery - reduce frequency
            base_interval_moving *= 2
            base_interval_idle *= 2
        elif rider_location.battery_level < 50:
            # Medium battery - slight increase
            base_interval_moving = int(base_interval_moving * 1.5)
            base_interval_idle = int(base_interval_idle * 1.5)
    
    # Adjust based on location mode
    if rider_settings.location_mode == 'BATTERY_SAVER':
        base_interval_moving *= 2
        base_interval_idle *= 3
    elif rider_settings.location_mode == 'HIGH_ACCURACY':
        base_interval_moving = max(3, int(base_interval_moving * 0.5))
        base_interval_idle = max(10, int(base_interval_idle * 0.5))
    
    # Use moving or idle interval based on movement state
    if rider_location.is_moving:
        return base_interval_moving
    else:
        return base_interval_idle

