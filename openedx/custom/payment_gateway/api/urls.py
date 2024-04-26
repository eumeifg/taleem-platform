from django.urls import path
from . import views

urlpatterns = [
    path("v1/balance/", views.VoucherBalanceView.as_view(), name="voucher_balance"),
    path("v1/redeem/", views.VoucherRedeemView.as_view(), name="voucher_redeem"),
]
