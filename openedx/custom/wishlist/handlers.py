"""
Wishlist related signal handlers.
"""


from django.dispatch import receiver

from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE

from .models import Wishlist


@receiver(ENROLL_STATUS_CHANGE)
def remove_from_wishlist_on_enrollment(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    """
    Remove a course from the wishlist for the given user on new enrollments.
    """
    if event == EnrollStatusChange.enroll:
        Wishlist.objects.filter(
            user=user,
            course_key=kwargs.get('course_id'),
        ).delete()
