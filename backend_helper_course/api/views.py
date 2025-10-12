import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, permissions
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from custom_groups.models import CustomGroup, GroupMember
from dialogs.find import find_candidates
from dialogs.models import Dialog, Message, Notification
from dialogs.tasks import refresh_candidate_cache
from feedback.models import Feedback
from users.models import CustomUser, Liked, Rejected

from .serializers import (
    CustomGroupSerializer,
    DialogSerializer,
    FeedbackSerializer,
    GroupMemberSerializer,
    MatchSerializer,
    MessageSerializer,
    ProfileSerializer,
    ShortUserSerializer,
)
from .utils import build_intro_message

channel_layer = get_channel_layer()
logger = logging.getLogger(__name__)


class HelloOutSerializer(drf_serializers.Serializer):
    message = drf_serializers.CharField()


class InteractionsListOutSerializer(drf_serializers.Serializer):
    liked = ShortUserSerializer(many=True)
    rejected = ShortUserSerializer(many=True)


class StatusOKSerializer(drf_serializers.Serializer):
    status = drf_serializers.CharField()


class SwipeInSerializer(drf_serializers.Serializer):
    action = drf_serializers.ChoiceField(choices=['like', 'skip', 'dislike'])


class SwipeOutSerializer(drf_serializers.Serializer):
    mutual = drf_serializers.BooleanField()
    dialog_id = drf_serializers.IntegerField(required=False, allow_null=True)


class MessageCreateIn(drf_serializers.Serializer):
    text = drf_serializers.CharField()


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer

    def get_permissions(self):
        if self.request.method in ('GET', 'POST'):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]

    def get_queryset(self):
        user = self.request.user
        if self.request.user.is_staff:
            return Feedback.objects.all()
        return Feedback.objects.filter(user=user)


class HelloViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=HelloOutSerializer)
    def list(self, request):
        username = (
            request.user.first_name + ' ' + request.user.last_name or 'аноним'
        )
        logger.debug(username)
        return Response({'message': f'Привет, {username}!'})


class ProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = CustomUser.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request, *args, **kwargs):
        if request.method == 'PATCH':
            return self.partial_update(request, *args, **kwargs)
        if request.method == 'PUT':
            return self.update(request, *args, **kwargs)
        return self.retrieve(request, *args, **kwargs)

    def get_object(self):
        if self.action == 'me':
            return self.request.user
        return super().get_object()


@extend_schema_view(
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter('pk', OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ),
    update=extend_schema(
        parameters=[
            OpenApiParameter('pk', OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ),
    partial_update=extend_schema(
        parameters=[
            OpenApiParameter('pk', OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ),
)
class GroupViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = CustomGroup.objects.all()
    serializer_class = CustomGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CustomGroup.objects.filter(
            members__user=self.request.user,
            members__is_active=True,
        ).distinct()

    def update(self, request, *args, **kwargs):
        group = self.get_object()
        is_member = GroupMember.objects.filter(
            group=group,
            user=request.user,
            is_active=True,
        ).exists()
        if not is_member:
            return Response({'detail': 'forbidden'}, status=403)
        return super().update(request, *args, **kwargs)

    @extend_schema(responses=GroupMemberSerializer(many=True))
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        qs = GroupMember.objects.filter(
            group_id=pk,
            is_active=True,
        ).select_related('user')
        return Response(GroupMemberSerializer(qs, many=True).data)

    @action(detail=False, methods=['get'])
    def me(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class InteractionsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = drf_serializers.Serializer
    lookup_url_kwarg = 'id'

    @extend_schema(responses=InteractionsListOutSerializer)
    def list(self, request):
        liked_qs = CustomUser.objects.filter(liked_by__user=request.user)
        reject_qs = CustomUser.objects.filter(rejected_by__user=request.user)
        return Response(
            {
                'liked': ShortUserSerializer(liked_qs, many=True).data,
                'rejected': ShortUserSerializer(reject_qs, many=True).data,
            },
        )

    @extend_schema(methods=['post'], responses=StatusOKSerializer)
    @action(detail=False, methods=['post'])
    def reset(self, request):
        Rejected.objects.filter(user=request.user).delete()
        return Response({'status': 'ok'})

    @extend_schema(
        methods=['delete'],
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
        responses=StatusOKSerializer,
    )
    @action(detail=True, methods=['delete'])
    def unreject(self, request, id: int = None):
        Rejected.objects.filter(
            user=request.user,
            rejected_user_id=id,
        ).delete()
        return Response({'status': 'ok'})


@extend_schema_view(
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter('pk', OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
    ),
)
class DialogViewSet(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
):
    queryset = Dialog.objects.all()
    serializer_class = DialogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Dialog.objects.filter(
            list_users=self.request.user,
        ).prefetch_related('groupchat', 'list_users')

    def create(self, request, *args, **kwargs):
        partner_id = request.data.get('partner')
        if not partner_id:
            return Response({'detail': 'partner is required'}, status=400)

        partner = get_object_or_404(CustomUser, pk=partner_id, is_active=True)
        if partner == request.user:
            return Response({'detail': 'self'}, status=400)

        dialog = (
            Dialog.objects.filter(groupchat__isnull=True)
            .filter(list_users=request.user)
            .filter(list_users=partner)
            .first()
        )

        with transaction.atomic():
            if not dialog:
                dialog = Dialog.objects.create()
                dialog.list_users.set([request.user, partner])

                Liked.objects.get_or_create(
                    user=request.user,
                    liked_user=partner,
                )

                txt = build_intro_message(request.user, partner)
                msg = Message.objects.create(sender=request.user, text=txt)
                dialog.messages.add(msg)

                payload = {
                    'id': msg.id,
                    'sender': request.user.id,
                    'sender_id': request.user.id,
                    'sender_name': request.user.username,
                    'sender_first_name': request.user.first_name or '',
                    'sender_last_name': request.user.last_name or '',
                    'sender_avatar': (
                        request.user.profile_photo.url
                        if request.user.profile_photo
                        else None
                    ),
                    'text': txt,
                    'created_at': msg.created_at.isoformat(),
                }

                async_to_sync(channel_layer.group_send)(
                    f'dialog_{dialog.id}',
                    {'type': 'chat.message', 'message': payload},
                )

                Notification.objects.create(
                    user=partner,
                    dialog=dialog,
                    text=f'Вам пришло личное сообщение от '
                    f'{request.user.first_name} {request.user.last_name}',
                )

                async_to_sync(channel_layer.group_send)(
                    f'user_{partner.id}',
                    {
                        'type': 'notify',
                        'payload': {
                            'dialog': dialog.id,
                            'text': 'Новое личное сообщение',
                        },
                    },
                )

        serializer = self.get_serializer(dialog)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=DialogSerializer(many=True))
    @action(detail=False, methods=['get'])
    def me(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @extend_schema(
        methods=['get'],
        parameters=[
            OpenApiParameter('pk', OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
        responses=MessageSerializer(many=True),
    )
    @extend_schema(
        methods=['post'],
        parameters=[
            OpenApiParameter('pk', OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
        request=MessageCreateIn,
        responses=MessageSerializer,
    )
    @action(detail=True, methods=['get', 'post'])
    def messages(self, request, pk=None):
        dialog = self.get_object()

        if request.method == 'POST':
            text = request.data.get('text', '').strip()
            if not text:
                return Response({'detail': 'Пустое сообщение'}, status=400)
            msg = Message.objects.create(sender=request.user, text=text)
            dialog.messages.add(msg)
            return Response(MessageSerializer(msg).data, status=201)
        qs = dialog.messages.order_by('created_at').select_related('sender')
        return Response(MessageSerializer(qs, many=True).data)


channel_layer = get_channel_layer()


class MatchViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'id'

    @extend_schema(responses=MatchSerializer(many=True))
    def list(self, request):
        raw_vec = request.user.interest_vector
        vec = list(raw_vec) if raw_vec is not None else []
        if not any(v > 2 for v in vec):
            return Response(
                {
                    'detail': 'Поставьте оценки интересам'
                    ' выше 2, чтобы начать поиск.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        pool = find_candidates(request.user, limit=10)
        if not pool:
            return Response([], status=200)
        return Response(MatchSerializer(pool, many=True).data)

    @extend_schema(
        methods=['post'],
        parameters=[
            OpenApiParameter('id', OpenApiTypes.INT, OpenApiParameter.PATH),
        ],
        request=SwipeInSerializer,
        responses=SwipeOutSerializer,
    )
    @action(detail=True, methods=['post'])
    def swipe(self, request, id: int = None):
        action = request.data.get('action')
        target = get_object_or_404(CustomUser, pk=id)

        if action == 'like':
            Liked.objects.get_or_create(user=request.user, liked_user=target)
            reciprocal = Liked.objects.filter(
                user=target,
                liked_user=request.user,
            ).exists()

            if reciprocal:
                dialog = (
                    Dialog.objects.filter(groupchat__isnull=True)
                    .filter(list_users=request.user)
                    .filter(list_users=target)
                    .first()
                )
                if not dialog:
                    dialog = Dialog.objects.create()
                    dialog.list_users.set([request.user, target])
                    for uid in (request.user.id, target.id):
                        Notification.objects.create(
                            user_id=uid,
                            dialog=dialog,
                            text='У вас новый матч! '
                            'Откройте чат и поздоровайтесь 🙂',
                        )
                        async_to_sync(channel_layer.group_send)(
                            f'user_{uid}',
                            {
                                'type': 'notify',
                                'payload': {
                                    'dialog': dialog.id,
                                    'text': 'У вас новый матч! 💚',
                                },
                            },
                        )
                refresh_candidate_cache.delay(request.user.id)
                return Response(
                    {'mutual': True, 'dialog_id': dialog.id},
                    status=status.HTTP_201_CREATED,
                )

            return Response({'mutual': False})

        Rejected.objects.get_or_create(
            user=request.user,
            rejected_user=target,
            reason=action,
        )
        return Response({'mutual': False})
