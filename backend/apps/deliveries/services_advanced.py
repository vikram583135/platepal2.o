"""
Advanced services for deliveries app
"""
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db import models
from .models import Delivery, RiderShift
try:
    from .models_advanced import (
        RiderAchievement, RiderLevel, MLETAPrediction,
        VoiceCommand, MultiTenantFleet, TenantRider
    )
except ImportError:
    RiderAchievement = RiderLevel = MLETAPrediction = None
    VoiceCommand = MultiTenantFleet = TenantRider = None


def check_and_award_achievements(rider, delivery):
    """
    Check and award achievements based on delivery completion
    
    Args:
        rider: Rider user object
        delivery: Completed delivery object
    """
    if not RiderAchievement:
        return  # Advanced features not available
    
    # Count total deliveries
    total_deliveries = Delivery.objects.filter(
        rider=rider,
        status=Delivery.Status.DELIVERED
    ).count()
    
    # Award milestones
    milestone_achievements = {
        1: RiderAchievement.AchievementType.FIRST_DELIVERY,
        10: RiderAchievement.AchievementType.COMPLETE_10,
        50: RiderAchievement.AchievementType.COMPLETE_50,
        100: RiderAchievement.AchievementType.COMPLETE_100,
        500: RiderAchievement.AchievementType.COMPLETE_500,
    }
    
    if total_deliveries in milestone_achievements:
        achievement_type = milestone_achievements[total_deliveries]
        achievement, created = RiderAchievement.objects.get_or_create(
            rider=rider,
            achievement_type=achievement_type,
            defaults={
                'title': f'Completed {total_deliveries} Deliveries',
                'description': f'Successfully completed {total_deliveries} deliveries',
                'points_awarded': total_deliveries * 10
            }
        )
        
        if created:
            # Add points to rider level
            add_points_to_rider(rider, achievement.points_awarded)
    
    # Check for perfect rating
    from .models import RiderRating
    avg_rating = RiderRating.objects.filter(
        rider=rider
    ).aggregate(avg=models.Avg('rating'))['avg'] or 0
    
    if avg_rating >= 5.0 and total_deliveries >= 10:
        achievement, created = RiderAchievement.objects.get_or_create(
            rider=rider,
            achievement_type=RiderAchievement.AchievementType.PERFECT_RATING,
            defaults={
                'title': 'Perfect 5-Star Rating',
                'description': 'Maintained a perfect 5-star rating',
                'points_awarded': 100
            }
        )
        
        if created:
            add_points_to_rider(rider, achievement.points_awarded)


def add_points_to_rider(rider, points):
    """
    Add points to rider level
    
    Args:
        rider: Rider user object
        points: Points to add
    """
    if not RiderLevel:
        return  # Advanced features not available
    
    rider_level, created = RiderLevel.objects.get_or_create(
        rider=rider,
        defaults={
            'level': 1,
            'total_points': 0,
            'points_needed_for_next_level': 100
        }
    )
    
    rider_level.add_points(points)


def predict_ml_eta(delivery, rider, traffic_conditions='MEDIUM', weather_conditions='CLEAR'):
    """
    ML-based ETA prediction (placeholder implementation)
    
    In production, this would call an ML service/API
    
    Args:
        delivery: Delivery object
        rider: Rider user object
        traffic_conditions: Traffic conditions (LOW, MEDIUM, HIGH)
        weather_conditions: Weather conditions (CLEAR, RAIN, SNOW, etc.)
    
    Returns:
        MLETAPrediction object or None
    """
    if not MLETAPrediction:
        return None  # Advanced features not available
    
    from .services import calculate_distance, calculate_eta
    
    # Get delivery coordinates
    if not (delivery.pickup_latitude and delivery.pickup_longitude and
            delivery.delivery_latitude and delivery.delivery_longitude):
        return None
    
    # Calculate base distance and ETA
    distance = calculate_distance(
        float(delivery.pickup_latitude),
        float(delivery.pickup_longitude),
        float(delivery.delivery_latitude),
        float(delivery.delivery_longitude)
    )
    
    base_eta = calculate_eta(distance, avg_speed_kmh=30)
    
    # Apply traffic multiplier
    traffic_multipliers = {
        'LOW': 1.0,
        'MEDIUM': 1.3,
        'HIGH': 1.7,
    }
    traffic_multiplier = traffic_multipliers.get(traffic_conditions, 1.3)
    
    # Apply weather multiplier
    weather_multipliers = {
        'CLEAR': 1.0,
        'RAIN': 1.2,
        'SNOW': 1.5,
        'FOG': 1.3,
    }
    weather_multiplier = weather_multipliers.get(weather_conditions, 1.0)
    
    # Predict ETA with ML factors (simplified)
    predicted_eta = int(base_eta * traffic_multiplier * weather_multiplier)
    
    # Get historical accuracy for confidence
    historical_predictions = MLETAPrediction.objects.filter(
        rider=rider,
        actual_eta_minutes__isnull=False
    ).order_by('-created_at')[:10]
    
    if historical_predictions:
        # Calculate average accuracy
        accuracies = []
        for pred in historical_predictions:
            if pred.ml_predicted_eta_minutes and pred.actual_eta_minutes:
                error = abs(pred.ml_predicted_eta_minutes - pred.actual_eta_minutes)
                accuracy = max(0, 1 - (error / max(pred.actual_eta_minutes, 1)))
                accuracies.append(accuracy)
        
        confidence = sum(accuracies) / len(accuracies) if accuracies else 0.7
    else:
        confidence = 0.7  # Default confidence for new riders
    
    # Create prediction
    prediction = MLETAPrediction.objects.create(
        delivery=delivery,
        rider=rider,
        ml_predicted_eta_minutes=predicted_eta,
        ml_predicted_distance_km=distance,
        confidence_score=round(confidence, 2),
        traffic_conditions=traffic_conditions,
        weather_conditions=weather_conditions,
        time_of_day=timezone.now().time(),
        day_of_week=timezone.now().weekday(),
        model_version='v1.0'  # In production, get from ML service
    )
    
    return prediction


def process_voice_command(rider, spoken_text, recognized_text, command_type, delivery=None):
    """
    Process voice command from rider
    
    Args:
        rider: Rider user object
        spoken_text: Original spoken text
        recognized_text: Recognized text from speech-to-text
        command_type: CommandType enum value
        delivery: Delivery object (if command is delivery-specific)
    
    Returns:
        VoiceCommand object and processing result
    """
    if not VoiceCommand:
        return None, {'success': False, 'error': 'Voice commands not available'}  # Advanced features not available
    
    from django.db import models
    
    # Create voice command record
    voice_cmd = VoiceCommand.objects.create(
        rider=rider,
        command_type=command_type,
        spoken_text=spoken_text,
        recognized_text=recognized_text,
        delivery=delivery,
        status=VoiceCommand.Status.PENDING
    )
    
    # Process command based on type
    result = {'success': False, 'message': ''}
    
    try:
        if command_type == VoiceCommand.CommandType.ACCEPT_OFFER:
            if delivery:
                # Accept delivery offer logic would go here
                result = {'success': True, 'message': 'Offer accepted'}
        
        elif command_type == VoiceCommand.CommandType.START_SHIFT:
            # Start shift logic
            active_shift = RiderShift.objects.filter(
                rider=rider,
                status=RiderShift.Status.ACTIVE
            ).first()
            
            if not active_shift:
                shift = RiderShift.objects.create(
                    rider=rider,
                    status=RiderShift.Status.ACTIVE,
                    actual_start_time=timezone.now()
                )
                result = {'success': True, 'message': 'Shift started', 'shift_id': shift.id}
            else:
                result = {'success': False, 'message': 'Shift already active'}
        
        elif command_type == VoiceCommand.CommandType.SOS:
            # Emergency SOS logic
            from .models import EmergencyContact
            # Notify emergency contacts logic would go here
            result = {'success': True, 'message': 'Emergency SOS activated'}
        
        if result['success']:
            voice_cmd.status = VoiceCommand.Status.PROCESSED
            voice_cmd.accuracy_score = 0.9  # In production, get from speech-to-text service
            voice_cmd.processed_at = timezone.now()
        else:
            voice_cmd.status = VoiceCommand.Status.FAILED
            voice_cmd.error_message = result.get('message', 'Unknown error')
        
        voice_cmd.save()
        
    except Exception as e:
        voice_cmd.status = VoiceCommand.Status.FAILED
        voice_cmd.error_message = str(e)
        voice_cmd.save()
        result = {'success': False, 'error': str(e)}
    
    return voice_cmd, result


def get_tenant_fleet_for_rider(rider):
    """
    Get tenant fleet for rider (if part of multi-tenant fleet)
    
    Args:
        rider: Rider user object
    
    Returns:
        MultiTenantFleet object or None
    """
    if not TenantRider:
        return None  # Advanced features not available
    
    tenant_rider = TenantRider.objects.filter(
        rider=rider,
        is_active=True
    ).select_related('tenant_fleet').first()
    
    return tenant_rider.tenant_fleet if tenant_rider else None


def get_rider_leaderboard(period='week', tenant_fleet=None, limit=10):
    """
    Get rider leaderboard
    
    Args:
        period: Time period ('day', 'week', 'month')
        tenant_fleet: Optional tenant fleet to filter by
        limit: Number of riders to return
    
    Returns:
        List of rider stats sorted by performance
    """
    from datetime import timedelta
    from django.db.models import Sum, Count, Avg
    
    if period == 'day':
        start_date = timezone.now().date()
    elif period == 'week':
        start_date = timezone.now().date() - timedelta(days=7)
    elif period == 'month':
        start_date = timezone.now().date() - timedelta(days=30)
    else:
        start_date = timezone.now().date() - timedelta(days=7)
    
    # Get deliveries in period
    deliveries_qs = Delivery.objects.filter(
        status=Delivery.Status.DELIVERED,
        actual_delivery_time__date__gte=start_date
    )
    
    # Filter by tenant if specified
    if tenant_fleet and TenantRider:
        tenant_riders = TenantRider.objects.filter(
            tenant_fleet=tenant_fleet,
            is_active=True
        ).values_list('rider_id', flat=True)
        deliveries_qs = deliveries_qs.filter(rider_id__in=tenant_riders)
    
    # Aggregate by rider
    leaderboard = deliveries_qs.values('rider').annotate(
        total_deliveries=Count('id'),
        total_earnings=Sum('total_earnings'),
        avg_rating=Avg('order__rating')  # Would need rating relation
    ).order_by('-total_deliveries')[:limit]
    
    return list(leaderboard)

