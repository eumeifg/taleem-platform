"""
Signal handlers for payment app
"""
import logging

from django.dispatch import receiver

from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE

from .models import VoucherUsage


log = logging.getLogger(__name__)

@receiver(ENROLL_STATUS_CHANGE)
def map_voucher_usage_with_enrollment(sender, event=None, user=None, **kwargs):
    if user and event == EnrollStatusChange.enroll:
        try:
            enrollment = CourseEnrollment.objects.get(
                user=user,
                course_id=kwargs['course_id']
            )
            VoucherUsage.objects.filter(
                user=user,
                course_id=kwargs['course_id']
            ).update(enrollment=enrollment)
            log.info("mapped voucher_usage user: {}, course:{}".format(
                user.username,
                kwargs['course_id']
            ))
        except:
            pass
