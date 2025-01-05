from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import UserProfile, Subscription
import base64
from django.core.files.uploadedfile import SimpleUploadedFile
import os

User = get_user_model()

class UserViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.profile = UserProfile.objects.create(user=self.user)
        
        # Create another user for subscription tests
        self.other_user = User.objects.create_user(
            email='other@example.com',
            username='otheruser',
            first_name='Other',
            last_name='User',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.other_user)

    def test_create_user(self):
        """Test creating a new user"""
        url = reverse('user-list')
        data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertNotIn('password', response.data)

    def test_me_endpoint(self):
        """Test the /users/me/ endpoint"""
        url = reverse('user-me')
        # Test unauthorized access
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test authorized access
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_change_password(self):
        """Test password change functionality"""
        url = reverse('user-set-password')
        self.client.force_authenticate(user=self.user)
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify old password doesn't work
        self.client.logout()
        response = self.client.post(reverse('token_login'), {
            'email': self.user.email,
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscription_endpoints(self):
        """Test subscription-related endpoints"""
        self.client.force_authenticate(user=self.user)
        
        # Test subscribe
        url = reverse('user-subscribe', kwargs={'pk': self.other_user.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test subscriptions list
        url = reverse('user-subscriptions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Test unsubscribe
        url = reverse('user-subscribe', kwargs={'pk': self.other_user.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_avatar_endpoints(self):
        """Test avatar upload and deletion"""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-avatar')
        
        # Create a test image
        image_content = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
        temp_image = SimpleUploadedFile("test_image.png", image_content, content_type="image/png")
        
        # Test upload
        response = self.client.put(url, {'avatar': temp_image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('avatar' in response.data)
        
        # Test deletion
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

class CustomAuthTokenTests(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_obtain_auth_token(self):
        """Test obtaining auth token"""
        url = reverse('token_login')
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)
        self.assertEqual(response.data['email'], self.user.email)

    def test_logout(self):
        """Test token logout"""
        # First login to get token
        login_url = reverse('token_login')
        response = self.client.post(login_url, {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        token = response.data['auth_token']
        
        # Then logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        logout_url = reverse('token_logout')
        response = self.client.post(logout_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)