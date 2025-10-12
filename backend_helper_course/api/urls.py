from rest_framework.routers import DefaultRouter

from .views import (
    DialogViewSet,
    FeedbackViewSet,
    GroupViewSet,
    HelloViewSet,
    InteractionsViewSet,
    MatchViewSet,
    ProfileViewSet,
)

router = DefaultRouter()
router.register(r'hello', HelloViewSet, basename='hello')
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'groups', GroupViewSet, basename='groups')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'dialogs', DialogViewSet, basename='dialogs')
router.register(r'matches', MatchViewSet, basename='matches')
router.register(r'interactions', InteractionsViewSet, basename='interactions')
urlpatterns = router.urls
