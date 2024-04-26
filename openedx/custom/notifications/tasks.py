"""
Celery tasks used by notification triggers
"""

from uuid import uuid4

import logging
from django.utils import timezone
from django.contrib.auth.models import User
from celery.task import task

from opaque_keys.edx.keys import CourseKey
from openedx.custom.notifications.utils import translate
from openedx.custom.notifications.api.utils import (
    add_notification_db,
    push_notification_fcm,
)
from django.contrib.auth.models import User
from openedx.custom.notifications.constants import NotificationTypes
from openedx.custom.taleem_grades.models import PersistentExamGrade
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.django_comment_common import comment_client as cc
from student.models import CourseEnrollment
from openedx.custom.notifications.permissions import (
    get_course_teachers,
    is_staff_or_course_teacher,
)
from .helpers import (
    send_new_post_notification,
    send_new_comment_notification,
)

log = logging.getLogger(__name__)


@task()
def send_announcement_notification(title='', message='', data={},
    course_id=None, users=None, to_all=False, resolve_link=None):
    """
    Send and store notifications.
    """

    log.info("Storing and sending announcement notifications")

    if users is None and course_id:
        # enrolled users excluding teachers/admins
        users = CourseEnrollment.objects.filter(
            course_id=course_id,
            is_active=True,
        ).exclude(
            user__courseaccessrole__role__in=('instructor', 'staff'),
        ).values_list("user_id", flat=True)
    db_users = users
    if users is None and to_all:
        db_users = User.objects.all().values_list('id', flat=True)

    data.update({
        'id': str(uuid4()),
        'created': str(timezone.localtime()),
        'read': False,
    })
    add_notification_db(db_users, title, message,
        course_id, data, resolve_link=resolve_link)
    push_notification_fcm(
        users=users,
        title=translate(title),
        message=translate(message),
        data=data,
        all_users=to_all,
    )


@task()
def notify_user_for_report_review(users, course_id, status):
    """
    Function responsible for notifying user about
    Proctoring Report Been Reviewed.
    """
    if status != 'clean':
        return

    course_key = CourseKey.from_string(course_id)
    exam_name = CourseOverview.objects.get(
        id=course_key,
    ).display_name
    title = "Your exam has been scored"
    message = "Your exam on {{exam_name:{exam_name}}} has been graded.".format(
        exam_name=exam_name
    )
    data = {
        'id': str(uuid4()),
        'created': str(timezone.localtime()),
        'read': False,
        'type': 'exam_score',
        'status': status, # possible values: suspicious/clean
        'exam_id': course_id,
        'exam_title': exam_name,
    }
    grades = {
        grade['user_id']: {
            'score': grade['percent_grade'],
            'total': 100.0,
        }
        for grade in PersistentExamGrade.objects.filter(
            course_id=course_key,
            user_id__in=users,
        ).values('user_id', 'percent_grade')
    }

    users = grades.keys()
    if not users:
        log.info("Score notification: grades not available data={}".format(data))
        return

    add_notification_db(users, title, message,
        course_id, data, grades)

    push_notification_fcm(
        users=users,
        title=translate(title),
        message=translate(message),
        data=data,
        personalize=grades,
    )


@task()
def send_discussion_notification(**kwargs):
    if kwargs["post_type"] == "thread":
        send_new_post_notification(**kwargs)
    else:
        send_new_comment_notification(**kwargs)
