"""
Serializers for restaurants app
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import OTP
from apps.accounts.serializers import UserSerializer
from apps.accounts.services import verify_otp
from .models import (
    DocumentReviewLog,
    ItemModifier,
    ManagerProfile,
    Menu,
    MenuCategory,
    MenuItem,
    Promotion,
    Restaurant,
    RestaurantAlert,
    RestaurantBranch,
    RestaurantDocument,
    RestaurantSettings,
)

User = get_user_model()


class ItemModifierSerializer(serializers.ModelSerializer):
    """Item modifier serializer"""

    class Meta:
        model = ItemModifier
        fields = (
            'id',
            'name',
            'type',
            'price',
            'is_required',
            'is_available',
            'display_order',
        )
        read_only_fields = ('id',)


class RestaurantSignupSerializer(serializers.Serializer):
    """Serializer for OTP-backed restaurant owner onboarding"""

    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100, allow_blank=True, required=False)
    password = serializers.CharField(write_only=True, min_length=8)
    otp_code = serializers.CharField(max_length=10)
    otp_type = serializers.ChoiceField(choices=OTP.OTPType.choices, default=OTP.OTPType.EMAIL_VERIFICATION)
    restaurant_name = serializers.CharField(max_length=255)
    restaurant_type = serializers.ChoiceField(choices=Restaurant.RestaurantType.choices, default=Restaurant.RestaurantType.NON_VEG)
    cuisine_types = serializers.ListField(
        allow_empty=False,
        child=serializers.ChoiceField(choices=Restaurant.CuisineType.choices),
    )
    description = serializers.CharField(allow_blank=True, required=False)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=100, required=False, default='India')
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False)
    delivery_radius_km = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=Decimal('5.00'))
    minimum_order_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal('0.00'))
    fssai_license_number = serializers.CharField(max_length=50, allow_blank=True, required=False)
    gst_number = serializers.CharField(max_length=50, allow_blank=True, required=False)
    manager_contact_phone = serializers.CharField(max_length=20, allow_blank=True, required=False)
    manager_contact_email = serializers.EmailField(allow_blank=True, required=False)

    def validate(self, attrs):
        email = attrs.get('email')
        phone = attrs.get('phone')
        otp_code = attrs.get('otp_code')
        otp_type = attrs.get('otp_type') or OTP.OTPType.EMAIL_VERIFICATION

        if User.objects.filter(email=email, is_deleted=False).exists():
            raise serializers.ValidationError({'email': 'An account with this email already exists.'})
        if phone and User.objects.filter(phone=phone, is_deleted=False).exists():
            raise serializers.ValidationError({'phone': 'An account with this phone already exists.'})

        if otp_type == OTP.OTPType.PHONE_VERIFICATION and not phone:
            raise serializers.ValidationError({'phone': 'Phone number is required for phone verification.'})

        cuisine_types = attrs.get('cuisine_types') or []
        if not cuisine_types:
            raise serializers.ValidationError({'cuisine_types': 'Select at least one cuisine.'})

        success, message = verify_otp(
            email=email,
            phone=phone,
            code=otp_code,
            otp_type=otp_type,
            user=None,
        )
        if not success:
            raise serializers.ValidationError({'otp_code': message})

        return attrs

    def create(self, validated_data):
        cuisine_types = validated_data.pop('cuisine_types')
        password = validated_data.pop('password')
        otp_type = validated_data.pop('otp_type', OTP.OTPType.EMAIL_VERIFICATION)
        otp_code = validated_data.pop('otp_code', None)

        latitude = validated_data.pop('latitude', Decimal('12.971600'))
        longitude = validated_data.pop('longitude', Decimal('77.594600'))

        email = validated_data.pop('email')
        phone = validated_data.pop('phone')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name', '')
        restaurant_name = validated_data.pop('restaurant_name')
        restaurant_type = validated_data.pop('restaurant_type', Restaurant.RestaurantType.NON_VEG)
        description = validated_data.pop('description', '')
        delivery_radius_km = validated_data.pop('delivery_radius_km', Decimal('5.00'))
        minimum_order_amount = validated_data.pop('minimum_order_amount', Decimal('0.00'))
        fssai_license_number = validated_data.pop('fssai_license_number', '')
        gst_number = validated_data.pop('gst_number', '')
        manager_contact_phone = validated_data.pop('manager_contact_phone', '')
        manager_contact_email = validated_data.pop('manager_contact_email', '')
        address = validated_data.pop('address')
        city = validated_data.pop('city')
        state = validated_data.pop('state')
        postal_code = validated_data.pop('postal_code')
        country = validated_data.pop('country', 'India')

        user = User.objects.create_user(
            email=email,
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            role=User.Role.RESTAURANT,
        )
        user.set_password(password)
        if otp_type == OTP.OTPType.EMAIL_VERIFICATION:
            user.is_email_verified = True
        if otp_type == OTP.OTPType.PHONE_VERIFICATION:
            user.is_phone_verified = True
        user.save()

        primary_cuisine = cuisine_types[0] if cuisine_types else Restaurant.CuisineType.OTHER

        restaurant = Restaurant.objects.create(
            owner=user,
            name=restaurant_name,
            description=description,
            cuisine_type=primary_cuisine,
            cuisine_types=cuisine_types,
            restaurant_type=restaurant_type,
            phone=phone,
            email=manager_contact_email or email,
            latitude=latitude,
            longitude=longitude,
            address=address,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            billing_address=address,
            billing_city=city,
            billing_state=state,
            billing_postal_code=postal_code,
            billing_country=country,
            status=Restaurant.Status.PENDING,
            onboarding_status=Restaurant.OnboardingStatus.IN_PROGRESS,
            delivery_radius_km=delivery_radius_km,
            minimum_order_amount=minimum_order_amount,
            fssai_license_number=fssai_license_number,
            gst_number=gst_number,
            manager_contact_name=f"{first_name} {last_name}".strip(),
            manager_contact_phone=manager_contact_phone or phone,
            manager_contact_email=manager_contact_email or email,
            support_phone=phone,
            support_email=email,
        )

        RestaurantSettings.objects.create(
            restaurant=restaurant,
            default_prep_time_minutes=20,
            max_delivery_distance_km=delivery_radius_km,
            delivery_radius_settings={'default_radius_km': float(delivery_radius_km)},
        )

        RestaurantBranch.objects.create(
            restaurant=restaurant,
            name='Main Kitchen',
            branch_type=RestaurantBranch.BranchType.MAIN,
            address_line1=address,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            latitude=latitude,
            longitude=longitude,
            contact_number=phone,
            contact_email=manager_contact_email or email,
            is_primary=True,
        )

        refresh = RefreshToken.for_user(user)
        request = self.context.get('request')
        return {
            'user': UserSerializer(user, context={'request': request}).data,
            'restaurant': RestaurantSerializer(restaurant, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'otp_code': otp_code,
        }


class MenuItemSerializer(serializers.ModelSerializer):
    """Menu item serializer"""

    modifiers = ItemModifierSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = (
            'id',
            'name',
            'description',
            'price',
            'image',
            'is_available',
            'inventory_count',
            'preparation_time_minutes',
            'is_vegetarian',
            'is_vegan',
            'is_spicy',
            'calories',
            'rating',
            'total_ratings',
            'is_featured',
            'modifiers',
            'category_name',
            'image_url',
            'allergens',
            'macros',
            'restaurant_name',
            'is_low_stock',
            'low_stock_threshold',
        )
        read_only_fields = ('id', 'rating', 'total_ratings')

    def get_is_low_stock(self, obj):
        if obj.inventory_count is None:
            return False
        return obj.inventory_count <= obj.low_stock_threshold


class MenuCategorySerializer(serializers.ModelSerializer):
    """Menu category serializer"""

    items = serializers.SerializerMethodField()

    class Meta:
        model = MenuCategory
        fields = ('id', 'name', 'description', 'display_order', 'is_active', 'items')
        read_only_fields = ('id',)
    
    def get_items(self, obj):
        # Filter out deleted and unavailable items
        items = obj.items.filter(is_deleted=False, is_available=True)
        return MenuItemSerializer(items, many=True).data


class MenuSerializer(serializers.ModelSerializer):
    """Menu serializer"""

    categories = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = ('id', 'name', 'description', 'is_active', 'available_from', 'available_until', 'categories')
        read_only_fields = ('id',)
    
    def get_categories(self, obj):
        # Filter out deleted and inactive categories
        categories = obj.categories.filter(is_deleted=False, is_active=True).order_by('display_order')
        return MenuCategorySerializer(categories, many=True).data


class RestaurantSettingsSerializer(serializers.ModelSerializer):
    """Restaurant settings serializer"""

    class Meta:
        model = RestaurantSettings
        fields = '__all__'
        read_only_fields = ('id', 'restaurant', 'created_at', 'updated_at', 'is_deleted')


class RestaurantSettingsUpdateSerializer(serializers.ModelSerializer):
    """Slim settings serializer for onboarding + dashboard toggles"""

    class Meta:
        model = RestaurantSettings
        fields = (
            'default_prep_time_minutes',
            'sla_threshold_minutes',
            'auto_accept_orders',
            'max_delivery_distance_km',
            'delivery_radius_settings',
            'supports_dine_in',
            'supports_takeaway',
            'supports_delivery',
            'kitchen_notes',
            'packaging_instructions',
            'order_notifications',
        )
class RestaurantBranchSerializer(serializers.ModelSerializer):
    """Restaurant branch serializer"""

    class Meta:
        model = RestaurantBranch
        fields = (
            'id',
            'restaurant',
            'name',
            'branch_code',
            'branch_type',
            'address_line1',
            'address_line2',
            'area',
            'city',
            'state',
            'postal_code',
            'country',
            'latitude',
            'longitude',
            'service_radius_km',
            'contact_number',
            'contact_email',
            'is_primary',
            'supports_delivery',
            'supports_pickup',
            'supports_dine_in',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'restaurant', 'created_at', 'updated_at')


class ManagerProfileSerializer(serializers.ModelSerializer):
    """Manager/staff serializer"""

    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ManagerProfile
        fields = (
            'id',
            'restaurant',
            'user',
            'first_name',
            'last_name',
            'email',
            'phone',
            'role',
            'is_primary',
            'permissions',
            'full_name',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'restaurant', 'created_at', 'updated_at')

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class DocumentReviewLogSerializer(serializers.ModelSerializer):
    """Serializer for document review history"""

    reviewer_email = serializers.EmailField(source='reviewer.email', read_only=True)

    class Meta:
        model = DocumentReviewLog
        fields = ('id', 'document', 'reviewer', 'reviewer_email', 'status_before', 'status_after', 'notes', 'created_at')
        read_only_fields = ('id', 'document', 'reviewer_email', 'created_at')


class RestaurantDocumentSerializer(serializers.ModelSerializer):
    """Restaurant document serializer"""

    review_logs = DocumentReviewLogSerializer(many=True, read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = RestaurantDocument
        fields = (
            'id',
            'restaurant',
            'branch',
            'branch_name',
            'document_type',
            'document_number',
            'file',
            'status',
            'submitted_at',
            'reviewed_at',
            'rejection_reason',
            'needs_reupload',
            'metadata',
            'review_logs',
        )
        read_only_fields = ('id', 'restaurant', 'submitted_at', 'reviewed_at', 'review_logs')


class RestaurantSerializer(serializers.ModelSerializer):
    """Restaurant serializer"""

    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    menus = MenuSerializer(many=True, read_only=True)
    active_promotions = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    next_opening_time = serializers.SerializerMethodField()
    settings = serializers.SerializerMethodField()
    branches = serializers.SerializerMethodField()
    managers = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    latest_alerts = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = (
            'id',
            'owner',
            'owner_email',
            'name',
            'description',
            'cuisine_type',
            'cuisine_types',
            'restaurant_type',
            'phone',
            'email',
            'latitude',
            'longitude',
            'address',
            'city',
            'state',
            'postal_code',
            'country',
            'billing_address',
            'billing_city',
            'billing_state',
            'billing_postal_code',
            'billing_country',
            'status',
            'onboarding_status',
            'rating',
            'total_ratings',
            'delivery_time_minutes',
            'minimum_order_amount',
            'delivery_fee',
            'delivery_radius_km',
            'opening_hours',
            'accepts_delivery',
            'accepts_pickup',
            'logo',
            'cover_image',
            'logo_image_url',
            'hero_image_url',
            'kyc_verified',
            'commission_rate',
            'menus',
            'created_at',
            'is_pure_veg',
            'is_halal',
            'hygiene_rating',
            'has_offers',
            'cost_for_two',
            'estimated_preparation_time',
            'manager_contact_name',
            'manager_contact_phone',
            'manager_contact_email',
            'support_phone',
            'support_email',
            'fssai_license_number',
            'gst_number',
            'bank_account_number',
            'bank_ifsc_code',
            'is_multi_branch',
            'active_promotions',
            'is_open',
            'next_opening_time',
            'settings',
            'branches',
            'managers',
            'documents',
            'latest_alerts',
        )
        read_only_fields = (
            'id',
            'owner',
            'rating',
            'total_ratings',
            'kyc_verified',
            'created_at',
            'menus',
            'active_promotions',
            'is_open',
            'next_opening_time',
            'settings',
            'branches',
            'managers',
            'documents',
            'latest_alerts',
        )

    def get_active_promotions(self, obj):
        from django.utils import timezone

        promotions = obj.promotions.filter(
            is_active=True,
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now(),
            is_deleted=False,
        )[:5]
        return PromotionSerializer(promotions, many=True).data

    def get_is_open(self, obj):
        from datetime import datetime
        from django.utils import timezone

        now = timezone.now()
        current_day = now.strftime('%A').lower()
        current_time = now.time()
        hours = obj.opening_hours.get(current_day, {})
        if not hours or not hours.get('open') or not hours.get('close'):
            return True
        try:
            open_time = datetime.strptime(hours['open'], '%H:%M').time()
            close_time = datetime.strptime(hours['close'], '%H:%M').time()
            return open_time <= current_time <= close_time
        except Exception:
            return True

    def get_next_opening_time(self, obj):
        from datetime import datetime
        from django.utils import timezone

        now = timezone.now()
        current_day = now.strftime('%A').lower()
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

        for i in range(7):
            day_index = (days.index(current_day) + i) % 7
            day_name = days[day_index]
            hours = obj.opening_hours.get(day_name, {})
            if hours.get('open'):
                try:
                    return f"{day_name.capitalize()} {hours['open']}"
                except Exception:
                    continue
        return None

    def get_settings(self, obj):
        if hasattr(obj, 'settings') and obj.settings:
            return RestaurantSettingsSerializer(obj.settings).data
        return None

    def get_branches(self, obj):
        branches = obj.branches.filter(is_deleted=False)
        return RestaurantBranchSerializer(branches, many=True).data

    def get_managers(self, obj):
        managers = obj.managers.filter(is_deleted=False)
        return ManagerProfileSerializer(managers, many=True).data

    def get_documents(self, obj):
        documents = obj.documents.filter(is_deleted=False)
        return RestaurantDocumentSerializer(documents, many=True).data
    
    def get_latest_alerts(self, obj):
        alerts = obj.alerts.filter(is_deleted=False).order_by('-created_at')[:5]
        return RestaurantAlertSerializer(alerts, many=True).data

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class RestaurantListSerializer(serializers.ModelSerializer):
    """Lightweight restaurant list serializer"""

    class Meta:
        model = Restaurant
        fields = (
            'id',
            'name',
            'cuisine_type',
            'cuisine_types',
            'restaurant_type',
            'status',
            'onboarding_status',
            'rating',
            'delivery_time_minutes',
            'delivery_fee',
            'delivery_radius_km',
            'minimum_order_amount',
            'logo',
            'cover_image',
            'logo_image_url',
            'hero_image_url',
            'latitude',
            'longitude',
            'city',
            'is_pure_veg',
            'is_halal',
            'hygiene_rating',
            'has_offers',
            'cost_for_two',
        )


class PromotionSerializer(serializers.ModelSerializer):
    """Promotion serializer"""

    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    discount_display = serializers.SerializerMethodField()

    class Meta:
        model = Promotion
        fields = (
            'id',
            'restaurant',
            'restaurant_name',
            'offer_type',
            'name',
            'description',
            'code',
            'discount_type',
            'discount_value',
            'minimum_order_amount',
            'maximum_discount',
            'valid_from',
            'valid_until',
            'is_active',
            'max_uses',
            'uses_count',
            'max_uses_per_user',
            'cashback_percentage',
            'cashback_max_amount',
            'applicable_banks',
            'applicable_upi_providers',
            'priority',
            'discount_display',
        )
        read_only_fields = ('id', 'uses_count')

    def get_discount_display(self, obj):
        if obj.discount_type == 'PERCENTAGE':
            return f"{obj.discount_value}% off"
        if obj.discount_type == 'FIXED':
            return f"₹{obj.discount_value} off"
        if obj.discount_type == 'FREE_DELIVERY':
            return 'Free Delivery'
        if obj.discount_type == 'CASHBACK':
            return f"{obj.cashback_percentage}% cashback"
        if obj.discount_type == 'BUY_ONE_GET_ONE':
            return 'Buy 1 Get 1'
        return ""


class RestaurantAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantAlert
        fields = (
            'id',
            'restaurant',
            'order',
            'alert_type',
            'severity',
            'title',
            'message',
            'metadata',
            'is_read',
            'read_at',
            'resolved_at',
            'created_at',
        )
        read_only_fields = ('id', 'restaurant', 'created_at')



