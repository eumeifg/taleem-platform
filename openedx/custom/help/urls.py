"""
URLs for the timed exam app.
"""

from django.conf.urls import url

from openedx.custom.help import views

app_name = 'help'

urlpatterns = [
    url(r'^', views.help_page, name='help_page'),
]
