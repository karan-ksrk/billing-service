from django.core.mail import EmailMessage
from celery import shared_task


@shared_task
def send_subscription_overdue_email(user_email, subscription_id):
    """
    Send an overdue subscription email to the user.

    :param user_email: Email address of the user
    :param subscription_id: ID of the subscription
    """
    subject = "Subscription Overdue Notice"
    body = f"Dear User,\n\nYour subscription with ID {subscription_id} is overdue. Please take action to avoid service interruption.\n\nThank you!"

    email = EmailMessage(subject, body, to=[user_email])
    email.send()
