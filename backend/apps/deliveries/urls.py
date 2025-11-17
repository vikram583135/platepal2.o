"""
URLs for deliveries app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DeliveryViewSet, RiderLocationViewSet, RiderEarningsViewSet, DeliveryDocumentViewSet,
    RiderProfileViewSet, RiderBankDetailViewSet, RiderOnboardingViewSet,
    RiderBackgroundCheckViewSet, RiderReferralViewSet, RiderShiftViewSet,
    DeliveryOfferViewSet, RiderWalletViewSet, EmergencyContactViewSet,
    AutoAcceptRuleViewSet, RiderRatingViewSet, RiderDisputeViewSet, RiderAgreementViewSet,
    FleetViewSet, FleetRiderViewSet, OfflineActionViewSet, TripLogViewSet, RiderSettingsViewSet
)

# Advanced features views (if available)
try:
    from .views_advanced import (
        RiderAchievementViewSet, RiderLevelViewSet, MLETAPredictionViewSet,
        VoiceCommandViewSet, MultiTenantFleetViewSet, TenantRiderViewSet
    )
    ADVANCED_VIEWS_AVAILABLE = True
except ImportError:
    ADVANCED_VIEWS_AVAILABLE = False

router = DefaultRouter()
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
router.register(r'rider-locations', RiderLocationViewSet, basename='rider-location')
router.register(r'rider-earnings', RiderEarningsViewSet, basename='rider-earnings')
router.register(r'documents', DeliveryDocumentViewSet, basename='delivery-document')
router.register(r'profiles', RiderProfileViewSet, basename='rider-profile')
router.register(r'bank-details', RiderBankDetailViewSet, basename='rider-bank-detail')
router.register(r'onboarding', RiderOnboardingViewSet, basename='rider-onboarding')
router.register(r'background-checks', RiderBackgroundCheckViewSet, basename='rider-background-check')
router.register(r'referrals', RiderReferralViewSet, basename='rider-referral')
router.register(r'shifts', RiderShiftViewSet, basename='rider-shift')
router.register(r'offers', DeliveryOfferViewSet, basename='delivery-offer')
router.register(r'wallets', RiderWalletViewSet, basename='rider-wallet')
router.register(r'emergency-contacts', EmergencyContactViewSet, basename='emergency-contact')
router.register(r'auto-accept-rules', AutoAcceptRuleViewSet, basename='auto-accept-rule')
router.register(r'ratings', RiderRatingViewSet, basename='rider-rating')
router.register(r'disputes', RiderDisputeViewSet, basename='rider-dispute')
router.register(r'agreements', RiderAgreementViewSet, basename='rider-agreement')
router.register(r'fleets', FleetViewSet, basename='fleet')
router.register(r'fleet-riders', FleetRiderViewSet, basename='fleet-rider')
router.register(r'offline-actions', OfflineActionViewSet, basename='offline-action')
router.register(r'trip-logs', TripLogViewSet, basename='trip-log')
router.register(r'settings', RiderSettingsViewSet, basename='rider-settings')

# Advanced features routes (if available)
if ADVANCED_VIEWS_AVAILABLE:
    router.register(r'achievements', RiderAchievementViewSet, basename='rider-achievement')
    router.register(r'levels', RiderLevelViewSet, basename='rider-level')
    router.register(r'ml-eta-predictions', MLETAPredictionViewSet, basename='ml-eta-prediction')
    router.register(r'voice-commands', VoiceCommandViewSet, basename='voice-command')
    router.register(r'multi-tenant-fleets', MultiTenantFleetViewSet, basename='multi-tenant-fleet')
    router.register(r'tenant-riders', TenantRiderViewSet, basename='tenant-rider')

urlpatterns = [
    path('', include(router.urls)),
]

