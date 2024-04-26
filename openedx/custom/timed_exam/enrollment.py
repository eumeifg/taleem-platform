
import logging

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from opaque_keys.edx.keys import CourseKey

from course_modes.models import CourseMode
from openedx.custom.utils import convert_comma_separated_string_to_list, parse_csv, utc_datetime_to_local_datetime
from student.models import CourseEnrollment

from openedx.custom.timed_exam.models import TimedExam, PendingTimedExamUser
from openedx.custom.timed_exam.exceptions import InvalidCSVDataError, InvalidEmailError
from openedx.custom.timed_exam.utils import send_pending_enrollment_email

log = logging.getLogger(__name__)
__MISSING_VALUE__ = object()


def bulk_enroll(csv_file, post_data):
    """
    Bulk Enrol the given emails with given mode.

    If email doesn't exist in our system then ignores it.

    Arguments:
        csv_file (File): CSV containing email adresses.
        post_data: request.data contains email in case of
            single enrollment request.

    Raises:
        (InvalidCSVDataError): Raised of CSV data is not valid.
    """
    course_id = post_data.get('course_key_string')
    mode = post_data.get('mode')
    enrollment_data = []
    invalid_emails = []
    total_email_count = 0

    if csv_file:
        for row in parse_csv(csv_file):
            try:
                total_email_count += 1
                validate_email(row['email'])
            except ValidationError:
                invalid_emails.append(row['email'])
            else:
                enrollment_data.append({
                    'email': row['email'],
                    'external_user_id': row.get('external_user_id', __MISSING_VALUE__),
                    'external_exam_id': row.get('external_exam_id', __MISSING_VALUE__),
                })
        validate_enrollment_csv(enrollment_data)
    else:
        for email in convert_comma_separated_string_to_list(post_data.get('email')):
            try:
                total_email_count += 1
                validate_email(email)
            except ValidationError:
                invalid_emails.append(email)
            else:
                enrollment_data.append({
                    'email': email,
                    'external_user_id': __MISSING_VALUE__,
                    'external_exam_id': __MISSING_VALUE__,
                })

    enrolled = enroll_users(course_id, mode, enrollment_data)

    if len(invalid_emails) > 0:
        if total_email_count == 1:
            error_string = 'Given email address is not valid'
        else:
            error_string = '{invalid_email_count} out of {total_email_count} given email addresses were not valid '\
                           'and enrollment is skipped for these addresses.'.format(
                                invalid_email_count=len(invalid_emails),
                                total_email_count=total_email_count,
                            )
        raise InvalidEmailError(error_string)

    return enrolled


def validate_enrollment_csv(enrollment_data):
    """
    Validate csv data and raise InvalidCSVDataError if data is not valid.

    Arguments:
        enrollment_data (list<dict>): Each dict will contain the following fields
            1. email (str): Email address of the user that needs to be enrolled
            2. external_user_id (str): User's external id
            3. external_exam_id (str): External timed exam id.
    Raises:
        (InvalidCSVDataError): Raised of CSV data is not valid.
    """
    # Only email field is required at the moment `external_user_id` and `external_exam_id` are optional.
    required_fields = {'email'}
    optional_fields = {'external_user_id', 'external_exam_id'}

    for enrollment in enrollment_data:
        # Validate that all dicts have the required key-value pairs.
        if not required_fields.issubset(enrollment.keys()):
            raise InvalidCSVDataError(
                'All required fields must be present in the csv. '
                'Required Fields: "{}", Optional Fields: {}. Given Fields: "{}".'.format(
                    ', '.join(required_fields), ', '.join(optional_fields), ', '.join(enrollment.keys())
                )
            )
    external_timed_exam_ids = set(
        enrollment['external_exam_id'] for enrollment in enrollment_data
        if enrollment['external_exam_id'] is not __MISSING_VALUE__
    )
    if len(external_timed_exam_ids) > 1:
        raise InvalidCSVDataError(
            'External Timed Exam Id must be same for all enrollments in single CSV, '
            'found "{}" unique External Timed Exam Ids'.format(
                len(external_timed_exam_ids),
            )
        )


def enroll_users(course_id, mode, enrollment_data):
    """
    Enroll users in course with given mode.

    Arguments:
        course_id: Unique id of the course or exam
        mode: mode of enrollment (honor or timed)
        enrollment_data (list<dict>): Each dict will contain the following fields
            1. email (str): Email address of the user that needs to be enrolled
            2. external_user_id (str): User's external id
            3. external_exam_id (str): External timed exam id.
    """
    enrolled = []
    course_key = CourseKey.from_string(course_id)

    if len(enrollment_data) > 0:
        # Update the external_exam_id of the given timed exam.
        if enrollment_data[0]['external_exam_id'] is not __MISSING_VALUE__:
            TimedExam.objects.filter(key=course_key).update(
                external_exam_id=enrollment_data[0]['external_exam_id']
            )

    for enrollment in enrollment_data:
        try:
            user = User.objects.get(email=enrollment['email'])
            course_enrollment = CourseEnrollment.enroll(
                user=user,
                course_key=course_key,
                mode=mode,
            )
            enrolled.append([
                user.email,
                {
                    'display': utc_datetime_to_local_datetime(
                        course_enrollment.created
                    ).strftime("%d-%m-%Y %I:%M %p"),
                    '@data-sort': course_enrollment.created.timestamp(),
                },
                user.username
            ])
        except User.DoesNotExist:
            if mode == CourseMode.TIMED:
                create_pending_enrollment(enrollment, course_id)
            else:
                continue
        else:
            if enrollment['external_user_id'] is not __MISSING_VALUE__:
                user.profile.external_user_id = enrollment['external_user_id']
                user.profile.save()

    return enrolled


def create_pending_enrollment(enrollment, course_id):
    timed_exam = get_object_or_404(TimedExam, key=course_id)
    if enrollment['external_user_id'] is __MISSING_VALUE__:
        defaults = None
    else:
        defaults = {
            'external_user_id': enrollment['external_user_id'],
        }
    # Add user to pending enrollment flow.
    _, created = PendingTimedExamUser.objects.update_or_create(
        user_email=enrollment['email'],
        timed_exam=timed_exam,
        defaults=defaults
    )
    if created:
        send_pending_enrollment_email(enrollment['email'])

    log.info(
        'User with email "{email}" does not exist so creating a pending enrollment record for '
        'this user in time exam "{timed_exam_id}"'.format(
            email=enrollment['email'], timed_exam_id=course_id
        )
    )


def unenroll_in_timed_exam(email, timed_exam_id):
    """
    email (str): Email of a user
    timed_exam_id (str): Course id for Timed exam.

    Unenrolled the given email in given Timed exam.
    """
    user_queryset = User.objects.filter(email=email)
    if user_queryset.exists():
        CourseEnrollment.unenroll(user_queryset.first(), timed_exam_id)
        log.info(
            "Unenrolled the student with email {email} in timed exam {timed_exam_id}".format(
                email=email, timed_exam_id=timed_exam_id
            )
        )
    else:
        log.warning(
            "User doesn't exist with email {email}".format(email=email)
        )


def delete_pending_enrollment(email, timed_exam_id):
    """
    Delete the pending enrollment of user with given email in given Timed exam.

    Arguments:
        email (str): Email of a user
        timed_exam_id (str): Course id for Timed exam.
    """
    PendingTimedExamUser.objects.filter(user_email=email, timed_exam__key=timed_exam_id).delete()
    log.info(
        "Deleted the pending enrollment of the student with email {email} from timed exam {timed_exam_id}".format(
            email=email, timed_exam_id=timed_exam_id
        )
    )


def get_timed_exam_enrollments(timed_exam_id):
    """
    timed_exam_id (str): Course id for Timed exam.

    Return the list of all the enrolled learners for the given Timed exam.
    """
    enrollments = CourseEnrollment.objects.filter(course_id=timed_exam_id, mode=CourseMode.TIMED, is_active=True)
    response = []
    for enrollment in enrollments:
        response.append(
            [
                enrollment.user.email,
                utc_datetime_to_local_datetime(enrollment.created),
            ]
        )
    return response


def get_timed_exam_pending_enrollments(timed_exam_id):
    """
    timed_exam_id (str): Course id for Timed exam.

    Return the list of all the pending enrollments of learners for the given Timed exam.
    """
    pending_enrollments = PendingTimedExamUser.objects.filter(timed_exam__key=timed_exam_id)
    response = []
    for enrollment in pending_enrollments:
        response.append(
            [
                enrollment.user_email,
                utc_datetime_to_local_datetime(enrollment.created),
            ]
        )
    return response
