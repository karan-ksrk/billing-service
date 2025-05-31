from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
import uuid
from rest_framework_simplejwt.tokens import RefreshToken


class MyUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(unique=True, blank=False, null=False)
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }

    def __str__(self):
        return self.username


class Plan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(help_text="Duration in months")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('cancelled', 'Cancelled'),
            ('expired', 'Expired')
        ],
        default='active'
    )

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date.")

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    class Meta:
        ordering = ['-start_date']


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issue_date = models.DateTimeField()
    due_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('paid', 'Paid'),
            ('unpaid', 'Unpaid'),
            ('overdue', 'Overdue')
        ],
        default='unpaid'
    )
    paid_at = models.DateTimeField(blank=True, null=True)
    billing_period_start = models.DateField(blank=True, null=True)
    billing_period_end = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Invoice {self.id} - {self.user.username}"

    class Meta:
        ordering = ['-issue_date']
