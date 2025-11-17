"""
Unit tests for deliveries views
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from apps.deliveries.models import (
    Delivery, RiderShift, DeliveryOffer, RiderWallet,
    RiderLocation, OfflineAction, TripLog, RiderSettings
)
from apps.orders.models import Order, Restaurant

User = get_user_model()


class DeliveryViewSetTestCase(TestCase):
    """Test DeliveryViewSet"""
    
    def setUp(self):
        self.client = APIClient()
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
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner=self.restaurant_owner,
            address='123 Test St',
            phone='1234567890'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            total_amount=50.00
        )
        self.delivery = Delivery.objects.create(
            order=self.order,
            rider=self.rider,
            pickup_address='123 Pickup St',
            delivery_address='456 Delivery St',
            status=Delivery.Status.ACCEPTED
        )
    
    def test_list_deliveries_as_rider(self):
        """Test rider can list their deliveries"""
        self.client.force_authenticate(user=self.rider)
        response = self.client.get('/api/deliveries/deliveries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_pause_delivery(self):
        """Test pausing a delivery"""
        self.client.force_authenticate(user=self.rider)
        response = self.client.post(
            f'/api/deliveries/deliveries/{self.delivery.id}/pause/',
            {'reason': 'Short break'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.delivery.refresh_from_db()
        self.assertTrue(self.delivery.is_paused)
    
    def test_resume_delivery(self):
        """Test resuming a paused delivery"""
        self.delivery.is_paused = True
        self.delivery.paused_at = timezone.now()
        self.delivery.save()
        
        self.client.force_authenticate(user=self.rider)
        response = self.client.post(
            f'/api/deliveries/deliveries/{self.delivery.id}/resume/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.delivery.refresh_from_db()
        self.assertFalse(self.delivery.is_paused)
    
    def test_unable_to_deliver(self):
        """Test marking delivery as unable to deliver"""
        self.delivery.status = Delivery.Status.IN_TRANSIT
        self.delivery.save()
        
        self.client.force_authenticate(user=self.rider)
        response = self.client.post(
            f'/api/deliveries/deliveries/{self.delivery.id}/unable_to_deliver/',
            {
                'reason': 'Customer not available',
                'code': 'CUSTOMER_UNAVAILABLE'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, Delivery.Status.FAILED)


class RiderShiftViewSetTestCase(TestCase):
    """Test RiderShiftViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
    
    def test_start_shift(self):
        """Test starting a shift"""
        self.client.force_authenticate(user=self.rider)
        response = self.client.post('/api/deliveries/shifts/start/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RiderShift.objects.filter(
            rider=self.rider,
            status=RiderShift.Status.ACTIVE
        ).exists())
    
    def test_stop_shift(self):
        """Test stopping a shift"""
        shift = RiderShift.objects.create(
            rider=self.rider,
            status=RiderShift.Status.ACTIVE,
            actual_start_time=timezone.now()
        )
        
        self.client.force_authenticate(user=self.rider)
        response = self.client.post(f'/api/deliveries/shifts/{shift.id}/stop/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        shift.refresh_from_db()
        self.assertEqual(shift.status, RiderShift.Status.COMPLETED)


class DeliveryOfferViewSetTestCase(TestCase):
    """Test DeliveryOfferViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
        self.customer = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            role=User.Role.CUSTOMER
        )
        self.restaurant_owner = User.objects.create_user(
            email='restaurant@test.com',
            password='testpass123',
            role=User.Role.RESTAURANT
        )
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner=self.restaurant_owner,
            address='123 Test St',
            phone='1234567890'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            total_amount=50.00
        )
        self.delivery = Delivery.objects.create(
            order=self.order,
            rider=None,
            pickup_address='123 Pickup St',
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            delivery_address='456 Delivery St'
        )
        # Create rider location
        RiderLocation.objects.create(
            rider=self.rider,
            latitude=40.7128,
            longitude=-74.0060
        )
    
    def test_get_nearby_offers(self):
        """Test getting nearby offers"""
        offer = DeliveryOffer.objects.create(
            delivery=self.delivery,
            rider=self.rider,
            estimated_earnings=15.00,
            distance_km=5.0,
            expires_at=timezone.now() + timedelta(minutes=5),
            status=DeliveryOffer.Status.SENT
        )
        
        self.client.force_authenticate(user=self.rider)
        response = self.client.get('/api/deliveries/offers/nearby/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_accept_offer(self):
        """Test accepting an offer"""
        offer = DeliveryOffer.objects.create(
            delivery=self.delivery,
            rider=self.rider,
            estimated_earnings=15.00,
            distance_km=5.0,
            expires_at=timezone.now() + timedelta(minutes=5),
            status=DeliveryOffer.Status.SENT
        )
        
        self.client.force_authenticate(user=self.rider)
        response = self.client.post(f'/api/deliveries/offers/{offer.id}/accept/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        offer.refresh_from_db()
        self.assertEqual(offer.status, DeliveryOffer.Status.ACCEPTED)


class RiderWalletViewSetTestCase(TestCase):
    """Test RiderWalletViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
        RiderWallet.objects.create(
            rider=self.rider,
            balance=100.00,
            currency='USD'
        )
    
    def test_get_my_wallet(self):
        """Test getting rider's wallet"""
        self.client.force_authenticate(user=self.rider)
        response = self.client.get('/api/deliveries/wallets/my_wallet/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['balance']), 100.00)
    
    def test_earnings_breakdown(self):
        """Test getting earnings breakdown"""
        self.client.force_authenticate(user=self.rider)
        response = self.client.get('/api/deliveries/wallets/earnings_breakdown/?period=week')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('breakdown', response.data)


class OfflineActionViewSetTestCase(TestCase):
    """Test OfflineActionViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
    
    def test_create_offline_action(self):
        """Test creating an offline action"""
        self.client.force_authenticate(user=self.rider)
        response = self.client.post('/api/deliveries/offline-actions/', {
            'action_type': 'ACCEPT_OFFER',
            'action_data': {'offer_id': 1},
            'resource_id': '1'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(OfflineAction.objects.filter(
            rider=self.rider,
            action_type=OfflineAction.ActionType.ACCEPT_OFFER
        ).exists())
    
    def test_get_pending_actions(self):
        """Test getting pending offline actions"""
        OfflineAction.objects.create(
            rider=self.rider,
            action_type=OfflineAction.ActionType.ACCEPT_OFFER,
            status=OfflineAction.Status.PENDING,
            action_data={'offer_id': 1},
            resource_id='1'
        )
        
        self.client.force_authenticate(user=self.rider)
        response = self.client.get('/api/deliveries/offline-actions/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class TripLogViewSetTestCase(TestCase):
    """Test TripLogViewSet"""
    
    def setUp(self):
        self.client = APIClient()
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
        self.customer = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            role=User.Role.CUSTOMER
        )
        self.restaurant_owner = User.objects.create_user(
            email='restaurant@test.com',
            password='testpass123',
            role=User.Role.RESTAURANT
        )
        self.restaurant = Restaurant.objects.create(
            name='Test Restaurant',
            owner=self.restaurant_owner,
            address='123 Test St',
            phone='1234567890'
        )
        self.order = Order.objects.create(
            customer=self.customer,
            restaurant=self.restaurant,
            total_amount=50.00
        )
        self.delivery = Delivery.objects.create(
            order=self.order,
            rider=self.rider,
            pickup_address='123 Pickup St',
            delivery_address='456 Delivery St',
            status=Delivery.Status.DELIVERED
        )
        TripLog.objects.create(
            rider=self.rider,
            delivery=self.delivery,
            total_distance_km=10.5,
            total_time_minutes=30,
            total_earnings=15.00,
            trip_started_at=timezone.now() - timedelta(days=1),
            trip_ended_at=timezone.now() - timedelta(days=1) + timedelta(minutes=30)
        )
    
    def test_list_trip_logs(self):
        """Test listing trip logs"""
        self.client.force_authenticate(user=self.rider)
        response = self.client.get('/api/deliveries/trip-logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_analytics(self):
        """Test getting trip analytics"""
        self.client.force_authenticate(user=self.rider)
        response = self.client.get('/api/deliveries/trip-logs/analytics/?period=week')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('analytics', response.data)

