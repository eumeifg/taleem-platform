import logging
import uuid

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import translation
from django.utils.translation import ugettext as _
from edx_ace import ace
from edx_ace.recipient import Recipient
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from six import text_type
from student.auth import has_course_author_access
from student.models import CourseEnrollment
from util.course import get_link_for_about_page

from lms.djangoapps.courseware.courses import get_course_date_blocks
from lms.djangoapps.courseware.date_summary import CourseAssignmentDate
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.core.lib.request_utils import course_id_from_url
from openedx.custom.live_class.models import LiveClass
from openedx.custom.live_class.utils import get_all_live_classes
from openedx.custom.notifications.constants import NotificationTypes
from openedx.custom.notifications.utils import notify_user
from openedx.custom.taleem_calendar.message_types import (NotificationMessage, ReminderMessage)
from openedx.custom.taleem_calendar.models import CalendarEvent, Ta3leemReminder
from openedx.custom.utils import utc_datetime_to_local_datetime

log = logging.getLogger(__name__)


def get_user_courses_between_dates(from_date, to_date, request):
    courses = []
    enrollments = CourseEnrollment.objects.filter(user=request.user, course__is_timed_exam=False)

    for enrollment in enrollments:
        course = enrollment.course
        # Adding Course Start Date Event
        if course.start_date and from_date <= course.start_date <= to_date:
            reminders = _get_reminders(reminder_type='course_start_date', key=course.id, user=request.user)
            course_start_event = {
                'title': _("Course Start Date"),
                'description': course.display_name,
                'start_date': course.start_date,
                'type': 'course_start_date',
                'course_id': text_type(course.id),
                'link': get_link_for_about_page(course),
                'reminders': reminders
            }
            courses.append(course_start_event)

        # Adding Course Important Dates
        important_dates = get_course_important_dates(course, request, from_date, to_date)
        courses = courses + important_dates

        # Adding Course End Date Event
        if course.end_date and (from_date <= course.end_date <= to_date):
            reminders = _get_reminders(reminder_type='course_end_date', key=course.id, user=request.user)
            course_end_event = {
                'title': _("Course End Date"),
                'description': course.display_name,
                'start_date': course.end_date,
                'type': 'course_end_date',
                'link': get_link_for_about_page(course),
                'course_id': text_type(course.id),
                'reminders': reminders
            }
            courses.append(course_end_event)

    return courses


def get_user_exams_between_dates(from_date, to_date, user):
    exams = []
    enrollments = CourseEnrollment.objects.filter(user=user, course__is_timed_exam=True)

    for enrollment in enrollments:
        timed_exam = enrollment.course
        reminders = _get_reminders(reminder_type='exam_start_date', key=timed_exam.id, user=user)
        if timed_exam.start_date and from_date <= timed_exam.start_date <= to_date:
            exam = {
                'title': _("Timed Exam Start"),
                'description': timed_exam.display_name,
                'start_date': utc_datetime_to_local_datetime(timed_exam.start_date),
                'type': 'exam_start_date',
                'exam_id': text_type(timed_exam.id),
                'reminders': reminders
            }
            exams.append(exam)

        if timed_exam.end_date and from_date <= timed_exam.end_date <= to_date:
            reminders = _get_reminders(reminder_type='exam_end_date', key=timed_exam.id, user=user)
            exam = {
                'title': _("Timed Exam End"),
                'description': timed_exam.display_name,
                'start_date': utc_datetime_to_local_datetime(timed_exam.end_date),
                'type': 'exam_end_date',
                'exam_id': text_type(timed_exam.id),
                'reminders': reminders
            }
            exams.append(exam)

    return exams


def get_user_live_classes_between_dates(from_date, to_date, user):
    classes = []
    live_classes = get_all_live_classes(user)

    for live_class in live_classes:
        if from_date <= live_class.scheduled_on <= to_date:
            reminders = _get_reminders(reminder_type='live_class', key=live_class.id, user=user)
            live_class_obj = {
                'title': _("Live Class"),
                'start_date': live_class.scheduled_on,
                'description': live_class.name,
                'type': 'live_class',
                'live_class_id': live_class.id,
                'reminders': reminders
            }

            if live_class.stage == LiveClass.SCHEDULED or live_class.stage == LiveClass.RUNNING:
                live_class_obj['link'] = reverse('go_to_class', args=[text_type(live_class.id)])

            classes.append(live_class_obj)

    return classes


def get_course_important_dates(course, request, from_date, to_date):
    important_dates = []

    blocks = get_course_date_blocks(course, request.user, request, include_access=True, include_past_dates=True)
    for block in blocks:
        if isinstance(block, CourseAssignmentDate) and block.link:
            if from_date <= block.date <= to_date:
                reminders = _get_reminders(reminder_type='course_important_date', key=block.link, user=request.user)
                block_link = request.build_absolute_uri(block.link)
                obj = {
                    'title': "{type} - {title}".format(type=_("Course Important Date"), title=block.title),
                    'description': course.display_name,
                    'start_date': block.date,
                    'type': 'course_important_date',
                    'link': block_link,
                    'course_important_date_id': block.link,
                    'reminders': reminders
                }
                important_dates.append(obj)

    return important_dates


def get_user_custom_events(from_date, to_date, user):
    events = []
    user_events = CalendarEvent.objects.filter(created_by=user)
    for event in user_events:
        if from_date <= event.time <= to_date:
            event_obj = {
                'event_id': event.id,
                'title': event.title,
                'start_date': event.time,
                'description': event.description,
                'type': 'custom_event',
                'reminders': []
            }

            events.append(event_obj)

    return events


def _get_reminders(reminder_type, key, user=None):
    reminders = []
    queryset = Ta3leemReminder.objects.filter(type=reminder_type, identifier=key)

    for reminder in queryset:
        if reminder.privacy == Ta3leemReminder.PRIVATE and not reminder.created_by == user:
            continue
        obj = {
            'description': reminder.message,
            'start_date': reminder.time,
            'reminder_id': reminder.id,
        }
        reminders.append(obj)

    return reminders


def validate_reminder_params(reminder_type, identifier, reminder_time, description):
    allowed_reminder_types = ['course_start_date', 'course_end_date', 'exam_start_date',
                              'exam_end_date', 'live_class', 'individual_user', 'course_important_date']
    error_message = ""

    if reminder_type not in allowed_reminder_types:
        error_message = "Reminder Type is not supported."

        return False, error_message

    if not identifier or not description or not reminder_time:
        error_message = 'Please enter valid identifier, description and reminder_time.'

        return False, error_message

    if reminder_type in Ta3leemReminder.COURSE_TYPE_REMINDERS:
        try:
            course_key = CourseKey.from_string(identifier)
        except InvalidKeyError:
            error_message = "Invalid Course ID."
            return False, error_message

    if reminder_type == Ta3leemReminder.LIVE_CLASS:
        try:
            uuid.UUID(str(identifier))
        except ValueError:
            error_message = "Invalid Class ID."

            return False, error_message

    if reminder_type == Ta3leemReminder.COURSE_IMPORTANT_DATE:
        if not course_id_from_url(identifier):
            error_message = "Invalid event url, Course not found."
            return False, error_message

    return True, error_message


def get_reminder_privacy(identifier, request, reminder_type):
    if reminder_type in Ta3leemReminder.COURSE_TYPE_REMINDERS:
        course_key = CourseKey.from_string(identifier)
        return 'public' if has_course_author_access(request.user, course_key) else 'private'

    if reminder_type == Ta3leemReminder.LIVE_CLASS:
        user_ta3leem_profile = request.user.ta3leem_profile
        live_class = LiveClass.objects.get(id=identifier)
        return 'public' if live_class.moderator == user_ta3leem_profile else 'private'

    if reminder_type == Ta3leemReminder.COURSE_IMPORTANT_DATE:
        course_key = course_id_from_url(identifier)
        return 'public' if has_course_author_access(request.user, course_key) else 'private'

    return 'public'


def send_reminder_email(user, reminder, event_name):
    """
    Send Reminder Email to specific student

    Arguments:
        user (User): User Object.
        reminder (Ta3leemReminder): Ta3leemReminder object.
        event_name (string): Reminder Event Name.
    """

    if not user_allowed_notifications(user):
        return

    site = Site.objects.get_current()
    email_context = get_reminder_email_context(site, reminder, event_name)

    failed = False

    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)

    msg = ReminderMessage().personalize(
        recipient=Recipient(user.username, user.email),
        language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
        user_context=email_context,
    )

    msg.options['from_address'] = from_address

    log.info(
        u'Sending Reminder Email to: "%s"',
        user.email
    )

    try:
        with emulate_http_request(site=site, user=user):
            ace.send(msg)
    except Exception:
        log.exception(
            'Unable to send reminder email to user: "%s"',
            user.email,
        )
        failed = True
    return failed


def user_allowed_notifications(user):
    setting_name = 'calendar_receive_reminder_notifications'
    try:
        user_ta3leem_profile = user.ta3leem_profile
    except ObjectDoesNotExist:
        log.warning(u"Ta3leem profile for the user [%s] does not exist", user.username)
        return False

    extra_settings = user_ta3leem_profile.extra_settings
    if setting_name in extra_settings.keys():
        if extra_settings[setting_name] == 'false':
            return False
        else:
            return True
    else:
        return True


def get_reminder_email_context(site, reminder, event_name):
    context = get_base_template_context(site)
    reminder_title = "{event_type} event has a reminder".format(
        event_type=Ta3leemReminder.REMINDER_TYPES_CONSTANTS[reminder.type],
    )
    context.update({
        'reminder_title': _(reminder_title),
        'event_name': event_name,
        'reminder_description': reminder.message if reminder.message else ''
    })

    return context


def add_reminder_notification(user, reminder, event_name):
    if user_allowed_notifications(user):
        notification_message = "{event_name} {event_type} event has a reminder".format(
            event_name=event_name,
            event_type=Ta3leemReminder.REMINDER_TYPES_CONSTANTS[reminder.type],
        )

        if reminder.message:
            notification_message = notification_message + "{reminder_message}".format(
                reminder_message=reminder.message,
            )

        notify_user(
            user=user,
            notification_type=NotificationTypes.REMINDER_NOTIFICATION,
            notification_message=notification_message
        )


def send_course_notification(user, course, notification_type, course_time_string):
    if user_allowed_notifications(user):
        time, offset = course_time_string.split(' ')
        if notification_type == 'start':
            extra_context = {
                "notification_title": translate_to_user_language(user, "Course Start Notification"),
                "notification_description": translate_to_user_language(user, "will start in:"),
                "event_name": course.display_name
            }
        else:
            extra_context = {
                "notification_title": translate_to_user_language(user, "Course End Notification"),
                "notification_description": translate_to_user_language(user, "will end in:"),
                "event_name": course.display_name
            }

        extra_context.update({
            "time": time,
            "offset": offset
        })

        send_notification_email(user, extra_context)


def send_exam_notification(user, exam, notification_type, exam_time_string):
    if user_allowed_notifications(user):
        time, offset = exam_time_string.split(' ')
        if notification_type == 'start':
            extra_context = {
                "notification_title": translate_to_user_language(user, "Exam Start Notification"),
                "notification_description": translate_to_user_language(user, "will start in:"),
                "event_name": exam.display_name
            }
        else:
            extra_context = {
                "notification_title": translate_to_user_language(user, "Exam End Notification"),
                "notification_description": translate_to_user_language(user, "is due in:"),
                "event_name": exam.display_name
            }

        extra_context.update({
            "time": time,
            "offset": offset
        })
        send_notification_email(user, extra_context)


def send_live_class_notification(user, live_class, live_class_time_string):
    if user_allowed_notifications(user):
        time, offset = live_class_time_string.split(' ')
        extra_context = {
            "notification_title": translate_to_user_language(user, "Live Class Start Notification"),
            "notification_description": translate_to_user_language(user, "will start in:"),
            "event_name": live_class.name,
            "time": time,
            "offset": offset
        }

        send_notification_email(user, extra_context)


def send_notification_email(user, extra_context):
    site = Site.objects.get_current()
    email_context = get_base_template_context(site)
    email_context.update(extra_context)

    failed = False

    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)

    msg = NotificationMessage().personalize(
        recipient=Recipient(user.username, user.email),
        language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
        user_context=email_context,
    )

    msg.options['from_address'] = from_address

    log.info(
        u'Sending Notification Email to: "%s"',
        user.email
    )

    try:
        with emulate_http_request(site=site, user=user):
            ace.send(msg)
    except Exception:
        log.exception(
            'Unable to send reminder email to user: "%s"',
            user.email,
        )
        failed = True
    return failed


def translate_to_user_language(user, message):
    language = preferences_api.get_user_preference(user, LANGUAGE_KEY)
    with translation.override(language):
        return translation.gettext(message)
