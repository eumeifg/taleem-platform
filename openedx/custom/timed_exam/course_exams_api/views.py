"""
Daily exam APIs.
"""

import logging
from six import text_type

from django.conf import settings
from django.http import Http404
from rest_framework import permissions
from rest_framework.views import APIView

from util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from lms.djangoapps.courseware.module_render import get_module_by_usage_id
from student.models import CourseEnrollment
from course_modes.models import CourseMode
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.custom.timed_exam.course_exams_api.utils import (
    check_course_access,
    get_course_exams_for_user,
    get_problem_json,
    get_review_status,
    get_total_number_of_question_in_exam,
    is_valid_question_type,
    start_exam_for_user,
    submit_exam_for_user,
)
from openedx.custom.timed_exam.utils import (
    get_attempted_at,
    get_timed_exam_attempt,
    is_user_attempted_exam,
)
from openedx.custom.timed_exam.helpers import get_assigned_problems
from openedx.custom.timed_exam.models import TimedExam

log = logging.getLogger(__name__)


class CourseExamsApiView(APIView):
    """
    WARNING: DEPRECATED, use MyExamListView instead
    Compatible app version 1.1.5

    **Use Cases**
    Retrieve all the exams for a course.

    **Example Requests**

        GET /courses/{course_id}/exams_list

    **GET Course Exams Parameters**:

        * course_id (required): The course to retrieve the exams for.

    """
    authentication_classes = (JwtAuthentication, BearerAuthenticationAllowInactiveUser,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, course_id):
        """
        Implement a handler for the GET method.
        """
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise Http404("Invalid location")

        # Checking the access of the user for the course
        check_course_access(request, course_key)
        # Getting the exams from the course that a requesting user can access
        course_exams = get_course_exams_for_user(request, course_key)

        exams = []

        for exam in course_exams:
            exam_key = CourseKey.from_string(exam.key)
            attempted = is_user_attempted_exam(request.user, exam)
            attempted_at = ''
            if attempted:
                attempted_at = get_attempted_at(exam_key, request.user)
            hh, mm = exam.allotted_time.split(":")
            obj = {
                "key": str(exam.key),
                "display_name": exam.display_name,
                "duration": int(hh) * 60 + int(mm),
                "due_date": exam.due_date,
                "release_date": exam.release_date,
                "mode": exam.mode,
                "attempted": True if attempted else False,
                "attempted_on": attempted_at,
                "total_questions": get_total_number_of_question_in_exam(exam_key)
            }

            exams.append(obj)

        return JsonResponse({
            "exams": exams
        })


class CourseExamsQuestionsApiView(APIView):
    """
    **Use Cases**
    Retrieve all questions of exam from a course.

    **Example Requests**

        GET /courses/exams/{exam_id}/questions

    **GET Course Exams Questions Parameters**:

        * course_id (required): The exam to retrieve the questions for.
    """
    authentication_classes = (JwtAuthentication, BearerAuthenticationAllowInactiveUser,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, course_id):
        """
        Implement a handler for the GET method.
        """
        user = request.user

        try:
            exam_key = CourseKey.from_string(course_id)
            exam = TimedExam.objects.get(key=exam_key)
        except InvalidKeyError:
            raise Http404("Invalid location")

        if exam.exam_type == TimedExam.PUBLIC:
            if not CourseEnrollment.objects.filter(
                course_id=exam_key,
                user=user,
                is_active=1,
                mode=CourseMode.TIMED,
            ).exists():
                CourseEnrollment.enroll(user, exam_key,
                    mode=CourseMode.TIMED)

        # Assigned questions
        questions = [
            text_type(question.location)
            for question in get_assigned_problems(
                request, user.id, exam_key, shallow=True
            )
            if is_valid_question_type(question)
        ]

        return JsonResponse({
            "key": course_id,
            "questions": questions,
            "time_remaining_seconds": start_exam_for_user(exam_key, user),
        })


class ExamReviewStatusApiView(APIView):
    """
    **Use Cases**
    Retrieve the review status of the exam.

    **Example Requests**

        GET /courses/exams/{exam_id}/review

    **GET Course Exams Questions Parameters**:

        * course_id (required): The exam to retrieve the questions for.
    """
    authentication_classes = (JwtAuthentication, BearerAuthenticationAllowInactiveUser,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, course_id):
        """
        Implement a handler for the GET method.
        """
        try:
            exam_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise Http404("Invalid location")

        is_attempt_available, timed_out = submit_exam_for_user(
            exam_key, request.user)

        if not is_attempt_available:
            return JsonResponse({
                "message": "User doesn't have any exam attempt"
            }, status=404)

        status = get_review_status(course_id, request.user)
        status['show_popup'] = timed_out
        return JsonResponse(status)


class ExamQuestionJsonView(APIView):
    """
    **Use Cases**
    Retrieve the json for the question of exam.

    **Example Requests**

        GET /courses/exams/{exam_id}/question/{block_usage_key}/json
    """
    authentication_classes = (JwtAuthentication, BearerAuthenticationAllowInactiveUser,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, course_id, usage_id):
        """
        Implement a handler for the GET method.
        """

        if not settings.FEATURES.get('ENABLE_XBLOCK_VIEW_ENDPOINT', False):
            log.warning("Attempt to use deactivated XBlock view endpoint -"
                        " see FEATURES['ENABLE_XBLOCK_VIEW_ENDPOINT']")
            raise Http404

        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise Http404("Invalid location")

        with modulestore().bulk_operations(course_key):
            course = modulestore().get_course(course_key)
            instance, _ = get_module_by_usage_id(request, course_id, usage_id, course=course)

        if not is_valid_question_type(instance):
            return JsonResponse({
                "message": "Problem type not supported."
            })

        question_json = get_problem_json(instance, text_type(course_key))

        if "error" in question_json.keys():
            return JsonResponse(question_json, status=400)

        return JsonResponse(question_json)


class ExamReviewReportApiView(APIView):
    """
        **Use Cases**
        Retrieve the data of the exam report.

        **Example Requests**

            GET /courses/exams/{exam_id}/report
        """
    authentication_classes = (JwtAuthentication, BearerAuthenticationAllowInactiveUser,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, course_id):
        """
        Implement a handler for the GET method.
        """
        user = request.user
        try:
            exam_key = CourseKey.from_string(course_id)
            course = modulestore().get_course(exam_key)
        except InvalidKeyError:
            raise Http404("Invalid location")

        # Assigned questions
        questions = []
        for question in get_assigned_problems(
            request, user.id, exam_key
        ):
            question_json = get_problem_json(
                question,
                text_type(exam_key),
                for_report=True
            )
            if "error" in question_json.keys():
                log.error("Error while getting report for problem:{}".format(
                    text_type(question.location)
                ))
            questions.append(question_json)

        attempt = get_timed_exam_attempt(exam_key, user)
        attempted_at = attempt and get_attempted_at(exam_key, request.user) or ''

        return JsonResponse({
            "questions": questions,
            "exam_key": text_type(exam_key),
            "exam_name": course.display_name,
            "attempted_on": attempted_at,
        }, status=200)
