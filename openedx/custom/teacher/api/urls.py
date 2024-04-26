"""
Course API URLs
"""


from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^access/request/$',
        views.AccessRequestView.as_view(),
        name="teacher_access_request"
    ),
]

