import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "billing_service.settings")

app = Celery("billing_service", broker=os.getenv("CELERY_BROKER_URL"))

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


app.conf.beat_schedule = {
    "generate-invoices-daily": {
        "task": "api.tasks.generate_daily_invoice",
        # "schedule": crontab(hour=0, minute=0),  # Run daily at midnight
        "schedule": crontab(minute='*/1'),  # Run every minute for testing
    },
    "mark-overdue-invoices": {
        "task": "api.tasks.mark_overdue_invoices",
        # "schedule": crontab(hour=1, minute=0),  # Run daily at 01:00
        "schedule": crontab(minute='*/1'),
    },
    "send-invoice-reminders": {
        "task": "api.tasks.send_invoice_reminders",
        "schedule": crontab(hour=9, minute=0),  # Run daily at 09:00
        "schedule": crontab(minute='*/1'),
    },
}
