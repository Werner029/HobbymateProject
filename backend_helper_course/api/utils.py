import numpy as np
from django.db import models

from interests.models import Interest, UserInterestRating


def recalc_interest_vector(user):
    size = Interest.objects.count()
    vec = np.zeros(size, dtype=float)
    qs = (
        UserInterestRating.objects.filter(user=user)
        .values('interest_id')
        .values('interest_id')
        .annotate(avg=models.Avg('rating'))
    )
    for row in qs:
        vec[row['interest_id'] - 1] = row['avg']
    user.interest_vector = vec.tolist()
    user.save(update_fields=['interest_vector'])


NUM_INTERESTS = 15


def build_intro_message(initiator, target):
    vec1 = (
        list(initiator.interest_vector)
        if initiator.interest_vector is not None
        else [0] * NUM_INTERESTS
    )
    vec2 = (
        list(target.interest_vector)
        if target.interest_vector is not None
        else [0] * NUM_INTERESTS
    )

    v1 = np.array(vec1, dtype=float)
    v2 = np.array(vec2, dtype=float)

    top_idx = np.argsort(np.abs(v1 - v2))[:3]
    names = (
        Interest.objects.filter(id__in=[i + 1 for i in top_idx])
        .order_by('id')
        .values_list('name', flat=True)
    )
    pretty = ', '.join(names)

    return (
        f'Привет, меня зовут {initiator.first_name} '
        f'{initiator.last_name}. Похоже, нам обоим интересны: {pretty}'
    )
