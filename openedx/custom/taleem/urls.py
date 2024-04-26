"""
URLs for the timed exam app.
"""

from django.conf.urls import url
from django.conf import settings

from openedx.custom.taleem import views

app_name = 'taleem'

urlpatterns = [
    url(r'^course-rating/{}'.format(settings.COURSE_ID_PATTERN), views.course_rating, name='course_rating'),
    url(r'^dashboard-reports', views.dashboard_reports, name='dashboard_reports'),
    url(r'^update-ip-address-session', views.update_ip_address_session, name='update_ip_address_session'),
    url(r'^captcha-verification', views.taleem_captcha, name='taleem_captcha'),
    url(r'^set-ip-address', views.set_ip_address_with_redirect, name='set_ip_address_with_redirect'),
    url(r'^allow_entrance', views.taleem_allow_entrance, name='taleem_allow_entrance'),
    url(r'^send-email/(?P<user_id>\w+)$', views.send_email, name='send_email'),
    url(r'^apply_for_teacher', views.apply_for_teacher_account, name='apply_for_teacher_account'),
    url(r'^teacher_account_requests/$', views.teacher_account_request, name='teacher_account_requests'),
    url(r'^teacher_account_request_state_change/(?P<request_id>[0-9-]+)/(?P<state>[a-z-]+)', views.teacher_account_request_state_change,
        name='teacher_account_request_state_change'),
    url(r'^get_teachers', views.get_teachers, name='get_list_of_teachers'),
    url(r'^download/mobile/app/', views.download_app, name='download_app'),
]
