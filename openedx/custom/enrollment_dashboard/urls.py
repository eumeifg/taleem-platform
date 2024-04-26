"""
URLs for the timed notes app.
"""


from django.conf.urls import url

from openedx.custom.enrollment_dashboard import views

app_name = 'enrollment_dashboard'

urlpatterns = [
    url(r'', views.enrollment_dashboard_view, name='enrollment_dashboard'),
]
