from django.urls import path
from .views import (SubscriptionView, UnSubscriptionView, SubscriptionListView, PlanListView, PayInvoiceView,
                    InvoiceListView, GetLatestInvoiceView, SignupView, CreateRazorPayInvoiceOrderView, VerifyRazorPayPaymentView)
urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("subscribe/", SubscriptionView.as_view(), name="subscribe"),
    path("unsubscribe/", UnSubscriptionView.as_view(), name="unsubscribe"),
    path("subscriptions/", SubscriptionListView.as_view(), name="subscription-list"),
    path("invoice/pay/", PayInvoiceView.as_view(), name="pay-invoice"),
    path("invoices/", InvoiceListView.as_view(), name="invoice-list"),
    path("invoice/latest/", GetLatestInvoiceView.as_view(), name="latest-invoice"),

    # payments
    path("invoice/create-order/", CreateRazorPayInvoiceOrderView.as_view(), name="create-razorpay-order"),
    path("invoice/verify-payment/", VerifyRazorPayPaymentView.as_view(), name="verify-razorpay-payment"),
]
