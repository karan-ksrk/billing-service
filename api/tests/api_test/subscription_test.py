from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import Plan, MyUser, Subscription, Invoice
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from uuid import UUID


class PlanListViewTest(APITestCase):

    def setUp(self):
        # Create 3 active plans
        Plan.objects.create(name="Plan A", description="Desc A", price=10.0, duration=1, is_active=True)
        Plan.objects.create(name="Plan B", description="Desc B", price=20.0, duration=2, is_active=True)
        Plan.objects.create(name="Plan C", description="Desc C", price=30.0, duration=3, is_active=True)

    def test_plan_list_returns_only_active_plans(self):
        url = reverse('plan-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 3)


class SubscribeViewTestCase(APITestCase):

    def setUp(self):
        # Create test user
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )

        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }

        # Create active plan
        self.plan = Plan.objects.create(
            name='Basic Plan',
            description='Test plan',
            price=99.0,
            duration=3,
            is_active=True
        )

    def test_user_can_subscribe_to_active_plan(self):
        url = reverse('subscribe')
        data = {'plan_id': self.plan.id}
        response = self.client.post(url, data, **self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Subscription.objects.count(), 1)
        self.assertEqual(Invoice.objects.count(), 1)

        subscription = Subscription.objects.first()
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.status, 'active')

        invoice = Invoice.objects.first()
        self.assertEqual(invoice.subscription, subscription)
        self.assertEqual(invoice.amount, self.plan.price)
        self.assertEqual(invoice.status, 'unpaid')

    def test_user_cannot_subscribe_if_already_active(self):
        # Create active subscription
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=90),
            status='active'
        )

        url = reverse('subscribe')
        data = {'plan_id': self.plan.id}
        response = self.client.post(url, data, **self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You already have an active subscription', response.json().get('error', ''))


class UnSubscribeViewTestCase(APITestCase):

    def setUp(self):
        # Create test user
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )
        # Generate JWT token
        refresh = RefreshToken.for_user(self.user)
        self.auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }
        # Create active plan
        self.plan = Plan.objects.create(
            name='Basic Plan',
            description='Test plan',
            price=99.0,
            duration=3,
            is_active=True
        )
        # Create active subscription
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=90),
            status='active'
        )

    def test_user_can_unsubscribe(self):
        url = reverse('unsubscribe')
        data = {'subscription_id': self.subscription.id}
        response = self.client.post(url, data, **self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'cancelled')


class SubscriptionListViewTestCase(APITestCase):

    def setUp(self):
        # Create test user
        self.user = MyUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword123'
        )

        refresh = RefreshToken.for_user(self.user)
        self.auth_headers = {
            'HTTP_AUTHORIZATION': f'Bearer {str(refresh.access_token)}'
        }

        # Another user (to test filtering)
        self.other_user = MyUser.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass'
        )

        # Create plan
        self.plan = Plan.objects.create(
            name='Standard Plan',
            description='Standard plan description',
            price=199.0,
            duration=6,
            is_active=True
        )

        # Subscriptions for self.user
        self.sub1 = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=180),
            status='active'
        )
        self.sub2 = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now() - timezone.timedelta(days=200),
            end_date=timezone.now() - timezone.timedelta(days=20),
            status='expired'
        )

    def test_list_subscriptions_for_authenticated_user(self):
        url = reverse('subscription-list')
        response = self.client.get(url, **self.auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 2)

        returned_ids = [sub['id'] for sub in response.json()]
        self.assertIn(str(self.sub1.id), returned_ids)
        self.assertIn(str(self.sub2.id), returned_ids)
