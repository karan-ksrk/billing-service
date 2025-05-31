from django.shortcuts import render
from rest_framework.views import APIView
from .serializers import RegisterUserSerializer, SubscriptionSerializer, PlanSerializer, InvoiceSerializer
from rest_framework import permissions, authentication, status
from django.http import JsonResponse
from rest_framework import viewsets
from .models import Plan, Subscription, Invoice
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from rest_framework_simplejwt.authentication import JWTAuthentication


class PlanListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(is_active=True)
        serializer = PlanSerializer(plans, many=True)
        return JsonResponse(serializer.data, safe=False)


class SignupView(APIView):
    """
    View to handle user registration.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return JsonResponse({'message': 'User created successfully', 'user_id': user.id}, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionView(APIView):
    """
    View to handle subscription creation.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            plan_id = request.POST.get('plan_id')
            plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return JsonResponse({'error': 'Plan not found or inactive'}, status=status.HTTP_400_BAD_REQUEST)
        # handle existing subscription
        existing_subscription = Subscription.objects.filter(user=user, plan=plan, status='active').first()
        if existing_subscription:
            return JsonResponse({'error': 'You already have an active subscription for this plan.'}, status=400)

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
    authentication_classes = [authentication.BasicAuthentication]
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(user=user)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return JsonResponse(serializer.data, safe=False)


class InvoiceListView(APIView):
    """
    View to list all invoices for the authenticated user.
    """
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        invoices = Invoice.objects.filter(user=user)
        serializer = InvoiceSerializer(invoices, many=True)
        return JsonResponse(serializer.data, safe=False)


class GetLatestInvoiceView(APIView):
    """
    View to get the latest invoice for the authenticated user.
    """
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            latest_invoice = Invoice.objects.filter(user=user).latest('issue_date')
            serializer = InvoiceSerializer(latest_invoice)
            return JsonResponse(serializer.data, status=status.HTTP_200_OK)
        except Invoice.DoesNotExist:
            return JsonResponse({'error': 'No invoices found'}, status=status.HTTP_404_NOT_FOUND)


class PayInvoiceView(APIView):
    """
    View to handle invoice payment.
    """
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            invoice_id = request.POST.get('invoice_id')
            invoice = Invoice.objects.get(id=invoice_id, user=user, status='unpaid')
        except Invoice.DoesNotExist:
            return JsonResponse({'error': 'Invoice not found or already paid'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # check payment is successful
            payment_successful = True  # Replace with actual payment check logic
            if not payment_successful:
                return JsonResponse({'error': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # mark the invoice as paid
        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.save()

        return JsonResponse({'message': 'Invoice paid successfully'}, status=status.HTTP_200_OK)
