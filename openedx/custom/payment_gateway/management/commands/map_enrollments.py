"""
Map enrollments to voucher usage
"""


from logging import getLogger

from django.core.management.base import BaseCommand

from student.models import CourseEnrollment
from openedx.custom.payment_gateway.models import VoucherUsage


logger = getLogger(__name__)


class Command(BaseCommand):
    """
    This command attempts to:
        For all active enrollments, in the platform,
        Update voucher usage pending to set enrollment
    Example usage:
        $ ./manage.py lms map_enrollments
    """
    help = 'Command to map enrollments to voucher usage.'

    def handle(self, *args, **options):
        logger.info("Mapping enrollments to voucher usage")
        enrollments = CourseEnrollment.objects.filter(is_active=True)
        logger.info("Found {} enrollments".format(enrollments.count()))
        for enrollment in enrollments:
            if not enrollment.course_overview:
                logger.info("Course {} removed, Skipping".format(enrollment.course_id))
                continue

            logger.info("processing user: {} course_id: {}".format(
                enrollment.username, enrollment.course_id))
            VoucherUsage.objects.filter(
                user=enrollment.user,
                course_id=enrollment.course_id,
            ).update(enrollment=enrollment)

        logger.info("=" * 50)
        logger.info("Done !")
