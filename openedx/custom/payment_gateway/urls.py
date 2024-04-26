"""
URLs for the timed exam app.
"""

from django.conf.urls import url
from django.conf import settings

from openedx.custom.payment_gateway import views

app_name = 'payment_gateway'

urlpatterns = [
    url(r'^vouchers/{}'.format(settings.COURSE_ID_PATTERN), views.vouchers, name='vouchers_page'),
]
