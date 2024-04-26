"""
URLs for the timed notes app.
"""


from django.urls import path
from django.conf.urls import url
from django.conf import settings

from . import views
from .course_notifications import CourseNotificationsView
from .announcements import AnnouncementView

app_name = 'notifications'

urlpatterns = [
    url(
        r'^{}/tools/'.format(
            settings.COURSE_ID_PATTERN,
        ),
        CourseNotificationsView.as_view(),
        name='course_notifications'
    ),
    url(
        r'^announcement/',
        AnnouncementView.as_view(),
        name='announcement'
    ),
    path(r'list/', views.list_messages, name='list_messages'),
    path(r'mark/as/read/<int:id>/', views.mark_as_read, name='mark_as_read'),
    path(r'mark/as/read/', views.mark_all_as_read, name='mark_all_as_read'),
    path(r'delete/<int:id>/', views.delete, name='delete'),
    path(r'delete/', views.delete_all, name='delete_all'),
    path(r'autocomplete/users/', views.autocomplete_users, name='autocomplete_users'),
    path(r'list-messages-in-json/', views.list_messages_in_json, name='list_messages_in_json'),
    path(r'timed_exam_alarms/', views.timed_exam_alarms, name='timed_exam_alarms'),
    path('preferences/', views.notification_preferences, name='notification_preferences'),
]
