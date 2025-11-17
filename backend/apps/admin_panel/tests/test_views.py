"""
Unit tests for admin panel views
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AdminAuthenticationTestCase(TestCase):
    """Test admin authentication"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=User.Role.ADMIN,
            is_staff=True
        )
    
    def test_admin_login(self):
        """Test admin can login"""
        response = self.client.post('/api/auth/token/', {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_non_admin_cannot_access(self):
        """Test non-admin cannot access admin endpoints"""
        regular_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            role=User.Role.CUSTOMER
        )
        self.client.force_authenticate(user=regular_user)
        response = self.client.get('/api/admin/roles/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserManagementTestCase(TestCase):
    """Test user management operations"""
    
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=User.Role.ADMIN,
            is_staff=True
        )
        self.client.force_authenticate(user=self.admin_user)
        self.test_user = User.objects.create_user(
            email='user@test.com',
            password='testpass123',
            role=User.Role.CUSTOMER
        )
    
    def test_list_users(self):
        """Test listing users"""
        response = self.client.get('/api/admin/management/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_ban_user(self):
        """Test banning a user"""
        response = self.client.post(
            f'/api/admin/management/users/{self.test_user.id}/ban/',
            {'reason': 'Test ban'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test_user.refresh_from_db()
        self.assertFalse(self.test_user.is_active)

