from django.contrib import admin
from .models import (
    Delivery, RiderLocation, RiderEarnings, DeliveryDocument,
    RiderProfile, RiderBankDetail, RiderOnboarding, RiderBackgroundCheck, RiderReferral,
    RiderShift, DeliveryOffer, RiderWallet, RiderWalletTransaction,
    RiderRating, RiderDispute, EmergencyContact, AutoAcceptRule,
    Fleet, FleetRider, RiderAgreement, OfflineAction, TripLog, RiderSettings
)
try:
    from .models_advanced import (
        RiderAchievement, RiderLevel, MLETAPrediction,
        VoiceCommand, MultiTenantFleet, TenantRider
    )
except ImportError:
    # Advanced models not available
    pass


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('order', 'rider', 'status', 'total_earnings', 'created_at')
    list_filter = ('status', 'is_contactless', 'created_at')
    search_fields = ('order__order_number', 'rider__email')
    readonly_fields = ('total_earnings', 'created_at')


@admin.register(RiderLocation)
class RiderLocationAdmin(admin.ModelAdmin):
    list_display = ('rider', 'latitude', 'longitude', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('rider__email',)
    readonly_fields = ('rider', 'latitude', 'longitude', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(RiderEarnings)
class RiderEarningsAdmin(admin.ModelAdmin):
    list_display = ('rider', 'delivery', 'total_amount', 'is_paid', 'payout_period_start', 'payout_period_end')
    list_filter = ('is_paid', 'payout_period_start', 'payout_period_end')
    search_fields = ('rider__email',)
    readonly_fields = ('total_amount',)


@admin.register(DeliveryDocument)
class DeliveryDocumentAdmin(admin.ModelAdmin):
    list_display = ('rider', 'document_type', 'document_number', 'is_verified', 'expiry_date')
    list_filter = ('document_type', 'is_verified', 'expiry_date')
    search_fields = ('rider__email', 'document_number')


@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ('rider', 'vehicle_type', 'profile_completion_percentage', 'created_at')
    list_filter = ('vehicle_type', 'profile_completion_percentage')
    search_fields = ('rider__email', 'vehicle_registration_number', 'driver_license_number')


@admin.register(RiderBankDetail)
class RiderBankDetailAdmin(admin.ModelAdmin):
    list_display = ('rider', 'bank_name', 'account_holder_name', 'is_verified', 'verified_at')
    list_filter = ('is_verified', 'bank_name')
    search_fields = ('rider__email', 'account_number', 'ifsc_code')


@admin.register(RiderOnboarding)
class RiderOnboardingAdmin(admin.ModelAdmin):
    list_display = ('rider', 'status', 'completion_percentage', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at', 'completed_at')
    search_fields = ('rider__email',)
    
    def completion_percentage(self, obj):
        return f"{obj.get_completion_percentage()}%"
    completion_percentage.short_description = 'Completion %'


@admin.register(RiderBackgroundCheck)
class RiderBackgroundCheckAdmin(admin.ModelAdmin):
    list_display = ('rider', 'status', 'initiated_at', 'completed_at', 'expires_at')
    list_filter = ('status', 'provider')
    search_fields = ('rider__email', 'report_id', 'provider_reference')


@admin.register(RiderReferral)
class RiderReferralAdmin(admin.ModelAdmin):
    list_display = ('referral_code', 'referrer', 'referred_user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('referral_code', 'referrer__email', 'referred_email', 'referred_phone')


@admin.register(RiderShift)
class RiderShiftAdmin(admin.ModelAdmin):
    list_display = ('rider', 'status', 'actual_start', 'actual_end', 'deliveries_completed', 'earnings_total')
    list_filter = ('status', 'actual_start', 'actual_end')
    search_fields = ('rider__email',)
    date_hierarchy = 'actual_start'


@admin.register(DeliveryOffer)
class DeliveryOfferAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'rider', 'status', 'estimated_earnings', 'distance_km', 'expires_at')
    list_filter = ('status', 'is_surge', 'expires_at')
    search_fields = ('delivery__order__order_number', 'rider__email')
    date_hierarchy = 'expires_at'


@admin.register(RiderWallet)
class RiderWalletAdmin(admin.ModelAdmin):
    list_display = ('rider', 'balance', 'pending_payout', 'last_payout_at')
    list_filter = ('currency',)
    search_fields = ('rider__email',)


@admin.register(RiderWalletTransaction)
class RiderWalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'source', 'amount', 'balance_after', 'created_at')
    list_filter = ('transaction_type', 'source', 'created_at')
    search_fields = ('wallet__rider__email',)
    date_hierarchy = 'created_at'


@admin.register(RiderRating)
class RiderRatingAdmin(admin.ModelAdmin):
    list_display = ('rider', 'customer', 'rating', 'delivery', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('rider__email', 'customer__email')


@admin.register(RiderDispute)
class RiderDisputeAdmin(admin.ModelAdmin):
    list_display = ('rider', 'dispute_type', 'status', 'title', 'created_at')
    list_filter = ('dispute_type', 'status', 'created_at')
    search_fields = ('rider__email', 'title', 'description')


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('rider', 'name', 'phone', 'relationship', 'is_primary')
    list_filter = ('is_primary', 'relationship')
    search_fields = ('rider__email', 'name', 'phone')


@admin.register(AutoAcceptRule)
class AutoAcceptRuleAdmin(admin.ModelAdmin):
    list_display = ('rider', 'is_enabled', 'max_distance_km', 'min_earnings', 'priority')
    list_filter = ('is_enabled',)
    search_fields = ('rider__email',)


@admin.register(Fleet)
class FleetAdmin(admin.ModelAdmin):
    list_display = ('name', 'manager', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'manager__email', 'contact_email')


@admin.register(FleetRider)
class FleetRiderAdmin(admin.ModelAdmin):
    list_display = ('fleet', 'rider', 'is_active', 'joined_at')
    list_filter = ('is_active', 'joined_at')
    search_fields = ('fleet__name', 'rider__email')


@admin.register(RiderAgreement)
class RiderAgreementAdmin(admin.ModelAdmin):
    list_display = ('rider', 'agreement_version', 'agreed_at', 'created_at')
    list_filter = ('agreement_version', 'agreed_at')
    search_fields = ('rider__email', 'agreement_version')


@admin.register(OfflineAction)
class OfflineActionAdmin(admin.ModelAdmin):
    list_display = ('rider', 'action_type', 'status', 'retry_count', 'created_at', 'synced_at')
    list_filter = ('action_type', 'status', 'created_at')
    search_fields = ('rider__email', 'resource_id')
    date_hierarchy = 'created_at'


@admin.register(TripLog)
class TripLogAdmin(admin.ModelAdmin):
    list_display = ('rider', 'delivery', 'total_distance_km', 'total_time_minutes', 'total_earnings', 'trip_started_at')
    list_filter = ('trip_started_at',)
    search_fields = ('rider__email', 'delivery__order__order_number')
    date_hierarchy = 'trip_started_at'


@admin.register(RiderSettings)
class RiderSettingsAdmin(admin.ModelAdmin):
    list_display = ('rider', 'location_tracking_enabled', 'push_notifications_enabled', 'auto_accept_enabled')
    list_filter = ('location_tracking_enabled', 'push_notifications_enabled', 'auto_accept_enabled', 'location_mode')
    search_fields = ('rider__email',)


# Advanced features admin (if available)
try:
    from .models_advanced import (
        RiderAchievement, RiderLevel, MLETAPrediction,
        VoiceCommand, MultiTenantFleet, TenantRider
    )
    
    @admin.register(RiderAchievement)
    class RiderAchievementAdmin(admin.ModelAdmin):
        list_display = ('rider', 'achievement_type', 'title', 'points_awarded', 'earned_at')
        list_filter = ('achievement_type', 'earned_at')
        search_fields = ('rider__email', 'title')
        date_hierarchy = 'earned_at'
    
    @admin.register(RiderLevel)
    class RiderLevelAdmin(admin.ModelAdmin):
        list_display = ('rider', 'level', 'total_points', 'total_deliveries', 'total_earnings', 'last_level_up_at')
        list_filter = ('level', 'last_level_up_at')
        search_fields = ('rider__email',)
        ordering = ('-total_points',)
    
    @admin.register(MLETAPrediction)
    class MLETAPredictionAdmin(admin.ModelAdmin):
        list_display = ('delivery', 'rider', 'ml_predicted_eta_minutes', 'actual_eta_minutes', 'confidence_score', 'prediction_timestamp')
        list_filter = ('traffic_conditions', 'weather_conditions', 'prediction_timestamp')
        search_fields = ('delivery__order__order_number', 'rider__email')
        date_hierarchy = 'prediction_timestamp'
    
    @admin.register(VoiceCommand)
    class VoiceCommandAdmin(admin.ModelAdmin):
        list_display = ('rider', 'command_type', 'recognized_text', 'status', 'accuracy_score', 'created_at')
        list_filter = ('command_type', 'status', 'created_at')
        search_fields = ('rider__email', 'spoken_text', 'recognized_text')
        date_hierarchy = 'created_at'
    
    @admin.register(MultiTenantFleet)
    class MultiTenantFleetAdmin(admin.ModelAdmin):
        list_display = ('name', 'organization_code', 'company_name', 'contact_email', 'is_active', 'max_riders')
        list_filter = ('is_active', 'custom_branding_enabled')
        search_fields = ('name', 'organization_code', 'company_name', 'contact_email')
    
    @admin.register(TenantRider)
    class TenantRiderAdmin(admin.ModelAdmin):
        list_display = ('tenant_fleet', 'rider', 'employee_id', 'department', 'is_active', 'joined_at')
        list_filter = ('is_active', 'department', 'joined_at')
        search_fields = ('tenant_fleet__name', 'rider__email', 'employee_id')
except ImportError:
    pass

