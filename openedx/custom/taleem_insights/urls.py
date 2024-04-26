"""
URLs for the taleem insights.
"""

from django.conf.urls import url

from openedx.custom.taleem_insights import views

app_name = 'taleem_insights'

urlpatterns = [
    url(r'^$', views.insights, name='insights'),
]
