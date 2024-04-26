"""
Library to manage offline exams and attemps.
"""
from __future__ import absolute_import

import logging
import uuid
from datetime import datetime, timedelta

import pytz
import six

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop

from openedx.custom.timed_exam.models import TimedExam
from openedx.custom.offline_exam.models import OfflineExamStudentAttempt
from openedx.custom.offline_exam.statuses import OfflineExamStudentAttemptStatus
from openedx.custom.offline_exam.exceptions import *
from openedx.custom.offline_exam.utils import (
    has_due_date_passed,
    humanized_time,
)


log = logging.getLogger(__name__)

SHOW_EXPIRY_MESSAGE_DURATION = 1 * 60  # duration within which expiry message is shown for a timed-out exam

USER_MODEL = get_user_model()


def _check_for_attempt_timeout(attempt):
    """
    Helper method to see if the status of an
    exam needs to be updated, e.g. timeout
    """
    # right now the only adjustment to
    # status is transitioning to timeout
    has_started_exam = (
        attempt and
        attempt.started_at and
        OfflineExamStudentAttemptStatus.is_incomplete_status(attempt.status)
    )
    if has_started_exam:
        now_utc = datetime.now(pytz.UTC)
        expires_at = attempt.started_at + timedelta(minutes=attempt.timed_exam.allowed_time_limit_mins)
        has_time_expired = now_utc > expires_at

        if has_time_expired:
            attempt = update_attempt_status(
                attempt,
                OfflineExamStudentAttemptStatus.timed_out,
                timeout_timestamp=expires_at
            )

    return attempt


def _get_exam_attempt(exam_attempt_obj):
    """
    Helper method to commonalize all query patterns
    """

    if not exam_attempt_obj:
        return None

    _check_for_attempt_timeout(exam_attempt_obj)

    return exam_attempt_obj


def get_exam_attempt(exam_id, user_id):
    """
    Args:
        int: exam id
        int: user_id
    Returns:
        dict: our exam attempt
    """
    exam_attempt_obj = OfflineExamStudentAttempt.objects.get_exam_attempt(exam_id, user_id)
    return _get_exam_attempt(exam_attempt_obj)


def get_exam_attempt_by_id(attempt_id):
    """
    Args:
        int: exam attempt id
    Returns:
        dict: our exam attempt
    """
    exam_attempt_obj = OfflineExamStudentAttempt.objects.get_exam_attempt_by_id(attempt_id)
    return _get_exam_attempt(exam_attempt_obj)


def get_exam_attempt_by_external_id(external_id):
    """
    Args:
        str: exam attempt external_id
    Returns:
        dict: our exam attempt
    """
    exam_attempt_obj = OfflineExamStudentAttempt.objects.get_exam_attempt_by_external_id(external_id)
    return _get_exam_attempt(exam_attempt_obj)


def get_exam_attempt_by_code(attempt_code):
    """
    Args:
        str: exam attempt attempt_code
    Returns:
        dict: our exam attempt
    """
    exam_attempt_obj = OfflineExamStudentAttempt.objects.get_exam_attempt_by_code(attempt_code)
    return _get_exam_attempt(exam_attempt_obj)


def is_exam_passed_due(exam):
    """
    Return whether the due date has passed.
    Uses edx_when to lookup the date for the subsection.
    """
    return has_due_date_passed(exam.due_date)


def create_exam_attempt(exam, user_id):
    """
    Creates an exam attempt for user_id against exam_id. There should only be
    one exam_attempt per user per exam. Multiple attempts by user will be archived
    in a separate table
    """
    # for now the student is allowed the exam default

    log_msg = (
        u'Creating exam attempt for exam_id {exam_id} for '
        u'user_id {user_id}'.format(
            exam_id=exam.id, user_id=user_id
        )
    )
    log.info(log_msg)

    existing_attempt = OfflineExamStudentAttempt.objects.get_exam_attempt(exam.id, user_id)
    if existing_attempt:
        err_msg = (
            u'Cannot create new exam attempt for exam_id = {exam_id} and '
            u'user_id = {user_id} because it already exists!'
        ).format(exam_id=exam.id, user_id=user_id)

        raise StudentExamAttemptAlreadyExistsException(err_msg)

    allowed_time_limit_mins = _calculate_allowed_mins(exam, user_id)
    attempt_code = six.text_type(uuid.uuid4()).upper()

    attempt = OfflineExamStudentAttempt.create_exam_attempt(
        exam.id,
        user_id,
        attempt_code,
        status=OfflineExamStudentAttemptStatus.created
    )

    log_msg = (
        u'Created exam attempt ({attempt_id}) for exam_id {exam_id} for '
        u'user_id {user_id}'
        u'Attempt_code {attempt_code} was generated'.format(
            attempt_id=attempt.id, exam_id=exam.id, user_id=user_id,
            attempt_code=attempt_code,
        )
    )
    log.info(log_msg)

    return attempt


def start_exam_attempt(exam, user_id):
    """
    Signals the beginning of an exam attempt for a given
    exam_id. If one already exists, then an exception should be thrown.

    Returns: exam_attempt_id (PK)
    """

    existing_attempt = OfflineExamStudentAttempt.objects.get_exam_attempt(exam.id, user_id)

    if not existing_attempt:
        err_msg = (
            u'Cannot start exam attempt for exam_id = {exam_id} '
            u'and user_id = {user_id} because it does not exist!'
        ).format(exam_id=exam.id, user_id=user_id)

        raise StudentExamAttemptDoesNotExistsException(err_msg)

    return _start_exam_attempt(existing_attempt)


def start_exam_attempt_by_code(attempt_code):
    """
    Signals the beginning of an exam attempt when we only have
    an attempt code
    """

    existing_attempt = OfflineExamStudentAttempt.objects.get_exam_attempt_by_code(attempt_code)

    if not existing_attempt:
        err_msg = (
            u'Cannot start exam attempt for attempt_code = {attempt_code} '
            u'because it does not exist!'
        ).format(attempt_code=attempt_code)

        raise StudentExamAttemptDoesNotExistsException(err_msg)

    return _start_exam_attempt(existing_attempt)


def _start_exam_attempt(existing_attempt):
    """
    Helper method
    """

    if existing_attempt.started_at and existing_attempt.status == OfflineExamStudentAttemptStatus.started:
        # cannot restart an attempt
        err_msg = (
            u'Cannot start exam attempt for exam_id = {exam_id} '
            u'and user_id = {user_id} because it has already started!'
        ).format(exam_id=existing_attempt.proctored_exam.id, user_id=existing_attempt.user_id)

        raise StudentExamAttemptedAlreadyStarted(err_msg)

    update_attempt_status(
        existing_attempt,
        OfflineExamStudentAttemptStatus.started
    )

    return existing_attempt


def mark_exam_attempt_timeout(attempt):
    """
    Marks the exam attempt as timed_out
    """
    return update_attempt_status(attempt, OfflineExamStudentAttemptStatus.timed_out)


def mark_exam_attempt_as_ready(attempt):
    """
    Marks the exam attemp as ready to start
    """
    return update_attempt_status(attempt, OfflineExamStudentAttemptStatus.ready_to_start)


# pylint: disable=inconsistent-return-statements
def update_attempt_status(exam_attempt_obj, to_status,
                          raise_if_not_found=True, cascade_effects=True, timeout_timestamp=None,
                          update_attributable_to=None):
    """
    Internal helper to handle state transitions of attempt status
    Also call the celery task to verify the images of web monitoring
    """

    if exam_attempt_obj is None:
        return

    from_status = exam_attempt_obj.status

    # we may treat timeouts the same as submitted
    if to_status == OfflineExamStudentAttemptStatus.timed_out:
        to_status = OfflineExamStudentAttemptStatus.submitted

    # don't allow state transitions from a completed state to an incomplete state
    # if a re-attempt is desired then the current attempt must be deleted
    #
    in_completed_status = OfflineExamStudentAttemptStatus.is_completed_status(from_status)
    to_incompleted_status = OfflineExamStudentAttemptStatus.is_incomplete_status(to_status)

    if in_completed_status and to_incompleted_status:
        err_msg = (
            u'A status transition from {from_status} to {to_status} was attempted '
            u'on exam_id {exam_id} for user_id {user_id}. This is not '
            u'allowed!'.format(
                from_status=from_status,
                to_status=to_status,
                exam_id=exam_id,
                user_id=user_id
            )
        )
        raise ProctoredExamIllegalStatusTransition(err_msg)

    # OK, state transition is fine, we can proceed
    exam_attempt_obj.status = to_status

    # if we have transitioned to started and haven't set our
    # started_at timestamp and calculate allowed minutes, do so now
    add_start_time = (
        to_status == OfflineExamStudentAttemptStatus.started and
        not exam_attempt_obj.started_at
    )
    if add_start_time:
        exam_attempt_obj.started_at = datetime.now(pytz.UTC)
    elif to_status == OfflineExamStudentAttemptStatus.timed_out:
        exam_attempt_obj.completed_at = timeout_timestamp
    elif to_status == OfflineExamStudentAttemptStatus.submitted:
        # likewise, when we transition to submitted mark
        # when the exam has been completed
        exam_attempt_obj.completed_at = datetime.now(pytz.UTC)

    exam_attempt_obj.save()

    return exam_attempt_obj


def remove_exam_attempt(attempt_id, requesting_user):
    """
    Removes an exam attempt given the attempt id. requesting_user is passed through to the instructor_service.
    """

    log_msg = (
        u'Removing exam attempt {attempt_id}'.format(attempt_id=attempt_id)
    )
    log.info(log_msg)

    existing_attempt = OfflineExamStudentAttempt.objects.get_exam_attempt_by_id(attempt_id)
    if not existing_attempt:
        err_msg = (
            u'Cannot remove attempt for attempt_id = {attempt_id} '
            u'because it does not exist!'
        ).format(attempt_id=attempt_id)

        raise StudentExamAttemptDoesNotExistsException(err_msg)

    existing_attempt.delete_exam_attempt()


def get_all_exam_attempts(course_id):
    """
    Returns all the exam attempts for the course id.
    """
    return OfflineExamStudentAttempt.objects.get_all_exam_attempts(course_id)


def get_filtered_exam_attempts(course_id, search_by):
    """
    Returns all exam attempts for a course id filtered by  the search_by string in user names and emails.
    """
    return OfflineExamStudentAttempt.objects.get_filtered_exam_attempts(course_id, search_by)


def get_last_exam_completion_date(course_id, username):
    """
    Return the completion date of last proctoring exam for the given course and username if
    all the proctored exams are attempted and completed otherwise None
    """
    exam_attempts = OfflineExamStudentAttempt.objects.get_proctored_exam_attempts(course_id, username)

    # Last proctored exam will be at first index, because attempts are sorted descending on completed_at
    return exam_attempts[0].completed_at if exam_attempts else None


STATUS_SUMMARY_MAP = {
    '_default': {
        'short_description': ugettext_noop('Taking As Offline Exam'),
        'suggested_icon': 'fa-clock-o',
        'in_completed_state': False
    },
    OfflineExamStudentAttemptStatus.submitted: {
        'short_description': ugettext_noop('Offline exam completed'),
        'suggested_icon': 'fa-spinner fa-spin',
        'in_completed_state': True
    },
    OfflineExamStudentAttemptStatus.expired: {
        'short_description': ugettext_noop('Offline Option No Longer Available'),
        'suggested_icon': 'fa-times-circle',
        'in_completed_state': False
    }
}


def get_attempt_status_summary(user_id, course_id):
    """
    Returns a summary about the status of the attempt for the user
    in the course_id

    If the exam is timed exam only then we simply
    return the dictionary with timed exam default summary

    Return will be:
    None: Not applicable
    - or -
    {
        'status': ['eligible', 'declined', 'submitted', 'verified', 'rejected'],
        'short_description': <short description of status>,
        'suggested_icon': <recommended font-awesome icon to use>,
        'in_completed_state': <if the status is considered in a 'completed' state>
    }
    """

    exam = TimedExam.get_obj_by_course_id(course_id)
    if not exam:
        # this really shouldn't happen, but log it at least
        log.exception(
            u'Cannot find the proctored exam in this course %s',
            course_id
        )
        return None

    attempt = get_exam_attempt(exam.id, user_id)
    if attempt:
        status = attempt.status

    status_map = STATUS_SUMMARY_MAP

    summary = {}
    if status in status_map:
        summary.update(status_map[status])
    else:
        summary.update(status_map['_default'])

    # Note: translate the short description as it was stored unlocalized
    summary.update({
        'status': status,
        'short_description': _(summary['short_description'])  # pylint: disable=translation-of-non-string
    })

    return summary


def _does_time_remain(attempt):
    """
    Helper function returns True if time remains for an attempt and False
    otherwise. Called from _get_offline_exam_view()
    """
    does_time_remain = False
    has_started_exam = (
        attempt and
        attempt.started_at and
        OfflineExamStudentAttemptStatus.is_incomplete_status(attempt.status)
    )
    if has_started_exam:
        expires_at = attempt.started_at + timedelta(minutes=attempt.timed_exam.allowed_time_limit_mins)
        does_time_remain = datetime.now(pytz.UTC) < expires_at
    return does_time_remain


def _calculate_allowed_mins(exam, user_id):
    """
    Returns the allowed minutes w.r.t due date
    """
    due_datetime = exam.due_date
    allowed_time_limit_mins = exam.allowed_time_limit_mins

    if due_datetime:
        current_datetime = datetime.now(pytz.UTC)
        if current_datetime + timedelta(minutes=allowed_time_limit_mins) > due_datetime:
            # e.g current_datetime=09:00, due_datetime=10:00 and allowed_mins=120(2hours)
            # then allowed_mins should be 60(1hour)
            allowed_time_limit_mins = max(int((due_datetime - current_datetime).total_seconds() / 60), 0)

    return allowed_time_limit_mins


# pylint: disable=inconsistent-return-statements
def get_offline_exam_view(exam, user_id):
    """
    Returns a rendered view for the Offline Exams
    """
    course_id = exam.key
    student_view_template = None
    context = {}
    attempt = get_exam_attempt(exam.id, user_id)
    has_time_expired = False
    entered_exam_room = False

    attempt_status = attempt.status if attempt else None
    if not attempt_status:
        if is_exam_passed_due(exam):
            student_view_template = 'offline_exam/expired.html'
        else:
            attempt = create_exam_attempt(exam, user_id)
            student_view_template = 'offline_exam/instructions.html'
    elif attempt_status == OfflineExamStudentAttemptStatus.created:
        student_view_template = 'offline_exam/instructions.html'
    elif attempt_status == OfflineExamStudentAttemptStatus.ready_to_start or attempt_status == OfflineExamStudentAttemptStatus.started:
        student_view_template = 'offline_exam/exam.html'
        entered_exam_room = True
    elif attempt_status == OfflineExamStudentAttemptStatus.submitted:
        student_view_template = 'offline_exam/submitted.html'

        current_datetime = datetime.now(pytz.UTC)
        start_time = attempt.started_at
        end_time = attempt.completed_at
        attempt_duration_sec = (end_time - start_time).total_seconds()
        allowed_duration_sec = exam.allowed_time_limit_mins * 60
        since_exam_ended_sec = (current_datetime - end_time).total_seconds()

        # if the user took >= the available time, then the exam must have expired.
        # but we show expiry message only when the exam was taken recently (less than SHOW_EXPIRY_MESSAGE_DURATION)
        if attempt_duration_sec >= allowed_duration_sec and since_exam_ended_sec < SHOW_EXPIRY_MESSAGE_DURATION:
            has_time_expired = True

    allowed_time_limit_mins = _calculate_allowed_mins(exam, user_id)

    total_time = humanized_time(allowed_time_limit_mins)

    context.update({
        'exam': exam,
        'attempt': attempt,
        'total_time': total_time,
        'does_time_remain': _does_time_remain(attempt),
        'has_time_expired': has_time_expired,
        'enter_exam_endpoint': reverse('offline_exam:enter_exam', args=(course_id, )),
        'attempt_status_endpoint': reverse('offline_exam:attempt_status', args=(course_id, )),
        'course_id': course_id,
    })
    return entered_exam_room, student_view_template, context

