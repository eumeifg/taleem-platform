from django.conf.urls import url
from django.conf import settings

from . import views


urlpatterns = [
    url(r'^get_h5p_extraction_status/{}$'.format(settings.USAGE_KEY_PATTERN),views.get_h5p_extraction_status,
        name='get_h5p_extraction_status'),
]
