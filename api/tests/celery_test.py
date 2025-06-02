from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import Plan, MyUser, Subscription, Invoice
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from uuid import UUID
from api.tasks import generate_daily_invoice, send_invoice_reminders, mark_overdue_invoices
from unittest.mock import patch
from dateutil.relativedelta import relativedelta


class CeleryTasksTest(APITestCase):

    def setUp(self):
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.plan = Plan.objects.create(
            name='Pro',
            description='Pro plan description',
            price=999,
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

    def test_generate_daily_invoice(self):
        # Mock the current date to a future date
        future_date = timezone.now() + relativedelta(months=3)
        with patch('django.utils.timezone.now', return_value=future_date):
            generate_daily_invoice()
            invoices = Invoice.objects.filter(user=self.user, status='unpaid')
            self.assertEqual(invoices.count(), 1)

    def test_mark_overdue_invoices(self):
        # Create an overdue invoice
        overdue_invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            plan=self.plan,
            amount=999,
            issue_date=timezone.now() - timezone.timedelta(days=10),
            due_date=timezone.now() - timezone.timedelta(days=5),
            billing_period_start=timezone.now().date(),
            billing_period_end=(timezone.now() + timezone.timedelta(days=30)).date(),
            status='unpaid'
        )

        mark_overdue_invoices()
        overdue_invoice.refresh_from_db()
        self.assertEqual(overdue_invoice.status, 'overdue')

    def test_mark_overdue_invoices_with_cancel_subscription(self):
        overdue_invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            plan=self.plan,
            amount=999,
            issue_date=timezone.now() - timezone.timedelta(days=10),
            due_date=timezone.now() - timezone.timedelta(days=5),
            billing_period_start=timezone.now().date(),
            billing_period_end=(timezone.now() + timezone.timedelta(days=30)).date(),
            status='unpaid'
        )
        future_date = timezone.now() + timezone.timedelta(days=2)
        with patch('django.utils.timezone.now', return_value=future_date):
            print(overdue_invoice.due_date)
            print(future_date)
            mark_overdue_invoices()
            overdue_invoice.refresh_from_db()
            self.assertEqual(overdue_invoice.status, 'overdue')
            self.subscription.refresh_from_db()
            # Check if subscription is cancelled
            self.assertEqual(self.subscription.status, 'cancelled')

    def test_send_invoice_reminders(self):
        # Create an overdue invoice
        overdue_invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            plan=self.plan,
            amount=999,
            issue_date=timezone.now() - timezone.timedelta(days=10),
            due_date=timezone.now() - timezone.timedelta(days=5),
            billing_period_start=timezone.now().date(),
            billing_period_end=(timezone.now() + timezone.timedelta(days=30)).date(),
            status='overdue'
        )

        with patch('api.tasks.send_subscription_overdue_email.delay') as mock_send_email:
            send_invoice_reminders()
            mock_send_email.assert_called_once_with(user_email=self.user.email, subscription_id=overdue_invoice.subscription.id)
