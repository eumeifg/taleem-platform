"""
URLs for the taleem calendar app.
"""

from django.conf.urls import url

from openedx.custom.taleem_calendar import views

app_name = 'taleem_calendar'

urlpatterns = [
    url(r'^get_all_calendar_events/', views.get_all_calendar_events, name='get_all_calendar_events'),
    url(r'^reminder/create/', views.create_reminder, name='create_reminder'),
    url(r'^event/create/', views.create_event, name='create_event')
]
