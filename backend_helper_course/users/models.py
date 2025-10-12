from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models as gis
from django.db import models
from pgvector.django import VectorField
from phonenumber_field.modelfields import PhoneNumberField

NUM_INTERESTS = 15
NUM_PRIVACY = 9


class CustomUser(AbstractUser):
    bio = models.TextField(blank=True)
    privacy_settings_vector = VectorField(
        dimensions=9,
        null=True,
        blank=True,
    )
    is_can_write = models.BooleanField(default=True)
    location = gis.PointField(geography=True, srid=4326, null=True, blank=True)
    city_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Город',
    )
    min_group_size = models.PositiveSmallIntegerField(default=5)
    max_group_size = models.PositiveSmallIntegerField(default=7)
    max_simultaneous_groups = models.PositiveSmallIntegerField(default=1)
    interest_vector = VectorField(dimensions=NUM_INTERESTS, null=True)
    is_active = models.BooleanField(default=True)
    is_offline = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    profile_photo = models.ImageField(
        upload_to='profiles/%Y/%m/%d/',
        null=True,
        blank=True,
    )
    tg_link = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    vk_link = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
    )
    phone_number = PhoneNumberField(
        blank=True,
        null=True,
    )

    def __str__(self):  # pragma: no cover
        return self.username


class Rejected(models.Model):
    SKIP = 'skip'
    DISLIKE = 'dislike'
    REASON_CHOICES = [
        (SKIP, 'Пропуск'),
        (DISLIKE, 'Дизлайк'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='rejections',
    )
    rejected_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='rejected_by',
    )
    reason = models.CharField(
        max_length=10,
        choices=REASON_CHOICES,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'rejected_user', 'reason')
        indexes = [
            models.Index(fields=['user', 'reason']),
        ]

    def __str__(self):  # pragma: no cover
        return f'{self.user} -> {self.rejected_user} ({self.reason})'


class Liked(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='likes',
    )
    liked_user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='liked_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'liked_user')
        indexes = [
            models.Index(fields=['user']),
        ]
