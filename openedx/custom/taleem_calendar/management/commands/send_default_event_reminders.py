from datetime import timedelta
from logging import getLogger

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from student.models import CourseEnrollment

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.live_class.models import LiveClass
from openedx.custom.notifications.models import EventReminderSettings
from openedx.custom.taleem_calendar.utils import (
    send_course_notification, send_exam_notification, send_live_class_notification
)
from openedx.custom.timed_exam.models import TimedExam

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    This command attempts to send notification for reminders.
    Example usage:
        $ ./manage.py lms send_default_event_reminders
    """
    help = 'Command to send notifications/email to student that have reminder.'

    def handle(self, *args, **options):
        course_time, exam_time, live_class_time = self.get_time_settings()
        course_time_string, exam_time_string, live_class_time_string = self.get_time_setting_string()
        time_now = timezone.now()
        extra_time = timedelta(minutes=5)

        course_event_start = time_now + course_time
        # Adding 5 min here because this command will run after every 5 minutes by cron job.
        course_event_end = course_event_start + extra_time

        exam_event_start = time_now + exam_time
        exam_event_end = exam_event_start + extra_time

        live_class_event_start = time_now + live_class_time
        live_class_event_end = live_class_event_start + extra_time

        self.handle_course_notifications(course_event_start, course_event_end, course_time_string)
        self.handle_timed_exam_notifications(exam_event_start, exam_event_end, exam_time_string)
        self.handle_live_class_notifications(live_class_event_start, live_class_event_end, live_class_time_string)

    def handle_course_notifications(self, course_event_start, course_event_end, course_time_string):
        courses = CourseOverview.get_all_courses()
        logger.info("Total Number of Courses: {total_courses}".format(total_courses=len(courses)))
        for course in courses:
            if not course.start_date_is_still_default and course.start and course_event_start <= course.start <= course_event_end:
                self._handle_course_notification(course, course_time_string, notification_type='start')
            if not course.start_date_is_still_default and course.end and course_event_start <= course.end <= course_event_end:
                self._handle_course_notification(course, course_time_string, notification_type='end')

    @staticmethod
    def _handle_course_notification(course, course_time_string, notification_type):
        logger.info("Sending Notification to Enrolled Student of Course: {course_name} for course {notification_type}"
                    " event".format(course_name=course.display_name, notification_type=notification_type)
                    )
        enrollments = CourseEnrollment.objects.filter(course=course, is_active=True)
        logger.info("Total enrolled users in course: {course_name} are {total_enrolled_count}".format(
            course_name=course.display_name,
            total_enrolled_count=len(enrollments)
        ))
        for enrollment in enrollments:
            send_course_notification(enrollment.user, course, notification_type, course_time_string)

    def handle_timed_exam_notifications(self, exam_event_start, exam_event_end, exam_time_string):
        exams = TimedExam.objects.all()
        logger.info("Total Number of Exams: {total_exams}".format(total_exams=len(exams)))
        for exam in exams:
            if exam_event_start <= exam.release_date <= exam_event_end:
                self._handle_exam_notification(exam, exam_time_string, notification_type='start')
            if exam_event_start <= exam.due_date <= exam_event_end:
                self._handle_exam_notification(exam, exam_time_string, notification_type='end')

    @staticmethod
    def _handle_exam_notification(exam, exam_time_string, notification_type):
        logger.info("Sending Notification to Enrolled Student of Exam: {exam_name} for exam {notification_type}"
                    " event".format(exam_name=exam.display_name, notification_type=notification_type)
                    )
        enrollments = CourseEnrollment.objects.filter(course=exam, is_active=True)
        logger.info("Total enrolled users in exam: {exam_name} are {total_enrolled_count}".format(
            exam_name=exam.display_name,
            total_enrolled_count=len(enrollments)
        ))
        enrollments = CourseEnrollment.objects.filter(course_id=exam.id, is_active=True)
        for enrollment in enrollments:
            send_exam_notification(enrollment.user, exam, notification_type, exam_time_string)

    def handle_live_class_notifications(self, live_class_event_start, live_class_event_end, live_class_time_string):
        classes = LiveClass.objects.filter(stage=LiveClass.SCHEDULED)
        logger.info("Total Number of Classes: {total_classes}".format(total_classes=len(classes)))
        for live_class in classes:
            if live_class_event_start <= live_class.scheduled_on <= live_class_event_end:
                self._handle_live_class_notification(live_class, live_class_time_string)

    @staticmethod
    def _handle_live_class_notification(live_class, live_class_time_string):
        logger.info("Sending Notification to Student of Class: {live_class_name} for class schedule.".format(
            live_class_name=live_class.name)
        )
        bookings = live_class.get_bookings()
        logger.info("Total user booked the class: {live_class_name} are {total_booked_count}".format(
            live_class_name=live_class.name,
            total_booked_count=len(bookings)
        ))
        for booking in bookings:
            send_live_class_notification(booking.user, live_class, live_class_time_string)

    def get_time_settings(self):
        event_configurations = EventReminderSettings.current()

        if not event_configurations:
            raise CommandError('No Event Configurations Available')

        course_time = self.get_timedelta_from_offset(event_configurations.course_reminder_time)
        exam_time = self.get_timedelta_from_offset(event_configurations.exam_reminder_time)
        live_class_time = self.get_timedelta_from_offset(event_configurations.live_class_reminder_time)
        return course_time, exam_time, live_class_time

    @staticmethod
    def get_time_setting_string():
        event_configurations = EventReminderSettings.current()

        course_time = event_configurations.course_reminder_time
        exam_time = event_configurations.exam_reminder_time
        live_class_time = event_configurations.live_class_reminder_time
        return course_time, exam_time, live_class_time

    @staticmethod
    def get_timedelta_from_offset(time_string):
        time, offset = time_string.split(' ')
        time = int(time)
        if offset == 'hours':
            time_obj = timedelta(hours=time)
        elif offset == 'days':
            time_obj = timedelta(days=time)
        else:
            time_obj = timedelta(minutes=time)
        return time_obj
