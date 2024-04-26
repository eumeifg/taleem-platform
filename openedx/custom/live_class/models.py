"""
Models used to store live classes.
"""


import logging
import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from model_utils.models import TimeStampedModel
from tinymce.models import HTMLField

from openedx.core.djangoapps.user_authn.utils import generate_password
from openedx.custom.payment_gateway.models import Voucher
from openedx.custom.taleem.models import Ta3leemUserProfile, UserType
from openedx.custom.taleem.utils import user_is_teacher
from openedx.custom.utils import utc_datetime_to_local_datetime

log = logging.getLogger(__name__)


class LiveClass(TimeStampedModel):
    """
    A django model storing live classes.

    .. no_pii:
    """
    SCHEDULED = 'sd'
    RUNNING = 'rg'
    ENDED = 'ed'
    UNDER_REVIEW = 'ur'
    DECLINED = 'de'

    MEETING_STAGES = (
        (UNDER_REVIEW, _('Under Review')),
        (DECLINED, _('Declined')),
        (SCHEDULED, _('Scheduled')),
        (RUNNING, _('Running')),
        (ENDED, _('Ended')),
    )

    PRIVATE = 'pr'
    PUBLIC_AT_INSTITUTION = 'pi'
    PUBLIC = 'pu'

    CLASS_TYPE = (
        (PRIVATE, _('Private')),
        (PUBLIC_AT_INSTITUTION, _('Public at Institution Level')),
        (PUBLIC, _('Public'))
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
        editable=False)
    name = models.CharField(_("Name"), max_length=255)
    description = HTMLField(_("Description"), null=True)
    poster = models.ImageField(_("Poster"), upload_to='live_classes', null=True, blank=True)
    scheduled_on = models.DateTimeField(_("Scheduled On"))
    duration = models.PositiveSmallIntegerField(_("Duration"), default=60)
    seats = models.PositiveSmallIntegerField(_("Seats"), default=150)
    price = models.PositiveSmallIntegerField(_("Price"), default=0)
    moderator = models.ForeignKey(
        Ta3leemUserProfile,
        limit_choices_to=Q(user_type=UserType.teacher.name)
        | Q(user__is_staff=True)
        | Q(user__is_superuser=True),
        on_delete=models.CASCADE,
        related_name='live_classes',
    )
    meeting_password = models.CharField(max_length=255,
        default=generate_password)
    stage = models.CharField(
        max_length=2,
        db_index=True,
        choices=MEETING_STAGES,
        default=UNDER_REVIEW
    )
    class_type = models.CharField(
        _("Class Type"),
        max_length=2,
        choices=CLASS_TYPE,
        default=PUBLIC
    )

    @property
    def display_name(self):
        return self.name

    @property
    def display_time(self):
        return utc_datetime_to_local_datetime(
            self.scheduled_on).strftime('%b %d, %Y %I:%M %p')

    @property
    def editable(self):
        right_now = timezone.now()
        return right_now < self.scheduled_on

    @property
    def running(self):
        return self.stage == LiveClass.RUNNING

    @property
    def upcoming(self):
        right_now = timezone.now()
        scheduled_duration = self.scheduled_on + timedelta(minutes=self.duration)
        return scheduled_duration > right_now

    @property
    def is_paid(self):
        return self.price > 0

    @property
    def seats_left(self):
        return self.seats - self.bookings.count()

    def has_booked(self, user):
        if user_is_teacher(user):
            return user == self.moderator.user
        return self.bookings.filter(user=user).exists()

    @classmethod
    def upcoming_classes(cls):
        right_now = timezone.now()
        return cls.objects.filter(
            scheduled_on__gt=right_now
        )

    def is_fully_paid(self, user):
        qs = LiveClassPaymentHistory.objects.filter(live_class=self, user=user)
        class_amount_paid = qs.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        return class_amount_paid >= self.price

    def remaining_amount(self, user):
        qs = LiveClassPaymentHistory.objects.filter(live_class=self, user=user)
        class_amount_paid = qs.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        return self.price - class_amount_paid

    def can_join(self, user):
        # coach/student both can join if meeting is running
        if self.stage == LiveClass.RUNNING:
            return True
        if self.moderator.user == user and self.stage != LiveClass.ENDED:
            minutes = (timezone.now() - self.scheduled_on).total_seconds() / 60.0
            # Teacher can start 15 minutes early and 60 minutes late
            earliest_possible = -15
            latest_possible = 60 if self.duration > 60 else self.duration
            return earliest_possible <= minutes <= latest_possible
        # student can not start meeting
        return False

    def get_bookings(self):
        return LiveClassBooking.objects.filter(live_class=self)

    class Meta:
        app_label = 'live_class'
        verbose_name = "Live Class"
        verbose_name_plural = "Live Classes"
        ordering = ('-scheduled_on',)

    def __str__(self):
        return self.name


class LiveClassBooking(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bookings"
    )
    live_class = models.ForeignKey(
        LiveClass,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    @classmethod
    def get_bookings(cls, user):
        return cls.objects.filter(
            user=user,
        ).select_related('live_class')

    class Meta:
        app_label = 'live_class'
        verbose_name = 'Live Class Booking'
        verbose_name_plural = 'Live Class Bookings'
        unique_together = (('user', 'live_class'), )

    def __unicode__(self):
        return str(self.id)


class LiveClassAttendance(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="class_attendance"
    )
    live_class = models.ForeignKey(
        LiveClass,
        on_delete=models.CASCADE,
        related_name="attendances"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True)

    class Meta:
        app_label = 'live_class'
        verbose_name = "Live Class Attendance"
        verbose_name_plural = "Live Class Attendances"


    @property
    def duration_string(self):
        time_string = ""
        if self.joined_at and self.left_at:
            difference = self.left_at - self.joined_at
            difference_in_seconds = difference.total_seconds()
            difference_in_mins = difference_in_seconds // 60
            difference_in_hours = difference_in_mins // 60

            if difference_in_hours > 0:
                time_string += "{hours} ".format(hours=int(difference_in_hours))
                time_string += ugettext("hours")
                time_string += " "
                difference_in_mins = difference_in_mins - (difference_in_hours * 60)

            if difference_in_mins > 0:
                time_string += "{mins} ".format(mins=int(difference_in_mins))
                time_string += ugettext("minutes")
            else:
                time_string += "0 "
                time_string += ugettext("minute")
        else:
            time_string = ugettext("Missing Attendance")

        return time_string


class LiveClassPaymentHistory(TimeStampedModel):
    live_class = models.ForeignKey(
        LiveClass,
        on_delete=models.SET_NULL,
        related_name="payment_history",
        null=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="live_class_payment",
        null=True
    )
    amount = models.DecimalField(
        _('Amount Paid'),
        decimal_places=2,
        max_digits=12,
        default=Decimal('0.00'),
    )
    voucher = models.ForeignKey(
        Voucher, related_name="voucher_usages_for_live_class", on_delete=models.SET_NULL, null=True
    )

    class Meta:
        """
        Provide human friendly verbose name.
        """
        app_label = 'live_class'
        verbose_name = 'Live Class Payment History'
        verbose_name_plural = 'Live Class Payment Histories'
