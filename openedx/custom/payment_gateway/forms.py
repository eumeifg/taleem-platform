"""
Forms for payment gateway app.
"""
from django import forms
from django.utils.translation import ugettext_lazy as _

from openedx.custom.payment_gateway.models import Voucher
from openedx.custom.live_class.models import LiveClassPaymentHistory


def validate_voucher(value):
    """
    Validate that voucher exist and has discount available.
    """
    # Voucher codes are case-insensitive
    value = value.upper()

    voucher = Voucher.objects.filter(code=value).first()
    if voucher is None:
        raise forms.ValidationError(
            _('Voucher with given code does not exist, please make sure you are adding the correct code.')
        )

    if not voucher.has_discount():
        raise forms.ValidationError(
            _('Given voucher is already redeemed and does not have any discount left. Please use a new voucher.')
        )


class VoucherRedemptionForm(forms.Form):
    """
    voucher redemption form.
    """
    __voucher_extra__ = {}
    code = forms.CharField(max_length=128, required=True, validators=[validate_voucher])

    def clean(self):
        cleaned_data = super().clean()
        code = cleaned_data.get('code')

        if code:
            code = code.upper()
            voucher = Voucher.objects.filter(code=code).first()
            # Caching voucher to reduce db queries.
            cleaned_data['voucher'] = voucher

        return cleaned_data

    def save(self, course_overview, user, course_price):
        """
        Perform the save operation on the form.

        Arguments:
           course_overview (CourseOverview): The course that is being discounted.
           user (User): The user getting the discount.
           course_price (CoursePrice): The course price object for the course being discounted.
        """
        voucher = self.cleaned_data['voucher']
        voucher.add_usage(
            course_overview=course_overview,
            user=user,
            course_price=course_price,
        )

    @property
    def errors(self):
        """
        Return error messages as a list.
        """
        errors = []
        for key, value in super().errors.items():
            errors.extend(value)
        return errors


class VoucherRedemptionLiveClassForm(VoucherRedemptionForm):
    """
    Voucher Redemption Form for Live Class.
    """

    def save(self, user, live_class):
        """
        Perform the save operation on the form.

        Arguments:
           user (User): The user getting the discount.
           live_class_price (Decimal): The live class price for the being used.
        """
        voucher = self.cleaned_data['voucher']
        amount_deducted = voucher.add_usage_price(
            user=user,
            price=live_class.price
        )

        if amount_deducted > 0:
            LiveClassPaymentHistory.objects.create(
                live_class=live_class,
                user=user,
                voucher=voucher,
                amount=amount_deducted
            )
