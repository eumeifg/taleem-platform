"""
URLs for the timed notes app.
"""


from django.conf.urls import url

from openedx.custom.verification import views

app_name = 'verification'

urlpatterns = [
    url(r'verify', views.PayAndVerifyView.as_view(), name="verify_student_identification"),
    url(r'handle-photos', views.HandlePhotosView.as_view(), name="handle_student_submit_photos"),
    url(r'already_verified', views.already_verified, name="already_verified"),
    url(r'requests/(?P<user_type>[A-z]+)/$', views.get_verifications_view, name='verification_requests_view'),
    url(r'status_change/', views.change_verification_status, name='change_verification_status_view'),
]
