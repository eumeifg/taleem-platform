from datetime import timedelta
from logging import getLogger

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils import timezone
from student.models import CourseAccessRole

from openedx.custom.notifications.constants import NotificationTypes
from openedx.custom.notifications.utils import notify_user
from openedx.custom.timed_exam.models import TimedExam
from openedx.custom.taleem.dashboard_reports import get_absent_students

logger = getLogger(__name__)


class Command(BaseCommand):
    """
    This command attempts to send notification for exam due today.
    Example usage:
        $ ./manage.py lms send_notifications_to_teacher
    """
    help = 'Command to send notifications to teacher for exam due passed and ready for being reviewed.'

    def handle(self, *args, **options):
        now = timezone.now()
        time_hour_before = now - timedelta(hours=3, minutes=59)

        exams = TimedExam.objects.filter(due_date__gte=time_hour_before, due_date__lte=now)

        for exam in exams:
            logger.info('Notifying the teacher about exam due date passed and ready for being reviewed for exam: "%s".',
                        exam.display_name)
            exam_id = exam.key

            try:
                exam_access_role = CourseAccessRole.objects.get(course_id=exam_id, role='staff')

                notify_user(
                    user=exam_access_role.user,
                    notification_type=NotificationTypes.EXAM_DUE_DATE_PASSED,
                    notification_message="{{exam_name:{exam_name}}} exam due date has been passed. Please review it.".format(
                        exam_name=exam.display_name,
                    )
                )

                absent_students = get_absent_students(exam)
                if len(absent_students) > 0:
                    notify_user(
                        user=exam_access_role.user,
                        notification_type=NotificationTypes.EXAM_DUE_DATE_PASSED,
                        notification_message="Some of the students missed the exam {{exam_name:{exam_name}}}".format(
                            exam_name=exam.display_name,
                        ),
                        resolve_link='/reports/'
                    )
            except ObjectDoesNotExist:
                logger.warning('Course Access Role for exam: %s not found', exam.display_name)

