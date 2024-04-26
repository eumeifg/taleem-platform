"""
Live class signals and handlers.
"""

from django.dispatch import receiver
from course_modes.models import CourseMode
from student.signals import ENROLL_STATUS_CHANGE

from .tasks import sync_enrollments

@receiver(ENROLL_STATUS_CHANGE)
def post_enrollment_live_class(sender, event=None, user=None, **kwargs):
    if not user or not event or kwargs.get('mode') == CourseMode.TIMED:
        return True

    # Handle time taking op in background
    sync_enrollments.delay(user.id, str(kwargs.get('course_id')), event)
