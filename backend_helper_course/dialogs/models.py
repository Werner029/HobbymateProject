from django.db import models
from django.utils import timezone

from custom_groups.models import CustomGroup
from users.models import CustomUser


class Message(models.Model):
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'


class Dialog(models.Model):
    list_users = models.ManyToManyField(CustomUser, related_name='list_users')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    messages = models.ManyToManyField(Message, related_name='dialogs')

    class Meta:
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'
        ordering = ['-created_at']


class GroupChat(Dialog):
    group = models.ForeignKey(
        CustomGroup,
        on_delete=models.CASCADE,
        related_name='group_chats',
    )

    class Meta:
        verbose_name = 'Групповой чат'
        verbose_name_plural = 'Групповые чаты'
        ordering = ['-created_at']


class Notification(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    dialog = models.ForeignKey(Dialog, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
