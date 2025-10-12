from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Rejected, UserSwipe


@receiver(post_save, sender=UserSwipe)
def add_to_rejected(sender, instance: UserSwipe, created, **kwargs):
    if not created:
        return
    if instance.swipe_type in {UserSwipe.SKIP, UserSwipe.DISLIKE}:
        Rejected.objects.get_or_create(
            user=instance.user,
            rejected_user=instance.target_user,
            reason=instance.swipe_type,
        )
