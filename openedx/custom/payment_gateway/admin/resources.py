"""
Resources for import/export
"""

from import_export import resources
from import_export.fields import Field

from openedx.custom.payment_gateway.models import Voucher, VoucherUsage


class VoucherResource(resources.ModelResource):
    voucher_name = Field(attribute='name', column_name='Voucher Name')
    voucher_code = Field(attribute='code', column_name='Voucher Code')
    total_discount = Field(column_name='Total Discount')
    used_amount = Field(column_name="Used Amount")
    remaining_amount = Field(column_name="Remaining Amount")

    class Meta:
        model = Voucher
        fields = ('id', 'voucher_name', 'voucher_code', 'total_discount',
            'used_amount', 'remaining_amount', 'created', 'modified', )
        export_order = ('id', 'voucher_name', 'voucher_code', 'total_discount',
            'used_amount', 'remaining_amount', 'created', 'modified', )

    def dehydrate_total_discount(self, obj):
        return "{discount} {currency}".format(
            discount=obj.discount,
            currency=obj.currency.upper()
        )

    def dehydrate_used_amount(self, obj):
        return "{amount} {currency}".format(
            amount=obj.discount - obj.remaining_amount,
            currency=obj.currency.upper()
        )

    def dehydrate_remaining_amount(self, obj):
        return "{amount} {currency}".format(
            amount=obj.remaining_amount,
            currency=obj.currency.upper()
        )


class VoucherUsageResource(resources.ModelResource):
    full_name = Field(column_name='User')
    email = Field(column_name='Email')
    course_name = Field(attribute='course__display_name', column_name='Course')
    voucher_id = Field(attribute='voucher__id', column_name='Voucher ID')
    voucher_name = Field(attribute='voucher__name', column_name='Voucher Name')
    voucher_code = Field(attribute='voucher__code', column_name='Voucher Code')
    total_discount = Field(column_name='Total Discount')
    used_amount = Field(column_name="Used Amount")
    remaining_amount = Field(column_name="Remaining Amount")

    class Meta:
        model = VoucherUsage
        fields = ('id', 'full_name', 'email', 'course_name',
            'voucher_id', 'voucher_name', 'voucher_code',
            'total_discount', 'used_amount', 'remaining_amount',
            'created', )
        export_order = ('id', 'full_name', 'email', 'course_name',
            'voucher_id', 'voucher_name', 'voucher_code',
            'total_discount', 'used_amount', 'remaining_amount',
            'created', )

    def dehydrate_full_name(self, obj):
        return obj.user.profile.name

    def dehydrate_email(self, obj):
        return obj.user.email

    def dehydrate_total_discount(self, obj):
        return obj.voucher.discount

    def dehydrate_used_amount(self, obj):
        return obj.voucher.discount - obj.voucher.remaining_amount

    def dehydrate_remaining_amount(self, obj):
        return obj.voucher.remaining_amount
