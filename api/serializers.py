from rest_framework import serializers
from .models import MyUser, Subscription, Plan, Invoice


class MyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['id', 'email', 'is_active', 'username']


class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, max_length=20)

    class Meta:
        model = MyUser
        fields = ["email", "username", "password"]

    def validate(self, attrs):
        email = attrs.get("email")
        username = attrs.get("username")

        if not username.isalnum():
            raise serializers.ValidationError(self.default_error_messages)
        return attrs

    def create(self, validated_data):
        return MyUser.objects.create_user(**validated_data)


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
