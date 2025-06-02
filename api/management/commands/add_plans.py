from django.core.management.base import BaseCommand
from api.models import Plan


class Command(BaseCommand):
    help = 'Add default subscription plans'

    def handle(self, *args, **kwargs):
        plans = [
            {
                "name": "Basic",
                "price": 499,
                "description": "Basic plan with limited features.",
                "duration": 1,
            },
            {
                "name": "Pro",
                "price": 999,
                "description": "Pro plan with more features.",
                "duration": 3,
            },
            {
                "name": "Enterprise",
                "price": 4999,
                "description": "Enterprise plan with all features.",
                "duration": 12,
            },
        ]

        for plan_data in plans:
            plan, created = Plan.objects.get_or_create(name=plan_data["name"], defaults=plan_data)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created plan: {plan.name}"))
            else:
                self.stdout.write(f"Plan already exists: {plan.name}")
