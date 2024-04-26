import six
import logging
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.utils import timezone
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.django_comment_common import comment_client as cc
from openedx.custom.notifications.permissions import (
    get_course_teachers,
    get_course_students,
    is_staff_or_course_teacher,
)
from openedx.custom.notifications.models import MutedPost
from openedx.custom.notifications.utils import translate
from openedx.custom.notifications.api.utils import (
    add_notification_db,
    push_notification_fcm,
)

User = get_user_model()
log = logging.getLogger(__name__)


def send_new_comment_notification(**kwargs):
    commented_by = User.objects.get(id=kwargs['user'])
    course_id = kwargs['course_id']
    course_key = CourseKey.from_string(course_id)
    thread = cc.Thread.find(kwargs['thread_id']).retrieve(
        with_responses=True,
        recursive=True,
        user_id=kwargs['user'],
    )
    course_name = CourseOverview.get_from_id(course_key).display_name
    data = {
        'id': str(uuid4()),
        'created': str(timezone.localtime()),
        'read': False,
        'course_id': course_id,
        'course_name' : course_name,
        'post': kwargs['post_title'],
        'post_id' : kwargs['post_id'],
        'thread_id' : kwargs['thread_id']
    }
    title = "Discussion"
    user_ids = set()

    if is_staff_or_course_teacher(commented_by, course_key):
        message = "{{teacher_name:{teacher_name}}} added a new comment on your post in {{course:{course}}}".format(
            teacher_name=commented_by.profile.name,
            course=course_name
        )
        data.update({
            'type': 'teacher_replied',
            'teacher_name': commented_by.profile.name,
        })
        user_ids.add(thread.user_id)
        if hasattr(thread,'children'):
            for thread_children in thread.children:
                user_ids.add(thread_children['user_id'])
                for children in thread_children['children']:
                    user_ids.add(children['user_id'])
    else:
        # Send to student as an update
        comment_author_id = kwargs['comment_author_id']
        thread_author_id = kwargs['thread_author_id']
        if comment_author_id != thread_author_id:
            if not MutedPost.objects.filter(
                course_id=course_id,
                post_id=kwargs['thread_id'],
                user_id=thread_author_id,
            ).exists():
                add_discussion_notification_for_user(
                    course_key,
                    data,
                    comment_author_id,
                    thread_author_id,
                )
        # Send to teachers as a discussion activity done by student
        teachers = get_course_teachers(course_key, preference_filter=True)
        teachers = teachers.filter(notification_preferences__isnull=False)
        if thread.thread_type == "private":
            teachers = teachers.filter(
                notification_preferences__replied_on_private_question=True,
            )
            message = "{{student:{student}}} replied on a private question in {{course:{course}}}".format(
                student=commented_by.profile.name,
                course=course_name,
            )
            data["type"] = "student_commented_private_question"
        elif thread.thread_type == "question":
            teachers = teachers.filter(
                notification_preferences__replied_on_question=True,
            )
            message = "{{student:{student}}} replied on a question in {{course:{course}}}".format(
                student=commented_by.profile.name,
                course=course_name,
            )
            data["type"] = "student_commented_question"
        else:
            teachers = teachers.filter(
                notification_preferences__added_discussion_comment=True,
            )
            message = "{{student:{student}}} replied on a post in {{course:{course}}}".format(
                student=commented_by.profile.name,
                course=course_name,
            )
            data["type"] = "student_commented_post"

        data['student_name'] = commented_by.profile.name
        user_ids = set(teachers.values_list("id", flat=True))

    muted = set(
        MutedPost.objects.filter(
            course_id=course_id,
            post_id=kwargs['thread_id'],
        ).values_list('user_id', flat=True)
    )
    muted.add(commented_by.id)
    user_ids = list(set(map(int, user_ids)) - muted)
    if not user_ids:
        return

    user_ids = list(user_ids)
    add_notification_db(user_ids, title, message, course_id, data=data)
    push_notification_fcm(
        users=user_ids,
        title=translate(title),
        message=translate(message),
        data=data,
    )


def add_discussion_notification_for_user(course_key, data,
    comment_author_id, thread_author_id):

    log.info('add_discussion_notification_for_user')
    comment_for = User.objects.get(id=thread_author_id)
    if is_staff_or_course_teacher(comment_for, course_key):
        return None

    commented_by = User.objects.get(id=comment_author_id)
    data.update({
        'id': str(uuid4()),
        'type': 'comment_added',
        'student_name': commented_by.profile.name,
    })
    message = "{{user:{user}}} added a comment on your post in {{course:{course}}}".format(
        user=commented_by.profile.name,
        course=data['course_name'],
    )
    user_ids = [thread_author_id]
    course_id = data['course_id']
    title = "Discussion"
    add_notification_db(user_ids, title, message, course_id, data=data)
    push_notification_fcm(
        users=user_ids,
        title=translate(title),
        message=translate(message),
        data=data,
    )

def send_new_post_notification(**kwargs):
    """
    Send the notification to the learners
    if the new post added by the teacher/staff.
    """
    user = User.objects.get(id=kwargs['user'])
    course_id = kwargs['course_id']
    course_key = CourseKey.from_string(course_id)
    course_title = CourseOverview.get_from_id(course_key).display_name
    title = "Discussion"
    message = "A new post has been added to {{course:{course}}}".format(
        course=course_title,
    )
    data = {
        'id':  str(uuid4()),
        'created': str(timezone.localtime()),
        'read': False,
        "type": "new_post",
        "course_id": course_id,
        "course_title": course_title,
        "author": user.profile.name,
        "post": kwargs['post_title'],
        "post_id": kwargs['post_id'],
        "number_of_likes": 0,
    }
    thread_type = kwargs['thread_type']
    teachers = get_course_teachers(course_key,
        preference_filter=True).exclude(id=user.id)
    students = get_course_students(course_key).exclude(id=user.id)
    if thread_type == "private":
        students = User.objects.none()
        teachers = teachers.exclude(
            notification_preferences__asked_private_question=False,
        )
        message = "{{student:{student}}} has asked a private question in {{course:{course}}}".format(
            student=user.profile.name,
            course=course_title,
        )
        data["type"] = "new_private_question"
    elif thread_type == "question":
        teachers = teachers.exclude(
            notification_preferences__asked_question=False,
        )
        message = "{{student:{student}}} has asked a question in {{course:{course}}}".format(
            student=user.profile.name,
            course=course_title,
        )
        data["type"] = "new_question"
    else:
        teachers = teachers.filter(
            notification_preferences__isnull=False,
            notification_preferences__added_discussion_post=True,
        )
        message = "{{student:{student}}} added a new post in {{course:{course}}}".format(
            student=user.profile.name,
            course=course_title,
        )
        data["type"] = "new_post"

    teacher_ids = set(teachers.values_list('id', flat=True))
    student_ids = set(students.values_list('id', flat=True))
    user_ids = set(teachers.values_list("id", flat=True)) | set(
        students.values_list("id", flat=True)
    )
    if not user_ids:
        return

    add_notification_db(user_ids, title, message, course_id, data=data)
    push_notification_fcm(
        users=user_ids,
        title=translate(title),
        message=translate(message),
        data=data,
    )
