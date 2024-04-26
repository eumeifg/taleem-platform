from datetime import timedelta
from logging import getLogger

from django.core.management.base import BaseCommand
from django.utils import timezone
from student.models import CourseEnrollment

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.request_utils import course_id_from_url
from openedx.custom.live_class.models import LiveClass
from openedx.custom.taleem_calendar.models import Ta3leemReminder
from openedx.custom.taleem_calendar.utils import add_reminder_notification, send_reminder_email, \
    user_allowed_notifications

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    This command attempts to send notification for reminders.
    Example usage:
        $ ./manage.py lms send_reminder_notifications_to_user
    """
    help = 'Command to send notifications/email to student that have reminder.'

    def handle(self, *args, **options):
        time_now = timezone.now()
        today = time_now.date()
        time_after = time_now + timedelta(minutes=5)

        reminders = Ta3leemReminder.objects.raw("Select * FROM `taleem_calendar_ta3leemreminder` where YEAR(time)={year} "
                                      "and MONTH(time)={month} and DAY(time)={day};".format(
                                        year=today.year, month=today.month, day=today.day))

        for reminder in reminders:
            if time_now <= reminder.time <= time_after:
                if reminder.send_notification:
                    self.reminder_notification_handler(reminder, notification_type='notification')
                if reminder.send_email:
                    self.reminder_notification_handler(reminder, notification_type='email')

    def reminder_notification_handler(self, reminder, notification_type):
        reminder_type = reminder.type
        course_reminder_types = [Ta3leemReminder.COURSE_START_DATE, Ta3leemReminder.COURSE_END_DATE,
                                 Ta3leemReminder.COURSE_IMPORTANT_DATE, Ta3leemReminder.EXAM_END_DATE,
                                 Ta3leemReminder.EXAM_START_DATE]

        if reminder_type in course_reminder_types:
            self.course_and_exam_reminder_handler(reminder, notification_type=notification_type)
        elif reminder_type == Ta3leemReminder.LIVE_CLASS:
            self.class_reminder_handler(reminder, notification_type=notification_type)

    @staticmethod
    def course_and_exam_reminder_handler(reminder, notification_type):
        reminder_identifier = reminder.identifier

        if reminder.type == Ta3leemReminder.COURSE_IMPORTANT_DATE:
            reminder_identifier = course_id_from_url(reminder_identifier)

        course_name = CourseOverview.objects.get(id=reminder_identifier).display_name

        if notification_type == 'notification':
            if reminder.privacy == Ta3leemReminder.PUBLIC:
                enrollments = CourseEnrollment.objects.filter(course_id=reminder_identifier, is_active=True)
                for enrollment in enrollments:
                    add_reminder_notification(enrollment.user, reminder, event_name=course_name)
            else:
                user = reminder.created_by
                add_reminder_notification(user, reminder, event_name=course_name)

        if notification_type == 'email':
            if reminder.privacy == Ta3leemReminder.PUBLIC:
                enrollments = CourseEnrollment.objects.filter(course_id=reminder_identifier, is_active=True)
                for enrollment in enrollments:
                    if user_allowed_notifications(enrollment.user):
                        send_reminder_email(enrollment.user, reminder, event_name=course_name)
            else:
                user = reminder.created_by
                send_reminder_email(user, reminder, event_name=course_name)

    @staticmethod
    def class_reminder_handler(reminder, notification_type):
        reminder_identifier = reminder.identifier
        live_class = LiveClass.objects.get(id=reminder_identifier)

        if notification_type == 'notification':
            if reminder.privacy == Ta3leemReminder.PUBLIC:
                bookings = live_class.get_bookings()
                for booking in bookings:
                    add_reminder_notification(booking.user, reminder, event_name=live_class.name)
            else:
                user = reminder.created_by
                add_reminder_notification(user, reminder, event_name=live_class.name)

        if notification_type == 'email':
            if reminder.privacy == Ta3leemReminder.PUBLIC:
                bookings = live_class.get_bookings()
                for booking in bookings:
                    send_reminder_email(booking.user, reminder, event_name=live_class.name)
            else:
                user = reminder.created_by
                send_reminder_email(user, reminder, event_name=live_class.name)
