from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.orders.models import Order
from apps.restaurants.models import Restaurant
from apps.payments.models import Payment
from decimal import Decimal

class PaymentGatewayTests(APITestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            role='CUSTOMER',
            first_name='Test',
            last_name='User'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create restaurant
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            owner=self.user,
            address="123 Test St",
            cuisine_type='ITALIAN',
            phone='1234567890',
            latitude=Decimal('12.9716'),
            longitude=Decimal('77.5946'),
            city='Bangalore',
            state='Karnataka',
            postal_code='560001'
        )
        
        # Create order
        self.order = Order.objects.create(
            customer=self.user,
            restaurant=self.restaurant,
            total_amount=Decimal('500.00'),
            status=Order.Status.PENDING
        )
        
        self.create_intent_url = reverse('create_payment_intent')
        self.confirm_payment_url = reverse('confirm_payment')

    def test_create_payment_intent(self):
        data = {
            'order_id': self.order.id,
            'payment_method': 'CARD',
            'amount': '500.00'
        }
        response = self.client.post(self.create_intent_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('payment_intent_id', response.data)
        self.assertIn('client_secret', response.data)
        self.assertEqual(response.data['status'], 'requires_payment_method')

    def test_confirm_payment_success(self):
        # First create intent to get an ID (though we can fake it for the mock service)
        payment_intent_id = "pi_test_123"
        
        data = {
            'order_id': self.order.id,
            'payment_intent_id': payment_intent_id,
            'payment_method': 'CARD'
        }
        
        # Since the mock service has a random failure chance (10%), we might want to patch it 
        # or retry. For now, let's patch the random to ensure success.
        from unittest.mock import patch
        with patch('random.random', return_value=0.5): # 0.5 > 0.1 so success
            response = self.client.post(self.confirm_payment_url, data)
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        
        # Verify payment record created
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, Payment.Status.COMPLETED)
        self.assertEqual(payment.amount, Decimal('500.00'))
        
        # Verify order status updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.ACCEPTED)

    def test_confirm_payment_failure(self):
        payment_intent_id = "pi_test_fail"
        
        data = {
            'order_id': self.order.id,
            'payment_intent_id': payment_intent_id,
            'payment_method': 'CARD'
        }
        
        # Patch random to ensure failure
        from unittest.mock import patch
        with patch('random.random', return_value=0.05): # 0.05 < 0.1 so failure
            response = self.client.post(self.confirm_payment_url, data)
            
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'failed')
        
        # Verify payment record created with failed status
        payment = Payment.objects.get(order=self.order)
        self.assertEqual(payment.status, Payment.Status.FAILED)
