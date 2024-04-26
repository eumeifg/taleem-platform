import re
import json
import logging
import six

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.utils import translation
from django.utils.translation import ugettext as _

from ccx_keys.locator import CCXLocator
from opaque_keys.edx.keys import CourseKey
from xmodule.error_module import ErrorDescriptor

from student.auth import has_studio_write_access
from student.models import CourseAccessRole, CourseEnrollment
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.notifications.constants import NotificationTypes
from openedx.custom.notifications.models import NotificationMessage


log = logging.getLogger(__name__)


def translate(msgid, language='ar'):
    msgstr = msgid
    values = {}
    for variable in re.findall(r'{(.+?)}', msgid):
        var_name, value = variable.split(":")
        values[var_name] = value
        msgstr = msgstr.replace(
            "{variable}".format(variable=variable),
            "{var_name}".format(var_name=var_name),
            1
        )
    with translation.override(language):
        return _(msgstr).format(**values)

def notify_user(user, notification_type=None, resolve_link=None, notification_message=None, title=None):

    if not notification_message:
        try:
            notification_message = NotificationTypes.messages[notification_type]
        except KeyError:
            log.exception(
                u'Invalid Notification Type : "%s"',
                notification_type
            )
            return

    if not title:
        title = NotificationTypes.titles.get(notification_type, "General")

    log.info(
        u'Adding a notification for "%s".',
        user.username
    )

    try:
        notification = NotificationMessage(user=user, message=notification_message, title=title)
        if resolve_link:
            notification.resolve_link = resolve_link
        notification.save()
    except Exception:
        log.error(
            u'Error occur while adding a notification for "%s".',
            user.username
        )
    else:
        log.info(
            u'Successfully added a notification for "%s".',
            user.username
        )


def get_user_courses(request):
    """
    List all courses available to the logged in user by iterating through all the courses.
    """
    courses_data = []

    def course_filter(course):
        """
        Filter out unusable and inaccessible courses
        """
        if isinstance(course, ErrorDescriptor):
            return False

        # Custom Courses for edX (CCX) is an edX feature for re-using course content.
        # CCXs cannot be edited in Studio (aka cms) and should not be shown in this dashboard.
        if isinstance(course.id, CCXLocator):
            return False

        # TODO remove this condition when templates purged from db
        if course.location.course == 'templates':
            return False


        return has_studio_write_access(request.user, course.id)

    params = json.loads(request.body.decode("utf-8"))
    page = params.get('page')
    page_size = params.get('page_size')
    start =  (page * page_size) - page_size
    end = start + page_size
    search_term = params.get('term')

    courses = CourseOverview.objects.filter(is_timed_exam=False)
    if search_term:
            courses = courses.filter(display_name__icontains=search_term)
    paginator = Paginator(courses, page_size)
    page_object = paginator.page(page)
    courses = courses[start:end]
    courses = six.moves.filter(course_filter, courses)

    for course in courses:
        course_obj = {
            'name': course.display_name,
            'id': str(course.location.course_key)
        }
        courses_data.append(course_obj)

    return courses_data, page_object


def get_user_timed_exams(request):
    """
    List all courses available to the logged in user by iterating through all the courses.
    """
    timed_exams_data = []

    def timed_exam_filter(course):
        """
        Filter out unusable and inaccessible courses
        """
        if isinstance(course, ErrorDescriptor):
            return False

        # Custom Courses for edX (CCX) is an edX feature for re-using course content.
        # CCXs cannot be edited in Studio (aka cms) and should not be shown in this dashboard.
        if isinstance(course.id, CCXLocator):
            return False

        # TODO remove this condition when templates purged from db
        if course.location.course == 'templates':
            return False


        return has_studio_write_access(request.user, course.id)
    
    params = json.loads(request.body.decode("utf-8"))
    page = params.get('page')
    page_size = params.get('page_size')
    start =  (page * page_size) - page_size
    end = start + page_size
    search_term = params.get('term')

    timed_exams = CourseOverview.objects.filter(is_timed_exam=True)
    if search_term:
            timed_exams = timed_exams.filter(display_name__icontains=search_term)
    paginator = Paginator(timed_exams, page_size)
    page_object = paginator.page(page)
    timed_exams = timed_exams[start:end]
    timed_exams = six.moves.filter(timed_exam_filter, timed_exams)
    
    for time_exam in timed_exams:
        time_exam_obj = {
            'name': time_exam.display_name,
            'id': str(time_exam.location.course_key)
        }
        timed_exams_data.append(time_exam_obj)

    return timed_exams_data, page_object



def get_users(request):
    params = json.loads(request.body.decode("utf-8"))
    page = params.get('page')
    page_size = params.get('page_size')
    start =  (page * page_size) - page_size
    end = start + page_size
    search_term = params.get('term')
    users_data = []

    users = User.objects.filter()
    if search_term:
        users = users.filter(profile__name__icontains=search_term)
    paginator = Paginator(users, page_size)
    page_object = paginator.page(page)
    for user in users[start:end]:
        user_obj = {
            'id': user.id,
            'name': user.profile.name
        }
        users_data.append(user_obj)
    return users_data, page_object


def add_notification(course_id, notification_message):
    """
    Function responsible for adding custom notification message for course or timed exams.
    """
    enrollments = CourseEnrollment.objects.filter(course_id=course_id, is_active=True)

    for enrollment in enrollments:
        notify_user(user=enrollment.user, notification_message=notification_message)


def add_user_notification(user_id, notification_message):
    """
    Function responsible for adding custom notification message for user.
    """
    user = User.objects.get(id=user_id)
    notify_user(user=user, notification_message=notification_message)


def send_exam_submit_notification(user, exam_attempt):
    course_id = exam_attempt.proctored_exam.course_id
    key = CourseKey.from_string(course_id)
    course_name = CourseOverview.objects.get(id=key).display_name

    # notify student
    notify_user(
        user=user,
        notification_type=NotificationTypes.EXAM_SUBMITTED,
        notification_message="You have successfully submitted exam {{exam_name:{exam_name}}}".format(
            exam_name=course_name,
        )
    )

    # notify teacher
    proctored_exam = exam_attempt.proctored_exam
    exam_id = proctored_exam.course_id

    try:
        exam_access_role = CourseAccessRole.objects.get(course_id=exam_id, role='instructor')
    except ObjectDoesNotExist:
        log.warning('Course Access Role for exam: %s not found', proctored_exam.exam_name)

    notify_user(
        user=exam_access_role.user,
        notification_type=NotificationTypes.EXAM_SUBMITTED_BY_STUDENT,
        notification_message="{{student_name:{student_name}}} has submitted exam {{exam_name:{exam_name}}}".format(
            student_name=user.profile.name,
            exam_name=course_name,
        )
    )


def user_can_add_new_notification(request):
    return request.user.is_staff or request.user.is_superuser
