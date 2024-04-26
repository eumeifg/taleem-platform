"""
Models for payment gateway.
"""
from enum import Enum
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.db.models import Sum
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from edx_django_utils.cache import TieredCache, get_cache_key

from netaddr import IPNetwork, IPAddress
from model_utils.models import TimeStampedModel
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.django.models import CourseKeyField

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment


User = get_user_model()


class IPAddressType(Enum):
    """
    User Types
    """
    single_ip = _(u'Single IP Address')
    subnet = _(u'Subnet')

    @classmethod
    def choices(cls):
        choices = list((i.name, i.value) for i in cls)
        return choices


class IpAddressWhitelist(TimeStampedModel):
    """
    Model for whitelisting ipaddress.

    This gives certain ip addresses access to courses without having them to buy anything.
    """
    ip_address = models.GenericIPAddressField()
    type = models.CharField(choices=IPAddressType.choices(), max_length=25, default=IPAddressType.single_ip.name)
    mask = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(32)
        ],
        default=0,
    )

    def clean(self):
        """
        Validate that mask is not zero if type is subnet.
        """
        if self.type == IPAddressType.subnet.name and self.mask == 0:
            raise ValidationError(_('Mask set with a non-zero value when type is subnet.'))

    class Meta:
        """
        Provide human friendly verbose name.
        """
        verbose_name = 'IP Address Whitelist'
        verbose_name_plural = 'IP Address Whitelist'

    def __str__(self):
        """
        Human readable string representation.
        """
        return '<IpAddressWhitelist id="{self.id}" ip="{self.ip_address}">'.format(self=self)

    def __repr__(self):
        """
        Human readable string representation.
        """
        return '<IpAddressWhitelist id="{self.id}" ip_address="{self.ip_address}">'.format(self=self)

    @classmethod
    def is_ip_in_whitelist(cls, ip_address):
        """
        Check if given ip_address is present in the whitelist or not.

        Arguments:
            ip_address (str): ip address to check for existence in the whitelist.

        Returns:
            (bool): True if given ip address is in the whitelist, False otherwise
        """
        # cache will expire after 300 seconds
        cache_timeout = 300
        cache_key = get_cache_key(name='is_ip_in_whitelist', ip_address=ip_address)
        cache_item = TieredCache.get_cached_response(cache_key)
        if cache_item.is_found:
            return cache_item.value

        if cls.objects.filter(ip_address=ip_address, type=IPAddressType.single_ip.name).exists():
            TieredCache.set_all_tiers(key=cache_key, value=True, django_cache_timeout=cache_timeout)
            return True

        ip_address = IPAddress(ip_address)
        for subnet in cls.objects.filter(type=IPAddressType.subnet.name):
            if ip_address in IPNetwork('{}/{}'.format(subnet.ip_address, subnet.mask)):
                TieredCache.set_all_tiers(key=cache_key, value=True, django_cache_timeout=cache_timeout)
                return True

        return False


class CoursePrice(TimeStampedModel):
    """
    Model for whitelisting ipaddress.

    This gives certain ip addresses access to courses without having them to buy anything.
    """
    course_key = CourseKeyField(db_index=True, unique=True, max_length=255)

    price = models.DecimalField(
        _('Course Price'),
        decimal_places=2,
        max_digits=12,
        default=Decimal('0.00'),
    )

    # the currency these prices are in, using lower case ISO currency codes
    # Default currency is Iraqi dinar with ISO code `IQD`.
    currency = models.CharField(default=u'iqd', max_length=8)

    class Meta:
        """
        Provide human friendly verbose name.
        """
        verbose_name = 'Course Price'
        verbose_name_plural = 'Course Prices'

    def __str__(self):
        """
        Human readable string representation.
        """
        return '<CoursePrice id="{self.id}" course="{self.course_key}" price="{self.price} {currency}">'.format(
            self=self,
            currency=self.currency.upper()
        )

    def __repr__(self):
        """
        Human readable string representation.
        """
        return '<CoursePrice id="{self.id}" course_key="{self.course_key}" price="{self.price} {currency}">'.format(
            self=self,
            currency=self.currency.upper()
        )

    @classmethod
    def get_course_price(cls, course_id):
        """
        Check if given ip_address is present in the whitelist or not.

        Arguments:
            course_id (str | CourseKeyField): course id whose price need to be fetched.

        Raises:
            (CoursePrice.DoesNotExist): Raised if course price object is not found for the given course id.

        Returns:
            (CoursePrice): CoursePrice object for the given course id.
        """
        if not isinstance(course_id, CourseKey):
            course_id = CourseKey.from_string(course_id)

        return cls.objects.get(course_key=course_id)

    def get_course_price_for_user(self, user):
        """
        Get the remaining price user needs to pay to access the course.

        Arguments:
            user (User): User instance who is trying to chek price of the course.
        Returns:
            (Decimal): Price of the course subtracting the voucher prices that user has already applied.
        """
        qs = VoucherUsage.objects.filter(course__id=self.course_key, user=user)
        discount_used = qs.aggregate(Sum('amount_used'))['amount_used__sum'] or Decimal('0.00')
        return self.price - discount_used


class Voucher(TimeStampedModel):
    """
    Model for storing information related to vouchers and discounts.
    """
    name = models.CharField(
        _("Name"),
        max_length=128,
    )
    code = models.CharField(
        _("Code"),
        max_length=128,
        db_index=True,
        unique=True,
        help_text=_("Case insensitive / No spaces allowed"),
    )
    discount = models.DecimalField(
        _("Total discount"),
        decimal_places=2,
        max_digits=12,
        default=Decimal('0.00'),
    )
    # the currency these prices are in, using lower case ISO currency codes
    # Default currency is Iraqi dinar with ISO code `IQD`.
    currency = models.CharField(default=u'iqd', max_length=8)

    class Meta:
        """
        Provide human friendly verbose name.
        """
        verbose_name = 'Voucher'
        verbose_name_plural = 'Vouchers'

    def __str__(self):
        """
        Human readable string representation.
        """
        return '<Voucher id="{self.id}" code="{self.code}" discount="{self.discount} {currency}">'.format(
            self=self,
            currency=self.currency.upper()
        )

    def __repr__(self):
        """
        Human readable string representation.
        """
        return '<Voucher id="{self.id}" code="{self.code}" discount="{self.discount} {currency}">'.format(
            self=self,
            currency=self.currency.upper()
        )

    @property
    def remaining_amount(self):
        """
        Get the remaining amount left in the voucher.

        Returns:
            (Decimal): Remaining amount left in the voucher.
        """
        used_amount = self.voucher_usages.aggregate(Sum('amount_used'))['amount_used__sum'] or Decimal('0.00')
        return self.discount - used_amount

    def has_discount(self):
        """
        Check if the voucher has any discount left.

        Returns:
            (bool): True if there is discount left for use, `False` otherwise.
        """
        return self.remaining_amount > 0

    def add_usage(self, course_overview, user, course_price):
        """
        Add a new voucher usage.

        Arguments:
           course_overview (CourseOverview): The course that is being discounted.
           user (User): The user getting the discount.
           course_price (CoursePrice): The course price object for the course being discounted.
        """
        course_price = course_price.get_course_price_for_user(user)

        if course_price >= self.remaining_amount:  # Use all the remaining discount from the voucher
            amount_used = self.remaining_amount
        else:
            # use the course price as discount amount, since there is enough discount in the voucher for this course
            amount_used = course_price

        return VoucherUsage.objects.create(
            voucher=self,
            course=course_overview,
            user=user,
            amount_used=amount_used,
        )

    def add_usage_price(self, user, price):
        """
        Add a new voucher usage.

        Arguments:
           user (User): The user getting the discount.
           price (Decimal): The price for being discounted.
        """

        if price >= self.remaining_amount:  # Use all the remaining discount from the voucher
            amount_used = self.remaining_amount
        else:
            amount_used = price

        VoucherUsage.objects.create(
            voucher=self,
            user=user,
            amount_used=amount_used,
        )

        return amount_used


class VoucherUsage(TimeStampedModel):
    """
    Model for recording the usage/usages of the voucher.
    """
    voucher = models.ForeignKey(
        Voucher, related_name="voucher_usages", on_delete=models.DO_NOTHING,
    )
    course = models.ForeignKey(
        CourseOverview, related_name="voucher_usages", on_delete=models.SET_NULL, null=True, default=None
    )
    user = models.ForeignKey(
        User, related_name="voucher_usages", on_delete=models.DO_NOTHING,
    )
    enrollment = models.ForeignKey(
        CourseEnrollment, related_name="voucher_usages", on_delete=models.SET_NULL, null=True, default=None
    )
    amount_used = models.DecimalField(
        _("Amount Used"),
        decimal_places=2,
        max_digits=12,
        default=Decimal('0.00'),
    )
    # the currency these prices are in, using lower case ISO currency codes
    # Default currency is Iraqi dinar with ISO code `IQD`.
    currency = models.CharField(default=u'iqd', max_length=8)

    class Meta:
        """
        Provide human friendly verbose name.
        """
        verbose_name = 'Voucher Usage'
        verbose_name_plural = 'Voucher Usages'

    def __str__(self):
        """
        Human readable string representation.
        """
        return '<VoucherUsage id="{self.id}" voucher="{self.voucher.code}" user="{self.user.username} ' \
               'course="{self.course.id}">'.format(self=self)

    def __repr__(self):
        """
        Human readable string representation.
        """
        return '<VoucherUsage id="{self.id}" voucher="{self.voucher!r}" user="{self.user!r}" course="{self.course!r}">'.format(self=self)
