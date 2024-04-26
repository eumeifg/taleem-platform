"""
URLs for the reports.
"""

from django.conf.urls import url

from openedx.custom.user_reports import views

app_name = 'reports'

urlpatterns = [
    url(r'^$', views.reports, name='reports'),
]
