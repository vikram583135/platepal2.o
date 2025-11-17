"""
Advanced features models for deliveries app
"""
from django.db import models
from django.utils import timezone
from apps.accounts.models import User, TimestampMixin, SoftDeleteMixin
from apps.deliveries.models import Delivery, RiderShift


class RiderAchievement(TimestampMixin):
    """Rider achievements and badges (Gamification)"""
    
    class AchievementType(models.TextChoices):
        FIRST_DELIVERY = 'FIRST_DELIVERY', 'First Delivery'
        COMPLETE_10 = 'COMPLETE_10', 'Complete 10 Deliveries'
        COMPLETE_50 = 'COMPLETE_50', 'Complete 50 Deliveries'
        COMPLETE_100 = 'COMPLETE_100', 'Complete 100 Deliveries'
        COMPLETE_500 = 'COMPLETE_500', 'Complete 500 Deliveries'
        PERFECT_RATING = 'PERFECT_RATING', 'Perfect 5-Star Rating'
        FAST_DELIVERY = 'FAST_DELIVERY', 'Fast Delivery'
        NIGHT_OWL = 'NIGHT_OWL', 'Night Owl'
        EARLY_BIRD = 'EARLY_BIRD', 'Early Bird'
        WEEKEND_WARRIOR = 'WEEKEND_WARRIOR', 'Weekend Warrior'
        STREAK_7 = 'STREAK_7', '7 Day Streak'
        STREAK_30 = 'STREAK_30', '30 Day Streak'
        MILEAGE_MILESTONE = 'MILEAGE_MILESTONE', 'Mileage Milestone'
    
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements', limit_choices_to={'role': User.Role.DELIVERY})
    achievement_type = models.CharField(max_length=50, choices=AchievementType.choices)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon_url = models.URLField(blank=True)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    # Points/Rewards
    points_awarded = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'rider_achievements'
        indexes = [
            models.Index(fields=['rider', '-earned_at']),
            models.Index(fields=['achievement_type']),
        ]
        unique_together = [['rider', 'achievement_type']]
        ordering = ['-earned_at']
    
    def __str__(self):
        return f"{self.title} - {self.rider.email}"


class RiderLevel(TimestampMixin):
    """Rider leveling system (Gamification)"""
    
    rider = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_level', limit_choices_to={'role': User.Role.DELIVERY})
    level = models.IntegerField(default=1)
    total_points = models.IntegerField(default=0)
    current_level_points = models.IntegerField(default=0)
    points_needed_for_next_level = models.IntegerField(default=100)
    
    # Statistics
    total_deliveries = models.IntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    last_level_up_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'rider_levels'
        indexes = [
            models.Index(fields=['rider']),
            models.Index(fields=['level', '-total_points']),
        ]
    
    def __str__(self):
        return f"Level {self.level} - {self.rider.email}"
    
    def add_points(self, points):
        """Add points and check for level up"""
        self.total_points += points
        self.current_level_points += points
        
        # Check for level up
        while self.current_level_points >= self.points_needed_for_next_level:
            self.current_level_points -= self.points_needed_for_next_level
            self.level_up()
        
        self.save()
    
    def level_up(self):
        """Level up the rider"""
        self.level += 1
        # Increase points needed exponentially
        self.points_needed_for_next_level = int(self.points_needed_for_next_level * 1.5)
        self.last_level_up_at = timezone.now()
        
        # Award achievement if reaching milestone levels
        if self.level in [5, 10, 20, 50, 100]:
            RiderAchievement.objects.get_or_create(
                rider=self.rider,
                achievement_type=f'LEVEL_{self.level}',
                defaults={
                    'title': f'Level {self.level} Achiever',
                    'description': f'Reached level {self.level}',
                    'points_awarded': self.level * 10
                }
            )


class MLETAPrediction(TimestampMixin):
    """ML-based ETA predictions"""
    
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='eta_predictions')
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eta_predictions', limit_choices_to={'role': User.Role.DELIVERY})
    
    # Predictions
    ml_predicted_eta_minutes = models.IntegerField(null=True, blank=True)
    ml_predicted_distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # 0-1 scale
    
    # Actual values (for training)
    actual_eta_minutes = models.IntegerField(null=True, blank=True)
    actual_distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Features used for prediction
    traffic_conditions = models.CharField(max_length=50, blank=True)  # LOW, MEDIUM, HIGH
    weather_conditions = models.CharField(max_length=50, blank=True)  # CLEAR, RAIN, SNOW, etc.
    time_of_day = models.TimeField(null=True, blank=True)
    day_of_week = models.IntegerField(null=True, blank=True)  # 0-6 (Monday-Sunday)
    
    # Model metadata
    model_version = models.CharField(max_length=50, blank=True)
    prediction_timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ml_eta_predictions'
        indexes = [
            models.Index(fields=['delivery', 'rider']),
            models.Index(fields=['prediction_timestamp']),
            models.Index(fields=['confidence_score']),
        ]
    
    def __str__(self):
        return f"ETA Prediction for Delivery {self.delivery.id} - {self.ml_predicted_eta_minutes} min"


class VoiceCommand(TimestampMixin):
    """Voice command tracking for riders"""
    
    class CommandType(models.TextChoices):
        ACCEPT_OFFER = 'ACCEPT_OFFER', 'Accept Offer'
        DECLINE_OFFER = 'DECLINE_OFFER', 'Decline Offer'
        START_SHIFT = 'START_SHIFT', 'Start Shift'
        END_SHIFT = 'END_SHIFT', 'End Shift'
        PAUSE_TRIP = 'PAUSE_TRIP', 'Pause Trip'
        RESUME_TRIP = 'RESUME_TRIP', 'Resume Trip'
        NAVIGATE = 'NAVIGATE', 'Navigate'
        CALL_CUSTOMER = 'CALL_CUSTOMER', 'Call Customer'
        CALL_RESTAURANT = 'CALL_RESTAURANT', 'Call Restaurant'
        SOS = 'SOS', 'Emergency SOS'
        OTHER = 'OTHER', 'Other'
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSED = 'PROCESSED', 'Processed'
        FAILED = 'FAILED', 'Failed'
    
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voice_commands', limit_choices_to={'role': User.Role.DELIVERY})
    command_type = models.CharField(max_length=50, choices=CommandType.choices)
    spoken_text = models.TextField()  # Original spoken command
    recognized_text = models.TextField()  # Recognized text from speech-to-text
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # Context
    delivery = models.ForeignKey(Delivery, on_delete=models.SET_NULL, null=True, blank=True)
    accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # 0-1 scale
    
    # Audio metadata
    audio_file_url = models.URLField(blank=True, null=True)
    duration_seconds = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'voice_commands'
        indexes = [
            models.Index(fields=['rider', '-created_at']),
            models.Index(fields=['command_type', 'status']),
            models.Index(fields=['status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.command_type} - {self.rider.email} - {self.status}"


class MultiTenantFleet(TimestampMixin, SoftDeleteMixin):
    """Multi-tenant fleet management for organizations"""
    
    name = models.CharField(max_length=255)
    organization_code = models.CharField(max_length=50, unique=True)  # Unique identifier for organization
    description = models.TextField(blank=True)
    
    # Organization details
    company_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    max_riders = models.IntegerField(default=100, null=True, blank=True)
    custom_branding_enabled = models.BooleanField(default=False)
    
    # Branding (if enabled)
    logo_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, blank=True)  # Hex color
    secondary_color = models.CharField(max_length=7, blank=True)  # Hex color
    
    # Configuration
    custom_settings = models.JSONField(default=dict)  # Custom app settings per tenant
    
    class Meta:
        db_table = 'multi_tenant_fleets'
        indexes = [
            models.Index(fields=['organization_code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.organization_code})"


class TenantRider(TimestampMixin):
    """Rider association with tenant fleet"""
    
    tenant_fleet = models.ForeignKey(MultiTenantFleet, on_delete=models.CASCADE, related_name='tenant_riders')
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_associations', limit_choices_to={'role': User.Role.DELIVERY})
    
    # Rider details in tenant context
    employee_id = models.CharField(max_length=50, blank=True)  # Company employee ID
    department = models.CharField(max_length=100, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenant_riders'
        indexes = [
            models.Index(fields=['tenant_fleet', 'rider']),
            models.Index(fields=['tenant_fleet', 'is_active']),
        ]
        unique_together = [['tenant_fleet', 'rider']]
    
    def __str__(self):
        return f"{self.rider.email} - {self.tenant_fleet.name}"

