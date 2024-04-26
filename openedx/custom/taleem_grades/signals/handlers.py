"""
Grades related signals.
"""


from logging import getLogger

from django.dispatch import receiver

from lms.djangoapps.grades.signals.signals import SUBSECTION_SCORE_CHANGED
from openedx.custom.taleem.views import tashgheel_grade_notification

log = getLogger(__name__)


@receiver(SUBSECTION_SCORE_CHANGED)
def exam_grade_handler(sender, course, course_structure, user, **kwargs):  # pylint: disable=unused-argument
    """
    Notify Tashgheel
    """
    tashgheel_grade_notification(user, course.id)
