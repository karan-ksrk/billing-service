from rest_framework import permissions, status
from rest_framework_simplejwt import authentication
from api.models import Invoice
from rest_framework.views import APIView
from django.http import JsonResponse
from api.serializers import InvoiceSerializer


class GetLatestInvoiceView(APIView):
    """
    View to get the latest invoice for the authenticated user.
    """
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            latest_invoice = Invoice.objects.filter(user=user).latest('issue_date')
            serializer = InvoiceSerializer(latest_invoice)
            return JsonResponse(serializer.data, status=status.HTTP_200_OK)
        except Invoice.DoesNotExist:
            return JsonResponse({'error': 'No invoices found'}, status=status.HTTP_404_NOT_FOUND)


class InvoiceListView(APIView):
    """
    View to list all invoices for the authenticated user.
    """
    authentication_classes = [authentication.JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        invoices = Invoice.objects.filter(user=user)
        serializer = InvoiceSerializer(invoices, many=True)
        return JsonResponse(serializer.data, safe=False)
