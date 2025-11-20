from django.test import TestCase
from django.contrib.auth import get_user_model

class SmokeTest(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(email='smoke@test.com', password='password')
        self.assertEqual(user.email, 'smoke@test.com')
