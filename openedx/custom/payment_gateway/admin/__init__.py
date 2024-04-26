"""
Django admin page for payment gateway management, to enable or
disable various features related to payment.
"""
from django.conf.urls import url
from django.contrib import admin
from djangoql.admin import DjangoQLSearchMixin
from rangefilter.filters import DateTimeRangeFilter
from import_export.admin import ExportActionModelAdmin

from openedx.custom.payment_gateway.admin.utils import UrlNames
from openedx.custom.payment_gateway.admin.views import BulkAddVouchersView
from openedx.custom.payment_gateway.models import (
    CoursePrice, IpAddressWhitelist, Voucher, VoucherUsage,
)
from openedx.custom.payment_gateway.utils import get_voucher_code
from .resources import VoucherResource, VoucherUsageResource

class ReadOnlyAdmin(admin.ModelAdmin):
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + \
               [field.name for field in obj._meta.fields] + \
               [field.name for field in obj._meta.many_to_many]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(IpAddressWhitelist)
class IpAddressWhitelistAdmin(admin.ModelAdmin):
    """
    Simple, admin page to add or remove ip addresses from whitelist.
    """
    list_display = ('id', 'ip_address', 'type', 'mask', 'created', 'modified', )
    search_fields = ('id', 'ip_address', )


@admin.register(CoursePrice)
class CoursePriceAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage course prices.
    """
    list_display = ('id', 'course_key', 'price', 'currency_in_uppercase', 'created', 'modified', )
    search_fields = ('id', 'course_key', 'price', )
    fields = ('course_key', 'price', )

    @staticmethod
    def currency_in_uppercase(obj):
        """
        Convert currency  code to upper case.
        """
        return obj.currency.upper()


@admin.register(Voucher)
class VoucherAdmin(ExportActionModelAdmin):
    """
    Simple, admin page to manage course prices.
    """
    list_display = ('id', 'voucher_name', 'voucher_code', 'total_discount', 'used_amount', 'remaining_amount', 'created', 'modified', )
    search_fields = ('id', 'name', 'code', )
    fields = ('name', 'discount', )
    resource_class = VoucherResource

    @staticmethod
    def voucher_name(obj):
        """
        Voucher name
        """
        return obj.name

    @staticmethod
    def voucher_code(obj):
        """
        voucher code
        """
        return obj.code

    @staticmethod
    def total_discount(obj):
        """
        Convert currency  code to upper case.
        """
        return "{discount} {currency}".format(discount=obj.discount, currency=obj.currency.upper())

    @staticmethod
    def used_amount(obj):
        """
        Convert currency  code to upper case.
        """
        return "{amount} {currency}".format(amount=obj.discount - obj.remaining_amount, currency=obj.currency.upper())

    @staticmethod
    def remaining_amount(obj):
        """
        Convert currency  code to upper case.
        """
        return "{amount} {currency}".format(amount=obj.remaining_amount, currency=obj.currency.upper())

    def save_model(self, request, obj, form, change):
        if not change:
            obj.code = get_voucher_code()

        super().save_model(request, obj, form, change)

    def get_urls(self):
        """
        Returns the additional urls used by the custom object tools.
        """
        customer_urls = [
            url(
                r"^add-in-bulk$",
                self.admin_site.admin_view(BulkAddVouchersView.as_view()),
                name=UrlNames.ADD_VOUCHERS
            ),
        ]
        return customer_urls + super().get_urls()


@admin.register(VoucherUsage)
class VoucherUsageAdmin(DjangoQLSearchMixin, ExportActionModelAdmin):
    """
    Simple, admin page to manage voucher usages.
    """
    autocomplete_fields = ('voucher', 'course', 'user', 'enrollment', )
    list_display = ('id', 'get_user_full_name', 'get_user_email', 'course', 'get_voucher_name',
                    'get_voucher_id', 'amount_used', 'get_voucher_total_price', 'get_voucher_remaining_price',
                    'get_voucher_code', 'created')
    list_filter = (("created", DateTimeRangeFilter),)
    resource_class = VoucherUsageResource

    def get_voucher_name(self, obj):
        return obj.voucher.name

    def get_voucher_id(self, obj):
        return obj.voucher.id

    def get_voucher_code(self, obj):
        return obj.voucher.code

    def get_user_full_name(self, obj):
        return obj.user.profile.name

    def get_user_email(self, obj):
        return obj.user.email

    def get_voucher_total_price(self, obj):
        return obj.voucher.discount

    def get_voucher_remaining_price(self, obj):
        return obj.voucher.remaining_amount

    get_voucher_code.admin_order_field = get_voucher_id.admin_order_field = 'voucher'
    get_voucher_name.admin_order_field = get_voucher_total_price.admin_order_field = 'voucher'
    get_voucher_remaining_price.admin_order_field = 'voucher'
    get_user_email.admin_order_field = get_user_full_name.admin_order_field = 'user'
    get_voucher_name.short_description = 'Voucher Name'
    get_voucher_id.short_description = 'Voucher ID'
    get_voucher_code.short_description = 'Voucher Code'
    get_user_full_name.short_description = 'User Fullname'
    get_user_email.short_description = 'User Email'
    get_voucher_total_price.short_description = 'Voucher Total Amount'
    get_voucher_remaining_price.short_description = 'Voucher Remaining Balance'
