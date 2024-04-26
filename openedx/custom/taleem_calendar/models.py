from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Ta3leemReminder(models.Model):
    COURSE_START_DATE = u'course_start_date'
    COURSE_END_DATE = u'course_end_date'
    EXAM_START_DATE = u'exam_start_date'
    EXAM_END_DATE = u'exam_end_date'
    LIVE_CLASS = u'live_class'
    INDIVIDUAL_USER = u'individual_user'
    COURSE_IMPORTANT_DATE = u'course_important_date'

    # Second value is the "human-readable" version.
    REMINDER_TYPES = (
        (COURSE_START_DATE, _(u'Course Start Date')),
        (COURSE_END_DATE, _(u'Course End Date')),
        (EXAM_START_DATE, _(u'Exam Start Date')),
        (EXAM_END_DATE, _(u'Exam End Date')),
        (LIVE_CLASS, _(u'Live Class')),
        (COURSE_IMPORTANT_DATE, _(u'Course Important Date'))
    )

    REMINDER_TYPES_CONSTANTS = {
        'course_start_date': 'Course Start Date',
        'course_end_date': 'Course End Date',
        'exam_start_date': 'Exam Start Date',
        'exam_end_date': 'Exam End Date',
        'live_class': 'Live Class',
        'course_important_date': 'Course Important Date'
    }

    COURSE_TYPE_REMINDERS = [
        COURSE_START_DATE,
        COURSE_END_DATE,
        EXAM_START_DATE,
        EXAM_END_DATE
    ]

    PUBLIC = u'public'
    PRIVATE = u'private'

    PRIVACY_CHOICES = (
        (PUBLIC, _(u'Public')),
        (PRIVATE, _(u'Private'))
    )

    type = models.CharField(max_length=24, choices=REMINDER_TYPES, blank=False,
                            help_text=_("Select the reminder type"))
    identifier = models.CharField(max_length=255, db_index=True,
                                  help_text=_("Column Used to store identifier of reminder type"))
    message = models.TextField(max_length=255)
    time = models.DateTimeField(help_text=_("Time of the reminder to show on calendar or send notification"))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reminders")
    send_email = models.BooleanField(default=True)
    send_notification = models.BooleanField(default=True)
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, blank=False, default=PUBLIC,
                               help_text=_("Privacy to identify if the reminder for all students or specific."))

    class Meta:
        app_label = 'taleem_calendar'
        verbose_name = _("Ta3leem Reminder")
        verbose_name_plural = _("Ta3leem Reminders")


class CalendarEvent(models.Model):
    title = models.CharField(max_length=255, blank=False, help_text=_("Title of the event"))
    description = models.TextField(max_length=1000)
    time = models.DateTimeField(help_text=_("Time of the event to show on calendar"))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="calender_events")

    class Meta:
        app_label = 'taleem_calendar'
        verbose_name = _("Calender Event")
        verbose_name_plural = _("Calendar Events")
