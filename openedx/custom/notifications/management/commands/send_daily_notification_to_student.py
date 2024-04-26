from logging import getLogger

from django.core.management.base import BaseCommand
from django.utils import timezone
from student.models import CourseEnrollment

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.notifications.constants import NotificationTypes
from openedx.custom.notifications.utils import notify_user
from openedx.custom.timed_exam.models import TimedExam

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    This command attempts to send notification for exam due today.
    Example usage:
        $ ./manage.py lms send_daily_notification_to_student
    """
    help = 'Command to send notifications to student that have exam due today.'

    def handle(self, *args, **options):
        # notify for exam due today

        today = timezone.now().date()
        exams = TimedExam.objects.raw("Select * FROM `timed_exam_timedexam` where YEAR(due_date)={year} "
                                      "and MONTH(due_date)={month} and DAY(due_date)={day};".format(
                                        year=today.year, month=today.month, day=today.day))

        for exam in exams:
            logger.info('Notifying the student enrolled in exam: "%s" for due date of exam.', exam.display_name)

            exam_key = exam.key
            exam_enrollments = CourseEnrollment.objects.filter(course_id=exam_key, is_active=True)

            for enrollment in exam_enrollments:
                notify_user(
                    user=enrollment.user,
                    notification_type=NotificationTypes.EXAM_DUE_TODAY,
                    notification_message="{{exam_name:{exam_name}}} exam is due today.".format(
                        exam_name=enrollment.course.display_name,
                    )
                )

        # notify for course due today
        courses = CourseOverview.objects.raw("Select * FROM `course_overviews_courseoverview` where "
                                             "YEAR(end_date)={year} and MONTH(end_date)={month} "
                                             "and DAY(end_date)={day} and is_timed_exam=False;".format(
                                                year=today.year,
                                                month=today.month,
                                                day=today.day))

        for course in courses:
            course_enrollments = CourseEnrollment.objects.filter(course=course, is_active=True)

            for enrollment in course_enrollments:
                notify_user(
                    user=enrollment.user,
                    notification_type=NotificationTypes.COURSE_DUE_TODAY,
                    notification_message="{{course_name:{course_name}}} course deadline is of today.".format(
                        course_name=enrollment.course.display_name,
                    )
                )
