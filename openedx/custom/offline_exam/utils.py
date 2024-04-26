"""
Helpers for the HTTP APIs
"""

from __future__ import absolute_import

import logging
from datetime import datetime, timedelta

import pytz
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from django.utils.translation import ugettext as _

from openedx.custom.offline_exam.models import OfflineExamStudentAttempt
from openedx.custom.offline_exam.statuses import OfflineExamStudentAttemptStatus

log = logging.getLogger(__name__)


class AuthenticatedAPIView(APIView):
    """
    Authenticate APi View.
    """
    authentication_classes = (SessionAuthentication, JwtAuthentication)
    permission_classes = (IsAuthenticated,)


def get_time_remaining_for_attempt(attempt):
    """
    Returns the remaining time (in seconds) on an attempt
    """

    # returns 0 if the attempt has not been started yet.
    if attempt.started_at is None:
        return 0

    # need to adjust for allowances
    expires_at = attempt.started_at + timedelta(minutes=attempt.timed_exam.allowed_time_limit_mins)
    now_utc = datetime.now(pytz.UTC)

    if expires_at > now_utc:
        time_remaining_seconds = (expires_at - now_utc).total_seconds()
    else:
        time_remaining_seconds = 0

    return time_remaining_seconds


def humanized_time(time_in_minutes):
    """
    Converts the given value in minutes to a more human readable format
    1 -> 1 Minute
    2 -> 2 Minutes
    60 -> 1 hour
    90 -> 1 hour and 30 Minutes
    120 -> 2 hours
    """
    hours = int(time_in_minutes / 60)
    minutes = time_in_minutes % 60

    hours_present = False
    if hours == 0:
        hours_present = False
        template = ""
    elif hours == 1:
        template = _(u"{num_of_hours} hour")
        hours_present = True
    elif hours >= 2:
        template = _(u"{num_of_hours} hours")
        hours_present = True
    else:
        template = "error"

    if template != "error":
        if minutes == 0:
            if not hours_present:
                template = _(u"{num_of_minutes} minutes")
        elif minutes == 1:
            if hours_present:
                template += _(u" and {num_of_minutes} minute")
            else:
                template += _(u"{num_of_minutes} minute")
        else:
            if hours_present:
                template += _(u" and {num_of_minutes} minutes")
            else:
                template += _(u"{num_of_minutes} minutes")

    human_time = template.format(num_of_hours=hours, num_of_minutes=minutes)
    return human_time


def locate_attempt_by_attempt_code(attempt_code):
    """
    Helper method to look up an attempt by attempt_code. This can be either in
    the OfflineExamStudentAttempt table
    we will return a tuple of (attempt, is_archived_attempt)
    """
    attempt_obj = OfflineExamStudentAttempt.objects.get_exam_attempt_by_code(attempt_code)

    if not attempt_obj:
        err_msg = (
            u'Could not locate attempt_code: {attempt_code}'.format(attempt_code=attempt_code)
        )
        log.error(err_msg)
    return attempt_obj


def has_due_date_passed(due_datetime):
    """
    Return True if due date is lesser than current datetime, otherwise False
    and if due_datetime is None then we don't have to consider the due date for return False
    """

    if due_datetime:
        return due_datetime <= datetime.now(pytz.UTC)
    return False


def is_reattempting_exam(from_status, to_status):
    """
    Returns a boolean representing whether or not a user is trying to reattempt an exam.

    Given user's exam is in progress, and he is kicked out due to low bandwidth or
    closes the secure browser. Its expected that the user should not be able to restart
    the exam workflow.
    This behavior is being implemented due to edX's integrity constraints.
    """
    return (
        OfflineExamStudentAttemptStatus.is_in_progress_status(from_status) and
        OfflineExamStudentAttemptStatus.is_pre_started_status(to_status)
    )

