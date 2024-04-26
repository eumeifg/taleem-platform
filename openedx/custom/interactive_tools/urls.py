"""
URLs for the interactive tools of any course.
"""

from django.conf import settings
from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^{}/report/'.format(settings.COURSE_ID_PATTERN),
        views.interactive_tools_report,
        name='interactive_tools_report'
    ),
    url(
        r'^{}/'.format(settings.COURSE_ID_PATTERN),
        views.interactive_tools_list,
        name='interactive_tools_list'
    ),
]
