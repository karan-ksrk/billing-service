from django.contrib import admin
from .models import MyUser, Plan, Subscription, Invoice
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule,
)

# Unregister django-celery-beat models
admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)


class MyUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'address')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'address')}),
    )


admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Plan)
admin.site.register(Subscription)
admin.site.register(Invoice)
