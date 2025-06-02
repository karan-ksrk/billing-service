from rest_framework.test import APITestCase
from unittest.mock import patch
from api.models import MyUser
from django.urls import reverse


class UserRegistrationTestCase(APITestCase):
    def setUp(self):
        self.valid_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword123'
        }

    def test_user_registration_success(self):
        url = reverse('signup')
        response = self.client.post(url, self.valid_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json())
        self.assertIn('user_id', response.json())

    def test_user_registration_invalid_data(self):
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'invalid-email'
        response = self.client.post('/api/signup/', invalid_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json())


class UserLoginTestCase(APITestCase):

    def setUp(self):
        self.valid_credentials = {
            'username': 'testuser',
            'password': 'testpassword123',
            'email': 'testuser@example.com'
        }
        user = MyUser.objects.create_user(
            username=self.valid_credentials['username'],
            email=self.valid_credentials['email'],
            password=self.valid_credentials['password']
        )

    def test_user_login_success(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, self.valid_credentials)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())

    def test_user_login_invalid_credentials(self):
        invalid_credentials = self.valid_credentials.copy()
        invalid_credentials['password'] = 'wrongpassword'
        response = self.client.post('/api/token/', invalid_credentials)
        self.assertEqual(response.status_code, 401)
