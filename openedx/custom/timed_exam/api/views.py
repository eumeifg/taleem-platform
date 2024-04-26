# -*- coding: UTF-8 -*-
"""
API end-points for the ebooks.
"""


import logging
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.authentication import SessionAuthentication

import edx_api_doc_tools as apidocs
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from course_modes.models import CourseMode
from student.models import CourseEnrollment
from openedx.custom.timed_exam.models import TimedExam, ExamTimedOutNotice
from edx_proctoring.models import ProctoredExamStudentAttempt
from edx_proctoring.statuses import ProctoredExamStudentAttemptStatus
from edx_proctoring.utils import get_time_remaining_for_attempt
from openedx.custom.utils import utc_datetime_to_local_datetime

from .serializers import ExamSerializer

log = logging.getLogger(__name__)
EXAM_STATUS = ('upcoming', 'ongoing', 'passed', )


class ExamPagination(DefaultPagination):
    """
    Paginator for exams API.
    """
    page_size = 10
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        response = super(ExamPagination, self).get_paginated_response(data)

        # Add `current_page` value, it's needed for pagination footer.
        response.data["current_page"] = self.page.number

        # Add `start` value, it's needed for the pagination header.
        response.data["start"] = (self.page.number - 1) * self.get_page_size(self.request)

        return response


@view_auth_classes(is_authenticated=True)
class MyExamListView(ListAPIView):
    """This endpoint list all of the enrolled exams for logged-in user"""
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthentication,
    )
    pagination_class = ExamPagination
    serializer_class = ExamSerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'status',
                apidocs.ParameterLocation.QUERY,
                description="The exam status to limit the list. upcoming, ongoing or passed.",
            ),
            apidocs.string_parameter(
                'course_id',
                apidocs.ParameterLocation.QUERY,
                description="The ID of the course, to limit the exams added in specific course.",
            ),
            apidocs.string_parameter(
                'exclude_older_than',
                apidocs.ParameterLocation.QUERY,
                description="The number of days, to exclude the exams older than given days.",
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        **Use Cases**

            Request to get exams for the logged-in user.

       **Example Requests**

           GET /api/exams/

        **Response Values**

           Body comprises a list of objects containing information about the exam.

        **Parameters**

            status (optional):
                If specified, filters exams by status. Status can be one
                of the `upcoming`, `ongoing' or `passed`.
                `upcoming` is default.

            course_id (optional):
                If specified, returns exams added to the given course.
                By default it returns all exams.

            exclude_older_than (optional):
                If specified, excludes the exams with due date older than the given days.
                By default 7 days if the course_id param is applied else it won't exclude.

        **Returns**

            * 200 on success, with a list of exams objects.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                      "key": "course-v1:Taleem+00b2eba1c8b041c+2021T1",
                      "display_name": "Example Course",
                      "duration": 60, # (minutes)
                      "release_date": "2021-08-20T15:53:31.231353+03:00",
                      "due_date": "2021-08-22T15:53:31.231353+03:00",
                      "mode": "Online/Offline",
                      "attempted": true/false,
                      "attempted_on": "2021-08-20T15:53:31.231353+03:00",
                      "total_questions": 20,
                      "tag": "completed"
                  }
                ]
        """
        # Get query param, assume `upcoming` by default
        status = request.query_params.get('status')
        if status and status not in EXAM_STATUS:
            return JsonResponse({'error': 'Invalid status'}, status=400)

        return super(MyExamListView, self).get(request, *args, **kwargs)

    def get_serializer_context(self):
        """
        Return the context for the serializer.
        """
        context = super(MyExamListView, self).get_serializer_context()
        if self.request.method == 'GET':
            user = self.request.user
            # Mark the dangling attempts
            for attempt in ProctoredExamStudentAttempt.objects.filter(
                user=user,
                status=ProctoredExamStudentAttemptStatus.started,
            ):
                remaining_time = get_time_remaining_for_attempt({
                    'started_at': attempt.started_at,
                    'allowed_time_limit_mins': attempt.allowed_time_limit_mins,
                })
                if not remaining_time:
                    ExamTimedOutNotice.add_notice(
                        str(attempt.proctored_exam.course_id),
                        user.id,
                    )
                    attempt.status = 'submitted'
                    attempt.completed_at = attempt.started_at + timedelta(
                        minutes=attempt.allowed_time_limit_mins
                    )
                    attempt.save()
            context.update({
                'requested_status': self.request.query_params.get('status'),
                'attempts': {
                    str(attempt.proctored_exam.course_id): \
                    utc_datetime_to_local_datetime(attempt.completed_at).isoformat()
                    for attempt in ProctoredExamStudentAttempt.objects.filter(
                        user=user,
                        status=ProctoredExamStudentAttemptStatus.submitted,
                    )
                },
                'dangling': ExamTimedOutNotice.exams_with_notice(user.id),
            })
        return context

    def get_queryset(self):
        """
        Returns queryset of my exams for GET requests.
        """
        status = self.request.query_params.get('status')
        course_id = self.request.query_params.get('course_id')
        exclude_older_than = self.request.query_params.get('exclude_older_than')
        if exclude_older_than:
            try:
                exclude_older_than = int(exclude_older_than)
            except Exception as e:
                exclude_older_than = None

        course_exams = []
        if course_id:
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
                return TimedExam.objects.none()

            # Default when course_id specified
            exclude_older_than = exclude_older_than or 7

            course_exams = [
                course_exam.exam_id
                for course_exam in modulestore().get_items(
                    course_key,
                    qualifiers={'category': 'exams'}
                )
                if course_exam.exam_id
            ]

        # Enrollment queryset
        enrolled_exams = CourseEnrollment.objects.filter(
            user=self.request.user,
            is_active=1,
            mode=CourseMode.TIMED,
        )
        if course_id:
            enrolled_exams = enrolled_exams.filter(course_id__in=course_exams)

        # Get the enrolled exam keys
        enrolled_keys = set(
            map(
                str,
                enrolled_exams.values_list('course_id', flat=True)
            )
        )

        # default queryset
        exams = TimedExam.objects.filter(
            key__in=enrolled_keys,
            mode=TimedExam.ONLINE,
        )
        if exclude_older_than:
            exams = exams.exclude(
                due_date__lt=timezone.now()-timedelta(days=exclude_older_than)
            )

        if status == 'upcoming':
            return exams.filter(release_date__gt=timezone.now(),)
        elif status == 'ongoing':
            attempted_exams = self.get_serializer_context(
                ).get('attempts').keys()
            return exams.filter(
                release_date__lt=timezone.now(),
                due_date__gt=timezone.now(),
            ).exclude(key__in=attempted_exams)
        elif status == 'passed':
            attempted_exams = self.get_serializer_context(
                ).get('attempts').keys()
            return exams.filter(
                Q(key__in=attempted_exams) | Q(due_date__lt=timezone.now())
            )

        return exams


@view_auth_classes(is_authenticated=True)
class ExamTimedOutNoticeApiView(APIView):
    """

    **Use Cases**
    Delete exam timed out notice.

    **Example Requests**

        DELETE /api/exams/{exam_key}/remove/timedout/notice/

    **Response**:

        * success (bool): if the operation was successfull.
        * error (string): error message if any

        {
            "success": true,
            "error": ""
        }

    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthentication,
    )

    def delete(self, request, exam_key):
        """
        Implement a handler for the DELETE method.
        """
        user = request.user
        success = True
        error = ''

        if ExamTimedOutNotice.has_notice(exam_key, user.id):
            ExamTimedOutNotice.remove_notice(exam_key, user.id)
        else:
            success = False
            error = "Notice not found"

        return JsonResponse({
            "success": success,
            "error": error,
        })


@view_auth_classes(is_authenticated=True)
class PublicExamListView(ListAPIView):
    """This endpoint list all of the public exams for logged-in user"""
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthentication,
    )
    pagination_class = ExamPagination
    serializer_class = ExamSerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'status',
                apidocs.ParameterLocation.QUERY,
                description="The exam status to limit the list. upcoming, ongoing or passed.",
            ),
            apidocs.string_parameter(
                'exclude_older_than',
                apidocs.ParameterLocation.QUERY,
                description="The number of days, to exclude the exams older than given days.",
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        **Use Cases**

            Request to get public exams for the logged-in user.

       **Example Requests**

           GET /api/exams/public/

        **Response Values**

           Body comprises a list of objects containing information about the exam.

        **Parameters**

            status (optional):
                If specified, filters exams by status. Status can be one
                of the `upcoming`, `ongoing' or `passed`.
                `upcoming` is default.

            exclude_older_than (optional):
                If specified, excludes the exams with due date older than the given days.
                By default 7 days if the course_id param is applied else it won't exclude.

        **Returns**

            * 200 on success, with a list of exams objects.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                      "key": "course-v1:Taleem+00b2eba1c8b041c+2021T1",
                      "display_name": "Example Course",
                      "duration": 60, # (minutes)
                      "release_date": "2021-08-20T15:53:31.231353+03:00",
                      "due_date": "2021-08-22T15:53:31.231353+03:00",
                      "mode": "Online/Offline",
                      "attempted": true/false,
                      "attempted_on": "2021-08-20T15:53:31.231353+03:00",
                      "total_questions": 20,
                      "tag": "completed"
                  }
                ]
        """
        # Get query param, assume `upcoming` by default
        status = request.query_params.get('status')
        if status and status not in EXAM_STATUS:
            return JsonResponse({'error': 'Invalid status'}, status=400)

        return super(PublicExamListView, self).get(request, *args, **kwargs)

    def get_serializer_context(self):
        """
        Return the context for the serializer.
        """
        context = super(PublicExamListView, self).get_serializer_context()
        if self.request.method == 'GET':
            user = self.request.user
            # Mark the dangling attempts
            for attempt in ProctoredExamStudentAttempt.objects.filter(
                user=user,
                status=ProctoredExamStudentAttemptStatus.started,
            ):
                remaining_time = get_time_remaining_for_attempt({
                    'started_at': attempt.started_at,
                    'allowed_time_limit_mins': attempt.allowed_time_limit_mins,
                })
                if not remaining_time:
                    ExamTimedOutNotice.add_notice(
                        str(attempt.proctored_exam.course_id),
                        user.id,
                    )
                    attempt.status = 'submitted'
                    attempt.completed_at = attempt.started_at + timedelta(
                        minutes=attempt.allowed_time_limit_mins
                    )
                    attempt.save()
            context.update({
                'requested_status': self.request.query_params.get('status'),
                'attempts': {
                    str(attempt.proctored_exam.course_id): \
                    utc_datetime_to_local_datetime(attempt.completed_at).isoformat()
                    for attempt in ProctoredExamStudentAttempt.objects.filter(
                        user=user,
                        status=ProctoredExamStudentAttemptStatus.submitted,
                    )
                },
                'dangling': ExamTimedOutNotice.exams_with_notice(user.id),
            })
        return context

    def get_queryset(self):
        """
        Returns queryset of public exams for GET requests.
        """
        status = self.request.query_params.get('status')
        exclude_older_than = self.request.query_params.get('exclude_older_than')
        if exclude_older_than:
            try:
                exclude_older_than = int(exclude_older_than)
            except Exception as e:
                exclude_older_than = None

        # default queryset
        exams = TimedExam.objects.filter(
            mode=TimedExam.ONLINE,
            exam_type=TimedExam.PUBLIC,
        )
        if exclude_older_than:
            exams = exams.exclude(
                due_date__lt=timezone.now()-timedelta(days=exclude_older_than)
            )

        if status == 'upcoming':
            return exams.filter(release_date__gt=timezone.now(),)
        elif status == 'ongoing':
            attempted_exams = self.get_serializer_context(
                ).get('attempts').keys()
            return exams.filter(
                release_date__lt=timezone.now(),
                due_date__gt=timezone.now(),
            ).exclude(key__in=attempted_exams)
        elif status == 'passed':
            attempted_exams = self.get_serializer_context(
                ).get('attempts').keys()
            return exams.filter(
                Q(key__in=attempted_exams) | Q(due_date__lt=timezone.now())
            )

        return exams
