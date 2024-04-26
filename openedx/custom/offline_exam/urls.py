"""
URLs for the timed exam app.
"""

from django.conf.urls import url
from django.conf import settings

from openedx.custom.offline_exam import views

app_name = 'offline_exam'

urlpatterns = [
    url(
        r'^{}/attempt/status/'.format(settings.COURSE_ID_PATTERN,),
        views.attempt_status,
        name='attempt_status',
    ),
    url(
        r'^{}/'.format(settings.COURSE_ID_PATTERN,),
        views.enter_exam,
        name='enter_exam',
    ),
]
