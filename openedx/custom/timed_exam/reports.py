# -*- coding: UTF-8 -*-
"""
Timed exam reports.
"""
import pytz
import logging
from collections import OrderedDict
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext as _

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.access import has_access
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.taleem.models import UserType
from openedx.custom.taleem_grades.models import PersistentExamGrade
from openedx.custom.timed_exam.models import TimedExam
from openedx.custom.utils import timedelta_to_hhmmss
from student.roles import CourseStaffRole
from edx_proctoring.models import (
    ProctoredExamStudentAttempt,
    ProctoredExamSessionConnectionHistory,
    ProctoredExamTabSwitchHistory,
    ProctoredExamWebMonitoringHistory,
    ProctoredExamReview,
)

from .helpers import get_problem_scores


log = logging.getLogger(__name__)


def proctoring_report_context(course_id, student_id, user):
    # Get the course key
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    # Only admin and allowed teacher can access the reports
    is_teacher = user.ta3leem_profile.user_type == UserType.teacher.name
    if not any((
        user.is_superuser,
        has_access(user, CourseStaffRole.ROLE, course_key),
        is_teacher and user.ta3leem_profile.can_create_exam,
    )):
        return HttpResponseForbidden()

    # Get the course
    course = get_object_or_404(CourseOverview, id=course_key)

    # Get the student
    try:
        student = User.objects.get(id=student_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()


    # Get the student attempt for the exam
    attempt = get_object_or_404(
        ProctoredExamStudentAttempt,
        proctored_exam__course_id=course_key,
        user=student,
    )

    timestamp = datetime.now(pytz.UTC)
    due_date_passed = course.end <= timestamp

    # elapsed_time: incident
    incidents = {}
    abnormalities = []

    # Attempt start/end time
    started_at = attempt.started_at
    completed_at = attempt.completed_at

    # Session incidents
    session_history_qs = ProctoredExamSessionConnectionHistory.objects.filter(
        course_id=course_id,
        user=student,
    ).order_by('started_at')
    prev_session = None
    for session_history in session_history_qs:
        incidents.update({
            timedelta_to_hhmmss(session_history.last_echo - started_at): \
            _("Session was disconnected.")
        })
        if prev_session:
            away_seconds = int((session_history.started_at - prev_session.last_echo).total_seconds())
            for second in range(away_seconds):
                abnormalities.append(
                    timedelta_to_hhmmss(prev_session.last_echo + timedelta(seconds=second) - started_at)
                )
        prev_session = session_history
    # Check abnormalities till submission time
    if prev_session:
        away_seconds = int((completed_at - prev_session.last_echo).total_seconds())
        for second in range(away_seconds):
            abnormalities.append(
                timedelta_to_hhmmss(prev_session.last_echo + timedelta(seconds=second) - started_at)
            )


    # Tab switch incidents
    tab_history_qs = ProctoredExamTabSwitchHistory.objects.filter(
        course_id=course_id,
        user=student,
    ).order_by('event_datetime')
    prev_out = None
    for tab_history in tab_history_qs:
        if tab_history.event_type == 'out':
            incidents.update({
                timedelta_to_hhmmss(tab_history.event_datetime - started_at): \
                _("User had switched to another tab.")
            })
            prev_out = tab_history
            continue
        if prev_out:
            away_seconds = int((tab_history.event_datetime - prev_out.event_datetime).total_seconds())
            for second in range(away_seconds):
                abnormalities.append(
                    timedelta_to_hhmmss(prev_out.event_datetime + timedelta(seconds=second) - started_at)
                )
    # Check abnormalities till submission time
    if prev_out:
        away_seconds = int((completed_at - prev_out.event_datetime).total_seconds())
        for second in range(away_seconds):
            abnormalities.append(
                timedelta_to_hhmmss(prev_out.event_datetime + timedelta(seconds=second) - started_at)
            )

    # Webcam incidents
    webcam_history_qs = ProctoredExamWebMonitoringHistory.objects.filter(
        proctored_exam_snapshot__course_id=course_id,
        proctored_exam_snapshot__user=student,
    ).order_by('proctored_exam_snapshot__created')
    prev_failed = None
    for webcam_history in webcam_history_qs:
        if webcam_history.status != ProctoredExamWebMonitoringHistory.FACE_FOUND:
            if webcam_history.status in [
                ProctoredExamWebMonitoringHistory.MULTIPLE_FACE_FOUND,
                ProctoredExamWebMonitoringHistory.MULTIPLE_PEOPLE_FOUND,
            ]:
                incident_warning = _("Multiple faces detected.")
            elif webcam_history.status == ProctoredExamWebMonitoringHistory.UNKNOWN_FACE:
                incident_warning = _("Unknown face detected.")
            else:
                incident_warning = _("Face not detected.")
            incident_time_elapsed = timedelta_to_hhmmss(
                webcam_history.proctored_exam_snapshot.created - started_at
            )
            incidents.update({incident_time_elapsed: incident_warning})
            if not prev_failed:
                prev_failed = webcam_history
            continue
        if prev_failed:
            away_seconds = int((
                webcam_history.proctored_exam_snapshot.created - prev_failed.proctored_exam_snapshot.created
            ).total_seconds())
            for second in range(away_seconds):
                abnormalities.append(timedelta_to_hhmmss(
                    prev_failed.proctored_exam_snapshot.created + timedelta(seconds=second) - started_at
                ))
            prev_failed = None
    # Check abnormalities till submission time
    if prev_failed:
        away_seconds = int((
            completed_at - prev_failed.proctored_exam_snapshot.created
        ).total_seconds())
        for second in range(away_seconds):
            abnormalities.append(timedelta_to_hhmmss(
                prev_failed.proctored_exam_snapshot.created + timedelta(seconds=second) - started_at
            ))

    # Timeline chart data
    timeline_x_axis = []
    timeline_y_axis = []
    attempt_duration = int((attempt.completed_at - started_at).total_seconds())
    for second in range(1, attempt_duration + 1):
        elapsed_time = timedelta_to_hhmmss(started_at + timedelta(seconds=second) - started_at)
        timeline_x_axis.append(elapsed_time)
        timeline_y_axis.append({
            "color": "#F6848E" if elapsed_time in abnormalities else "#97D637",
            "y": 0.1,   # 0.1 is fixed, just to show it as column height
        })

    # Exam score
    try:
        score = PersistentExamGrade.objects.get(
            course_id=course_id,
            user_id=student_id,
        ).percent_grade
    except PersistentExamGrade.DoesNotExist:
        score = 0

    return {
        'course': course,
        'is_monitored_timed_exam': TimedExam.is_monitored_timed_exam(course_key),
        'attempt': attempt,
        'score': score,
        'student': student,
        'review_status': ProctoredExamReview.get_review_status(student, course_id),
        'session_history': session_history_qs,
        'tab_history': tab_history_qs,
        'webcam_history': webcam_history_qs,
        'incidents': OrderedDict(sorted(incidents.items())),
        'timeline_x_axis': timeline_x_axis,
        'timeline_y_axis': timeline_y_axis,
        'due_date_passed': due_date_passed,
        'problem_scores': get_problem_scores(student, course_key, started_at),
        'rescore_url': reverse('override_problem_score', kwargs={'course_id': course_id}),
    }


def distribute_scores(sorted_scores):
    less_than_10 = 0
    bet_11_20 = 0
    bet_21_30 = 0
    bet_31_40 = 0
    bet_41_50 = 0
    bet_51_60 = 0
    bet_61_70 = 0
    bet_71_80 = 0
    bet_81_90 = 0
    obove_90 = 0

    for score in sorted_scores:
        if score < 10:
            less_than_10 += 1
        elif score >= 11 and score <= 20:
            bet_11_20 += 1
        elif score >= 21 and score <= 30:
            bet_21_30 += 1
        elif score >= 31 and score <= 40:
            bet_31_40 += 1
        elif score >= 41 and score <= 50:
            bet_41_50 += 1
        elif score >= 51 and score <= 60:
            bet_51_60 += 1
        elif score >= 61 and score <= 70:
            bet_61_70 += 1
        elif score >= 71 and score <= 80:
            bet_71_80 += 1
        elif score >= 81 and score <= 90:
            bet_81_90 += 1
        else:
            obove_90 += 1

    return [
        less_than_10,
        bet_11_20,
        bet_21_30,
        bet_31_40,
        bet_41_50,
        bet_51_60,
        bet_61_70,
        bet_71_80,
        bet_81_90,
        obove_90,
    ]
