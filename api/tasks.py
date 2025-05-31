from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Subscription, Invoice
from dateutil.relativedelta import relativedelta
from api.mails.send_subsciption_overdue_email import send_subscription_overdue_email


@shared_task
def generate_daily_invoice():
    today = timezone.now().date()
    active_subs = Subscription.objects.filter(status="active")

    for sub in active_subs:
        plan_duration_months = sub.plan.duration  # duration in months
        start_date = sub.start_date.date()
        end_date = sub.end_date.date()

        # if subscription is not active today, skip it
        if today < start_date or today > end_date:
            continue

        ''' 
        Figure out which billing cycle today is in.
        example-
        start_date = Jan 21, 2025
        today = May 31, 2025
        months_since_start = (2025-2025) * 12 + (5-1) = 4
        '''
        months_since_start = (today.year - start_date.year) * 12 + (today.month - start_date.month)

        '''
        4 % 1 = 0 means we are at the start of a billing cycle.
        4 % 3 = 1 means we are in the middle of a billing cycle.
        '''
        if months_since_start % plan_duration_months != 0:
            continue  # we are not at the start of a billing cycle, used the basic modulus operation to check

        '''
        if we are in the start of a billing cycle, calculate its end of billing cycle
        here we calculate the next billing cycle start and end dates.
        '''
        cycle_start = start_date + relativedelta(months=+months_since_start)
        cycle_end = cycle_start + relativedelta(months=+plan_duration_months)

        # Check if invoice already exists for this cycle # mostly this case will not happen approx 99.9% miss
        if Invoice.objects.filter(subscription=sub, billing_period_start=cycle_start).exists():
            continue

        # Creating the invoice for the new billing cycle
        Invoice.objects.create(
            user=sub.user,
            subscription=sub,
            plan=sub.plan,
            amount=sub.plan.price,
            issue_date=timezone.now(),
            due_date=timezone.now() + timedelta(days=5),
            status='unpaid',
            billing_period_start=cycle_start,  # new billing cycle start date
            billing_period_end=cycle_end,  # new billing cycle end
        )
        print(f"Invoice created for user: {sub.user.username} ({cycle_start} - {cycle_end})")


@shared_task
def mark_overdue_invoices():
    now = timezone.now()
    invoices = Invoice.objects.filter(status='unpaid', due_date__lt=now)
    for inv in invoices:
        inv.status = 'overdue'
        inv.save()
        print(f'Invoice {inv.id} marked as overdue.')
        # cancel subscription if overdue for more than 7 days
        if now - inv.due_date > timedelta(days=7):
            sub = inv.subscription
            sub.status = 'cancelled'
            sub.save()
            # send mail or notification to user about subscription expired
            print(f'Subscription {sub.id} for user {sub.user.username} cancelled due to overdue invoice.')


@shared_task
def send_invoice_reminders():
    overdue = Invoice.objects.filter(status='overdue', subscription__status='active')

    for inv in overdue:
        send_subscription_overdue_email.delay(
            user_email=inv.user.email,
            subscription_id=inv.subscription.id
        )
        print(f"Reminder: Invoice {inv.id} for {inv.user.username} is overdue.")
