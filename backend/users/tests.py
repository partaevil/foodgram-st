from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import UserProfile, Subscription, Recipe
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

class UserSecurityAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        # Create main test user
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            first_name='User',
            last_name='One',
            password='testpass123'
        )
        self.profile1 = UserProfile.objects.create(user=self.user1)
        
        # Create secondary test user
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            first_name='User',
            last_name='Two',
            password='testpass123'
        )
        self.profile2 = UserProfile.objects.create(user=self.user2)
    
    def test_duplicate_email_registration(self):
        """Test that users cannot register with an existing email"""
        url = reverse('user-list')
        data = {
            'email': 'user1@example.com',  # Existing email
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_username_registration(self):
        """Test that users cannot register with an existing username"""
        url = reverse('user-list')
        data = {
            'email': 'new@example.com',
            'username': 'user1',  # Existing username
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_validation(self):
        """Test password validation rules"""
        url = reverse('user-list')
        test_cases = [
            {
                'password': '123',  # Too short
                'expected_status': status.HTTP_400_BAD_REQUEST
            },
            {
                'password': 'password',  # Too common
                'expected_status': status.HTTP_400_BAD_REQUEST
            },
            {
                'password': '12345678',  # Numeric only
                'expected_status': status.HTTP_400_BAD_REQUEST
            }
        ]
        
        base_data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        for test_case in test_cases:
            data = base_data.copy()
            data['password'] = test_case['password']
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, test_case['expected_status'])

    def test_self_subscription_prevention(self):
        """Test that users cannot subscribe to themselves"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-subscribe', kwargs={'pk': self.user1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_current_password(self):
        """Test password change with invalid current password"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-set-password')
        data = {
            'current_password': 'wrongpassword',
            'new_password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscription_count_accuracy(self):
        """Test that subscription count is accurate when subscribing/unsubscribing"""
        self.client.force_authenticate(user=self.user1)
        
        # Create some recipes for user2
        for i in range(3):
            Recipe.objects.create(
                author=self.user2,
                name=f'Recipe {i}',
                text='Description',
                cooking_time=30,
                image=SimpleUploadedFile(
                    f"recipe_{i}.png",
                    base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='),
                    content_type="image/png"
                )
            )
        
        # Subscribe
        url = reverse('user-subscribe', kwargs={'pk': self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['recipes_count'], 3)

    def test_multiple_subscription_attempts(self):
        """Test multiple subscription attempts to the same author"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-subscribe', kwargs={'pk': self.user2.id})
        
        # First subscription should succeed
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Second attempt should fail
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_token_login(self):
        """Test login attempts with invalid tokens"""
        url = reverse('token_login')
        test_cases = [
            {
                'data': {'email': 'user1@example.com'},  # Missing password
                'expected_status': status.HTTP_400_BAD_REQUEST
            },
            {
                'data': {'password': 'testpass123'},  # Missing email
                'expected_status': status.HTTP_400_BAD_REQUEST
            },
            {
                'data': {'email': 'nonexistent@example.com', 'password': 'testpass123'},  # Non-existent user
                'expected_status': status.HTTP_400_BAD_REQUEST
            }
        ]
        
        for test_case in test_cases:
            response = self.client.post(url, test_case['data'], format='json')
            self.assertEqual(response.status_code, test_case['expected_status'])

    def test_unauthorized_avatar_operations(self):
        """Test avatar operations without authentication"""
        url = reverse('user-avatar')
        
        # Test unauthorized upload
        image_content = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
        temp_image = SimpleUploadedFile("test_image.png", image_content, content_type="image/png")
        response = self.client.put(url, {'avatar': temp_image}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test unauthorized deletion
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_file_upload(self):
        """Test uploading invalid files as avatar"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('user-avatar')
        
        # Test non-image file
        text_file = SimpleUploadedFile("test.txt", b"hello world", content_type="text/plain")
        response = self.client.put(url, {'avatar': text_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subscription_list_pagination(self):
        """Test pagination of subscription list"""
        self.client.force_authenticate(user=self.user1)
        
        # Create multiple users and subscribe to them
        test_users = []
        for i in range(15):  # Create enough users to trigger pagination
            test_user = User.objects.create_user(
                email=f'testuser{i+100}@example.com',  
                username=f'testuser{i+100}',  
                first_name=f'Test{i+100}',
                last_name='User',
                password='testpass123'
            )
            UserProfile.objects.create(user=test_user)
            test_users.append(test_user)
            
            # Subscribe to each user
            url = reverse('user-subscribe', kwargs={'pk': test_user.id})
            self.client.post(url)
        
        # Test first page
        url = reverse('user-subscriptions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('next' in response.data)  # Should have next page
        self.assertEqual(len(response.data['results']), 10)  # Default pagination size
        
        # Test second page
        response = self.client.get(response.data['next'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)  # Remaining items
        self.assertFalse('next' == None)  # No more pages

        for user in test_users:
            user.delete()