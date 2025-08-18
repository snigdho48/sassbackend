from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import APIToken, APIUsage

User = get_user_model()

class JWTAuthenticationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            role='client'
        )
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='adminpass123',
            role='admin',
            is_staff=True,
            is_superuser=True
        )

    def test_jwt_login(self):
        """Test JWT token generation on login."""
        url = '/api/auth/token/'
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_protected_endpoint_with_jwt(self):
        """Test accessing protected endpoint with JWT token."""
        # Get token
        token_response = self.client.post('/api/auth/token/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        token = token_response.data['access']
        
        # Access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_invalid_token(self):
        """Test accessing protected endpoint with invalid token."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get('/api/auth/profile/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class APIUsageTest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='adminpass123',
            role='admin',
            is_staff=True,
            is_superuser=True
        )

    def test_api_usage_tracking(self):
        """Test that API usage is tracked."""
        # Get token
        token_response = self.client.post('/api/auth/token/', {
            'email': 'admin@example.com',
            'password': 'adminpass123'
        })
        token = token_response.data['access']
        
        # Make API call
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/auth/profile/')
        
        # Check if usage was tracked
        usage_count = APIUsage.objects.count()
        self.assertGreater(usage_count, 0)
        
        # Check usage details
        usage = APIUsage.objects.first()
        self.assertEqual(usage.endpoint, '/api/auth/profile/')
        self.assertEqual(usage.method, 'GET')
        self.assertEqual(usage.status_code, 200)
