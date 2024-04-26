"""
Celery tasks for live class
"""

import logging
from celery.task import task
from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import modulestore
from openedx.custom.utils import utc_datetime_to_local_datetime
from openedx.custom.notifications.tasks import send_announcement_notification
from student.models import EnrollStatusChange, CourseEnrollment

from .models import LiveClass, LiveClassBooking

log = logging.getLogger(__name__)


@task()
def sync_enrollments(user_id, course_id, event):
    """
    Enroll or unenroll from live class
    as the user joined/left the course.
    """
    # Get the live classes mapped to the course
    live_classes = [
        block.live_class_id
        for block in modulestore().get_items(
            CourseKey.from_string(course_id),
            qualifiers={'category': 'liveclass'}
        )
        if block.live_class_id and block.auto_invite
    ]

    if event == EnrollStatusChange.enroll:
        for live_class_id in live_classes:
            try:
                LiveClassBooking.objects.create(
                    user_id=user_id,
                    live_class_id=live_class_id,
                )
            except:
                continue
    elif event == EnrollStatusChange.unenroll:
        LiveClassBooking.objects.filter(
            user_id=user_id,
            live_class_id__in=live_classes,
        ).delete()

@task()
def start_live_class(live_class_id):
    """
    Run the class.
    Notify students.
    """

    log.info("Moving class {} to running".format(live_class_id))

    try:
        live_class = LiveClass.objects.get(id=live_class_id)
    except Exception as e:
        log.info("could not start the class {}, error: {}".format(
            live_class_id,
            str(e),
        ))

    # Bounce if already running
    if live_class.stage == LiveClass.RUNNING:
        return True

    live_class.stage = LiveClass.RUNNING
    live_class.save()

    users_to_be_notified = LiveClassBooking.objects.filter(
        live_class=live_class,
    ).values_list("user_id", flat=True)
    if users_to_be_notified:
        send_announcement_notification.delay(
            title="Live class started",
            message="Class {{live_class_name:{live_class_name}}} is live now".format(
                live_class_name=live_class.name,
            ),
            data={
                'type': 'live_class_started',
                'live_class_id': live_class_id,
                'display_name': live_class.name,
                'stage': live_class.stage,
                'scheduled_on': utc_datetime_to_local_datetime(
                    live_class.scheduled_on
                ).isoformat(),
            },
            users=list(users_to_be_notified),
        )
