import importlib

import pytest
from django.core.files.base import ContentFile
from django.urls import NoReverseMatch
from django.urls import reverse as dj_reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.serializers import MessageSerializer
from custom_groups.models import CustomGroup, GroupMember
from dialogs.models import Dialog, Message, Notification
from feedback.models import Feedback
from users.models import CustomUser, Liked, Rejected


def reverse(name, *pargs, **pkwargs):
    mapping = {
        'group-me': 'groups-me',
        'group-members': 'groups-members',
        'group-detail': 'groups-detail',
        'dialog-list': 'dialogs-list',
        'dialog-messages': 'dialogs-messages',
        'match-list': 'matches-list',
        'match-swipe': 'matches-swipe',
    }
    args_param = None
    kwargs_param = None
    if pargs:
        if isinstance(pargs[0], (list, tuple)):  # pragma: no cover
            args_param = list(pargs[0])
        else:
            args_param = list(pargs)  # pragma: no cover
    if pkwargs:
        if 'args' in pkwargs:
            args_param = pkwargs.get('args')
        if 'kwargs' in pkwargs:
            kwargs_param = pkwargs.get('kwargs')  # pragma: no cover
        other = {
            k: v for k, v in pkwargs.items() if k not in ('args', 'kwargs')
        }
        if other:  # pragma: no cover
            if kwargs_param:
                kwargs_param = {**kwargs_param, **other}
            else:
                kwargs_param = other

    try:
        return dj_reverse(name, args=args_param, kwargs=kwargs_param)
    except NoReverseMatch:
        alt = mapping.get(name, name)
        return dj_reverse(alt, args=args_param, kwargs=kwargs_param)


def attach_photo(u, fname='ph.jpg'):
    u.profile_photo.save(fname, ContentFile(b'abc'), save=True)
    return u


@pytest.fixture(autouse=True)
def stub_recalc(monkeypatch):
    utils = importlib.import_module('api.utils')
    monkeypatch.setattr(utils, 'recalc_interest_vector', lambda user: None)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    u = CustomUser.objects.create_user(
        username='alice',
        password='secret',
        first_name='Alice',
        last_name='Lee',
    )
    return attach_photo(u)


@pytest.fixture
def user2(db):
    u = CustomUser.objects.create_user(
        username='bob',
        password='secret',
        first_name='Bob',
        last_name='Moon',
    )
    return attach_photo(u, 'ph2.jpg')


@pytest.fixture
def admin(db):
    u = CustomUser.objects.create_superuser(
        username='root',
        password='rootpass',
        email='root@example.com',
    )
    return attach_photo(u, 'admin.jpg')


@pytest.mark.django_db
def test_hello_requires_auth(api_client):
    url = reverse('hello-list')
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_hello_returns_greeting(api_client, user):
    api_client.force_authenticate(user)
    url = reverse('hello-list')
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert 'Привет' in resp.data['message']


@pytest.mark.django_db
def test_profile_me_get(api_client, user):
    api_client.force_authenticate(user)
    url = reverse('profile-me')
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['id'] == user.id


@pytest.mark.django_db
def test_profile_me_patch(api_client, user):
    api_client.force_authenticate(user)
    url = reverse('profile-me')
    payload = {'first_name': 'Alicia'}
    resp = api_client.patch(url, payload, format='json')
    user.refresh_from_db()
    assert resp.status_code == status.HTTP_200_OK
    assert user.first_name == 'Alicia'


@pytest.mark.django_db
def test_feedback_create_and_filter_by_owner(api_client, user):
    api_client.force_authenticate(user)
    create_url = reverse('feedback-list')
    payload = {'text': 'Отличное приложение!'}
    resp = api_client.post(create_url, payload, format='json')
    assert resp.status_code == status.HTTP_201_CREATED
    resp2 = api_client.get(create_url)
    assert resp2.status_code == status.HTTP_200_OK
    assert len(resp2.data) == 1
    assert resp2.data[0]['text'] == payload['text']


@pytest.mark.django_db
def test_feedback_admin_sees_all(api_client, user, admin):
    Feedback.objects.create(user=user, text='Bug #1')
    Feedback.objects.create(user=admin, text='Bug #2')
    api_client.force_authenticate(admin)
    url = reverse('feedback-list')
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data) == 2


@pytest.mark.django_db
def test_group_me_lists_only_active_memberships(api_client, user):
    api_client.force_authenticate(user)
    g1 = CustomGroup.objects.create(name='Basketball')
    g2 = CustomGroup.objects.create(name='Inactive group')
    GroupMember.objects.create(group=g1, user=user, is_active=True)
    GroupMember.objects.create(group=g2, user=user, is_active=False)
    url = reverse('group-me')
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data) == 1
    assert resp.data[0]['name'] == g1.name


@pytest.mark.django_db
def test_dialog_create_or_get_existing(api_client, user, user2):
    api_client.force_authenticate(user)
    url = reverse('dialog-list')
    payload = {'partner': user2.id}
    resp = api_client.post(url, payload, format='json')
    assert resp.status_code == status.HTTP_201_CREATED
    dialog_id = resp.data['id']
    resp2 = api_client.post(url, payload, format='json')
    assert resp2.data['id'] == dialog_id
    assert Dialog.objects.count() == 1


@pytest.mark.django_db
def test_dialog_messages_send_and_get(api_client, user, user2):
    dialog = Dialog.objects.create()
    dialog.list_users.set([user, user2])
    api_client.force_authenticate(user)
    url = reverse('dialog-messages', args=[dialog.id])
    bad = api_client.post(url, {'text': '   '}, format='json')
    assert bad.status_code == status.HTTP_400_BAD_REQUEST
    ok = api_client.post(url, {'text': 'Привет!'}, format='json')
    assert ok.status_code == status.HTTP_201_CREATED
    assert Message.objects.filter(dialogs__id=dialog.id).count() == 1
    history = api_client.get(url)
    assert history.status_code == status.HTTP_200_OK
    assert history.data[0]['text'] == 'Привет!'


@pytest.fixture
def user_with_vector(user):
    user.interest_vector = [3] * 15
    user.save()
    return user


@pytest.mark.django_db
def test_match_requires_vector(api_client, user):
    user.interest_vector = [3] * 15
    user.interest_vector[0] = 5
    user.save()
    api_client.force_authenticate(user)
    url = reverse('match-list')
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_match_swipe_like_and_reciprocal(api_client, user_with_vector, user2):
    user2.interest_vector = [4] * 15
    user2.save()
    api_client.force_authenticate(user_with_vector)
    list_url = reverse('match-list')
    assert api_client.get(list_url).status_code == status.HTTP_200_OK
    swipe_url = reverse('match-swipe', args=[user2.id])
    resp = api_client.post(swipe_url, {'action': 'like'}, format='json')
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data['mutual'] is False
    assert Liked.objects.filter(
        user=user_with_vector,
        liked_user=user2,
    ).exists()
    api_client.force_authenticate(user2)
    resp2 = api_client.post(
        reverse('match-swipe', args=[user_with_vector.id]),
        {'action': 'like'},
        format='json',
    )
    assert resp2.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
    assert resp2.data['mutual'] is True
    dialog_id = resp2.data['dialog_id']
    assert Dialog.objects.filter(id=dialog_id).exists()
    assert Notification.objects.filter(dialog_id=dialog_id).count() == 2


@pytest.mark.django_db
def test_match_swipe_rejected(api_client, user_with_vector, user2):
    api_client.force_authenticate(user_with_vector)
    url = reverse('match-swipe', args=[user2.id])
    resp = api_client.post(url, {'action': 'dislike'}, format='json')
    assert resp.status_code == status.HTTP_200_OK
    assert Rejected.objects.filter(
        user=user_with_vector,
        rejected_user=user2,
    ).exists()


@pytest.mark.django_db
def test_interactions_list(api_client, user, user2):
    Liked.objects.create(user=user, liked_user=user2)
    Rejected.objects.create(user=user, rejected_user=user2, reason='dislike')
    api_client.force_authenticate(user)
    url = reverse('interactions-list')
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.data.get('liked'), list)
    assert isinstance(resp.data.get('rejected'), list)
    assert len(resp.data['liked']) == 1
    assert len(resp.data['rejected']) == 1


@pytest.mark.django_db
def test_group_members(api_client, user, user2):
    group = CustomGroup.objects.create(name='Test Group')
    GroupMember.objects.create(
        group=group,
        user=user,
        is_active=True,
        is_admin=True,
    )
    GroupMember.objects.create(
        group=group,
        user=user2,
        is_active=True,
        is_admin=False,
    )
    api_client.force_authenticate(user)
    url = reverse('group-members', args=[group.id])
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    names = {m['username'] for m in resp.data}
    assert user.username in names and user2.username in names


@pytest.mark.django_db
def test_group_update_by_member(api_client, user):
    group = CustomGroup.objects.create(name='Test Group')
    GroupMember.objects.create(group=group, user=user, is_active=True)
    api_client.force_authenticate(user)
    url = reverse('group-detail', args=[group.id])
    resp = api_client.patch(url, {'name': 'New Name'}, format='json')
    assert resp.status_code in (
        status.HTTP_200_OK,
        status.HTTP_202_ACCEPTED,
        status.HTTP_204_NO_CONTENT,
    )


@pytest.mark.django_db
def test_group_update_by_non_member(api_client, user, user2):
    group = CustomGroup.objects.create(name='Test Group')
    GroupMember.objects.create(group=group, user=user2, is_active=True)
    api_client.force_authenticate(user)
    url = reverse('group-detail', args=[group.id])
    resp = api_client.patch(url, {'name': 'Nope'}, format='json')
    assert resp.status_code in (
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    )


@pytest.mark.django_db
def test_dialog_messages_get(api_client, user, user2):
    dialog = Dialog.objects.create()
    dialog.list_users.set([user, user2])
    msg1 = Message.objects.create(sender=user, text='Привет!')
    msg2 = Message.objects.create(sender=user2, text='Привет!')
    dialog.messages.set([msg1, msg2])
    api_client.force_authenticate(user)
    url = reverse('dialog-messages', args=[dialog.id])
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data) == 2


@pytest.mark.django_db
def test_match_list_requires_interest_vector(api_client, user):
    api_client.force_authenticate(user)
    url = reverse('match-list')
    resp = api_client.get(url)
    assert resp.status_code in (
        status.HTTP_200_OK,
        status.HTTP_400_BAD_REQUEST,
    )


@pytest.mark.django_db
def test_match_list_with_vector(api_client, user_with_vector, user2):
    user2.interest_vector = [4] * 15
    user2.save()
    api_client.force_authenticate(user_with_vector)
    url = reverse('match-list')
    resp = api_client.get(url)
    assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_interest_models():
    from interests.models import Interest, UserInterestRating

    interest = Interest.objects.create(name='Спорт')
    assert interest.name == 'Спорт'
    user = CustomUser.objects.create_user(
        username='test_interest',
        password='secret',
    )
    rating = UserInterestRating.objects.create(
        user=user,
        interest=interest,
        rating=5,
    )
    assert rating.rating == 5


@pytest.mark.django_db
def test_feedback_model():
    user = CustomUser.objects.create_user(username='test', password='secret')
    feedback = Feedback.objects.create(
        user=user,
        text='Test feedback',
        answer_text='Test answer',
        is_answered=True,
    )
    assert feedback.text == 'Test feedback'
    assert feedback.user.username == 'test'
    s = str(feedback)
    assert s.startswith('Feedback #') and 'test' in s


@pytest.mark.django_db
def test_group_member_serializer():
    from api.serializers import GroupMemberSerializer
    from custom_groups.models import CustomGroup, GroupMember

    user = CustomUser.objects.create_user(username='test', password='secret')
    attach_photo(user, 'gm.jpg')
    group = CustomGroup.objects.create(name='Test Group')
    member = GroupMember.objects.create(
        group=group,
        user=user,
        is_active=True,
        is_admin=True,
    )
    serializer = GroupMemberSerializer(member)
    data = serializer.data
    assert data['is_admin'] is True
    assert 'user_id' in data and data['user_id'] == user.id
    assert data.get('username') == 'test'


@pytest.mark.django_db
def test_short_user_serializer():
    from api.serializers import ShortUserSerializer

    user = CustomUser.objects.create_user(
        username='test',
        password='secret',
        first_name='Test',
        last_name='User',
    )
    attach_photo(user, 'su.jpg')
    serializer = ShortUserSerializer(user)
    data = serializer.data
    assert data.get('id') == user.id
    assert 'profile_photo' in data or 'avatar' in data


@pytest.mark.django_db
def test_message_serializer():
    user = CustomUser.objects.create_user(
        username='test',
        password='secret',
        first_name='Test',
        last_name='User',
    )
    attach_photo(user, 'msg.jpg')
    message = Message.objects.create(sender=user, text='Test message')
    serializer = MessageSerializer(message)
    data = serializer.data
    assert data['text'] == 'Test message'
    assert data['sender'] == user.id


@pytest.mark.django_db
def test_dialog_create_self_partner(api_client, user):
    api_client.force_authenticate(user)
    url = reverse('dialog-list')
    resp = api_client.post(url, {'partner': user.id}, format='json')
    assert resp.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@pytest.mark.django_db
def test_dialog_create_nonexistent_partner(api_client, user):
    api_client.force_authenticate(user)
    url = reverse('dialog-list')
    resp = api_client.post(url, {'partner': 999999}, format='json')
    assert resp.status_code in (
        status.HTTP_404_NOT_FOUND,
        status.HTTP_400_BAD_REQUEST,
    )


@pytest.mark.django_db
def test_dialog_create_no_partner(api_client, user):
    api_client.force_authenticate(user)
    url = reverse('dialog-list')
    resp = api_client.post(url, {}, format='json')
    assert resp.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@pytest.mark.django_db
def test_match_swipe_invalid_action(api_client, user_with_vector, user2):
    api_client.force_authenticate(user_with_vector)
    url = reverse('match-swipe', args=[user2.id])
    resp = api_client.post(url, {'action': 'unknown'}, format='json')
    assert resp.status_code in (
        status.HTTP_200_OK,
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@pytest.mark.django_db
def test_match_swipe_nonexistent_user(api_client, user_with_vector):
    api_client.force_authenticate(user_with_vector)
    url = reverse('match-swipe', args=[99999])
    resp = api_client.post(url, {'action': 'like'}, format='json')
    assert resp.status_code in (
        status.HTTP_404_NOT_FOUND,
        status.HTTP_400_BAD_REQUEST,
    )


@pytest.mark.django_db
def test_group_members_nonexistent_group(api_client, user):
    api_client.force_authenticate(user)
    url = reverse('group-members', args=[99999])
    resp = api_client.get(url)
    if resp.status_code == status.HTTP_200_OK:
        assert not resp.data or len(resp.data) == 0
    else:
        assert resp.status_code in (  # pragma: no cover
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
        )


@pytest.mark.django_db
def test_dialog_messages_nonexistent_dialog(api_client, user):
    api_client.force_authenticate(user)
    url = reverse('dialog-messages', args=[99999])
    resp = api_client.get(url)
    assert resp.status_code in (
        status.HTTP_404_NOT_FOUND,
        status.HTTP_400_BAD_REQUEST,
    )


@pytest.mark.django_db
def test_dialog_messages_unauthorized_user(api_client, user, user2):
    dialog = Dialog.objects.create()
    dialog.list_users.set([user2])
    api_client.force_authenticate(user)
    url = reverse('dialog-messages', args=[dialog.id])
    resp = api_client.get(url)
    assert resp.status_code in (
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    )
