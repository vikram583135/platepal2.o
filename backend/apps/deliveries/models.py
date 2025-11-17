from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.accounts.models import User, Address, TimestampMixin, SoftDeleteMixin
from apps.orders.models import Order


class Delivery(TimestampMixin, SoftDeleteMixin):
    """Delivery assignment and tracking"""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Assignment'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        ACCEPTED = 'ACCEPTED', 'Accepted by Rider'
        REJECTED = 'REJECTED', 'Rejected by Rider'
        ARRIVED_AT_PICKUP = 'ARRIVED_AT_PICKUP', 'Arrived at Pickup'
        PICKED_UP = 'PICKED_UP', 'Picked Up'
        IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
        DELIVERED = 'DELIVERED', 'Delivered'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    rider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries', limit_choices_to={'role': User.Role.DELIVERY})
    
    # Locations
    pickup_address = models.TextField()  # Restaurant address
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    estimated_pickup_time = models.DateTimeField(null=True, blank=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_pickup_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    
    # Earnings
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    distance_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Failure details
    failure_reason = models.TextField(blank=True)
    failure_code = models.CharField(max_length=50, blank=True)  # CUSTOMER_UNAVAILABLE, ADDRESS_INCORRECT, etc.
    
    # Safety
    is_contactless = models.BooleanField(default=False)
    delivery_photo = models.ImageField(upload_to='deliveries/photos/', blank=True, null=True)
    
    # Navigation & Route
    route_preview_data = models.JSONField(default=dict, blank=True)  # Route points, polyline, etc.
    estimated_distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_travel_time_minutes = models.IntegerField(null=True, blank=True)
    live_eta = models.DateTimeField(null=True, blank=True)  # Live ETA updates
    
    # Trip Status
    is_paused = models.BooleanField(default=False)
    paused_at = models.DateTimeField(null=True, blank=True)
    pause_reason = models.CharField(max_length=100, blank=True)
    resumed_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery Proof
    delivery_otp = models.CharField(max_length=10, blank=True)  # For contactless delivery verification
    signature_image = models.ImageField(upload_to='deliveries/signatures/', blank=True, null=True)
    unable_to_deliver_reason = models.CharField(max_length=100, blank=True)
    unable_to_deliver_code = models.CharField(max_length=50, blank=True)
    unable_to_deliver_photo = models.ImageField(upload_to='deliveries/unable_to_deliver/', blank=True, null=True)
    
    # Contact Information (masked)
    customer_phone_masked = models.CharField(max_length=20, blank=True)
    customer_name = models.CharField(max_length=150, blank=True)
    restaurant_phone_masked = models.CharField(max_length=20, blank=True)
    special_instructions = models.TextField(blank=True)
    
    class Meta:
        db_table = 'deliveries'
        indexes = [
            models.Index(fields=['rider', 'status']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Delivery for {self.order.order_number}"


class RiderLocation(TimestampMixin):
    """Real-time rider location tracking"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations', limit_choices_to={'role': User.Role.DELIVERY})
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True, blank=True)  # GPS accuracy in meters
    heading = models.FloatField(null=True, blank=True)  # Direction in degrees
    speed = models.FloatField(null=True, blank=True)  # Speed in m/s
    
    # Location tracking settings
    battery_level = models.IntegerField(null=True, blank=True)  # Battery percentage
    location_mode = models.CharField(max_length=20, default='BALANCED')  # BALANCED, BATTERY_SAVER, HIGH_ACCURACY
    is_moving = models.BooleanField(default=False)  # Estimated movement state
    
    # Geo-fencing
    near_pickup_zone = models.BooleanField(default=False)
    near_drop_zone = models.BooleanField(default=False)
    pickup_zone_entered_at = models.DateTimeField(null=True, blank=True)
    drop_zone_entered_at = models.DateTimeField(null=True, blank=True)
    
    # Offline support
    is_offline_sync = models.BooleanField(default=False)  # True if this was synced after being offline
    offline_queued_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'rider_locations'
        indexes = [
            models.Index(fields=['rider', '-created_at']),  # Most recent location per rider
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rider.email} at ({self.latitude}, {self.longitude})"


class RiderEarnings(TimestampMixin):
    """Rider earnings tracking"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earnings', limit_choices_to={'role': User.Role.DELIVERY})
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='earnings', null=True, blank=True)
    
    # Earnings breakdown
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    distance_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payout status
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    payout_period_start = models.DateField()
    payout_period_end = models.DateField()
    
    class Meta:
        db_table = 'rider_earnings'
        indexes = [
            models.Index(fields=['rider', 'is_paid']),
            models.Index(fields=['payout_period_start', 'payout_period_end']),
        ]
    
    def __str__(self):
        return f"Earnings for {self.rider.email} - {self.total_amount}"


class DeliveryDocument(TimestampMixin, SoftDeleteMixin):
    """Delivery rider documents (license, insurance, etc.)"""
    class DocumentType(models.TextChoices):
        LICENSE = 'LICENSE', 'Driver License'
        INSURANCE = 'INSURANCE', 'Insurance'
        VEHICLE_REGISTRATION = 'VEHICLE_REGISTRATION', 'Vehicle Registration'
        BACKGROUND_CHECK = 'BACKGROUND_CHECK', 'Background Check'
        OTHER = 'OTHER', 'Other'
    
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents', limit_choices_to={'role': User.Role.DELIVERY})
    document_type = models.CharField(max_length=50, choices=DocumentType.choices)
    document_file = models.FileField(upload_to='deliveries/documents/')
    document_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'delivery_documents'
        indexes = [
            models.Index(fields=['rider', 'is_verified']),
            models.Index(fields=['document_type']),
        ]
    
    def __str__(self):
        return f"{self.rider.email} - {self.document_type}"


class RiderProfile(TimestampMixin, SoftDeleteMixin):
    """Extended rider profile with KYC information"""
    rider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_profile', limit_choices_to={'role': User.Role.DELIVERY})
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    government_id_number = models.CharField(max_length=100, blank=True)
    government_id_file = models.FileField(upload_to='riders/government_id/', blank=True, null=True)
    selfie_photo = models.ImageField(upload_to='riders/selfies/', blank=True, null=True)
    
    # Vehicle Information
    vehicle_type = models.CharField(max_length=50, blank=True)  # BIKE, CAR, SCOOTER, etc.
    vehicle_registration_number = models.CharField(max_length=50, blank=True)
    vehicle_registration_file = models.FileField(upload_to='riders/vehicle_registration/', blank=True, null=True)
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_color = models.CharField(max_length=50, blank=True)
    
    # Driver License
    driver_license_number = models.CharField(max_length=100, blank=True)
    driver_license_file = models.FileField(upload_to='riders/driver_license/', blank=True, null=True)
    driver_license_expiry = models.DateField(null=True, blank=True)
    
    # Additional Information
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    
    # Profile Completion
    profile_completion_percentage = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        db_table = 'rider_profiles'
        indexes = [
            models.Index(fields=['rider']),
            models.Index(fields=['profile_completion_percentage']),
        ]
    
    def __str__(self):
        return f"Profile for {self.rider.email}"
    
    def calculate_completion_percentage(self):
        """Calculate profile completion percentage"""
        fields_required = [
            self.date_of_birth,
            self.government_id_number,
            self.government_id_file,
            self.selfie_photo,
            self.vehicle_type,
            self.vehicle_registration_number,
            self.vehicle_registration_file,
            self.driver_license_number,
            self.driver_license_file,
            self.emergency_contact_name,
            self.emergency_contact_phone,
        ]
        completed = sum(1 for field in fields_required if field)
        return int((completed / len(fields_required)) * 100)


class RiderBankDetail(TimestampMixin, SoftDeleteMixin):
    """Bank details for rider payouts"""
    rider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='bank_detail', limit_choices_to={'role': User.Role.DELIVERY})
    
    # Bank Information
    bank_name = models.CharField(max_length=255)
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20, blank=True)
    bank_branch = models.CharField(max_length=255, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    cancelled_cheque_file = models.FileField(upload_to='riders/cancelled_cheques/', blank=True, null=True)
    
    class Meta:
        db_table = 'rider_bank_details'
        indexes = [
            models.Index(fields=['rider', 'is_verified']),
        ]
    
    def __str__(self):
        return f"Bank details for {self.rider.email}"


class RiderOnboarding(TimestampMixin):
    """Rider onboarding progress tracking"""
    rider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding', limit_choices_to={'role': User.Role.DELIVERY})
    
    class OnboardingStatus(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Not Started'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        PENDING_VERIFICATION = 'PENDING_VERIFICATION', 'Pending Verification'
        VERIFIED = 'VERIFIED', 'Verified'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
    
    status = models.CharField(max_length=50, choices=OnboardingStatus.choices, default=OnboardingStatus.NOT_STARTED)
    
    # Checklist items
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)
    documents_uploaded = models.BooleanField(default=False)
    bank_details_added = models.BooleanField(default=False)
    background_check_completed = models.BooleanField(default=False)
    agreement_signed = models.BooleanField(default=False)
    induction_video_watched = models.BooleanField(default=False)
    
    # Progress tracking
    current_step = models.IntegerField(default=0)
    completed_steps = models.JSONField(default=list)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Referral
    referral_code_used = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'rider_onboarding'
        indexes = [
            models.Index(fields=['rider', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Onboarding for {self.rider.email} - {self.status}"
    
    def get_completion_percentage(self):
        """Calculate onboarding completion percentage"""
        items = [
            self.phone_verified,
            self.email_verified,
            self.profile_completed,
            self.documents_uploaded,
            self.bank_details_added,
            self.background_check_completed,
            self.agreement_signed,
            self.induction_video_watched,
        ]
        completed = sum(1 for item in items if item)
        return int((completed / len(items)) * 100)


class RiderBackgroundCheck(TimestampMixin, SoftDeleteMixin):
    """Background check status for riders"""
    rider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='background_check', limit_choices_to={'role': User.Role.DELIVERY})
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXPIRED = 'EXPIRED', 'Expired'
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Check details
    initiated_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    report_id = models.CharField(max_length=100, blank=True)
    report_file = models.FileField(upload_to='riders/background_checks/', blank=True, null=True)
    notes = models.TextField(blank=True)
    
    # Provider (if using external service)
    provider = models.CharField(max_length=100, blank=True)
    provider_reference = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'rider_background_checks'
        indexes = [
            models.Index(fields=['rider', 'status']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Background check for {self.rider.email} - {self.status}"
    
    def is_expired(self):
        """Check if background check has expired"""
        if self.expires_at and self.status == self.Status.APPROVED:
            return timezone.now() > self.expires_at
        return False


class RiderReferral(TimestampMixin):
    """Referral system for riders"""
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrals_sent', limit_choices_to={'role': User.Role.DELIVERY})
    referred_user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='referral_received', null=True, blank=True)
    
    # Referral codes
    referral_code = models.CharField(max_length=50, unique=True)
    referred_email = models.EmailField(blank=True)
    referred_phone = models.CharField(max_length=20, blank=True)
    
    # Status
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        EXPIRED = 'EXPIRED', 'Expired'
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Bonuses
    referrer_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    referred_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Tracking
    signup_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'rider_referrals'
        indexes = [
            models.Index(fields=['referrer', 'status']),
            models.Index(fields=['referral_code']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Referral {self.referral_code} - {self.status}"


class RiderShift(TimestampMixin):
    """Rider shift management"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shifts', limit_choices_to={'role': User.Role.DELIVERY})
    
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        ACTIVE = 'ACTIVE', 'Active'
        PAUSED = 'PAUSED', 'Paused'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    
    # Shift times
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    time_online_minutes = models.IntegerField(default=0)
    idle_time_minutes = models.IntegerField(default=0)
    distance_traveled_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    deliveries_completed = models.IntegerField(default=0)
    earnings_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Auto-offline settings
    auto_offline_enabled = models.BooleanField(default=False)
    auto_offline_after_minutes = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'rider_shifts'
        indexes = [
            models.Index(fields=['rider', 'status']),
            models.Index(fields=['scheduled_start', 'scheduled_end']),
            models.Index(fields=['status', 'actual_start']),
        ]
        ordering = ['-actual_start']
    
    def __str__(self):
        return f"Shift for {self.rider.email} - {self.status}"


class DeliveryOffer(TimestampMixin):
    """Job offers for riders (separate from Delivery assignment)"""
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='offers')
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_offers', limit_choices_to={'role': User.Role.DELIVERY}, null=True, blank=True)
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'
        EXPIRED = 'EXPIRED', 'Expired'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Offer details
    estimated_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_pickup_time = models.DateTimeField()
    estimated_drop_time = models.DateTimeField()
    
    # Expiry
    expires_at = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    declined_at = models.DateTimeField(null=True, blank=True)
    
    # Decline reason
    decline_reason = models.CharField(max_length=100, blank=True)
    decline_code = models.CharField(max_length=50, blank=True)
    
    # Priority
    priority = models.IntegerField(default=0)  # Higher = more priority
    is_surge = models.BooleanField(default=False)
    surge_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    
    class Meta:
        db_table = 'delivery_offers'
        indexes = [
            models.Index(fields=['rider', 'status']),
            models.Index(fields=['delivery', 'status']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['priority', '-created_at']),
        ]
    
    def __str__(self):
        return f"Offer for {self.delivery.order.order_number} - {self.status}"
    
    def is_expired(self):
        """Check if offer has expired"""
        return timezone.now() > self.expires_at


class RiderWallet(TimestampMixin, SoftDeleteMixin):
    """Wallet for riders (separate from customer wallet)"""
    rider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_wallet', limit_choices_to={'role': User.Role.DELIVERY})
    
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    
    # Pending payout
    pending_payout = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_payout_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'rider_wallets'
        indexes = [
            models.Index(fields=['rider']),
        ]
    
    def __str__(self):
        return f"Wallet for {self.rider.email} - {self.balance} {self.currency}"


class RiderWalletTransaction(TimestampMixin):
    """Wallet transaction history for riders"""
    
    class TransactionType(models.TextChoices):
        CREDIT = 'CREDIT', 'Credit'
        DEBIT = 'DEBIT', 'Debit'
    
    class TransactionSource(models.TextChoices):
        EARNINGS = 'EARNINGS', 'Earnings'
        PAYOUT = 'PAYOUT', 'Payout'
        BONUS = 'BONUS', 'Bonus'
        REFUND = 'REFUND', 'Refund'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
        REFERRAL_BONUS = 'REFERRAL_BONUS', 'Referral Bonus'
    
    wallet = models.ForeignKey(RiderWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    source = models.CharField(max_length=20, choices=TransactionSource.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    
    # Related entities
    delivery = models.ForeignKey(Delivery, on_delete=models.SET_NULL, null=True, blank=True)
    earnings = models.ForeignKey(RiderEarnings, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'rider_wallet_transactions'
        indexes = [
            models.Index(fields=['wallet', '-created_at']),
            models.Index(fields=['transaction_type', 'source']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} {self.amount} - {self.wallet.rider.email}"


class RiderRating(TimestampMixin):
    """Ratings and feedback for riders"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings', limit_choices_to={'role': User.Role.DELIVERY})
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rider_ratings_given', limit_choices_to={'role': User.Role.CUSTOMER})
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='ratings', null=True, blank=True)
    
    rating = models.IntegerField(validators=[MinValueValidator(1)])  # 1-5 stars
    comment = models.TextField(blank=True)
    
    # Categories
    punctuality_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    communication_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    service_rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    
    is_visible = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'rider_ratings'
        indexes = [
            models.Index(fields=['rider', '-created_at']),
            models.Index(fields=['customer']),
            models.Index(fields=['delivery']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Rating {self.rating} for {self.rider.email}"


class RiderDispute(TimestampMixin, SoftDeleteMixin):
    """Disputes and complaints for riders"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='disputes', limit_choices_to={'role': User.Role.DELIVERY})
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='disputes', null=True, blank=True)
    
    class DisputeType(models.TextChoices):
        CHARGEBACK = 'CHARGEBACK', 'Chargeback'
        FALSE_COMPLAINT = 'FALSE_COMPLAINT', 'False Complaint'
        PAYMENT_ISSUE = 'PAYMENT_ISSUE', 'Payment Issue'
        RATING_DISPUTE = 'RATING_DISPUTE', 'Rating Dispute'
        OTHER = 'OTHER', 'Other'
    
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'
    
    dispute_type = models.CharField(max_length=50, choices=DisputeType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    evidence_photos = models.JSONField(default=list)  # List of photo URLs
    
    # Resolution
    resolution = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_disputes')
    
    class Meta:
        db_table = 'rider_disputes'
        indexes = [
            models.Index(fields=['rider', 'status']),
            models.Index(fields=['dispute_type', 'status']),
        ]
    
    def __str__(self):
        return f"Dispute {self.dispute_type} for {self.rider.email} - {self.status}"


class EmergencyContact(TimestampMixin, SoftDeleteMixin):
    """Emergency contacts for riders"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emergency_contacts', limit_choices_to={'role': User.Role.DELIVERY})
    
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    relationship = models.CharField(max_length=50)
    is_primary = models.BooleanField(default=False)
    
    # Location sharing
    share_location_with_emergency = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'emergency_contacts'
        indexes = [
            models.Index(fields=['rider', 'is_primary']),
        ]
    
    def __str__(self):
        return f"Emergency contact for {self.rider.email}: {self.name}"


class AutoAcceptRule(TimestampMixin, SoftDeleteMixin):
    """Auto-accept rules for riders"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auto_accept_rules', limit_choices_to={'role': User.Role.DELIVERY})
    
    is_enabled = models.BooleanField(default=False)
    
    # Rules
    max_distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_earnings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_earnings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    allowed_areas = models.JSONField(default=list)  # List of area/zone IDs
    
    # Priority
    priority = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'auto_accept_rules'
        indexes = [
            models.Index(fields=['rider', 'is_enabled']),
        ]
    
    def __str__(self):
        return f"Auto-accept rule for {self.rider.email} - {'Enabled' if self.is_enabled else 'Disabled'}"
    
    def matches_offer(self, offer):
        """Check if offer matches this rule"""
        if not self.is_enabled:
            return False
        
        if self.max_distance_km and offer.distance_km > self.max_distance_km:
            return False
        
        if self.min_earnings and offer.estimated_earnings < self.min_earnings:
            return False
        
        if self.max_earnings and offer.estimated_earnings > self.max_earnings:
            return False
        
        return True


class Fleet(TimestampMixin, SoftDeleteMixin):
    """Fleet management"""
    name = models.CharField(max_length=255)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_fleets', limit_choices_to={'role__in': [User.Role.ADMIN, User.Role.DELIVERY]})
    
    # Fleet details
    description = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'fleets'
        indexes = [
            models.Index(fields=['manager', 'is_active']),
        ]
    
    def __str__(self):
        return f"Fleet: {self.name}"


class FleetRider(TimestampMixin):
    """Riders in a fleet"""
    fleet = models.ForeignKey(Fleet, on_delete=models.CASCADE, related_name='riders')
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fleet_memberships', limit_choices_to={'role': User.Role.DELIVERY})
    
    # Assignment
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fleet_riders'
        unique_together = [['fleet', 'rider']]
        indexes = [
            models.Index(fields=['fleet', 'is_active']),
            models.Index(fields=['rider', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.rider.email} in {self.fleet.name}"


class RiderAgreement(TimestampMixin):
    """Rider agreements with versioning"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agreements', limit_choices_to={'role': User.Role.DELIVERY})
    
    agreement_version = models.CharField(max_length=50)
    agreement_text = models.TextField()
    agreed_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'rider_agreements'
        indexes = [
            models.Index(fields=['rider', '-agreed_at']),
            models.Index(fields=['agreement_version']),
        ]
        ordering = ['-agreed_at']
    
    def __str__(self):
        return f"Agreement {self.agreement_version} for {self.rider.email}"


class OfflineAction(TimestampMixin):
    """Offline action queue for riders"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offline_actions', limit_choices_to={'role': User.Role.DELIVERY})
    
    class ActionType(models.TextChoices):
        ACCEPT_OFFER = 'ACCEPT_OFFER', 'Accept Offer'
        DECLINE_OFFER = 'DECLINE_OFFER', 'Decline Offer'
        COMPLETE_DELIVERY = 'COMPLETE_DELIVERY', 'Complete Delivery'
        UPDATE_LOCATION = 'UPDATE_LOCATION', 'Update Location'
        PAUSE_TRIP = 'PAUSE_TRIP', 'Pause Trip'
        RESUME_TRIP = 'RESUME_TRIP', 'Resume Trip'
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SYNCING = 'SYNCING', 'Syncing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
    
    action_type = models.CharField(max_length=50, choices=ActionType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Action data
    action_data = models.JSONField(default=dict)  # Store the action payload
    resource_id = models.CharField(max_length=100, blank=True)  # ID of the resource (delivery_id, offer_id, etc.)
    
    # Retry logic
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=5)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Sync
    synced_at = models.DateTimeField(null=True, blank=True)
    sync_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'offline_actions'
        indexes = [
            models.Index(fields=['rider', 'status']),
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['action_type', 'status']),
        ]
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.action_type} for {self.rider.email} - {self.status}"


class TripLog(TimestampMixin):
    """Trip logs for analytics and reporting"""
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_logs', limit_choices_to={'role': User.Role.DELIVERY})
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='trip_logs')
    
    # Trip metrics
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_time_minutes = models.IntegerField(default=0)
    idle_time_minutes = models.IntegerField(default=0)
    
    # Timestamps
    trip_started_at = models.DateTimeField()
    trip_ended_at = models.DateTimeField(null=True, blank=True)
    pickup_arrived_at = models.DateTimeField(null=True, blank=True)
    pickup_completed_at = models.DateTimeField(null=True, blank=True)
    delivery_arrived_at = models.DateTimeField(null=True, blank=True)
    delivery_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Earnings
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    distance_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    time_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    surge_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Route data
    route_taken = models.JSONField(default=list)  # List of location points
    route_efficiency = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Efficiency percentage
    
    class Meta:
        db_table = 'trip_logs'
        indexes = [
            models.Index(fields=['rider', '-trip_started_at']),
            models.Index(fields=['delivery']),
            models.Index(fields=['trip_started_at']),
        ]
        ordering = ['-trip_started_at']
    
    def __str__(self):
        return f"Trip log for {self.delivery.order.order_number} - {self.rider.email}"


class RiderSettings(TimestampMixin):
    """Rider app settings and preferences"""
    rider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_settings', limit_choices_to={'role': User.Role.DELIVERY})
    
    # Location tracking
    location_tracking_enabled = models.BooleanField(default=True)
    location_mode = models.CharField(max_length=20, default='BALANCED')  # BALANCED, BATTERY_SAVER, HIGH_ACCURACY
    location_update_interval_moving = models.IntegerField(default=5)  # Seconds when moving
    location_update_interval_idle = models.IntegerField(default=30)  # Seconds when idle
    share_location_during_shift_only = models.BooleanField(default=True)
    
    # Notifications
    push_notifications_enabled = models.BooleanField(default=True)
    sound_alerts_enabled = models.BooleanField(default=True)
    offer_sound_enabled = models.BooleanField(default=True)
    snooze_mode_enabled = models.BooleanField(default=False)
    snooze_until = models.DateTimeField(null=True, blank=True)
    
    # Navigation
    preferred_navigation_app = models.CharField(max_length=50, default='GOOGLE_MAPS')  # GOOGLE_MAPS, WAZE, APPLE_MAPS
    
    # Auto-accept
    auto_accept_enabled = models.BooleanField(default=False)
    
    # Privacy
    location_privacy_enabled = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'rider_settings'
        indexes = [
            models.Index(fields=['rider']),
        ]
    
    def __str__(self):
        return f"Settings for {self.rider.email}"

