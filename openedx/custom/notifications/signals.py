import six

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from student.models import EnrollStatusChange
from student.signals import ENROLL_STATUS_CHANGE
from lms.djangoapps.discussion.tasks import _is_user_subscribed_to_thread
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.django_comment_common import comment_client as cc
from openedx.core.djangoapps.django_comment_common import signals
from openedx.custom.notifications.constants import NotificationTypes
from openedx.custom.notifications.utils import notify_user
from openedx.custom.verification.models import CustomSoftwareSecurePhotoVerification
from openedx.custom.notifications.permissions import (
    get_course_teachers,
    get_course_students,
    is_staff_or_course_teacher,
)

from .tasks import send_discussion_notification

User = get_user_model()


@receiver(ENROLL_STATUS_CHANGE)
def send_enrollment_notification(sender, event=None, user=None, **kwargs):
    course = CourseOverview.objects.get(id=kwargs['course_id'])
    mode = kwargs.get('mode')
    notification_message = None
    if event == EnrollStatusChange.enroll:
        if mode == 'timed':
            notification_type = NotificationTypes.TIMED_EXAM_ENROLLMENT
            notification_message = "You have been enrolled in a timed exam {{exam_name:{exam_name}}}".format(
                exam_name=course.display_name,
            )
        else:
            notification_type = NotificationTypes.COURSE_ENROLLMENT
            notification_message = "You have been enrolled in a course {{course_name:{course_name}}}".format(
                course_name=course.display_name,
            )
    elif event == EnrollStatusChange.unenroll:
        if mode == 'timed':
            notification_type = NotificationTypes.TIMED_EXAM_UNENROLLMENT,
            notification_message = "You have been un-enrolled from a timed exam {{exam_name:{exam_name}}}".format(
                exam_name=course.display_name,
            )

    if notification_message:
        notify_user(notification_type=notification_type, user=user,
            notification_message=notification_message)


@receiver(post_save, sender=CustomSoftwareSecurePhotoVerification)
def send_verification_notification(sender, instance, created, **kwargs):
    """
    Add user to Ta3leemTeacher group whenever it's verification is approved.
    """
    if instance.status == 'approved':
        notify_user(user=instance.user,
            notification_type=NotificationTypes.ID_VERIFICATION_COMPLETED)
    elif instance.status == 'denied':
        notify_user(user=instance.user,
            notification_type=NotificationTypes.ID_VERIFICATION_DENIED)

@receiver(signals.thread_created)
@receiver(signals.comment_created)
def trigger_discussion_notification(sender, **kwargs):
    post = kwargs['post']
    # Skip if posted anonymously
    if not post.user_id:
        return
    user = kwargs['user']
    if post.type == 'thread':
        thread_author_id = post.user_id
        thread_id = post.id
        post_title = post.title
        thread_type = post.thread_type
    else:
        thread = getattr(post, 'thread', None)
        thread_author_id = thread.user_id
        thread_id = thread.id
        post_title = post.body
        thread_type = thread.thread_type
    kwargs = {
        "post_type": post.type,
        "user": user.id,
        "course_id": six.text_type(post.course_id),
        "comment_author_id": post.user_id,
        'thread_author_id': thread_author_id,
        "thread_id": thread_id,
        "post_id" : post.id,
        "post_title": post_title,
        "thread_type": thread_type,
    }
    send_discussion_notification.apply_async(kwargs=kwargs)
