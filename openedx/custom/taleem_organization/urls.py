"""
URLs for the taleem organization app.
"""

from django.conf.urls import url

from openedx.custom.taleem_organization import views

app_name = 'taleem_organization'

urlpatterns = [
    url(
        r'organization_type/(?P<organization>([^/]*))/', views.get_organization_type, name="get_organization_type_view"
    ),
    url(
        r'colleges/(?P<university>([^/]*))/', views.get_colleges, name='get_colleges_view'
    ),
    url(
        r'departments/(?P<university>([^/]*))/(?P<college>([^/]*))', views.get_departments, name='get_departments_view'
    ),
    url(
        r'csv-samples/(?P<sample_source>({})).csv'.format(r'|'.join(views.ALLOWED_SOURCES)), views.csv_samples,
        name='csv_samples',
    ),
    url(r'tashgeel-login/(?P<token_uuid>[0-9a-f-]+)/', views.tashgeel_user_login, name='tashgeel_user_login'),
]
