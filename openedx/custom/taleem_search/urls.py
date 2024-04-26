from django.conf.urls import url

from openedx.custom.taleem_search import views

urlpatterns = [
    url(r'^filtered_course/$', views.get_filtered_courses, name='filtered_courses'),
    url(r'^filters/(?P<category_id>[0-9]+)/$', views.get_category_filters, name='get_category_filters'),
]
