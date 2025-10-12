from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone


@shared_task
def deactivate_inactive_users():
    user_model = get_user_model()
    week_ago = timezone.now() - timedelta(days=7)
    n = user_model.objects.filter(
        last_login__lt=week_ago,
        is_active=True,
    ).update(
        is_active=False,
    )
    return f'deactivated {n}'
