from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^permission/(?P<edx_video_id>[-\w]+)',
        views.VideoPermissionView.as_view(),
        name='video_permission'
    ),
]
