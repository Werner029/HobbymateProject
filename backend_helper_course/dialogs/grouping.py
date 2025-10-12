import networkx as nx
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.postgres.aggregates import ArrayAgg
from django.db import transaction
from django.db.models import Count

from custom_groups.models import CustomGroup, GroupMember
from dialogs.models import GroupChat, Notification
from users.models import CustomUser

channel_layer = get_channel_layer()
MIN_SIZE = 5
MAX_SIZE = 7


def build_graph():
    g = nx.Graph()
    users = CustomUser.objects.filter(is_active=True)
    for user in users:
        g.add_node(user.id)
    from users.models import Liked

    for like in Liked.objects.select_related('user', 'liked_user'):
        if Liked.objects.filter(
            user=like.liked_user,
            liked_user=like.user,
        ).exists():
            g.add_edge(like.user_id, like.liked_user_id)
    return g


def split_clique(clique):
    if len(clique) <= MAX_SIZE:
        return [clique]
    chunks = []
    for i in range(0, len(clique), MAX_SIZE):
        chunk = clique[i : i + MAX_SIZE]
        if len(chunk) >= MIN_SIZE:
            chunks.append(chunk)

    return chunks


def group_exists(user_ids):
    sorted_ids = sorted(user_ids)
    return (
        CustomGroup.objects.annotate(
            members_ids=ArrayAgg(
                'members__user_id',
                distinct=True,
                ordering='members__user_id',
            ),
            members_cnt=Count('members'),
        )
        .filter(members_cnt=len(sorted_ids), members_ids=sorted_ids)
        .exists()
    )


@transaction.atomic
def build_groups():
    g = build_graph()
    for clique in nx.find_cliques(g):
        if len(clique) < MIN_SIZE:
            continue
        for chunk in split_clique(clique):
            if group_exists(chunk):
                continue
            create_group(chunk)


def create_group(user_ids):
    users = CustomUser.objects.filter(id__in=user_ids)
    name = ', '.join(u.first_name or u.username for u in users[:3]) + '…'
    group = CustomGroup.objects.create(
        name=f'Группа {name}',
        description='Сформирована автоматически по интересам',
    )
    GroupMember.objects.bulk_create(
        [GroupMember(user=u, group=group) for u in users],
    )
    chat = GroupChat.objects.create(group=group)
    chat.list_users.set(user_ids)
    for uid in user_ids:
        Notification.objects.create(
            user_id=uid,
            dialog=chat,
            text=f'Вы добавлены в новую группу «{group.name}»',
        )
        async_to_sync(channel_layer.group_send)(
            f'user_{uid}',
            {
                'type': 'notify',
                'payload': {
                    'dialog': chat.id,
                    'text': f'Вы добавлены в новую группу «{group.name}»',
                },
            },
        )
