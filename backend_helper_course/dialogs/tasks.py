import json

import redis
from celery import shared_task
from django.conf import settings

from dialogs.find import find_candidates
from dialogs.grouping import build_groups

redis_cli = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    db=5,
)


@shared_task
def refresh_candidate_cache(user_id):
    from users.models import CustomUser

    user = CustomUser.objects.get(pk=user_id)
    pool = find_candidates(user, limit=100)
    redis_cli.set(f'cand:{user_id}', json.dumps(pool), ex=24 * 3600)


@shared_task
def refresh_all_caches():
    from users.models import CustomUser

    for user in CustomUser.objects.filter(is_active=True):
        refresh_candidate_cache.delay(user.id)


@shared_task
def refresh_groups():
    build_groups()
