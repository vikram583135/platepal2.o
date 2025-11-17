"""
Advanced features serializers for deliveries app
"""
from rest_framework import serializers

try:
    from .models_advanced import (
        RiderAchievement, RiderLevel, MLETAPrediction,
        VoiceCommand, MultiTenantFleet, TenantRider
    )
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False


if ADVANCED_FEATURES_AVAILABLE:
    class RiderAchievementSerializer(serializers.ModelSerializer):
        """Rider achievement serializer"""
        rider_email = serializers.EmailField(source='rider.email', read_only=True)
        
        class Meta:
            model = RiderAchievement
            fields = ('id', 'rider', 'rider_email', 'achievement_type', 'title', 'description',
                     'icon_url', 'points_awarded', 'earned_at', 'created_at', 'updated_at')
            read_only_fields = ('id', 'rider', 'earned_at', 'created_at', 'updated_at')
    
    
    class RiderLevelSerializer(serializers.ModelSerializer):
        """Rider level serializer"""
        rider_email = serializers.EmailField(source='rider.email', read_only=True)
        progress_percentage = serializers.SerializerMethodField()
        
        class Meta:
            model = RiderLevel
            fields = ('id', 'rider', 'rider_email', 'level', 'total_points',
                     'current_level_points', 'points_needed_for_next_level',
                     'progress_percentage', 'total_deliveries', 'total_earnings',
                     'total_distance_km', 'last_level_up_at', 'created_at', 'updated_at')
            read_only_fields = ('id', 'rider', 'last_level_up_at', 'created_at', 'updated_at')
        
        def get_progress_percentage(self, obj):
            """Calculate progress to next level"""
            if obj.points_needed_for_next_level > 0:
                return int((obj.current_level_points / obj.points_needed_for_next_level) * 100)
            return 0
    
    
    class MLETAPredictionSerializer(serializers.ModelSerializer):
        """ML ETA prediction serializer"""
        rider_email = serializers.EmailField(source='rider.email', read_only=True)
        delivery_order_number = serializers.CharField(source='delivery.order.order_number', read_only=True)
        accuracy_percentage = serializers.SerializerMethodField()
        
        class Meta:
            model = MLETAPrediction
            fields = ('id', 'delivery', 'delivery_order_number', 'rider', 'rider_email',
                     'ml_predicted_eta_minutes', 'ml_predicted_distance_km', 'confidence_score',
                     'actual_eta_minutes', 'actual_distance_km', 'traffic_conditions',
                     'weather_conditions', 'time_of_day', 'day_of_week', 'model_version',
                     'prediction_timestamp', 'accuracy_percentage', 'created_at', 'updated_at')
            read_only_fields = ('id', 'delivery', 'rider', 'prediction_timestamp', 'created_at', 'updated_at')
        
        def get_accuracy_percentage(self, obj):
            """Calculate prediction accuracy"""
            if obj.confidence_score:
                return int(float(obj.confidence_score) * 100)
            return None
    
    
    class VoiceCommandSerializer(serializers.ModelSerializer):
        """Voice command serializer"""
        rider_email = serializers.EmailField(source='rider.email', read_only=True)
        delivery_order_number = serializers.CharField(source='delivery.order.order_number', read_only=True)
        accuracy_percentage = serializers.SerializerMethodField()
        
        class Meta:
            model = VoiceCommand
            fields = ('id', 'rider', 'rider_email', 'command_type', 'spoken_text',
                     'recognized_text', 'status', 'delivery', 'delivery_order_number',
                     'accuracy_score', 'accuracy_percentage', 'audio_file_url',
                     'duration_seconds', 'processed_at', 'error_message',
                     'created_at', 'updated_at')
            read_only_fields = ('id', 'rider', 'status', 'processed_at', 'error_message',
                              'created_at', 'updated_at')
        
        def get_accuracy_percentage(self, obj):
            """Calculate recognition accuracy"""
            if obj.accuracy_score:
                return int(float(obj.accuracy_score) * 100)
            return None
    
    
    class MultiTenantFleetSerializer(serializers.ModelSerializer):
        """Multi-tenant fleet serializer"""
        rider_count = serializers.SerializerMethodField()
        
        class Meta:
            model = MultiTenantFleet
            fields = ('id', 'name', 'organization_code', 'description', 'company_name',
                     'contact_email', 'contact_phone', 'is_active', 'max_riders',
                     'custom_branding_enabled', 'logo_url', 'primary_color',
                     'secondary_color', 'custom_settings', 'rider_count',
                     'created_at', 'updated_at')
            read_only_fields = ('id', 'created_at', 'updated_at')
        
        def get_rider_count(self, obj):
            """Get active rider count"""
            return obj.tenant_riders.filter(is_active=True).count()
    
    
    class TenantRiderSerializer(serializers.ModelSerializer):
        """Tenant rider serializer"""
        rider_email = serializers.EmailField(source='rider.email', read_only=True)
        fleet_name = serializers.CharField(source='tenant_fleet.name', read_only=True)
        
        class Meta:
            model = TenantRider
            fields = ('id', 'tenant_fleet', 'fleet_name', 'rider', 'rider_email',
                     'employee_id', 'department', 'is_active', 'joined_at',
                     'created_at', 'updated_at')
            read_only_fields = ('id', 'rider', 'joined_at', 'created_at', 'updated_at')

