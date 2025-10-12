from django.db import models

from users.models import CustomUser


class CustomGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['-created_at']

    def __str__(self):  # pragma: no cover
        return self.name


class GroupMember(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='group_memberships',
        verbose_name='Пользователь',
    )
    group = models.ForeignKey(
        CustomGroup,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='Группа',
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Участник группы'
        verbose_name_plural = 'Участники групп'
        ordering = ['group', 'joined_at']
        unique_together = ('user', 'group')

    def __str__(self):  # pragma: no cover
        role = 'Admin' if self.is_admin else 'Member'
        return f'{self.user.username} в {self.group.name} ({role})'
