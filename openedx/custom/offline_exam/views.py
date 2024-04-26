# -*- coding: UTF-8 -*-
"""
Offline exam views.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from edxmako.shortcuts import render_to_response
from student.models import CourseEnrollment
from openedx.custom.timed_exam.models import TimedExam, TimedExamAlarmConfiguration
from openedx.custom.timed_exam.helpers import get_assigned_problems
from openedx.custom.offline_exam.api import (
    get_offline_exam_view,
    get_exam_attempt,
    update_attempt_status,
)
from openedx.custom.offline_exam.utils import get_time_remaining_for_attempt
from openedx.custom.offline_exam.exceptions import OfflineExamIllegalStatusTransition

log = logging.getLogger(__name__)


@login_required
@ensure_csrf_cookie
def enter_exam(request, course_id):
    user = request.user

    # get the course key
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    # get the exam
    exam = get_object_or_404(TimedExam, key=course_id)

    # check if the user is enrolled
    if not CourseEnrollment.is_enrolled(user, course_key):
        return HttpResponseForbidden("You are not enrolled to the exam")

    # get context and template based on attempt status
    entered_exam_room, template_name, context = get_offline_exam_view(exam, user.id)

    # add questions to context if needed
    if entered_exam_room:
        context.update({
            'disable_support_chat': True,
            'problems': get_assigned_problems(request, user.id, course_key),
        })

    # render the page
    return render_to_response(template_name, context)


@login_required
@ensure_csrf_cookie
@require_POST
def attempt_status(request, course_id):
    user = request.user

    # get the course key
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest("Invalid exam id")

    # get the exam
    exam = get_object_or_404(TimedExam, key=course_id)

    # check if the user is enrolled
    if not CourseEnrollment.is_enrolled(user, course_key):
        return HttpResponseForbidden("You are not enrolled to the exam")

    # get attempt
    attempt = get_exam_attempt(exam.id, user.id)
    if not attempt:
        return HttpResponseBadRequest("Attempt not found")

    # get and validate the status
    status = request.POST.get('status')
    if not status:
        return HttpResponseBadRequest("Invalid status")

    # update status
    try:
        update_attempt_status(attempt, status)
    except OfflineExamIllegalStatusTransition as e:
        return HttpResponseBadRequest("Invalid status")

    # return JSON response
    return JsonResponse({
        'success': 1,
        'time_remaining_seconds': get_time_remaining_for_attempt(attempt),
        'alarms': [
            minutes * 60
            for minutes in TimedExamAlarmConfiguration.objects.filter(
                is_active=True
            ).values_list('alarm_time', flat=True)
        ],
    })
