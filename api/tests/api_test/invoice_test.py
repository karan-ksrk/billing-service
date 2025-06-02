from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from api.models import MyUser, Plan, Subscription, Invoice
from uuid import UUID


class InvoiceListViewTestCase(APITestCase):

    def setUp(self):
        # Authenticated test user
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepass'
        )

        refresh = RefreshToken.for_user(self.user)
        self.auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }

        # Another user
        self.other_user = MyUser.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass'
        )

        # Common plan
        self.plan = Plan.objects.create(
            name='Premium Plan',
            description='Access to all features',
            price=299.0,
            duration=12,
            is_active=True
        )

        # Subscription for test user
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=365),
            status='active'
        )

        # Invoices for test user
        self.invoice1 = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            plan=self.plan,
            amount=299.0,
            issue_date=timezone.now(),
            due_date=timezone.now() + timezone.timedelta(days=5),
            billing_period_start=timezone.now().date(),
            billing_period_end=(timezone.now() + timezone.timedelta(days=365)).date(),
            status='unpaid'
        )

        self.invoice2 = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            plan=self.plan,
            amount=299.0,
            issue_date=timezone.now() - timezone.timedelta(days=365),
            due_date=timezone.now() - timezone.timedelta(days=360),
            billing_period_start=(timezone.now() - timezone.timedelta(days=365)).date(),
            billing_period_end=(timezone.now()).date(),
            status='paid'
        )

    def test_list_invoices_for_authenticated_user(self):
        url = reverse('invoice-list')
        response = self.client.get(url, **self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 2)

        invoice_ids = [invoice['id'] for invoice in response.json()]
        self.assertIn(str(self.invoice1.id), invoice_ids)
        self.assertIn(str(self.invoice2.id), invoice_ids)


class InvoiceViewsTestCase(APITestCase):
    def setUp(self):
        # Create user
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )

        refresh = RefreshToken.for_user(self.user)
        self.auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }

        # Create plan and subscription
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

        # Create invoices with different issue_dates
        self.invoice_old = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            plan=self.plan,
            amount=100,
            issue_date=timezone.now() - timezone.timedelta(days=30),
            due_date=timezone.now() - timezone.timedelta(days=25),
            billing_period_start=(timezone.now() - timezone.timedelta(days=30)).date(),
            billing_period_end=(timezone.now() - timezone.timedelta(days=1)).date(),
            status='paid'
        )

        self.invoice_latest = Invoice.objects.create(
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

    def test_get_latest_invoice(self):
        url = reverse('latest-invoice')
        response = self.client.get(url, **self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], str(self.invoice_latest.id))
        self.assertEqual(data['status'], 'unpaid')

    def test_get_latest_invoice_no_invoices(self):
        # Create new user with no invoices
        new_user = MyUser.objects.create_user(username='nouser', email='nouser@example.com', password='pass')
        refresh = RefreshToken.for_user(new_user)
        auth_headers = {'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'}

        url = reverse('latest-invoice')
        response = self.client.get(url, **auth_headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['error'], 'No invoices found')
