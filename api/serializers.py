from rest_framework import serializers
from .models import MyUser, Subscription, Plan, Invoice


class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined']


class PlanSerializer(serializers.ModelSerializer):
    duration_in_months = serializers.IntegerField(source='duration')

    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price', 'duration_in_months', 'is_active']


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'start_date', 'end_date', 'status']


class InvoiceSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'user', 'subscription', 'amount', 'issue_date', 'due_date', 'status']
