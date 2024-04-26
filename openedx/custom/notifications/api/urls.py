"""
URLs for notification API
"""

from rest_framework import routers
from django.conf.urls import include, url

from .views import (
    NotificationsListView,
    HasCourseNotifications,
    FCMDeviceCreateOnlyViewSet,
    MutePostView,
    NotificationPreferenceView,
)

router = routers.DefaultRouter()
router.register(r'subscribe', FCMDeviceCreateOnlyViewSet, basename='subscribe_push')

urlpatterns = [
    url('^v1/notifications/$',
        NotificationsListView.as_view(),
        name='notifications'
    ),
    url(
        '^v1/courses/has_notifications/$',
        HasCourseNotifications.as_view(),
        name='has_course_notifications'
    ),
    url('^v1/mute/post/$',
        MutePostView.as_view(),
        name='mute_post'
    ),
    url('^v1/preferences/$',
        NotificationPreferenceView.as_view(),
        name='api_notification_preferences'
    ),
    url('^v1/', include(router.urls)),
]
