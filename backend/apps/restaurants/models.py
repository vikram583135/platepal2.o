from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from apps.accounts.models import User, TimestampMixin, SoftDeleteMixin


class Restaurant(TimestampMixin, SoftDeleteMixin):
    """Restaurant model"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        ACTIVE = 'ACTIVE', 'Active'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        INACTIVE = 'INACTIVE', 'Inactive'
    
    class RestaurantType(models.TextChoices):
        VEG = 'VEG', 'Vegetarian'
        NON_VEG = 'NON_VEG', 'Non-Vegetarian'
        PURE_VEG = 'PURE_VEG', 'Pure Vegetarian'
    
    class OnboardingStatus(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Not Started'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUBMITTED = 'SUBMITTED', 'Submitted for Review'
        APPROVED = 'APPROVED', 'Approved'
        REVISIONS_REQUIRED = 'REVISIONS_REQUIRED', 'Revisions Required'
    
    class CuisineType(models.TextChoices):
        ITALIAN = 'ITALIAN', 'Italian'
        CHINESE = 'CHINESE', 'Chinese'
        INDIAN = 'INDIAN', 'Indian'
        MEXICAN = 'MEXICAN', 'Mexican'
        JAPANESE = 'JAPANESE', 'Japanese'
        AMERICAN = 'AMERICAN', 'American'
        THAI = 'THAI', 'Thai'
        MEDITERRANEAN = 'MEDITERRANEAN', 'Mediterranean'
        FAST_FOOD = 'FAST_FOOD', 'Fast Food'
        VEGETARIAN = 'VEGETARIAN', 'Vegetarian'
        VEGAN = 'VEGAN', 'Vegan'
        OTHER = 'OTHER', 'Other'
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restaurants')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cuisine_type = models.CharField(max_length=50, choices=CuisineType.choices)
    cuisine_types = ArrayField(models.CharField(max_length=50, choices=CuisineType.choices), default=list, blank=True)
    restaurant_type = models.CharField(max_length=20, choices=RestaurantType.choices, default=RestaurantType.NON_VEG)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    
    # Location - using standard DecimalField for now (PostGIS optional)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    billing_address = models.TextField(blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    
    # Business details
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    onboarding_status = models.CharField(max_length=30, choices=OnboardingStatus.choices, default=OnboardingStatus.NOT_STARTED)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_ratings = models.IntegerField(default=0)
    delivery_time_minutes = models.IntegerField(default=30)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_radius_km = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    
    # Operating hours (stored as JSON for flexibility)
    opening_hours = models.JSONField(default=dict)  # {monday: {open: "09:00", close: "22:00"}, ...}
    
    # Features
    accepts_delivery = models.BooleanField(default=True)
    accepts_pickup = models.BooleanField(default=False)
    is_pure_veg = models.BooleanField(default=False)
    is_halal = models.BooleanField(default=False)
    hygiene_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    has_offers = models.BooleanField(default=False)  # Computed field or manual flag
    cost_for_two = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Estimated cost for two
    estimated_preparation_time = models.IntegerField(default=20)
    manager_contact_name = models.CharField(max_length=255, blank=True)
    manager_contact_phone = models.CharField(max_length=20, blank=True)
    manager_contact_email = models.EmailField(blank=True)
    support_phone = models.CharField(max_length=20, blank=True)
    support_email = models.EmailField(blank=True)
    fssai_license_number = models.CharField(max_length=50, blank=True)
    gst_number = models.CharField(max_length=50, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc_code = models.CharField(max_length=20, blank=True)
    is_multi_branch = models.BooleanField(default=False)
    
    # Media
    logo = models.ImageField(upload_to='restaurants/logos/', blank=True, null=True)
    cover_image = models.ImageField(upload_to='restaurants/covers/', blank=True, null=True)
    logo_image_url = models.URLField(blank=True)
    hero_image_url = models.URLField(blank=True)
    
    # KYC Documents
    kyc_document = models.FileField(upload_to='restaurants/kyc/', blank=True, null=True)
    kyc_verified = models.BooleanField(default=False)
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Commission settings
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)  # Percentage
    
    class Meta:
        db_table = 'restaurants'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['cuisine_type']),
            models.Index(fields=['restaurant_type']),
            models.Index(fields=['rating']),
            models.Index(fields=['latitude', 'longitude']),  # For geo queries
            models.Index(fields=['onboarding_status']),
        ]
    
    def __str__(self):
        return self.name


class Menu(TimestampMixin, SoftDeleteMixin):
    """Menu model - each restaurant can have multiple menus (e.g., breakfast, lunch, dinner)"""
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menus')
    name = models.CharField(max_length=100)  # Breakfast, Lunch, Dinner, etc.
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    available_from = models.TimeField(null=True, blank=True)  # e.g., 09:00
    available_until = models.TimeField(null=True, blank=True)  # e.g., 22:00
    
    class Meta:
        db_table = 'menus'
        unique_together = [['restaurant', 'name']]
        indexes = [
            models.Index(fields=['restaurant', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class MenuCategory(TimestampMixin, SoftDeleteMixin):
    """Menu categories (e.g., Appetizers, Main Course, Desserts)"""
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'menu_categories'
        verbose_name_plural = 'Menu Categories'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['menu', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.menu.name} - {self.name}"


class MenuItem(TimestampMixin, SoftDeleteMixin):
    """Menu items"""
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    image_url = models.URLField(blank=True)
    
    # Availability
    is_available = models.BooleanField(default=True)
    inventory_count = models.IntegerField(null=True, blank=True)  # null = unlimited
    low_stock_threshold = models.IntegerField(default=10)
    
    # Item details
    preparation_time_minutes = models.IntegerField(default=15)
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_spicy = models.BooleanField(default=False)
    calories = models.IntegerField(null=True, blank=True)
    allergens = models.JSONField(default=list)  # ['gluten', 'dairy', 'nuts', etc.]
    macros = models.JSONField(default=dict)  # {protein: 20, carbs: 30, fat: 10}
    
    # Ratings
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_ratings = models.IntegerField(default=0)
    
    # Display
    display_order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'menu_items'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['rating']),
        ]
    
    def __str__(self):
        return f"{self.category.menu.restaurant.name} - {self.name}"
    
    @property
    def restaurant(self):
        return self.category.menu.restaurant


class ItemModifier(TimestampMixin, SoftDeleteMixin):
    """Item modifiers/add-ons (e.g., Extra cheese, Size options)"""
    class ModifierType(models.TextChoices):
        ADDON = 'ADDON', 'Add-on'
        VARIANT = 'VARIANT', 'Variant'
        CUSTOMIZATION = 'CUSTOMIZATION', 'Customization'
    
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='modifiers')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=ModifierType.choices, default=ModifierType.ADDON)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_required = models.BooleanField(default=False)  # For variants (e.g., size)
    is_available = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'item_modifiers'
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['menu_item', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.menu_item.name} - {self.name}"


class Promotion(TimestampMixin, SoftDeleteMixin):
    """Promotions and discounts"""
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', 'Percentage'
        FIXED = 'FIXED', 'Fixed Amount'
        BUY_ONE_GET_ONE = 'BUY_ONE_GET_ONE', 'Buy One Get One'
        FREE_DELIVERY = 'FREE_DELIVERY', 'Free Delivery'
        CASHBACK = 'CASHBACK', 'Cashback'
    
    class OfferType(models.TextChoices):
        RESTAURANT = 'RESTAURANT', 'Restaurant Offer'
        PLATFORM = 'PLATFORM', 'Platform Offer'
        BANK = 'BANK', 'Bank Offer'
        UPI = 'UPI', 'UPI Offer'
    
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='promotions', null=True, blank=True)
    offer_type = models.CharField(max_length=20, choices=OfferType.choices, default=OfferType.RESTAURANT)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=50, unique=True, blank=True)  # Some offers don't need codes
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Cashback specific
    cashback_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cashback_max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Bank/UPI specific
    applicable_banks = models.JSONField(default=list)  # ['HDFC', 'ICICI', etc.]
    applicable_upi_providers = models.JSONField(default=list)  # ['paytm', 'phonepe', etc.]
    
    # Validity
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Applicability
    applicable_items = models.ManyToManyField(MenuItem, blank=True)  # If empty, applies to all items
    applicable_categories = models.ManyToManyField(MenuCategory, blank=True)
    max_uses = models.IntegerField(null=True, blank=True)  # null = unlimited
    uses_count = models.IntegerField(default=0)
    max_uses_per_user = models.IntegerField(default=1)
    
    # Priority (higher = shown first)
    priority = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'promotions'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'valid_from', 'valid_until']),
            models.Index(fields=['restaurant']),
            models.Index(fields=['offer_type', 'is_active']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code or 'No Code'})"


class SearchHistory(TimestampMixin):
    """User search history"""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='search_history', null=True, blank=True)
    query = models.CharField(max_length=255)
    search_type = models.CharField(max_length=50, default='general')  # general, dish, ingredient, restaurant
    
    class Meta:
        db_table = 'search_history'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['query']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.query} - {self.user.email if self.user else 'Anonymous'}"


class PopularSearch(TimestampMixin):
    """Popular searches (aggregated)"""
    query = models.CharField(max_length=255, unique=True)
    search_count = models.IntegerField(default=1)
    last_searched = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'popular_searches'
        indexes = [
            models.Index(fields=['-search_count']),
            models.Index(fields=['-last_searched']),
        ]
        ordering = ['-search_count']
    
    def __str__(self):
        return f"{self.query} ({self.search_count})"


class RestaurantSettings(TimestampMixin, SoftDeleteMixin):
    """Runtime configuration for restaurants"""
    restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='settings')
    default_prep_time_minutes = models.IntegerField(default=20)
    max_delivery_distance_km = models.DecimalField(max_digits=5, decimal_places=2, default=8.00)
    auto_accept_orders = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    order_notifications = models.JSONField(default=dict)
    sla_threshold_minutes = models.IntegerField(default=35)
    kitchen_notes = models.TextField(blank=True)
    packaging_instructions = models.TextField(blank=True)
    supports_dine_in = models.BooleanField(default=False)
    supports_takeaway = models.BooleanField(default=True)
    supports_delivery = models.BooleanField(default=True)
    delivery_radius_settings = models.JSONField(default=dict)

    class Meta:
        db_table = 'restaurant_settings'
        indexes = [
            models.Index(fields=['restaurant']),
            models.Index(fields=['is_online']),
        ]

    def __str__(self):
        return f"Settings for {self.restaurant.name}"


class RestaurantBranch(TimestampMixin, SoftDeleteMixin):
    """Branches / outlets for a restaurant"""

    class BranchType(models.TextChoices):
        MAIN = 'MAIN', 'Main Kitchen'
        CLOUD = 'CLOUD', 'Cloud Kitchen'
        BILLING = 'BILLING', 'Billing Office'
        PICKUP = 'PICKUP', 'Pickup Counter'
        DINE_IN = 'DINE_IN', 'Dine-in Outlet'

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255)
    branch_code = models.CharField(max_length=50, blank=True)
    branch_type = models.CharField(max_length=20, choices=BranchType.choices, default=BranchType.MAIN)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    area = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    service_radius_km = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    contact_number = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    is_primary = models.BooleanField(default=False)
    supports_delivery = models.BooleanField(default=True)
    supports_pickup = models.BooleanField(default=True)
    supports_dine_in = models.BooleanField(default=False)

    class Meta:
        db_table = 'restaurant_branches'
        indexes = [
            models.Index(fields=['restaurant', 'branch_type']),
            models.Index(fields=['city', 'state']),
            models.Index(fields=['is_primary']),
        ]
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.restaurant.name} - {self.name}"


class ManagerProfile(TimestampMixin, SoftDeleteMixin):
    """Restaurant manager/staff profiles with permissions"""

    class ManagerRole(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        GENERAL_MANAGER = 'GENERAL_MANAGER', 'General Manager'
        KITCHEN_MANAGER = 'KITCHEN_MANAGER', 'Kitchen Manager'
        OPERATIONS = 'OPERATIONS', 'Operations Manager'
        FINANCE = 'FINANCE', 'Finance Manager'
        STAFF = 'STAFF', 'Staff'

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='managers')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_restaurants')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=30, choices=ManagerRole.choices, default=ManagerRole.GENERAL_MANAGER)
    is_primary = models.BooleanField(default=False)
    permissions = ArrayField(models.CharField(max_length=50), default=list, blank=True)

    class Meta:
        db_table = 'restaurant_managers'
        indexes = [
            models.Index(fields=['restaurant', 'role']),
            models.Index(fields=['email']),
            models.Index(fields=['is_primary']),
        ]

    def __str__(self):
        return f"{self.first_name} ({self.restaurant.name})"


class RestaurantDocument(TimestampMixin, SoftDeleteMixin):
    """Submitted documents for KYC/compliance"""

    class DocumentType(models.TextChoices):
        PAN = 'PAN', 'PAN Card'
        GST = 'GST', 'GST Certificate'
        FSSAI = 'FSSAI', 'FSSAI License'
        BANK = 'BANK', 'Bank Statement'
        CANCELLED_CHEQUE = 'CANCELLED_CHEQUE', 'Cancelled Cheque'
        MENU = 'MENU', 'Menu Document'
        OTHER = 'OTHER', 'Other'

    class DocumentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='documents')
    branch = models.ForeignKey(RestaurantBranch, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    document_number = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='restaurants/kyc/documents/')
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    needs_reupload = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'restaurant_documents'
        indexes = [
            models.Index(fields=['restaurant', 'document_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.document_type}"


class DocumentReviewLog(TimestampMixin):
    """Review history for restaurant documents"""
    document = models.ForeignKey(RestaurantDocument, on_delete=models.CASCADE, related_name='review_logs')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='document_reviews')
    status_before = models.CharField(max_length=20, blank=True)
    status_after = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'restaurant_document_reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"Review log for {self.document_id}"


class RestaurantAlert(TimestampMixin, SoftDeleteMixin):
    """Actionable alerts for restaurant dashboard"""

    class AlertType(models.TextChoices):
        SLA_BREACH = 'SLA_BREACH', 'SLA Breach'
        INVENTORY_LOW = 'INVENTORY_LOW', 'Low Inventory'
        NEW_REVIEW = 'NEW_REVIEW', 'New Review'
        PAYOUT = 'PAYOUT', 'Payout'
        REFUND_SPIKE = 'REFUND_SPIKE', 'Refund Spike'
        SYSTEM = 'SYSTEM', 'System Alert'

    class Severity(models.TextChoices):
        INFO = 'INFO', 'Info'
        WARNING = 'WARNING', 'Warning'
        CRITICAL = 'CRITICAL', 'Critical'

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='alerts')
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='alerts')
    alert_type = models.CharField(max_length=30, choices=AlertType.choices, default=AlertType.SYSTEM)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.INFO)
    title = models.CharField(max_length=255)
    message = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'restaurant_alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'alert_type']),
            models.Index(fields=['restaurant', 'is_read']),
            models.Index(fields=['severity']),
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.alert_type}"
