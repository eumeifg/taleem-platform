"""
Notifications models.
"""

import logging
import re

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _

from jsonfield import JSONField
from model_utils.models import TimeStampedModel
from config_models.models import ConfigurationModel

log = logging.getLogger(__name__)


# pylint: disable=model-has-unicode
class NotificationMessage(TimeStampedModel, models.Model):
    """
    Store notification message.
    """
    id = models.BigAutoField(primary_key=True)  # pylint: disable=invalid-name
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField(max_length=255)
    resolve_link = models.TextField(max_length=255, null=True, blank=True)
    read = models.BooleanField(default=False)
    course_key = models.CharField(max_length=255, null=True, blank=True)
    notification_id = models.UUIDField(null=True, blank=True)
    data = JSONField(default=dict)

    def mark_as_read(self):
        """
        Mark the given notification as read.
        """
        self.read = True
        self.save()

    @classmethod
    def mark_all_as_read(cls, user):
        """
        Change read status of all the notiications
        for a given user.
        """
        cls.objects.filter(
            user=user,
            read=False,
        ).update(read=True)

    @classmethod
    def get_messages(cls, user, include_read=False):
        """
        Returns the mapping of time and notes taken by a user in the given course and video
        Return message:
            message = <NotificationMessage>
        """
        receive_on = NotificationPreference.BOTH
        if hasattr(user, 'notification_preferences'):
            receive_on = user.notification_preferences.receive_on

        messages = cls.objects.filter(user=user)
        if receive_on not in (NotificationPreference.BOTH,
            NotificationPreference.WEB):
            messages = messages.exclude(title="Discussion")

        if not include_read:
            messages = messages.exclude(read=True)

        return messages.order_by('-modified')

    class Meta:
        index_together = [
            ('user', 'modified'),
        ]

        get_latest_by = 'modified'

    def __unicode__(self):
        return 'NotificationMessage: {username}, {message}: {read}'.format(
            username=self.user.username,
            message=self.message,
            read=self.read,
        )


class MutedPost(models.Model):
    """
    User who opt-out from discussion forum
    post notification messages.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course_id = models.CharField(max_length=255)
    post_id = models.CharField(max_length=255)

    def __unicode__(self):
        return 'MutedPost: {username}, {course_id}, {post_id}'.format(
            username=self.user.username,
            course_id=self.course_id,
            post_id=self.post_id,
        )


def validate_time_string(time):
    minute_choices = ["min", "minutes", "mins", "minute"]
    hour_choices = ["hour", "hours"]
    day_choices = ["day", "days"]
    time_choices = list() + minute_choices + hour_choices + day_choices
    time_split = time.split(' ')

    if len(time_split) < 2 or len(time_split) > 2:
        raise ValidationError(_("Time should be in proper format take a look at field help text."))

    if not time_split[1] in time_choices:
        raise ValidationError(_("Time should be in proper format take a look at field help text."))

    if time_split[1] in minute_choices:
        minutes = int(time_split[0])
        if minutes <= 5:
            raise ValidationError(_("Time should be greater than 5 minutes."))


class EventReminderSettings(ConfigurationModel):
    course_reminder_time = models.CharField(
        max_length=10,
        default="24 hours",
        verbose_name=_("Course Reminder Time"),
        help_text=_(
            "Time to send the email before the course start date, course end date and any "
            "other important date like assignment or quiz or any section due date. Time should be in "
            "format like:  `10 mins` or `2 hours` or `2 days`. You can only set the min, hours and days"
        ),
        validators=[validate_time_string]
    )
    exam_reminder_time = models.CharField(
        max_length=10,
        default="24 hours",
        verbose_name=_("Exam Reminder Time"),
        help_text=_(
            "Time to send the email before the exam start date and exam end date. Time should be "
            "in format like:  `10 mins` or `2 hours` or `2 days`. You can only set the min, hours and days"
        ),
        validators=[validate_time_string]
    )
    live_class_reminder_time = models.CharField(
        max_length=10,
        default="24 hours",
        verbose_name=_("Live Class Reminder Time"),
        help_text=_(
            "Time to send the email before the live class start. Time should be "
            "in format like:  `10 mins` or `2 hours` or `2 days`. You can only set the min, hours and days"
        ),
        validators=[validate_time_string]
    )

    class Meta(ConfigurationModel.Meta):
        app_label = 'notifications'
        verbose_name = _("Auto Notification Configuration")
        verbose_name_plural = _("Auto Notification Configurations")

    def save(self, *args, **kwargs):
        self.course_reminder_time = self.get_proper_time(self.course_reminder_time)
        self.exam_reminder_time = self.get_proper_time(self.exam_reminder_time)
        self.live_class_reminder_time = self.get_proper_time(self.live_class_reminder_time)

        super(EventReminderSettings, self).save(*args, **kwargs)

    @staticmethod
    def get_proper_time(time):
        minute_choices = ["min", "minutes", "mins", "minute"]
        hour_choices = ["hour", "hours"]
        day_choices = ["day", "days"]

        time, offset = time.split(' ')

        if offset in minute_choices:
            offset = "minutes"
        elif offset in hour_choices:
            offset = "hours"
        elif offset in day_choices:
            offset = "days"

        proper_time = "{time} {offset}".format(time=time, offset=offset)
        return proper_time


class NotificationPreference(models.Model):
    """
    User preferences on notification.
    """
    WEB = 'wb'
    MOBILE = 'mb'
    BOTH = 'bt'
    NOWHERE = 'nw'

    RECEIVE_CHOICES = (
        (WEB, 'Web'),
        (MOBILE, 'Mobile'),
        (BOTH, 'Both'),
        (NOWHERE, 'Nowhere'),
    )

    receive_on = models.CharField(
        max_length=2,
        db_index=True,
        choices=RECEIVE_CHOICES,
        default=BOTH
    )
    user = models.OneToOneField(
        User,
        related_name="notification_preferences",
        on_delete=models.CASCADE
    )
    # On which events the user prefer notifications
    added_discussion_post = models.BooleanField(
        _("Notify when students adds new discussion post"),
        default=False
    )
    added_discussion_comment = models.BooleanField(
        _("Notify when students adds new discussion comment"),
        default=False
    )
    asked_question = models.BooleanField(
        _("Notify when students asks question"),
        default=True
    )
    replied_on_question = models.BooleanField(
        _("Notify when students replies on question"),
        default=False
    )
    asked_private_question = models.BooleanField(
        _("Notify when students asks private question"),
        default=True
    )
    replied_on_private_question = models.BooleanField(
        _("Notify when students replies on private question"),
        default=False
    )

    def __str__(self):
        return '{}'.format(self.user)

    def __unicode__(self):
        return u'{}'.format(self.user)
