import logging

from django.contrib.gis.db.models.functions import Distance

from users.models import CustomUser, Liked, Rejected

from .utils import similarity

logger = logging.getLogger(__name__)


def find_candidates(
    user,
    limit=10,
    alpha=0.5,
    geo_radius_km=50,
    pool_size=200,
):
    logger.debug('=== find_candidates for %s ===', user.id)
    me = user
    vec_me = me.interest_vector
    rejected_ids = Rejected.objects.filter(user=me).values_list(
        'rejected_user_id',
        flat=True,
    )
    logger.debug(rejected_ids)
    liked_ids = Liked.objects.filter(user=me).values_list(
        'liked_user_id',
        flat=True,
    )
    logger.debug('rejected=%s  liked=%s', rejected_ids, liked_ids)
    qs = (
        CustomUser.objects.filter(is_active=True, is_superuser=False)
        .exclude(id=me.id)
        .exclude(id__in=rejected_ids)
        .exclude(id__in=liked_ids)
    )
    logger.debug('after basic filters: %s users', qs.count())
    if me.location:
        qs = (
            qs.annotate(dist=Distance('location', me.location))
            .filter(dist__lte=geo_radius_km * 1000)
            .order_by('dist')
        )
    candidates = list(qs[:pool_size])
    logger.debug('pool sliced to %s users', len(candidates))
    scored = [
        (similarity(vec_me, c.interest_vector, alpha=alpha), c)
        for c in candidates
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    logger.debug(
        'top score=%s  bottom score=%s',
        scored[0][0] if scored else None,
        scored[-1][0] if scored else None,
    )
    return [c for _, c in scored[:limit]]
