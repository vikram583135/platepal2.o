"""
Unit tests for deliveries models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.deliveries.models import (
    Delivery, RiderLocation, RiderShift, DeliveryOffer,
    RiderWallet, RiderWalletTransaction, TripLog, OfflineAction,
    RiderSettings, RiderProfile, RiderBankDetail
)
from apps.orders.models import Order, Restaurant

User = get_user_model()


class DeliveryModelTestCase(TestCase):
    """Test Delivery model"""
    
    def setUp(self):
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
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
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
            total_amount=50.00,
            status=Order.Status.PENDING
        )
    
    def test_create_delivery(self):
        """Test creating a delivery"""
        delivery = Delivery.objects.create(
            order=self.order,
            rider=self.rider,
            pickup_address='123 Pickup St',
            delivery_address='456 Delivery St',
            status=Delivery.Status.PENDING
        )
        self.assertEqual(delivery.order, self.order)
        self.assertEqual(delivery.rider, self.rider)
        self.assertEqual(delivery.status, Delivery.Status.PENDING)
        self.assertFalse(delivery.is_paused)
    
    def test_pause_delivery(self):
        """Test pausing a delivery"""
        delivery = Delivery.objects.create(
            order=self.order,
            rider=self.rider,
            pickup_address='123 Pickup St',
            delivery_address='456 Delivery St',
            status=Delivery.Status.ACCEPTED
        )
        delivery.is_paused = True
        delivery.paused_at = timezone.now()
        delivery.pause_reason = 'Short break'
        delivery.save()
        
        self.assertTrue(delivery.is_paused)
        self.assertIsNotNone(delivery.paused_at)
    
    def test_delivery_navigation_fields(self):
        """Test delivery navigation fields"""
        delivery = Delivery.objects.create(
            order=self.order,
            rider=self.rider,
            pickup_address='123 Pickup St',
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            delivery_address='456 Delivery St',
            delivery_latitude=40.7589,
            delivery_longitude=-73.9851,
            estimated_distance_km=10.5,
            estimated_travel_time_minutes=30
        )
        
        self.assertEqual(float(delivery.estimated_distance_km), 10.5)
        self.assertEqual(delivery.estimated_travel_time_minutes, 30)


class RiderShiftModelTestCase(TestCase):
    """Test RiderShift model"""
    
    def setUp(self):
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
    
    def test_create_shift(self):
        """Test creating a shift"""
        shift = RiderShift.objects.create(
            rider=self.rider,
            status=RiderShift.Status.SCHEDULED,
            scheduled_start_time=timezone.now(),
            scheduled_end_time=timezone.now() + timedelta(hours=8)
        )
        
        self.assertEqual(shift.rider, self.rider)
        self.assertEqual(shift.status, RiderShift.Status.SCHEDULED)
        self.assertEqual(shift.total_earnings, 0)
    
    def test_start_shift(self):
        """Test starting a shift"""
        shift = RiderShift.objects.create(
            rider=self.rider,
            status=RiderShift.Status.SCHEDULED,
            scheduled_start_time=timezone.now(),
            scheduled_end_time=timezone.now() + timedelta(hours=8)
        )
        
        shift.status = RiderShift.Status.ACTIVE
        shift.actual_start_time = timezone.now()
        shift.save()
        
        self.assertEqual(shift.status, RiderShift.Status.ACTIVE)
        self.assertIsNotNone(shift.actual_start_time)


class DeliveryOfferModelTestCase(TestCase):
    """Test DeliveryOffer model"""
    
    def setUp(self):
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
            delivery_address='456 Delivery St'
        )
    
    def test_create_offer(self):
        """Test creating a delivery offer"""
        offer = DeliveryOffer.objects.create(
            delivery=self.delivery,
            rider=self.rider,
            estimated_earnings=15.00,
            distance_km=5.0,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        
        self.assertEqual(offer.delivery, self.delivery)
        self.assertEqual(offer.rider, self.rider)
        self.assertFalse(offer.is_expired())
    
    def test_offer_expiry(self):
        """Test offer expiry"""
        offer = DeliveryOffer.objects.create(
            delivery=self.delivery,
            rider=self.rider,
            estimated_earnings=15.00,
            distance_km=5.0,
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        
        self.assertTrue(offer.is_expired())


class RiderWalletModelTestCase(TestCase):
    """Test RiderWallet model"""
    
    def setUp(self):
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
    
    def test_create_wallet(self):
        """Test creating a wallet"""
        wallet = RiderWallet.objects.create(
            rider=self.rider,
            balance=100.00,
            currency='USD'
        )
        
        self.assertEqual(wallet.rider, self.rider)
        self.assertEqual(float(wallet.balance), 100.00)
        self.assertEqual(wallet.currency, 'USD')
    
    def test_add_transaction(self):
        """Test adding a transaction"""
        wallet = RiderWallet.objects.create(
            rider=self.rider,
            balance=100.00
        )
        
        transaction = RiderWalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=RiderWalletTransaction.TransactionType.CREDIT,
            source=RiderWalletTransaction.TransactionSource.DELIVERY,
            amount=25.00,
            balance_after=125.00,
            description='Delivery earnings'
        )
        
        self.assertEqual(float(transaction.amount), 25.00)
        self.assertEqual(float(transaction.balance_after), 125.00)


class TripLogModelTestCase(TestCase):
    """Test TripLog model"""
    
    def setUp(self):
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
    
    def test_create_trip_log(self):
        """Test creating a trip log"""
        trip_log = TripLog.objects.create(
            rider=self.rider,
            delivery=self.delivery,
            total_distance_km=10.5,
            total_time_minutes=30,
            base_fee=10.00,
            distance_fee=5.00,
            total_earnings=15.00,
            trip_started_at=timezone.now() - timedelta(minutes=30),
            trip_ended_at=timezone.now()
        )
        
        self.assertEqual(float(trip_log.total_distance_km), 10.5)
        self.assertEqual(trip_log.total_time_minutes, 30)
        self.assertEqual(float(trip_log.total_earnings), 15.00)


class OfflineActionModelTestCase(TestCase):
    """Test OfflineAction model"""
    
    def setUp(self):
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
    
    def test_create_offline_action(self):
        """Test creating an offline action"""
        action = OfflineAction.objects.create(
            rider=self.rider,
            action_type=OfflineAction.ActionType.ACCEPT_OFFER,
            status=OfflineAction.Status.PENDING,
            action_data={'offer_id': 1},
            resource_id='1'
        )
        
        self.assertEqual(action.rider, self.rider)
        self.assertEqual(action.action_type, OfflineAction.ActionType.ACCEPT_OFFER)
        self.assertEqual(action.status, OfflineAction.Status.PENDING)
        self.assertEqual(action.retry_count, 0)


class RiderSettingsModelTestCase(TestCase):
    """Test RiderSettings model"""
    
    def setUp(self):
        self.rider = User.objects.create_user(
            email='rider@test.com',
            password='testpass123',
            role=User.Role.DELIVERY
        )
    
    def test_create_settings(self):
        """Test creating rider settings"""
        settings = RiderSettings.objects.create(
            rider=self.rider,
            location_tracking_enabled=True,
            location_mode='BALANCED',
            push_notifications_enabled=True,
            sound_alerts_enabled=True
        )
        
        self.assertEqual(settings.rider, self.rider)
        self.assertTrue(settings.location_tracking_enabled)
        self.assertEqual(settings.location_mode, 'BALANCED')
        self.assertTrue(settings.push_notifications_enabled)

