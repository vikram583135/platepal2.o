"""
Serializers for deliveries app
"""
from rest_framework import serializers
from .models import (
    Delivery, RiderLocation, RiderEarnings, DeliveryDocument,
    RiderProfile, RiderBankDetail, RiderOnboarding, RiderBackgroundCheck, RiderReferral,
    RiderShift, DeliveryOffer, RiderWallet, RiderWalletTransaction,
    RiderRating, RiderDispute, EmergencyContact, AutoAcceptRule,
    Fleet, FleetRider, RiderAgreement, OfflineAction, TripLog, RiderSettings
)
from apps.orders.serializers import OrderSerializer
from apps.accounts.serializers import UserSerializer


class DeliverySerializer(serializers.ModelSerializer):
    """Delivery serializer"""
    order = OrderSerializer(read_only=True)
    rider_email = serializers.EmailField(source='rider.email', read_only=True)
    
    # Navigation fields
    navigation_deep_link = serializers.SerializerMethodField()
    
    class Meta:
        model = Delivery
        fields = ('id', 'order', 'rider', 'rider_email', 'status', 'pickup_address',
                  'pickup_latitude', 'pickup_longitude', 'delivery_address',
                  'delivery_latitude', 'delivery_longitude', 'estimated_pickup_time',
                  'estimated_delivery_time', 'actual_pickup_time', 'actual_delivery_time',
                  'base_fee', 'distance_fee', 'tip_amount', 'total_earnings',
                  'failure_reason', 'failure_code', 'is_contactless', 'delivery_photo',
                  'route_preview_data', 'estimated_distance_km', 'estimated_travel_time_minutes',
                  'live_eta', 'is_paused', 'paused_at', 'pause_reason', 'resumed_at',
                  'delivery_otp', 'signature_image', 'unable_to_deliver_reason',
                  'unable_to_deliver_code', 'unable_to_deliver_photo',
                  'customer_phone_masked', 'customer_name', 'restaurant_phone_masked',
                  'special_instructions', 'navigation_deep_link', 'created_at')
        read_only_fields = ('id', 'order', 'rider', 'total_earnings', 'created_at')
    
    def get_navigation_deep_link(self, obj):
        """Generate navigation deep link based on preferences"""
        # Get rider's preferred navigation app (default to Google Maps)
        rider = obj.rider
        if rider and hasattr(rider, 'rider_settings'):
            nav_app = rider.rider_settings.preferred_navigation_app or 'GOOGLE_MAPS'
        else:
            nav_app = 'GOOGLE_MAPS'
        
        # Generate deep links for different navigation apps
        if obj.pickup_latitude and obj.pickup_longitude:
            pickup_lat = float(obj.pickup_latitude)
            pickup_lng = float(obj.pickup_longitude)
            
            if obj.delivery_latitude and obj.delivery_longitude:
                drop_lat = float(obj.delivery_latitude)
                drop_lng = float(obj.delivery_longitude)
                
                if nav_app == 'GOOGLE_MAPS':
                    return f"https://www.google.com/maps/dir/?api=1&origin={pickup_lat},{pickup_lng}&destination={drop_lat},{drop_lng}&travelmode=driving"
                elif nav_app == 'WAZE':
                    return f"https://waze.com/ul?ll={pickup_lat},{pickup_lng}&navigate=yes"
                elif nav_app == 'APPLE_MAPS':
                    return f"http://maps.apple.com/?daddr={drop_lat},{drop_lng}&saddr={pickup_lat},{pickup_lng}"
        
        return None


class RiderLocationSerializer(serializers.ModelSerializer):
    """Rider location serializer"""
    
    class Meta:
        model = RiderLocation
        fields = ('id', 'rider', 'latitude', 'longitude', 'accuracy', 'heading', 'speed',
                  'battery_level', 'location_mode', 'is_moving', 'near_pickup_zone',
                  'near_drop_zone', 'pickup_zone_entered_at', 'drop_zone_entered_at',
                  'is_offline_sync', 'offline_queued_at', 'created_at')
        read_only_fields = ('id', 'created_at')


class RiderEarningsSerializer(serializers.ModelSerializer):
    """Rider earnings serializer"""
    
    class Meta:
        model = RiderEarnings
        fields = ('id', 'rider', 'delivery', 'base_fee', 'distance_fee', 'tip_amount',
                  'bonus', 'total_amount', 'is_paid', 'paid_at', 'payout_period_start',
                  'payout_period_end', 'created_at')
        read_only_fields = ('id', 'created_at')


class DeliveryDocumentSerializer(serializers.ModelSerializer):
    """Delivery document serializer"""
    
    class Meta:
        model = DeliveryDocument
        fields = ('id', 'rider', 'document_type', 'document_file', 'document_number',
                  'expiry_date', 'is_verified', 'verified_at', 'notes', 'created_at')
        read_only_fields = ('id', 'is_verified', 'verified_at', 'created_at')


class RiderProfileSerializer(serializers.ModelSerializer):
    """Rider profile serializer"""
    
    class Meta:
        model = RiderProfile
        fields = ('id', 'rider', 'date_of_birth', 'government_id_number', 'government_id_file',
                  'selfie_photo', 'vehicle_type', 'vehicle_registration_number', 'vehicle_registration_file',
                  'vehicle_model', 'vehicle_color', 'driver_license_number', 'driver_license_file',
                  'driver_license_expiry', 'emergency_contact_name', 'emergency_contact_phone',
                  'emergency_contact_relationship', 'profile_completion_percentage', 'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'profile_completion_percentage', 'created_at', 'updated_at')


class RiderBankDetailSerializer(serializers.ModelSerializer):
    """Rider bank detail serializer"""
    
    class Meta:
        model = RiderBankDetail
        fields = ('id', 'rider', 'bank_name', 'account_holder_name', 'account_number',
                  'ifsc_code', 'bank_branch', 'is_verified', 'verified_at', 'cancelled_cheque_file',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'is_verified', 'verified_at', 'created_at', 'updated_at')


class RiderOnboardingSerializer(serializers.ModelSerializer):
    """Rider onboarding serializer"""
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = RiderOnboarding
        fields = ('id', 'rider', 'status', 'phone_verified', 'email_verified', 'profile_completed',
                  'documents_uploaded', 'bank_details_added', 'background_check_completed',
                  'agreement_signed', 'induction_video_watched', 'current_step', 'completed_steps',
                  'started_at', 'completed_at', 'approved_at', 'rejected_at', 'rejection_reason',
                  'referral_code_used', 'completion_percentage', 'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'completion_percentage', 'created_at', 'updated_at')
    
    def get_completion_percentage(self, obj):
        return obj.get_completion_percentage()


class RiderBackgroundCheckSerializer(serializers.ModelSerializer):
    """Rider background check serializer"""
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = RiderBackgroundCheck
        fields = ('id', 'rider', 'status', 'initiated_at', 'completed_at', 'expires_at',
                  'report_id', 'report_file', 'notes', 'provider', 'provider_reference',
                  'is_expired', 'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'is_expired', 'created_at', 'updated_at')
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class RiderReferralSerializer(serializers.ModelSerializer):
    """Rider referral serializer"""
    
    class Meta:
        model = RiderReferral
        fields = ('id', 'referrer', 'referred_user', 'referral_code', 'referred_email',
                  'referred_phone', 'status', 'referrer_bonus', 'referred_bonus',
                  'signup_date', 'completed_at', 'expires_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'referrer', 'referred_user', 'completed_at', 'created_at', 'updated_at')


class RiderShiftSerializer(serializers.ModelSerializer):
    """Rider shift serializer"""
    
    class Meta:
        model = RiderShift
        fields = ('id', 'rider', 'status', 'scheduled_start', 'scheduled_end', 'actual_start',
                  'actual_end', 'time_online_minutes', 'idle_time_minutes', 'distance_traveled_km',
                  'deliveries_completed', 'earnings_total', 'auto_offline_enabled',
                  'auto_offline_after_minutes', 'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'created_at', 'updated_at')


class DeliveryOfferSerializer(serializers.ModelSerializer):
    """Delivery offer serializer"""
    delivery = DeliverySerializer(read_only=True)
    rider_email = serializers.EmailField(source='rider.email', read_only=True)
    is_expired = serializers.SerializerMethodField()
    time_remaining_seconds = serializers.SerializerMethodField()
    
    class Meta:
        model = DeliveryOffer
        fields = ('id', 'delivery', 'rider', 'rider_email', 'status', 'estimated_earnings',
                  'distance_km', 'estimated_pickup_time', 'estimated_drop_time', 'expires_at',
                  'sent_at', 'accepted_at', 'declined_at', 'decline_reason', 'decline_code',
                  'priority', 'is_surge', 'surge_multiplier', 'is_expired', 'time_remaining_seconds',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'delivery', 'rider', 'time_remaining_seconds', 'created_at', 'updated_at')
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_time_remaining_seconds(self, obj):
        from django.utils import timezone
        if obj.expires_at and obj.status == DeliveryOffer.Status.SENT:
            remaining = obj.expires_at - timezone.now()
            return max(0, int(remaining.total_seconds()))
        return 0


class RiderWalletSerializer(serializers.ModelSerializer):
    """Rider wallet serializer"""
    
    class Meta:
        model = RiderWallet
        fields = ('id', 'rider', 'balance', 'currency', 'pending_payout', 'last_payout_at',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'balance', 'pending_payout', 'last_payout_at',
                           'created_at', 'updated_at')


class RiderWalletTransactionSerializer(serializers.ModelSerializer):
    """Rider wallet transaction serializer"""
    
    class Meta:
        model = RiderWalletTransaction
        fields = ('id', 'wallet', 'transaction_type', 'source', 'amount', 'balance_after',
                  'description', 'delivery', 'earnings', 'created_at')
        read_only_fields = ('id', 'wallet', 'balance_after', 'created_at')


class RiderRatingSerializer(serializers.ModelSerializer):
    """Rider rating serializer"""
    rider_email = serializers.EmailField(source='rider.email', read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    
    class Meta:
        model = RiderRating
        fields = ('id', 'rider', 'rider_email', 'customer', 'customer_email', 'delivery',
                  'rating', 'comment', 'punctuality_rating', 'communication_rating',
                  'service_rating', 'is_visible', 'created_at')
        read_only_fields = ('id', 'rider', 'customer', 'created_at')


class RiderDisputeSerializer(serializers.ModelSerializer):
    """Rider dispute serializer"""
    rider_email = serializers.EmailField(source='rider.email', read_only=True)
    
    class Meta:
        model = RiderDispute
        fields = ('id', 'rider', 'rider_email', 'delivery', 'dispute_type', 'status', 'title',
                  'description', 'evidence_photos', 'resolution', 'resolved_at', 'resolved_by',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'resolved_at', 'resolved_by', 'created_at', 'updated_at')


class EmergencyContactSerializer(serializers.ModelSerializer):
    """Emergency contact serializer"""
    
    class Meta:
        model = EmergencyContact
        fields = ('id', 'rider', 'name', 'phone', 'relationship', 'is_primary',
                  'share_location_with_emergency', 'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'created_at', 'updated_at')


class AutoAcceptRuleSerializer(serializers.ModelSerializer):
    """Auto-accept rule serializer"""
    
    class Meta:
        model = AutoAcceptRule
        fields = ('id', 'rider', 'is_enabled', 'max_distance_km', 'min_earnings',
                  'max_earnings', 'allowed_areas', 'priority', 'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'created_at', 'updated_at')


class FleetSerializer(serializers.ModelSerializer):
    """Fleet serializer"""
    manager_email = serializers.EmailField(source='manager.email', read_only=True)
    
    class Meta:
        model = Fleet
        fields = ('id', 'name', 'manager', 'manager_email', 'description', 'contact_email',
                  'contact_phone', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'manager', 'created_at', 'updated_at')


class FleetRiderSerializer(serializers.ModelSerializer):
    """Fleet rider serializer"""
    rider_email = serializers.EmailField(source='rider.email', read_only=True)
    fleet_name = serializers.CharField(source='fleet.name', read_only=True)
    
    class Meta:
        model = FleetRider
        fields = ('id', 'fleet', 'fleet_name', 'rider', 'rider_email', 'is_active',
                  'joined_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'joined_at', 'created_at', 'updated_at')


class RiderAgreementSerializer(serializers.ModelSerializer):
    """Rider agreement serializer"""
    
    class Meta:
        model = RiderAgreement
        fields = ('id', 'rider', 'agreement_version', 'agreement_text', 'agreed_at',
                  'ip_address', 'user_agent', 'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'ip_address', 'user_agent', 'created_at', 'updated_at')


class OfflineActionSerializer(serializers.ModelSerializer):
    """Offline action serializer"""
    
    class Meta:
        model = OfflineAction
        fields = ('id', 'rider', 'action_type', 'status', 'action_data', 'resource_id',
                  'retry_count', 'max_retries', 'next_retry_at', 'synced_at', 'sync_error',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'synced_at', 'sync_error', 'created_at', 'updated_at')


class TripLogSerializer(serializers.ModelSerializer):
    """Trip log serializer"""
    rider_email = serializers.EmailField(source='rider.email', read_only=True)
    delivery_order_number = serializers.CharField(source='delivery.order.order_number', read_only=True)
    
    class Meta:
        model = TripLog
        fields = ('id', 'rider', 'rider_email', 'delivery', 'delivery_order_number',
                  'total_distance_km', 'total_time_minutes', 'idle_time_minutes',
                  'trip_started_at', 'trip_ended_at', 'pickup_arrived_at', 'pickup_completed_at',
                  'delivery_arrived_at', 'delivery_completed_at', 'base_fee', 'distance_fee',
                  'time_fee', 'surge_multiplier', 'tip_amount', 'total_earnings',
                  'route_taken', 'route_efficiency', 'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'delivery', 'created_at', 'updated_at')


class RiderSettingsSerializer(serializers.ModelSerializer):
    """Rider settings serializer"""
    
    class Meta:
        model = RiderSettings
        fields = ('id', 'rider', 'location_tracking_enabled', 'location_mode',
                  'location_update_interval_moving', 'location_update_interval_idle',
                  'share_location_during_shift_only', 'push_notifications_enabled',
                  'sound_alerts_enabled', 'offer_sound_enabled', 'snooze_mode_enabled',
                  'snooze_until', 'preferred_navigation_app', 'auto_accept_enabled',
                  'location_privacy_enabled', 'created_at', 'updated_at')
        read_only_fields = ('id', 'rider', 'created_at', 'updated_at')


