import json
import jwt
from six import text_type

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.safestring import mark_safe

from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user
from openedx.custom.live_class.models import LiveClass, LiveClassBooking
from openedx.custom.notifications.constants import NotificationTypes
from openedx.custom.notifications.utils import notify_user
from openedx.custom.taleem.utils import user_is_ta3leem_admin, user_is_teacher
from openedx.custom.taleem_organization.models import OrganizationType
from openedx.custom.timed_exam.exceptions import InvalidCSVDataError, InvalidEmailError
from openedx.custom.utils import (
    convert_comma_separated_string_to_list,
    parse_csv,
    utc_datetime_to_local_datetime,
)

from openedx.custom.notifications.tasks import send_announcement_notification

__MISSING_VALUE__ = object()

TOOLBAR_BUTTONS = [
    'microphone', 'camera', 'closedcaptions', 'fullscreen', 'fodeviceselection',
    'hangup', 'chat', 'etherpad', 'shareaudio', 'raisehand', 'videoquality',
    'filmstrip', 'feedback', 'shortcuts', 'tileview', 'select-background', 'download',
    'help', 'participants-pane', 
]

MODERATOR_BUTTONS = TOOLBAR_BUTTONS + [
    'desktop', 'mute-everyone', 'mute-video-everyone',
    'stats', 'settings', 'livestreaming', 'sharedvideo',
]


def get_class_url(live_class):
    live_class_id = live_class.id
    return reverse('running_class', kwargs={'class_id': live_class_id})


def can_browse_live_class(live_class, user):
    if live_class.class_type == LiveClass.PUBLIC:
        return True

    user_organization = user.ta3leem_profile.organization
    if live_class.class_type == LiveClass.PUBLIC_AT_INSTITUTION:
        moderator = live_class.moderator
        moderator_organization = moderator.organization
        if moderator_organization == user_organization:
            if user_organization.type == OrganizationType.SCHOOL and user_organization == moderator_organization:
                return True
            elif [department for department in moderator.department.all()
                  if department in user.ta3leem_profile.department.all()]:
                return True

    return False


def generate_jwt_token(user, is_teacher, live_class):
    payload = {}

    user_context = _get_user_context(user, is_teacher)

    payload["context"] = user_context
    payload["aud"] = settings.JITSI_SERVER_APP_ID
    payload["iss"] = settings.JITSI_SERVER_APP_ID
    payload["sub"] = settings.JITSI_SERVER_URL
    payload["room"] = text_type(live_class.id)
    payload["moderator"] = is_teacher

    jwt_token = jwt.encode(payload, settings.JITSI_SERVER_SECRET, algorithm="HS256")

    return jwt_token


def _get_user_context(user, is_teacher):
    profile_image_url = get_profile_image_urls_for_user(user)['medium']
    context = {
        "user": {
            "id": "TA{}".format(user.id),
            "name": user.profile.name,
            "email": user.email,
            "affiliation": is_teacher and "owner" or "member"
        }
    }

    if profile_image_url:
        context["user"]["avatar"] = profile_image_url

    return context


def get_class_settings(is_teacher, live_class):
    return mark_safe(json.dumps({
        'subject': live_class.name,
        'startWithVideoMuted': True,
        'startWithAudioMuted': True,
        'buttonsWithNotifyClick': ['hangup'],
        'toolbarButtons': is_teacher and MODERATOR_BUTTONS or TOOLBAR_BUTTONS
    }))


def get_all_live_classes(user):
    if user_is_teacher(user) or user.is_superuser or user_is_ta3leem_admin(user):
        live_classes = LiveClass.objects.filter(moderator=user.ta3leem_profile)
    else:
        bookings = LiveClassBooking.get_bookings(user)
        live_classes = [booking.live_class for booking in bookings]

    return live_classes


def enroll_in_live_class(request, live_class):
    """
    Enrol the given emails in given Timed exam.

    If email doesn't exist in our system then ignores it.

    Arguments:
        request (WSGI request object): request object.
        live_class (LiveClass): LiveClass Object.

    Raises:
        (InvalidCSVDataError): Raised of CSV data is not valid.
    """
    students_data = []
    invalid_emails = []
    total_email_count = 0

    if request.FILES:
        for row in parse_csv(request.FILES['book_csv_file']):
            try:
                total_email_count += 1
                validate_student_email(row['email'])
            except ValidationError:
                invalid_emails.append(row['email'])
            else:
                students_data.append({'email': row['email']})
        validate_students_data(students_data)
    else:
        for email in convert_comma_separated_string_to_list(request.POST['student_email']):
            try:
                total_email_count += 1
                validate_student_email(email)
            except ValidationError:
                invalid_emails.append(email)
            else:
                students_data.append({'email': email})

    enroll_user_in_live_class(students_data, live_class)

    if len(invalid_emails) > 0:
        if total_email_count == 1:
            error_string = 'Given email address is not valid'
        else:
            error_string = '{invalid_email_count} out of {total_email_count} given email addresses were not valid ' \
                           'and booking is skipped for these addresses.'.format(
                            invalid_email_count=len(invalid_emails), total_email_count=total_email_count)
        raise InvalidEmailError(error_string)


def validate_students_data(students_data):
    """
    Validate csv data and raise InvalidCSVDataError if data is not valid.

    Arguments:
        students_data (list<dict>): Each dict will contain the following fields
            1. email (str): Email address of the user that needs to be enrolled
    Raises:
        (InvalidCSVDataError): Raised of CSV data is not valid.
    """
    required_fields = {'email'}

    for student_data in students_data:
        # Validate that all dicts have the required key-value pairs.
        if not required_fields.issubset(student_data.keys()):
            raise InvalidCSVDataError(
                'All required fields must be present in the csv. '
                'Required Fields: "{}", Given Fields: "{}".'.format(
                    ', '.join(required_fields), ', '.join(student_data.keys())
                )
            )


def validate_student_email(student_email):
    """
    Validate that student with the given email address exists.
    """
    try:
        User.objects.get(email=student_email)
    except User.DoesNotExist:
        raise ValidationError(message="User doesn't Exists with email: {}".format(student_email))


def enroll_user_in_live_class(students_data, live_class):
    """
    Create the Booking Object for user.

    Arguments:
        students_data (list<dict>): Each dict will contain the following fields
            1. email (str): Email address of the user that needs to be enrolled
        live_class (LiveClass): The live class object for the booking.
    """
    users_to_be_notified = []
    for student_data in students_data:
        student_email = student_data['email']
        student = User.objects.get(email=student_email)
        _, created = LiveClassBooking.objects.get_or_create(
            user=student,
            live_class=live_class
        )

        if created:
            users_to_be_notified.append(student.id)
            notify_user(
                user=student,
                notification_type=NotificationTypes.LIVE_CLASS_BOOKED,
                notification_message="You have been enrolled in new live class {{live_class_name:{live_class_name}}}".format(
                    live_class_name=live_class.name,
                )
            )
    # send notification in background
    if users_to_be_notified:
        send_announcement_notification.delay(
            title="Live class invite",
            message="You have been invited to join a live session {{live_class_name:{live_class_name}}}".format(
                live_class_name=live_class.name,
            ),
            data={
                'type': 'live_class_invite',
                'live_class_id': text_type(live_class.id),
                'display_name': live_class.name,
                'stage': live_class.stage,
                'scheduled_on': utc_datetime_to_local_datetime(
                    live_class.scheduled_on
                ).isoformat(),
            },
            users=users_to_be_notified,
        )
