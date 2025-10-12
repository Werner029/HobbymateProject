from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import CustomUser


class Interest(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = 'Интерес'
        verbose_name_plural = 'Интересы'


class UserInterestRating(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='interests_ratings',
    )
    interest = models.ForeignKey(
        Interest,
        on_delete=models.CASCADE,
        related_name='interest_ratings',
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'interest')
        verbose_name = 'Рейтинг интересов'
        verbose_name_plural = 'Рейтинги интересов'

    def __str__(self):  # pragma: no cover
        return f'{self.user.username} — {self.interest.name}: {self.rating}'
