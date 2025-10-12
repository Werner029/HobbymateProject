import json
import logging

from django.core.exceptions import ValidationError
from django.http import QueryDict
from drf_spectacular.utils import OpenApiTypes, extend_schema_field
from rest_framework import serializers

from api.geocode import geocode_to_point
from custom_groups.models import CustomGroup, GroupMember
from dialogs.models import Dialog, GroupChat, Message
from feedback.models import Feedback
from interests.models import Interest, UserInterestRating
from users.models import CustomUser, Liked

logger = logging.getLogger(__name__)


class GroupMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id')
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    profile_photo = serializers.CharField(
        source='user.profile_photo.url',
        read_only=True,
    )

    class Meta:
        model = GroupMember
        fields = [
            'user_id',
            'username',
            'first_name',
            'last_name',
            'profile_photo',
            'is_admin',
        ]


class ShortUserSerializer(serializers.ModelSerializer):
    profile_photo = serializers.CharField(
        source='profile_photo.url',
        read_only=True,
    )

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'profile_photo']


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            'id',
            'text',
            'answer_text',
            'is_answered',
            'created_at',
            'answered_at',
            'answered_by',
        ]
        read_only_fields = [
            'id',
            'is_answered',
            'created_at',
            'answered_at',
            'answered_by',
        ]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserInterestRatingSerializer(serializers.ModelSerializer):
    interest_id = serializers.IntegerField()
    interest_name = serializers.CharField(
        source='interest.name',
        read_only=True,
    )

    class Meta:
        model = UserInterestRating
        fields = ['interest_id', 'interest_name', 'rating']


class ProfileSerializer(serializers.ModelSerializer):
    privacy_settings_vector = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=1),
        required=False,
        allow_null=True,
    )
    date_of_birth = serializers.DateField(
        required=False,
        allow_null=True,
        input_formats=['%Y-%m-%d', '%d-%m-%Y'],
    )
    interests_ratings = UserInterestRatingSerializer(many=True, required=False)
    profile_photo = serializers.ImageField(required=False, allow_null=True)
    city_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        label='Город',
    )
    interest_vector = serializers.ListField(read_only=True)
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'privacy_settings_vector',
            'date_of_birth',
            'bio',
            'tg_link',
            'vk_link',
            'profile_photo',
            'is_can_write',
            'city_name',
            'is_offline',
            'interest_vector',
            'interests_ratings',
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
        read_only_fields = ('id', 'email', 'interest_vector')

    def to_internal_value(self, data):
        if isinstance(data, QueryDict):
            data = data.copy()

        if data.get('date_of_birth') == '':
            data['date_of_birth'] = None

        if isinstance(data, QueryDict):
            data = dict(data.lists())
            data = {
                k: v[0] if isinstance(v, list) and len(v) == 1 else v
                for k, v in data.items()
            }

        raw = data.get('interests_ratings')
        if isinstance(raw, str):
            try:
                data['interests_ratings'] = json.loads(raw)
            except json.JSONDecodeError:
                pass
        raw1 = data.get('privacy_settings_vector')
        if isinstance(raw1, str):
            try:
                data['privacy_settings_vector'] = json.loads(raw1)
            except json.JSONDecodeError:
                pass
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        city = validated_data.pop('city_name', None)
        if city is not None:
            instance.city_name = city
        if city:
            try:
                instance.location = geocode_to_point(city)
            except Exception:
                raise serializers.ValidationError(
                    {'city': 'Не удалось распознать город'},
                )
        ratings = validated_data.pop('interests_ratings', [])
        logger.debug(f' ratings after pop: {ratings!r}')

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        for r in ratings:
            UserInterestRating.objects.update_or_create(
                user=instance,
                interest_id=r['interest_id'],
                defaults={'rating': r['rating']},
            )

        from .utils import recalc_interest_vector

        recalc_interest_vector(instance)
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)

        raw_vec = instance.privacy_settings_vector
        vec = list(raw_vec) if raw_vec is not None else []
        if len(vec) < 9:
            vec.extend([1] * (9 - len(vec)))

        given = {r['interest_id']: r for r in data['interests_ratings']}
        data['interests_ratings'] = [
            {
                'interest_id': it.id,
                'interest_name': it.name,
                'rating': given.get(it.id, {}).get('rating', 1),
            }
            for it in Interest.objects.order_by('id')
        ]

        req_user = self.context['request'].user
        liked_this_viewer = Liked.objects.filter(
            user=instance,
            liked_user=req_user,
        ).exists()

        if req_user != instance and not liked_this_viewer:
            if not vec[0]:
                data['profile_photo'] = None
            if not vec[1]:
                data.pop('email', None)
            if not vec[2]:
                data.pop('phone_number', None)
            if not vec[3]:
                data.pop('date_of_birth', None)
            if not vec[4]:
                data.pop('bio', None)
            if not vec[5]:
                data.pop('tg_link', None)
            if not vec[6]:
                data.pop('vk_link', None)
            if not vec[7]:
                data.pop('city_name', None)
            if not vec[8]:
                data.pop('is_offline', None)

        return data

    def validate_profile_photo(self, photo):
        ext = photo.name.split('.')[-1].lower()
        if ext not in ('jpg', 'jpeg', 'png', 'webp'):
            raise ValidationError('Допустимые форматы: JPG, PNG, WEBP.')
        if photo.size > 15 * 1024 * 1024:
            raise ValidationError('Файл должен быть ≤ 15 МБ.')
        return photo


class CustomGroupSerializer(serializers.ModelSerializer):
    members_count = serializers.IntegerField(
        source='members.count',
        read_only=True,
    )
    chat_id = serializers.SerializerMethodField()

    class Meta:
        model = CustomGroup
        fields = [
            'id',
            'name',
            'description',
            'created_at',
            'members_count',
            'chat_id',
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_chat_id(self, group):
        chat, created = GroupChat.objects.get_or_create(group=group)
        if created:
            user_ids = group.members.filter(is_active=True).values_list(
                'user_id',
                flat=True,
            )
            chat.list_users.set(user_ids)
        return chat.id


class GroupChatSerializer(serializers.ModelSerializer):
    group = CustomGroupSerializer()

    class Meta:
        model = GroupChat
        fields = ['id', 'group', 'created_at']


class DialogSerializer(serializers.ModelSerializer):
    is_group = serializers.SerializerMethodField()
    partner = serializers.SerializerMethodField()
    group_name = serializers.CharField(
        source='groupchat.group.name',
        read_only=True,
    )

    class Meta:
        model = Dialog
        fields = ['id', 'created_at', 'is_group', 'partner', 'group_name']

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_is_group(self, obj):
        return hasattr(obj, 'groupchat')

    @extend_schema_field(ShortUserSerializer)
    def get_partner(self, obj):
        if self.get_is_group(obj):
            return None
        me = self.context['request'].user
        other = obj.list_users.exclude(id=me.id).first()
        return (
            ShortUserSerializer(other, context=self.context).data
            if other
            else None
        )


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.IntegerField(source='sender.id', read_only=True)

    sender_name = serializers.SerializerMethodField()
    sender_avatar = serializers.CharField(
        source='sender.profile_photo.url',
        read_only=True,
    )

    class Meta:
        model = Message
        fields = [
            'id',
            'sender',
            'sender_name',
            'sender_avatar',
            'text',
            'created_at',
        ]
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.STR)
    def get_sender_name(self, obj):
        u = obj.sender
        return f'{u.first_name} {u.last_name}'.strip() or u.username


class MatchSerializer(serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'first_name',
            'last_name',
            'profile_photo',
            'vk_link',
            'tg_link',
            'phone_number',
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_profile_photo(self, obj):
        vec = list(obj.privacy_settings_vector or [1] * 9)
        return obj.profile_photo.url if vec[0] and obj.profile_photo else None
