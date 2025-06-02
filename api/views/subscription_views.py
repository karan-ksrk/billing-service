from dateutil.relativedelta import relativedelta
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework_simplejwt import authentication

from api.models import Invoice, Plan, Subscription
from api.serializers import (InvoiceSerializer, PlanSerializer,
                             SubscriptionSerializer)


class PlanListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(is_active=True)
        serializer = PlanSerializer(plans, many=True)
        return JsonResponse(serializer.data, safe=False)


class SubscriptionView(APIView):
    """
    View to handle subscription creation.
    """
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            plan_id = request.POST.get('plan_id')
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return JsonResponse({'error': 'Plan not found or inactive'}, status=status.HTTP_400_BAD_REQUEST)
        # handle existing subscription
        existing_subscription = Subscription.objects.filter(user=user, status='active').first()
        if existing_subscription:
            return JsonResponse({'error': f'You already have an active subscription for {existing_subscription.plan.name}.'}, status=400)

        # create new subscription
        start_date = timezone.now()
        end_date = start_date + relativedelta(months=plan.duration)
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status='active'
        )

        # generate first invoice
        Invoice.objects.create(
            user=user,
            subscription=subscription,
            plan=plan,
            amount=plan.price,
            issue_date=start_date,
            due_date=start_date + timezone.timedelta(days=5),  # due date is 5 days after issue date
            billing_period_start=start_date.date(),
            billing_period_end=end_date.date(),
            status='unpaid'
        )

        serializer = SubscriptionSerializer(subscription)
        return JsonResponse(serializer.data, status=201)


class UnSubscriptionView(APIView):
    """
    View to handle subscription cancellation.
    """
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            subscription_id = request.POST.get('subscription_id')
            if not subscription_id:
                return JsonResponse({'error': 'subscription_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            subscription = Subscription.objects.get(id=subscription_id, user=user, status='active')
        except Subscription.DoesNotExist:
            return JsonResponse({'error': 'Subscription not found or inactive'}, status=status.HTTP_400_BAD_REQUEST)

        # cancel the subscription
        subscription.status = 'cancelled'  # not expired because it can be reactivated
        subscription.save()

        return JsonResponse({'message': 'Subscription cancelled successfully'}, status=status.HTTP_200_OK)


class SubscriptionListView(APIView):
    """
    View to list all subscriptions for the authenticated user.
    """
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return JsonResponse(serializer.data, safe=False)
