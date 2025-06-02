from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import MyUser, Plan, Subscription, Invoice
from django.utils import timezone
import uuid
import os


class CreateRazorPayInvoiceOrderViewTest(APITestCase):

    def setUp(self):
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        refresh = RefreshToken.for_user(self.user)
        self.auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }

        self.plan = Plan.objects.create(
            name='Test Plan',
            description='Test Description',
            price=100,
            duration=6,
            is_active=True
        )

        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=180),
            status='active'
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            plan=self.plan,
            amount=100,
            issue_date=timezone.now(),
            due_date=timezone.now() + timezone.timedelta(days=5),
            billing_period_start=timezone.now().date(),
            billing_period_end=(timezone.now() + timezone.timedelta(days=30)).date(),
            status='unpaid'
        )

    @patch('razorpay.client.Client')
    def test_create_razorpay_order_success(self, mock_razorpay_client):
        # Setup mock for razorpay client order create
        mock_client_instance = MagicMock()
        mock_razorpay_client.return_value = mock_client_instance
        mock_client_instance.order.create.return_value = {
            'id': 'order_12345'
        }

        url = reverse('create-razorpay-order')
        data = {'invoice_id': str(self.invoice.id)}

        response = self.client.post(url, data, **self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_id', response.json())
        self.assertEqual(response.json()['order_id'], 'order_12345')

        # Check that invoice was updated with razorpay_order_id
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.razorpay_order_id, 'order_12345')

        # Verify the razorpay client was called with expected data
        expected_order_data = {
            'amount': int(self.invoice.amount * 100),
            'currency': 'INR',
            'receipt': str(self.invoice.id),
            'payment_capture': 1
        }
        mock_client_instance.order.create.assert_called_once_with(data=expected_order_data)

    def test_create_razorpay_order_invoice_not_found(self):
        url = reverse('create-razorpay-order')
        data = {'invoice_id': str(uuid.uuid4())}  # Invalid UUID

        response = self.client.post(url, data, **self.auth_headers)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], "Invoice not found or already paid")


class VerifyRazorPayPaymentViewTest(APITestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        refresh = RefreshToken.for_user(self.user)
        self.auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }

        self.plan = Plan.objects.create(
            name='Test Plan',
            description='Test Description',
            price=100,
            duration=3,
            is_active=True
        )

        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=90),
            status='active'
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            plan=self.plan,
            amount=100,
            issue_date=timezone.now(),
            due_date=timezone.now() + timezone.timedelta(days=10),
            billing_period_start=timezone.now().date(),
            billing_period_end=(timezone.now() + timezone.timedelta(days=30)).date(),
            status='unpaid',
            razorpay_order_id='order_ABC123'
        )

        # mock payment IDs
        self.payment_data = {
            'razorpay_order_id': 'order_ABC123',
            'razorpay_payment_id': 'pay_123456',
            'razorpay_signature': 'dummy_signature',
            'invoice_id': str(self.invoice.id),
        }

    @patch.dict(os.environ, {"MOCK_PAYMENT_SUCCESS": "True"})
    @patch('razorpay.client.Client')
    def test_verify_payment_success(self, mock_razorpay_client):
        mock_client_instance = MagicMock()
        mock_razorpay_client.return_value = mock_client_instance

        url = reverse('verify-razorpay-payment')
        response = self.client.post(url, self.payment_data, **self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['message'], 'Payment verified and invoice marked as paid')

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'paid')
        self.assertIsNotNone(self.invoice.paid_at)

    @patch.dict(os.environ, {"MOCK_PAYMENT_SUCCESS": "False"})
    @patch('razorpay.client.Client')
    def test_verify_payment_failure_due_to_invalid_signature(self, mock_razorpay_client):
        mock_client_instance = MagicMock()
        mock_razorpay_client.return_value = mock_client_instance

        url = reverse('verify-razorpay-payment')
        response = self.client.post(url, self.payment_data, **self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'Invalid signature')
