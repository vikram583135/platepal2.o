# Advanced Features Documentation

This document describes the advanced features implemented for the PlatePal delivery backend.

## Gamification System

### Rider Achievements
- **Model**: `RiderAchievement`
- **Features**:
  - Achievement types: First Delivery, Complete 10/50/100/500 Deliveries, Perfect Rating, Fast Delivery, Night Owl, Early Bird, Weekend Warrior, Streaks, Mileage Milestones
  - Points awarded per achievement
  - Unique constraint (one achievement per type per rider)
  - Auto-awarding based on delivery completion

### Rider Leveling System
- **Model**: `RiderLevel`
- **Features**:
  - Level progression based on points
  - Exponential point requirements for next level
  - Statistics tracking (deliveries, earnings, distance)
  - Automatic level-up detection
  - Achievement awarding at milestone levels

### API Endpoints
- `GET /api/deliveries/achievements/` - List all achievements
- `GET /api/deliveries/achievements/my_achievements/` - Get rider's achievements
- `GET /api/deliveries/achievements/leaderboard/` - Get achievement leaderboard
- `GET /api/deliveries/levels/` - List all levels
- `GET /api/deliveries/levels/my_level/` - Get rider's level
- `GET /api/deliveries/levels/leaderboard/` - Get level leaderboard

## Voice Commands

### Voice Command Processing
- **Model**: `VoiceCommand`
- **Features**:
  - Command types: Accept Offer, Decline Offer, Start Shift, End Shift, Pause Trip, Resume Trip, Navigate, Call Customer, Call Restaurant, Emergency SOS
  - Speech-to-text integration support
  - Accuracy scoring
  - Command status tracking (Pending, Processed, Failed)
  - Audio file URL storage

### API Endpoints
- `GET /api/deliveries/voice-commands/` - List voice commands
- `POST /api/deliveries/voice-commands/process/` - Process voice command

### Usage Example
```python
# Process voice command
POST /api/deliveries/voice-commands/process/
{
    "spoken_text": "Start shift",
    "recognized_text": "start shift",
    "command_type": "START_SHIFT",
    "delivery_id": null
}
```

## ML-Based ETA Prediction

### ML ETA Prediction
- **Model**: `MLETAPrediction`
- **Features**:
  - Traffic condition factors (LOW, MEDIUM, HIGH)
  - Weather condition factors (CLEAR, RAIN, SNOW, FOG)
  - Time of day and day of week consideration
  - Confidence scoring based on historical accuracy
  - Actual vs predicted comparison for model training
  - Model version tracking

### API Endpoints
- `GET /api/deliveries/ml-eta-predictions/` - List predictions
- `POST /api/deliveries/ml-eta-predictions/predict/` - Get ML-based ETA prediction

### Usage Example
```python
# Get ML ETA prediction
POST /api/deliveries/ml-eta-predictions/predict/
{
    "delivery_id": 1,
    "traffic_conditions": "MEDIUM",
    "weather_conditions": "CLEAR"
}
```

### Implementation Notes
- Current implementation is a placeholder with simplified prediction logic
- In production, this would integrate with an ML service/API
- Historical predictions are used to calculate confidence scores
- Actual values are stored for model training purposes

## Multi-Tenant Fleet Management

### Multi-Tenant Fleet
- **Model**: `MultiTenantFleet`
- **Features**:
  - Organization code for unique identification
  - Custom branding support (logo, colors)
  - Custom settings per tenant (JSON field)
  - Active/inactive status
  - Maximum riders per fleet
  - Company contact information

### Tenant Rider Association
- **Model**: `TenantRider`
- **Features**:
  - Rider association with tenant fleet
  - Employee ID for company records
  - Department assignment
  - Active/inactive status per tenant

### API Endpoints
- `GET /api/deliveries/multi-tenant-fleets/` - List fleets
- `GET /api/deliveries/multi-tenant-fleets/my_fleet/` - Get rider's tenant fleet
- `GET /api/deliveries/multi-tenant-fleets/{id}/leaderboard/` - Get fleet leaderboard
- `GET /api/deliveries/tenant-riders/` - List tenant riders

### Usage Example
```python
# Get tenant fleet leaderboard
GET /api/deliveries/multi-tenant-fleets/{fleet_id}/leaderboard/?period=week&limit=10
```

## Service Functions

### Achievement System
- `check_and_award_achievements(rider, delivery)` - Check and award achievements after delivery completion
- `add_points_to_rider(rider, points)` - Add points to rider level (auto level-up)

### ML ETA Prediction
- `predict_ml_eta(delivery, rider, traffic_conditions, weather_conditions)` - Generate ML-based ETA prediction

### Voice Commands
- `process_voice_command(rider, spoken_text, recognized_text, command_type, delivery)` - Process voice command

### Multi-Tenant
- `get_tenant_fleet_for_rider(rider)` - Get tenant fleet for rider
- `get_rider_leaderboard(period, tenant_fleet, limit)` - Get rider leaderboard

## Testing

### Test Files
- `backend/apps/deliveries/tests/test_advanced_features.py` - Unit tests for advanced features

### Running Tests
```bash
# Run advanced features tests
python manage.py test apps.deliveries.tests.test_advanced_features

# Run all delivery tests
python manage.py test apps.deliveries
```

## Notes

- Advanced features are implemented in separate files (`models_advanced.py`, `views_advanced.py`, `serializers_advanced.py`)
- Features are conditionally loaded (graceful fallback if not available)
- All models are registered with Django admin
- Migrations are created automatically
- Services are in `services_advanced.py`

## Future Enhancements

1. **ML Integration**: Replace placeholder ML ETA with actual ML model integration
2. **Voice Recognition**: Integrate with speech-to-text service (Google Cloud Speech, AWS Transcribe, etc.)
3. **Real-time Leaderboards**: Use WebSocket for real-time leaderboard updates
4. **Achievement Badges**: Add visual badge images and display in UI
5. **Gamification Analytics**: Track engagement metrics and rewards effectiveness

