"""
Unit tests for advanced features
"""
import unittest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

try:
    from apps.deliveries.models_advanced import (
        RiderAchievement, RiderLevel, MLETAPrediction,
        VoiceCommand, MultiTenantFleet, TenantRider
    )
    from apps.deliveries.services_advanced import (
        check_and_award_achievements, add_points_to_rider,
        predict_ml_eta, process_voice_command, get_tenant_fleet_for_rider
    )
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False


class AdvancedFeaturesTestCase(TestCase):
    """Test advanced features"""
    
    def setUp(self):
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
    
    @unittest.skipUnless(ADVANCED_FEATURES_AVAILABLE, "Advanced features not available")
    def test_add_points_to_rider(self):
        """Test adding points to rider level"""
        add_points_to_rider(self.rider, 50)
        
        rider_level = RiderLevel.objects.get(rider=self.rider)
        self.assertEqual(rider_level.total_points, 50)
        self.assertEqual(rider_level.level, 1)
    
    @unittest.skipUnless(ADVANCED_FEATURES_AVAILABLE, "Advanced features not available")
    def test_level_up(self):
        """Test rider level up"""
        rider_level = RiderLevel.objects.create(
            rider=self.rider,
            level=1,
            total_points=0,
            points_needed_for_next_level=100
        )
        
        # Add enough points to level up
        add_points_to_rider(self.rider, 100)
        
        rider_level.refresh_from_db()
        self.assertEqual(rider_level.level, 2)
        self.assertGreater(rider_level.points_needed_for_next_level, 100)
    
    @unittest.skipUnless(ADVANCED_FEATURES_AVAILABLE, "Advanced features not available")
    def test_voice_command_processing(self):
        """Test voice command processing"""
        voice_cmd, result = process_voice_command(
            self.rider,
            spoken_text='Start shift',
            recognized_text='start shift',
            command_type=VoiceCommand.CommandType.START_SHIFT
        )
        
        self.assertIsNotNone(voice_cmd)
        self.assertEqual(voice_cmd.command_type, VoiceCommand.CommandType.START_SHIFT)
    
    @unittest.skipUnless(ADVANCED_FEATURES_AVAILABLE, "Advanced features not available")
    def test_multi_tenant_fleet(self):
        """Test multi-tenant fleet"""
        fleet = MultiTenantFleet.objects.create(
            name='Test Fleet',
            organization_code='TEST001',
            company_name='Test Company',
            contact_email='fleet@test.com'
        )
        
        tenant_rider = TenantRider.objects.create(
            tenant_fleet=fleet,
            rider=self.rider,
            employee_id='EMP001',
            is_active=True
        )
        
        self.assertEqual(tenant_rider.tenant_fleet, fleet)
        self.assertEqual(tenant_rider.rider, self.rider)
        
        # Get tenant fleet for rider
        retrieved_fleet = get_tenant_fleet_for_rider(self.rider)
        self.assertEqual(retrieved_fleet, fleet)


if not ADVANCED_FEATURES_AVAILABLE:
    print("Skipping advanced features tests - models_advanced.py not available")

