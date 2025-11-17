"""
Unit tests for deliveries services
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.deliveries.services import (
    calculate_distance, calculate_eta, generate_navigation_deep_link,
    calculate_earnings_breakdown, calculate_surge_multiplier, mask_phone_number
)

User = get_user_model()


class ServicesTestCase(TestCase):
    """Test deliveries services"""
    
    def test_calculate_distance(self):
        """Test distance calculation using Haversine formula"""
        # Distance between New York (40.7128, -74.0060) and Philadelphia (39.9526, -75.1652)
        # Should be approximately 94.7 km
        distance = calculate_distance(40.7128, -74.0060, 39.9526, -75.1652)
        self.assertAlmostEqual(distance, 94.7, delta=5.0)  # Allow 5km tolerance
    
    def test_calculate_eta(self):
        """Test ETA calculation"""
        # 10 km at 30 km/h should take 20 minutes
        eta = calculate_eta(10, 30)
        self.assertEqual(eta, 20)
        
        # 5 km at 60 km/h should take 5 minutes
        eta = calculate_eta(5, 60)
        self.assertEqual(eta, 5)
    
    def test_generate_navigation_deep_link(self):
        """Test navigation deep link generation"""
        link = generate_navigation_deep_link(
            40.7128, -74.0060,  # NYC
            40.7589, -73.9851,  # Central Park
            'GOOGLE_MAPS'
        )
        self.assertIn('google.com/maps', link)
        self.assertIn('40.7128', link)
        self.assertIn('40.7589', link)
    
    def test_calculate_earnings_breakdown(self):
        """Test earnings breakdown calculation"""
        breakdown = calculate_earnings_breakdown(
            base_fee=10.00,
            distance_km=5.0,
            time_minutes=15,
            surge_multiplier=1.5,
            tip=2.00
        )
        
        self.assertEqual(breakdown['surge_multiplier'], 1.5)
        self.assertEqual(breakdown['tip_amount'], 2.00)
        self.assertGreater(breakdown['total_earnings'], 0)
    
    def test_mask_phone_number(self):
        """Test phone number masking"""
        masked = mask_phone_number('1234567890')
        self.assertEqual(masked, '***-***-7890')
        
        masked = mask_phone_number('+1234567890')
        self.assertEqual(masked, '***-***-7890')
        
        # Short number
        masked = mask_phone_number('123')
        self.assertEqual(masked, '***-***-****')

