"""
URLs for the timed notes app.
"""


from django.conf.urls import url

from . import views

app_name = 'video_feedback'

urlpatterns = [
    url(r'^rate/', views.rate_video, name='rate_video'),
    url(r'^like/', views.like_video, name='like_video'),
    url(r'^fetch/', views.get_feedback, name='get_feedback'),
]
