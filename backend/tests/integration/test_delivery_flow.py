"""
Integration tests for delivery flow
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from apps.deliveries.models import Delivery, DeliveryOffer, RiderShift, RiderLocation
from apps.orders.models import Order, Restaurant

User = get_user_model()


class DeliveryFlowIntegrationTestCase(TransactionTestCase):
    """Integration test for complete delivery flow"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.customer = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            role=User.Role.CUSTOMER
        )
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
        self.restaurant_owner = User.objects.create_user(
            email='restaurant@test.com',
            password='testpass123',
            role=User.Role.RESTAURANT
        )
        
        # Create restaurant and order
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner=self.restaurant_owner,
            address='123 Test St',
            phone='1234567890'
        )
        
        self.order = Order.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            total_amount=50.00,
            status=Order.Status.PENDING
        )
    
    def test_complete_delivery_flow(self):
        """Test complete delivery flow from offer to completion"""
        # 1. Rider starts shift
        self.client.force_authenticate(user=self.rider)
        response = self.client.post('/api/deliveries/shifts/start/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 2. Update rider location
        response = self.client.post('/api/deliveries/rider-locations/', {
            'latitude': 40.7128,
            'longitude': -74.0060,
            'accuracy': 10.0
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Create delivery
        delivery = Delivery.objects.create(
            order=self.order,
            rider=None,
            pickup_address='123 Pickup St',
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            delivery_address='456 Delivery St',
            delivery_latitude=40.7589,
            delivery_longitude=-73.9851
        )
        
        # 4. Create offer
        offer = DeliveryOffer.objects.create(
            delivery=delivery,
            rider=self.rider,
            estimated_earnings=15.00,
            distance_km=5.0,
            expires_at=timezone.now() + timedelta(minutes=5),
            status=DeliveryOffer.Status.SENT
        )
        
        # 5. Rider accepts offer
        response = self.client.post(f'/api/deliveries/offers/{offer.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, Delivery.Status.ACCEPTED)
        self.assertEqual(delivery.rider, self.rider)
        
        # 6. Rider picks up order
        response = self.client.post(f'/api/deliveries/deliveries/{delivery.id}/pickup/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, Delivery.Status.PICKED_UP)
        
        # 7. Rider completes delivery
        response = self.client.post(f'/api/deliveries/deliveries/{delivery.id}/complete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, Delivery.Status.DELIVERED)
        
        # 8. Verify order status
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.DELIVERED)

