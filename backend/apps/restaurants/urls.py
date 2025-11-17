"""
URLs for restaurants app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RestaurantSignupView,
    RestaurantDashboardView,
    RestaurantOnlineStatusView,
    RestaurantViewSet,
    MenuViewSet,
    MenuCategoryViewSet,
    MenuItemViewSet,
    ItemModifierViewSet,
    PromotionViewSet,
    RestaurantSettingsViewSet,
    RestaurantBranchViewSet,
    ManagerProfileViewSet,
    RestaurantDocumentViewSet,
    RestaurantAlertViewSet,
    RestaurantOnboardingViewSet,
    detect_location,
    search_suggestions,
    popular_searches,
    recent_searches,
    save_search,
    advanced_search,
    trending_dishes,
)

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
router.register(r'menus', MenuViewSet, basename='menu')
router.register(r'categories', MenuCategoryViewSet, basename='category')
router.register(r'items', MenuItemViewSet, basename='item')
router.register(r'modifiers', ItemModifierViewSet, basename='modifier')
router.register(r'promotions', PromotionViewSet, basename='promotion')
router.register(r'settings', RestaurantSettingsViewSet, basename='restaurant-settings')
router.register(r'branches', RestaurantBranchViewSet, basename='restaurant-branch')
router.register(r'managers', ManagerProfileViewSet, basename='restaurant-manager')
router.register(r'documents', RestaurantDocumentViewSet, basename='restaurant-document')
router.register(r'alerts', RestaurantAlertViewSet, basename='restaurant-alert')
router.register(r'onboarding', RestaurantOnboardingViewSet, basename='restaurant-onboarding')

urlpatterns = [
    path('onboarding/signup/', RestaurantSignupView.as_view(), name='restaurant-signup'),
    path('dashboard/overview/', RestaurantDashboardView.as_view(), name='restaurant-dashboard-overview'),
    path('dashboard/online-status/', RestaurantOnlineStatusView.as_view(), name='restaurant-online-status'),
    path('', include(router.urls)),
    path('location/detect/', detect_location, name='detect_location'),
    path('search/suggestions/', search_suggestions, name='search_suggestions'),
    path('search/popular/', popular_searches, name='popular_searches'),
    path('search/recent/', recent_searches, name='recent_searches'),
    path('search/save/', save_search, name='save_search'),
    path('search/advanced/', advanced_search, name='advanced_search'),
    path('search/trending/', trending_dishes, name='trending_dishes'),
]

