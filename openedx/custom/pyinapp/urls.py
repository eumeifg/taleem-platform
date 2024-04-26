from django.urls import path
from . import views

urlpatterns = [
    path(
        "verify/",
        views.VerifyReceiptView.as_view(),
        name="verify_receipt"
    ),
    path(
        "location/",
        views.UserLocationView.as_view(),
        name="log_user_location"
    )
]
