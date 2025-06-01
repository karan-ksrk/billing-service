import hashlib
import hmac
import os

import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from dotenv import load_dotenv
from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from api.models import Invoice

load_dotenv()


class PayInvoiceView(APIView):
    """
    View to handle invoice payment.
    """
    authentication_classes = [JWTAuthentication]
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


class CreateRazorPayInvoiceOrderView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        print(type(request.user))
        try:
            invoice_id = request.POST.get('invoice_id')
            print(invoice_id)
            invoice = Invoice.objects.get(id=invoice_id, user=user, status='unpaid')
        except Invoice.DoesNotExist:
            return JsonResponse({"error": "Invoice not found or already paid"}, status=400)

        # create razorpay order
        client = razorpay.client.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            order_data = {
                'amount': int(invoice.amount * 100),  # amount in paise
                'currency': 'INR',
                'receipt': str(invoice.id),
                'payment_capture': 1  # auto capture
            }
            razorpay_order = client.order.create(data=order_data)
            invoice.razorpay_order_id = razorpay_order['id']
            invoice.save()
            return JsonResponse({'order_id': razorpay_order['id']}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyRazorPayPaymentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def generate_razorpay_signature(self, order_id, payment_id):
        """Generates a Razorpay signature for payment verification."""

        message = f"{order_id}|{payment_id}"
        key = settings.RAZORPAY_KEY_SECRET.encode('utf-8')
        message_encoded = message.encode('utf-8')

        generated_signature = hmac.new(key, message_encoded, hashlib.sha256).hexdigest()
        return generated_signature

    # mocking razorpay payment ID for testing purposes

    def verify_signature(self, order_id, payment_id, signature):
        # https://razorpay.com/docs/payments/server-integration/python/integration-steps/#14-verify-payment-signature
        """
        Verify the Razorpay payment signature.
        """
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            })
            return True
        except razorpay.errors.SignatureVerificationError:
            return False

    def post(self, request):
        user = request.user

        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get(
            'razorpay_signature', self.generate_razorpay_signature(razorpay_order_id, razorpay_payment_id))
        invoice_id = request.POST.get('invoice_id')

        # Check if all required parameters are provided
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature, invoice_id]):
            return JsonResponse({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        # veify the signature and mock successful payment
        if True:
            is_payment_successful = self.verify_signature(
                razorpay_order_id, razorpay_payment_id, razorpay_signature)
            is_payment_successful = os.getenv("MOCK_PAYMENT_SUCCESS", "False") == "True"
            if not is_payment_successful:
                return JsonResponse({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark invoice as paid
        invoice = Invoice.objects.get(id=invoice_id, user=user, razorpay_order_id=razorpay_order_id)
        if invoice.status == 'paid':
            return JsonResponse({'message': 'Invoice already paid'}, status=status.HTTP_200_OK)

        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.save()

        return JsonResponse({'message': 'Payment verified and invoice marked as paid'}, status=status.HTTP_200_OK)
