from rest_framework.test import APITestCase
from unittest.mock import patch
from django.utils import timezone
from datetime import datetime, timedelta
from api.models import Invoice, MyUser, Plan, Subscription
from dateutil.relativedelta import relativedelta


class MyUserTestCase(APITestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'testuser@example.com')


class PlanTestCase(APITestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Basic Plan',
            price=9.99,
            description='Basic subscription plan',
            duration=1,
            is_active=True
        )

    def test_plan_creation(self):
        self.assertEqual(self.plan.name, 'Basic Plan')
        self.assertEqual(self.plan.price, 9.99)
        self.assertEqual(self.plan.duration, 1)
        self.assertTrue(self.plan.is_active)
        self.assertIsNotNone(self.plan.created_at)
        self.assertIsNotNone(self.plan.updated_at)


class SubscriptionTestCase(APITestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.plan = Plan.objects.create(
            name='Basic Plan',
            price=9.99,
            description='Basic subscription plan',
            duration=1,
            is_active=True
        )

        self.start_date = datetime(2025, 1, 1)
        self.end_date = self.start_date + relativedelta(months=self.plan.duration)
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=self.start_date,
            end_date=self.end_date,
            status='active'
        )

    def test_subscription_creation(self):
        self.assertEqual(self.subscription.user, self.user)
        self.assertEqual(self.subscription.plan, self.plan)
        self.assertEqual(self.subscription.status, 'active')
        self.assertEqual(self.subscription.start_date.strftime('%Y-%m-%d'), '2025-01-01')
        self.assertEqual(self.subscription.end_date.strftime('%Y-%m-%d'), '2025-02-01')


class InvoiceTestCase(APITestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )
        self.plan = Plan.objects.create(
            name='Basic Plan',
            price=9.99,
            description='Basic subscription plan',
            duration=1,
            is_active=True
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + relativedelta(months=self.plan.duration),
            status='active'
        )
        current_time = timezone.now()
        self.invoice = Invoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            plan=self.plan,
            amount=self.plan.price,
            issue_date=current_time,
            due_date=current_time + timedelta(days=5),
            status='unpaid',
        )

        self.invoice.billing_period_start = self.invoice.issue_date.date()
        self.invoice.billing_period_end = self.invoice.issue_date + relativedelta(months=self.plan.duration)
        self.invoice.save()

    def test_invoice_creation(self):
        self.assertEqual(self.invoice.user, self.user)
        self.assertEqual(self.invoice.subscription, self.subscription)
        self.assertEqual(self.invoice.amount, self.plan.price)
        self.assertEqual(self.invoice.status, 'unpaid')
        self.assertEqual(self.invoice.issue_date.date(), timezone.now().date())
        self.assertEqual(self.invoice.due_date, self.invoice.issue_date + timedelta(days=5))
        self.assertEqual(self.invoice.billing_period_start, self.invoice.issue_date.date())
        self.assertEqual(self.invoice.billing_period_end, self.invoice.issue_date +
                         relativedelta(months=self.plan.duration))
