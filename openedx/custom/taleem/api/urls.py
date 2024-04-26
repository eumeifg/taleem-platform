from django.conf.urls import url
from django.urls import path

from openedx.custom.taleem.api import views


urlpatterns = [
    url(
        r"^re-send-activation-email/$",
        views.re_send_activation_email,
        name="re_send_activation_email",
    ),
    path("social_signin/", views.SocialSignIn.as_view(), name="social_signin_api"),
    path(
        "mobile/app/version/",
        views.mobile_app_version,
        name="mobile_app_version",
    ),
]
