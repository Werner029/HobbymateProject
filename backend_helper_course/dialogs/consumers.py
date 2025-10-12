import logging

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer

from users.models import Liked

from .models import Dialog, Message, Notification

channel_layer = get_channel_layer()

logger = logging.getLogger('django.channels')


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.dialog_id = self.scope['url_route']['kwargs']['dialog_id']
        self.group_name = f'dialog_{self.dialog_id}'
        user = self.scope['user']
        logger.debug(
            '[ChatConsumer] CONNECT '
            f'user={user.id!r} dialog={self.dialog_id!r}',
        )
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug('[ChatConsumer] ACCEPTED')

    async def disconnect(self, close_code):
        logger.debug(
            f'[ChatConsumer] DISCONNECT '
            f'code={close_code} dialog={self.dialog_id}',
        )
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    @database_sync_to_async
    def get_recipient_ids(self):
        dialog = Dialog.objects.get(pk=self.dialog_id)
        return list(
            dialog.list_users.exclude(id=self.scope['user'].id).values_list(
                'id',
                flat=True,
            ),
        )

    @database_sync_to_async
    def get_chat_title(self):
        from .models import Dialog

        dialog = Dialog.objects.get(pk=self.dialog_id)
        if hasattr(dialog, 'groupchat'):
            return dialog.groupchat.group.name
        other = dialog.list_users.exclude(id=self.scope['user'].id).first()
        return (
            f'{other.first_name} {other.last_name}'.strip()
            if (other.first_name or other.last_name)
            else other.username
        )

    async def receive_json(self, content):
        logger.debug(
            f'[ChatConsumer] RECEIVE_JSON '
            f'dialog={self.dialog_id} content={content!r}',
        )
        try:
            msg = await self.create_message(content['text'])
            await self._ensure_like_on_reply(msg.sender_id)
        except Exception as e:
            logger.error(
                f'[ChatConsumer] Failed to create message: {e}',
                exc_info=True,
            )
            return
        payload = {
            'id': msg.id,
            'sender': msg.sender.id,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.username,
            'sender_first_name': msg.sender.first_name or '',
            'sender_last_name': msg.sender.last_name or '',
            'sender_avatar': (
                msg.sender.profile_photo.url
                if msg.sender.profile_photo
                else None
            ),
            'text': msg.text,
            'created_at': msg.created_at.isoformat(),
        }
        logger.debug(f'[ChatConsumer] BROADCAST {payload}')
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'chat.message', 'message': payload},
        )
        recipient_ids = await self.get_recipient_ids()
        title = await self.get_chat_title()
        for uid in recipient_ids:
            await database_sync_to_async(Notification.objects.create)(
                user_id=uid,
                dialog_id=self.dialog_id,
                text=f'Новое сообщение в чате «{title}»: {msg.text[:50]}',
            )
            await channel_layer.group_send(
                f'user_{uid}',
                {
                    'type': 'notify',
                    'payload': {
                        'dialog': self.dialog_id,
                        'text': (
                            f'Новое сообщение в '
                            f'чате «{title}»: {payload["text"][:50]}'
                        ),
                    },
                },
            )

    async def chat_message(self, event):
        logger.debug(
            f'[ChatConsumer] CHAT_MESSAGE to client: {event["message"]!r}',
        )
        await self.send_json(event['message'])

    @database_sync_to_async
    def create_message(self, text):
        msg = Message.objects.create(sender=self.scope['user'], text=text)
        dialog = Dialog.objects.get(pk=self.dialog_id)
        dialog.messages.add(msg)
        return msg

    @database_sync_to_async
    def _other_participants(self):
        dialog = Dialog.objects.get(pk=self.dialog_id)
        return list(
            dialog.list_users.exclude(id=self.scope['user'].id).values_list(
                'id',
                flat=True,
            ),
        )

    @database_sync_to_async
    def _ensure_like_on_reply(self, sender_id):
        dialog = Dialog.objects.select_related('groupchat').get(
            pk=self.dialog_id,
        )
        if hasattr(dialog, 'groupchat'):
            return
        users = list(dialog.list_users.values_list('id', flat=True))
        if len(users) != 2 or sender_id not in users:
            return
        other_id = users[1] if users[0] == sender_id else users[0]
        if Liked.objects.filter(
            user_id=sender_id,
            liked_user_id=other_id,
        ).exists():
            return
        Liked.objects.create(user_id=sender_id, liked_user_id=other_id)
        if Liked.objects.filter(
            user_id=other_id,
            liked_user_id=sender_id,
        ).exists():
            for uid in users:
                Notification.objects.create(
                    user_id=uid,
                    dialog_id=self.dialog_id,
                    text='У вас новый матч! Откройте чат и поздоровайтесь 🙂',
                )
                async_to_sync(channel_layer.group_send)(
                    f'user_{uid}',
                    {
                        'type': 'notify',
                        'payload': {
                            'dialog': self.dialog_id,
                            'text': 'У вас новый матч! 💚',
                        },
                    },
                )


class NotifyConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_anonymous:
            await self.close()
            return

        self.group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.debug(f'[Notify] CONNECT user={self.user.id}')
        payloads = await self.fetch_unread_payloads()
        for p in payloads:
            await self.send_json(p)
            await self._mark_read(p['id'])

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    async def notify(self, event):
        await self.send_json(event['payload'])

    @database_sync_to_async
    def fetch_unread_payloads(self):
        notifs = Notification.objects.filter(
            user=self.user,
            read=False,
        ).select_related('dialog')
        result = []
        for n in notifs:
            dialog = n.dialog
            other = dialog.list_users.exclude(id=self.user.id).first()
            result.append(
                {
                    'dialog': str(n.dialog_id),
                    'text': n.text,
                    'from': other.id if other else None,
                    'id': n.id,
                    'created_at': n.created_at.isoformat(),
                },
            )
        return result

    @database_sync_to_async
    def _mark_read(self, nid):
        Notification.objects.filter(pk=nid).update(read=True)
