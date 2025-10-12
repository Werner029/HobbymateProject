from django.db import models

from users.models import CustomUser


class Feedback(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='feedbacks',
    )
    text = models.TextField(verbose_name='Текст отзыва')
    answer_text = models.TextField(verbose_name='Текст ответа', null=True)
    is_answered = models.BooleanField(default=False)
    answered_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='handled_feedbacks',
        blank=True,
        null=True,
        verbose_name='Ответил',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
    )
    answered_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Дата ответа',
    )

    class Meta:
        verbose_name = 'Обратная связь'
        verbose_name_plural = 'Обратная связь'
        ordering = ['-created_at']

    def __str__(self):
        return f'Feedback #{self.pk} от {self.user.username}'
