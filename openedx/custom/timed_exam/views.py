# -*- coding: UTF-8 -*-
"""
Timed exam views.
"""
import logging
import uuid
from datetime import datetime

import numpy
import pytz
import six
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Count, Q
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.views.generic import View
from edx_proctoring.models import (
    ProctoredExamReview,
    ProctoredExamSessionConnectionHistory,
    ProctoredExamStudentAttempt,
    ProctoredExamTabSwitchHistory,
    ProctoredExamWebMonitoringHistory,
)
from edx_proctoring.statuses import ProctoredExamStudentAttemptStatus
from edx_proctoring.utils import AuthenticatedAPIView
from edxmako.shortcuts import render_to_response, render_to_string
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.response import Response
from scipy import stats
from student.auth import has_course_author_access
from student.models import CourseAccessRole, CourseEnrollment
from student.roles import CourseStaffRole
from util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore

from common.djangoapps.util.json_request import (
    expect_json,
    JsonResponse,
    JsonResponseBadRequest,
)
from lms.djangoapps.courseware.access import has_access
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.question_bank.models import QuestionTags
from openedx.custom.taleem_emails.models import Ta3leemEmail
from openedx.custom.question_bank.utils import get_question_bank
from openedx.custom.taleem.models import Ta3leemUserProfile, UserType
from openedx.custom.taleem_grades.models import PersistentExamGrade
from openedx.custom.taleem_grades.tasks import calculate_exam_grades
from openedx.custom.taleem_organization.models import Skill
from openedx.custom.taleem_search.utils import get_filters_data
from openedx.custom.timed_exam.enrollment import (
    delete_pending_enrollment,
    get_timed_exam_enrollments,
    get_timed_exam_pending_enrollments,
    unenroll_in_timed_exam,
)
from openedx.custom.timed_exam.forms import (
    ProctoredExamSnapshotForm,
    TimedExamAlarmConfigurationForm,
    TimedExamEnrollmentForm,
    TimedExamForm,
)
from openedx.custom.timed_exam.models import (
    TimedExam,
    TimedExamAlarmConfiguration,
    TimedExamExtras,
    TimedExamHide,
)
from openedx.custom.timed_exam.utils import (
    check_read_permission_or_raise,
    check_timed_exam_or_raise,
    check_write_permission_or_raise,
    create_run,
    create_timed_exam_content,
    create_timed_exam_mode,
    delete_timed_exam,
    get_users_verification_status,
    send_pending_enrollment_email,
    update_grading_for_timed_exam,
    update_timed_exam_dates,
)
from openedx.custom.utils import local_datetime_to_utc_datetime
from openedx.custom.xhtml2pdf import pisa
from .helpers import analyze_questions
from .models import PendingTimedExamUser
from .reports import distribute_scores, proctoring_report_context
from .tasks import (
    bulk_re_assign_question_set,
    delete_timed_exam_proctoring_snapshots,
)

log = logging.getLogger(__name__)


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST"))
def timed_exam_handler(request, course_key_string=None):
    """
    RESTful interface to the most of the question bank related functionality.
    """
    from contentstore.views.library import get_timed_exam_creator_status

    timed_exam_key_string = course_key_string

    if request.method == "POST":
        if not get_timed_exam_creator_status(request.user):
            return HttpResponseForbidden()

        if timed_exam_key_string is not None:
            return update_exam_handler(request, timed_exam_key_string)

        return create_exam_handler(request)

    else:
        if timed_exam_key_string:
            return display_timed_exams(request, timed_exam_key_string)

        return list_timed_exams(request)


@expect_json
def create_exam_handler(request):
    """
    Helper method for creating a new question bank.
    """
    form = TimedExamForm(request.json, user_id=request.user.id)
    if form.is_valid():
        question_bank = get_question_bank(form.cleaned_data["question_bank"])
        org = question_bank.location.library_key.org
        course = "{number}".format(number=str(uuid.uuid4()).replace("-", "")[0:15])
        run = create_run()

        utc_release_date = local_datetime_to_utc_datetime(
            form.cleaned_data["timed_exam_release_date"]
        )
        utc_due_date = local_datetime_to_utc_datetime(
            form.cleaned_data["timed_exam_due_date"]
        )
        fields = {
            "start": utc_release_date,
            "end": utc_due_date,
            "display_name": form.cleaned_data["display_name"],
            "wiki_slug": "{0}.{1}.{2}".format(org, course, run),
            "is_timed_exam": True,
        }
        from cms.djangoapps.contentstore.views.course import create_new_course

        new_course = create_new_course(request.user, org, course, run, fields)

        # Create the content of timed exam
        create_timed_exam_content(request, new_course, form.cleaned_data)

        # Change the grading policy for timed exam.
        update_grading_for_timed_exam(
            user=request.user,
            course_key=new_course.id,
        )

        # Create course's Mode
        create_timed_exam_mode(course_key=new_course.id)

    else:
        log.exception("Unable to create library, Errors: \n{}".format(form.errors))
        return JsonResponseBadRequest(
            {
                "ErrMsg": _("Unable to create timed exam."),
                "errors": form.errors,
            }
        )

    return JsonResponse({"url": reverse("home")})


@expect_json
def update_exam_handler(request, timed_exam_key_string):
    """
    Helper method for updating a timed exam.
    """
    timed_exam_key = CourseKey.from_string(timed_exam_key_string)

    # Check has write permission
    check_write_permission_or_raise(request.user, timed_exam_key)

    timed_exam = modulestore().get_course(timed_exam_key, depth=None)

    # Check timed exam exist in mongo and mysql DB.
    check_timed_exam_or_raise(timed_exam, timed_exam_key_string)

    form = TimedExamForm(
        request.json, user_id=request.user.id, timed_exam_key=timed_exam_key_string
    )
    if form.is_valid():
        create_timed_exam_content(request, timed_exam, form_data=form.cleaned_data)
    else:
        log.exception("Unable to create library, Errors: \n{}".format(form.errors))
        return JsonResponseBadRequest(
            {
                "ErrMsg": _("Unable to create timed exam."),
                "errors": form.errors,
            }
        )

    # Update questions set for already enrolled users
    bulk_re_assign_question_set.delay(timed_exam_key_string)

    success_message = _('Timed Exam "{time_exam_name}" updated successfully.')
    messages.add_message(
        request,
        messages.SUCCESS,
        success_message.format(time_exam_name=form.cleaned_data["display_name"]),
    )
    return JsonResponse(
        {
            "url": reverse("timed_exam_handler", args=(timed_exam_key_string,)),
            "course_key": six.text_type(timed_exam_key_string),
        }
    )


def display_timed_exams(request, timed_exam_key_string):
    """
    Displays single question bank
    """
    from openedx.custom.timed_exam.utils import does_timed_exam_has_attempts
    from contentstore.utils import reverse_library_url
    from contentstore.views.library import LIBRARIES_ENABLED
    from contentstore.views.course import (
        _accessible_libraries_iter,
        get_courses_accessible_to_user,
        _process_courses_list,
    )

    # import is placed here to avoid circular imports
    from student.auth import has_studio_write_access

    if does_timed_exam_has_attempts(timed_exam_key_string):
        return HttpResponseForbidden()

    timed_exam_key = CourseKey.from_string(timed_exam_key_string)

    # Check has write permission
    check_read_permission_or_raise(request.user, timed_exam_key)

    timed_exam = modulestore().get_course(timed_exam_key, depth=None)

    # Check timed exam exist in mongo and mysql DB.
    check_timed_exam_or_raise(timed_exam, timed_exam_key_string)

    timed_exam_model_instance = TimedExam.objects.get(key=timed_exam_key_string)

    skills = Skill.objects.all()

    def format_skill_for_view(skill):
        """
        Return a dict of the data which the view requires for each skill.
        """
        return {
            "id": getattr(skill, "id", None),
            "name": getattr(skill, "name", None),
        }

    def format_library_for_view(library):
        """
        Return a dict of the data which the view requires for each library
        """

        try:
            # grade is saved as part of of the number on library as the following format
            # {Display Name}-{Grade}-{unique 4 digit number}
            # ref: cms/djangoapps/contentstore/views/library.py::_get_unique_library_code
            grade = (library.display_number_with_default or " - ").split("-")[1]
        except (IndexError, ValueError, TypeError):
            grade = ""

        return {
            "display_name": library.display_name,
            "library_key": six.text_type(library.location.library_key),
            "url": reverse_library_url(
                "library_handler", six.text_type(library.location.library_key)
            ),
            "org": library.display_org_with_default,
            "number": library.display_number_with_default,
            "grade": grade,
            "can_edit": has_studio_write_access(
                request.user, library.location.library_key
            ),
        }

    courses_iter, in_process_course_actions = get_courses_accessible_to_user(
        request, None
    )
    split_archived = settings.FEATURES.get("ENABLE_SEPARATE_ARCHIVED_COURSES", False)
    courses, _, _ = _process_courses_list(
        courses_iter, in_process_course_actions, split_archived, request
    )

    libraries = _accessible_libraries_iter(request.user) if LIBRARIES_ENABLED else []
    library_names = ["Biology", "Maths", "Computer Science", "Creative Cloud"]
    organizations = ["edX", "Taleem", "creativeX", "Zoke"]
    library_codes = [
        "Grade1",
        "Grade2",
        "Grade3",
        "Grade4",
        "Grade5",
        "Grade6",
        "Grade7",
        "Grade8",
        "Grade9",
        "Grade10",
        "Grade11",
        "Grade12",
    ]
    from openedx.custom.question_bank.utils import (
        get_grouped_tags,
        get_question_bank_stats,
    )

    tags = get_grouped_tags(timed_exam_model_instance.question_bank)
    question_bank_stats = get_question_bank_stats(
        timed_exam_model_instance.question_bank
    )

    return render_to_response(
        "taleem/timed_exam.html",
        {
            "user": request.user,
            "timed_exam_key_string": timed_exam_key_string,
            "timed_exam": timed_exam,
            "skills": [format_skill_for_view(skill) for skill in skills],
            "courses": courses,
            "libraries": [format_library_for_view(lib) for lib in libraries],
            "library_names": library_names,
            "organizations": organizations,
            "library_codes": library_codes,
            "chapters": tags[QuestionTags.CHAPTER],
            "topics": tags[QuestionTags.TOPIC],
            "learning_outputs": tags[QuestionTags.LEARNING_OUTPUT],
            "timed_exam_model_instance": timed_exam_model_instance,
            "selected_values": {
                "chapters": timed_exam_model_instance.chapters.split(","),
                "topics": timed_exam_model_instance.topics.split(","),
                "learning_output": timed_exam_model_instance.learning_output.split(","),
            },
            "question_bank_stats": question_bank_stats,
        },
    )


def list_timed_exams(request):
    """
    List all accessible timed exams, after applying filters in the request

    Query params:
        org - The organization used to filter libraries
        text_search - The string used to filter libraries by searching in title, id or org
    """
    raise Http404


@login_required
@ensure_csrf_cookie
@require_http_methods(("POST",))
def update_timed_exam_fields(request, course_key_string):
    """
    Helper method for deleting a timed exam's main section not the whole timed exam.
    """
    timed_exam_key_string = course_key_string
    timed_exam_key = CourseKey.from_string(timed_exam_key_string)

    # Check has write permission
    check_write_permission_or_raise(request.user, timed_exam_key)

    timed_exam = modulestore().get_course(timed_exam_key, depth=None)

    # Check timed exam exist in mongo and mysql DB.
    check_timed_exam_or_raise(timed_exam, timed_exam_key_string)

    from cms.djangoapps.contentstore.views.item import delete_item

    # Delete all the course sections to empty the course.
    for section_key in timed_exam.children:
        delete_item(request, section_key)

    update_timed_exam_dates(request, timed_exam_key)

    # Return an empty success response.
    return JsonResponse()


@login_required
@ensure_csrf_cookie
def reports(request, course_id):
    user = request.user

    # Get the course key
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    # Get the course and exam
    course = get_object_or_404(CourseOverview, id=course_key)
    exam = get_object_or_404(TimedExam, key=course_id)

    # Only admin and allowed teacher can access the reports
    is_teacher = user.ta3leem_profile.user_type == UserType.teacher.name
    if not any(
        (
            user.is_superuser,
            has_access(user, CourseStaffRole.ROLE, course_key),
            is_teacher and user.ta3leem_profile.can_create_exam,
        )
    ):
        return HttpResponseForbidden()

    # Get the list of teachers for this course
    teachers = CourseAccessRole.objects.filter(
        course_id=course_key, role__in=["staff", "instructor"]
    ).values_list("user")

    # Get the enrolled students
    students = (
        User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            is_staff=False,
        )
        .exclude(id__in=teachers)
        .order_by("username")
        .select_related("profile")
    )

    id_verification_statuses = get_users_verification_status(students)

    # Student IDs who have have attempted the exam
    all_submitted_attempts = (
        ProctoredExamStudentAttempt.objects.filter(
            proctored_exam__course_id=course_key,
            status=ProctoredExamStudentAttemptStatus.submitted,
            user__is_staff=False,
        )
        .exclude(user__in=teachers)
        .order_by()
    )

    attendees = all_submitted_attempts.values_list("user", flat=True).distinct()

    # Student IDs who are either in-progress or left in between
    live_students = []
    dangling_students = []
    timestamp = datetime.now(pytz.UTC)
    due_date_passed = course.end <= timestamp
    away_time_limit = exam.allowed_disconnection_minutes
    filtered_query = Q(proctored_exam__course_id=course_id) & (
        Q(status=ProctoredExamStudentAttemptStatus.started)
        | Q(status=ProctoredExamStudentAttemptStatus.ready_to_submit)
    )
    in_progress_attempts = ProctoredExamStudentAttempt.objects.filter(filtered_query)
    for attempt in in_progress_attempts:
        if (
            timestamp - attempt.last_poll_timestamp
        ).total_seconds() / 60 <= away_time_limit:
            live_students.append(attempt.user.id)
        else:
            dangling_students.append(attempt.user.id)

    # Session violations per student e.g. {student_id: num_violations}
    session_violations = dict(
        ProctoredExamSessionConnectionHistory.objects.filter(
            course_id=course_id,
        )
        .values_list(
            "user",
        )
        .annotate(violations=Count(id) - 1)
        .order_by()
    )

    # Tab violations per student e.g. {student_id: num_violations}
    tab_violations = dict(
        ProctoredExamTabSwitchHistory.objects.filter(
            course_id=course_id,
            event_type="out",
        )
        .values_list(
            "user",
        )
        .annotate(violations=Count(id))
        .order_by()
    )

    # Webcam abnormalities
    snapshots_taken = dict(
        ProctoredExamWebMonitoringHistory.objects.filter(
            proctored_exam_snapshot__course_id=course_id,
        )
        .values_list("proctored_exam_snapshot__user")
        .annotate(violations=Count(id))
        .order_by()
    )
    face_not_found_violations = dict(
        ProctoredExamWebMonitoringHistory.objects.filter(
            proctored_exam_snapshot__course_id=course_id,
            status=ProctoredExamWebMonitoringHistory.FACE_NOT_FOUND,
        )
        .values_list("proctored_exam_snapshot__user")
        .annotate(violations=Count(id))
        .order_by()
    )
    multiple_faces_found_violations = dict(
        ProctoredExamWebMonitoringHistory.objects.filter(
            proctored_exam_snapshot__course_id=course_id,
            status__in=[
                ProctoredExamWebMonitoringHistory.MULTIPLE_FACE_FOUND,
                ProctoredExamWebMonitoringHistory.MULTIPLE_PEOPLE_FOUND,
            ],
        )
        .values_list("proctored_exam_snapshot__user")
        .annotate(violations=Count(id))
        .order_by()
    )
    unknown_face_found_violations = dict(
        ProctoredExamWebMonitoringHistory.objects.filter(
            proctored_exam_snapshot__course_id=course_id,
            status=ProctoredExamWebMonitoringHistory.UNKNOWN_FACE,
        )
        .values_list("proctored_exam_snapshot__user")
        .annotate(violations=Count(id))
        .order_by()
    )

    # Exam scores per student e.g. {student_id: score}
    scores = dict(
        PersistentExamGrade.objects.filter(
            course_id=course_id,
        ).values_list("user_id", "percent_grade")
    )
    score_distribution = {
        "highest": 0.0,
        "lowest": 0.0,
        "mean": 0.0,
        "median": 0.0,
        "mode": 0.0,
        "scores_y_axis": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    }
    sorted_scores = sorted(scores.values())
    if sorted_scores:
        score_distribution.update(
            {
                "highest": sorted_scores[-1],
                "lowest": sorted_scores[0],
                "mean": round(numpy.mean(sorted_scores), 2),
                "median": round(numpy.median(sorted_scores), 2),
                "mode": stats.mode(sorted_scores),
                "scores_y_axis": distribute_scores(sorted_scores),
            }
        )

    # Exam review status by student
    review_status = {
        review.user.id: review.status
        for review in ProctoredExamReview.objects.filter(course_id=course_id)
    }

    mandatory, optional = exam.count_questions
    problems = analyze_questions(course_key)

    return render_to_response(
        "timed_exam/reports.html",
        {
            "course": course,
            "exam": exam,
            "scores": scores,
            "num_questions": mandatory + optional,
            "num_optional_questions": optional,
            "p_value": exam.p_value,
            "score_distribution": score_distribution,
            "problems": problems,
            "students": students,
            "id_verification_statuses": id_verification_statuses,
            "attendees": attendees,
            "live_students": live_students,
            "due_date_passed": due_date_passed,
            "dangling_students": dangling_students,
            "session_violations": session_violations,
            "tab_violations": tab_violations,
            "snapshots_taken": snapshots_taken,
            "face_not_found_violations": face_not_found_violations,
            "multiple_faces_found_violations": multiple_faces_found_violations,
            "unknown_face_found_violations": unknown_face_found_violations,
            "review_status": review_status,
            "is_monitored_timed_exam": TimedExam.is_monitored_timed_exam(course_key),
        },
    )


@login_required
@ensure_csrf_cookie
def refresh_exam_grades(request, course_id):
    user = request.user

    # Get the course key
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    # Only admin and allowed teacher can access the reports
    is_teacher = user.ta3leem_profile.user_type == UserType.teacher.name
    if not any(
        (
            user.is_superuser,
            has_access(user, CourseStaffRole.ROLE, course_key),
            is_teacher and user.ta3leem_profile.can_create_exam,
        )
    ):
        return HttpResponseForbidden()

    # Update scores in needed
    calculate_exam_grades(course_id)

    # Exam scores per student e.g. {student_id: score}
    scores = dict(
        PersistentExamGrade.objects.filter(
            course_id=course_id,
        ).values_list("user_id", "percent_grade")
    )

    # return JSON response
    return JsonResponse(scores)


@login_required
@ensure_csrf_cookie
def proctoring(request, course_id, student_id):
    # Get the context
    try:
        context = proctoring_report_context(course_id, student_id, request.user)
    except Exception as e:
        return HttpResponse("Developer message: {}".format(e))

    return render_to_response("timed_exam/proctoring.html", context)


@login_required
@ensure_csrf_cookie
def proctoring_pdf(request, course_id, student_id):
    # Get the course key
    try:
        context = proctoring_report_context(course_id, student_id, request.user)
    except Exception as e:
        return HttpResponse("Developer message: {}".format(e))

    response = HttpResponse(content_type="application/pdf")
    report_file_name = "report_{}.pdf".format(student_id)
    response["Content-Disposition"] = 'attachment; filename="' + report_file_name + '"'
    report_html = render_to_string("timed_exam/pdf_report.html", context)
    pisa_status = pisa.CreatePDF(
        report_html,
        dest=response,
        path=settings.LMS_ROOT_URL,
    )
    if pisa_status.err:
        return HttpResponse("We had some errors <pre>" + html + "</pre>")
    return response


@login_required
@ensure_csrf_cookie
@require_http_methods(("GET",))
def enrollment_dashboard(request, course_key_string):
    """
    Enrollment Dashboard for the admin.
    """
    try:
        course_key = CourseKey.from_string(course_key_string)
    except InvalidKeyError:
        return redirect(reverse("home"))

    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    timed_exam = get_object_or_404(TimedExam, key=course_key_string)

    return render_to_response(
        "taleem/enrollment_dashboard.html",
        {
            "user": request.user,
            "timed_exam": timed_exam,
            "course_key_string": course_key_string,
        },
    )


@login_required
def learner_enrollments(request, course_key_string):
    """
    Learner enrollments endpoint.
    """
    return JsonResponse({"enrollments": get_timed_exam_enrollments(course_key_string)})


@login_required
def learner_pending_enrollments(request, course_key_string):
    """
    Learner enrollments endpoint.
    """
    return JsonResponse(
        {"pending_enrollments": get_timed_exam_pending_enrollments(course_key_string)}
    )


@login_required
def unenroll_learner(request, course_key_string):
    """
    Learner unenroll endpoint.
    """
    try:
        CourseKey.from_string(course_key_string)
    except InvalidKeyError:
        return redirect(reverse("home"))

    email = request.GET.get("email")
    unenroll_in_timed_exam(email, course_key_string)

    return redirect(
        reverse("timed_exam:enrollment_dashboard", args=(course_key_string,))
    )


@login_required
def delete_pending_enrollment_view(request, course_key_string):
    """
    Delete pending enrollment view.
    """
    try:
        CourseKey.from_string(course_key_string)
    except InvalidKeyError:
        return redirect(reverse("home"))

    email = request.GET.get("email")
    delete_pending_enrollment(email, course_key_string)

    # sending an email for un-enrollment
    try:
        user = User.objects.get(email=email)
    except:
        user = None

    if user:
        # Add email to queue
        Ta3leemEmail.objects.create(
            user=user,
            email_type='unenroll',
            params={
                'user_id': user.id,
                'mode': "timed",
            }
        )

    return redirect(
        reverse("timed_exam:enrollment_dashboard", args=(course_key_string,))
    )


@login_required
def resend_notification(request, course_key_string):
    """
    Resend notification to learner for this enrollment
    """
    email = request.GET.get("email")
    course_key = CourseKey.from_string(course_key_string)

    try:
        enrollment = CourseEnrollment.objects.get(
            user__email=email, course__id=course_key
        )
    except:
        enrollment = None

    # Need to implement the send email function for this
    if enrollment:
        # Add email to queue
        Ta3leemEmail.objects.create(
            user=enrollment.user,
            email_type='enroll',
            params={
                'user_id': enrollment.user.id,
                'mode': "timed",
            }
        )

    return redirect(
        reverse("timed_exam:enrollment_dashboard", args=(course_key_string,))
    )


@login_required
def resend_pending_notification(request, course_key_string):
    """
    Resend notification to learner for this enrollment
    """
    email = request.GET.get("email")

    does_pending_enrollment_exists = PendingTimedExamUser.objects.filter(
        user_email=email, timed_exam__key=course_key_string
    ).exists()
    if does_pending_enrollment_exists:
        # Need to implement the send email function for this
        send_pending_enrollment_email(email)

    return redirect(
        reverse("timed_exam:enrollment_dashboard", args=(course_key_string,))
        + "?tab=pending-enrollments"
    )


@login_required
@ensure_csrf_cookie
@require_http_methods(("POST",))
def delete_course(request, course_key_string):
    """
    Endpoint to delete the timed exam.
    """
    delete_timed_exam(course_key_string, request.user)
    return JsonResponse({"url": reverse("home")})


@login_required
@ensure_csrf_cookie
@require_http_methods(("POST",))
def generate_enrollment_code(request, course_key_string):
    """
    Endpoint to delete the timed exam.
    """
    from openedx.core.djangoapps.user_authn.utils import generate_random_enrollment_code

    timed_exam = TimedExam.get_obj_by_course_id(course_key_string)
    enrollment_code = None
    response = {"enrollment_code": enrollment_code, "status": 500}
    if timed_exam:
        timed_exam.generate_enrollment_code = True
        enrollment_code = str(generate_random_enrollment_code())
        timed_exam.enrollment_code = enrollment_code
        timed_exam.save()
        response["enrollment_code"] = enrollment_code
        response["status"] = 200
    return JsonResponse(response)


@login_required
@ensure_csrf_cookie
@require_http_methods(("POST",))
def generate_enrollment_password(request, course_key_string):
    """
    Endpoint to delete the timed exam.
    """
    from openedx.core.djangoapps.user_authn.utils import generate_random_enrollment_code

    timed_exam = TimedExam.get_obj_by_course_id(course_key_string)
    enrollment_password = None
    response = {"enrollment_password": enrollment_password, "status": 500}
    if timed_exam:
        timed_exam.generate_enrollment_code = True
        enrollment_password = str(generate_random_enrollment_code())
        TimedExamExtras.objects.get_or_create(
            timed_exam=timed_exam, defaults={"enrollment_password": enrollment_password}
        )

        response["enrollment_password"] = enrollment_password
        response["status"] = 200
    return JsonResponse(response)


@login_required
@ensure_csrf_cookie
@require_http_methods(("POST",))
def remove_snapshots(request, course_id):
    """
    Endpoint to delete the proctoring snapshots.
    """
    logging.info(
        "[Delete Proctoring Snapshot] Teacher has initiated the request to delete the proctoring snapshots for "
        "timed exam: {}".format(course_id)
    )
    delete_timed_exam_proctoring_snapshots.delay(course_id)
    return JsonResponse({})


@login_required
@ensure_csrf_cookie
@require_http_methods(("POST",))
def edit_data_retention_period(request, course_id):
    """
    Endpoint to edit the data retention period for timed exam.
    """
    data_retention_period = request.POST.get("data_retention_period", 10)
    log.info(
        "Going to change the data retention period to {data_retention_period} for course: [{course_id}]".format(
            data_retention_period=data_retention_period, course_id=course_id
        )
    )
    time_exam = TimedExam.get_obj_by_course_id(course_id)
    time_exam.data_retention_period = data_retention_period
    time_exam.save()
    return JsonResponse({})


class ProctoredExamUserSnapshotView(AuthenticatedAPIView):
    """
    Proctored exam user snapshots.
    """

    def post(self, request, course_id):  # pylint: disable=unused-argument
        """Save snapshot for the given user and course id"""
        form = ProctoredExamSnapshotForm(
            data={
                "user": request.user.id,
                "course_id": request.POST.get("course_id"),
            },
            files=request.FILES,
        )

        if form.is_valid():
            form.save()
            return Response(status=status.HTTP_200_OK)

        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


class TimedExamAlarmConfigurationView(View):
    """
    Timed exam alarm configuration view.
    """

    template = "admin/timed_exam/add_timed_exam_alarm_configuration.html"
    form = TimedExamAlarmConfigurationForm

    class ContextParameters:
        """
        Namespace-style class for custom context parameters.
        """

        TIMED_EXAM_ALARM_CONFIGURATION = "timed_exam_alarm_configurations"
        COUNT = "count"

    def _get_view_context(self):
        """
        Return the default context parameters.
        """
        timed_exam_alarm_configurations = TimedExamAlarmConfiguration.active_objects()
        return {
            self.ContextParameters.TIMED_EXAM_ALARM_CONFIGURATION: timed_exam_alarm_configurations,
            self.ContextParameters.COUNT: timed_exam_alarm_configurations.count(),
        }

    @staticmethod
    def _get_admin_context():
        """
        Build admin context.
        """
        opts = TimedExamAlarmConfiguration._meta
        return {"opts": opts}

    def _build_context(self, request):
        """
        Build admin and view context used by the template.
        """
        context = self._get_view_context()
        context.update(admin.site.each_context(request))
        context.update(self._get_admin_context())
        return context

    def get(self, request):
        """
        Handle GET request - renders the template.

        Arguments:
            request (django.http.request.HttpRequest): Request instance

        Returns:
            django.http.response.HttpResponse: HttpResponse
        """
        context = self._build_context(request)
        return render(request, self.template, context)

    def post(self, request):
        """
        Handle POST request - saves excluded/included skills.

        Arguments:
            request (django.http.request.HttpRequest): Request instance

        Returns:
            django.http.response.HttpResponse: HttpResponse
        """
        form = self.form(data=request.POST)
        if form.is_valid():
            form.save(request.user)

            message = _("The timed exam alarm configuration were updated successfully.")
            messages.add_message(self.request, messages.SUCCESS, message)
        else:
            for message in form.error_list:
                messages.add_message(self.request, messages.ERROR, message)

        meta = TimedExamAlarmConfiguration._meta

        return HttpResponseRedirect(
            reverse("admin:timed_exam_timedexamalarmconfiguration_changelist")
        )


@login_required
@ensure_csrf_cookie
def management(request, course_key_string):
    from contentstore.views.course import get_course_and_check_access

    if course_key_string is None:
        return redirect(reverse("home"))

    course_key = CourseKey.from_string(course_key_string)

    with modulestore().bulk_operations(course_key):
        course_module = get_course_and_check_access(course_key, request.user)

    if request.method == "POST":
        teacher_email = request.POST.get("teacher_email")
        teacher = User.objects.get(email=teacher_email)
        CourseStaffRole(course_key).add_users(teacher)

    co_teachers = CourseAccessRole.objects.filter(
        role__in=["staff", "instructor"], course_id=course_key, org=course_key.org
    ).exclude(user=request.user)

    co_teachers = set([teacher.user for teacher in co_teachers])

    teachers = (
        Ta3leemUserProfile.objects.filter(
            user_type=UserType.teacher.name, user__is_active=True
        )
        .exclude(user__in=co_teachers)
        .exclude(user=request.user)
    )

    teachers = set([teacher.user for teacher in teachers])

    return render_to_response(
        "timed_exam/timed_exam_management.html",
        {
            "co_teachers": co_teachers,
            "context_course": course_module,
            "teachers": teachers,
            "course_key": course_key_string,
            "exam_key": course_key_string,
        },
    )


@login_required
@ensure_csrf_cookie
def delete_co_teacher(request, course_key_string, teacher_id):
    from contentstore.views.course import get_course_and_check_access

    if course_key_string is None:
        return redirect(reverse("home"))

    course_key = CourseKey.from_string(course_key_string)

    with modulestore().bulk_operations(course_key):
        course_module = get_course_and_check_access(course_key, request.user)

    teacher = User.objects.get(id=teacher_id)

    CourseStaffRole(course_key).remove_users(teacher)

    return redirect(
        reverse(
            "timed_exam:timed_exam_management",
            kwargs={"course_key_string": course_key_string},
        )
    )


@login_required
@ensure_csrf_cookie
def hide_exam(request, course_id):
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    user = request.user
    timed_exam = TimedExam.objects.get(key=course_key)
    if not timed_exam.is_hidden(user=user):
        TimedExamHide.objects.create(timed_exam=timed_exam, user=user)

    return redirect(reverse("dashboard"))


@login_required
@ensure_csrf_cookie
def unhide_exam(request, course_key_string):
    try:
        course_key = CourseKey.from_string(course_key_string)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    user = request.user
    timed_exam = TimedExam.objects.get(key=course_key)
    if timed_exam.is_hidden(user=user):
        TimedExamHide.objects.filter(timed_exam=timed_exam, user=user).delete()

    return redirect(reverse("home"))


@login_required
@ensure_csrf_cookie
def enroll_exam(request, course_id):
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    timed_exam = get_object_or_404(TimedExam, key=course_id)
    if timed_exam.exam_type == TimedExam.PUBLIC or CourseEnrollment.is_enrolled(
        request.user, course_key
    ):
        return redirect(reverse("courseware", kwargs={"course_id": course_id}))

    errors = ""

    if request.method == "GET":
        form = TimedExamEnrollmentForm()
    else:
        form = TimedExamEnrollmentForm(
            {
                "timed_exam": course_id,
                "enrollment_password": request.POST.get("enrollment_password"),
            }
        )
        if form.is_valid():
            form.save(request.user)
            return redirect(reverse("courseware", kwargs={"course_id": course_id}))
        else:
            errors = "Invalid enrollment password or timed exam provided."
    return render_to_response(
        "timed_exam/timed_exams_enrollment.html",
        {
            "timed_exam": timed_exam,
            "form": form,
            "errors": errors,
        },
    )


def discover_exams(request):
    """
    Discover public exams.
    """
    if not request.user.is_active:
        return redirect(reverse("dashboard"))
    return render_to_response(
        "timed_exam/discover/exams.html", {"filters_data": get_filters_data()}
    )


@login_required
@ensure_csrf_cookie
def can_add_teacher(request, course_key_string):
    can_add_without_consent = True
    if course_key_string is None:
        return JsonResponseBadRequest(
            {"message": "Exam ID is missing in the URL Params."}
        )

    try:
        course_key = CourseKey.from_string(course_key_string)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    if request.method == "POST":
        teacher_email = request.POST.get("teacher_email")
        try:
            teacher = User.objects.get(email=teacher_email)
        except ObjectDoesNotExist:
            return JsonResponseBadRequest({"message": "Invalid Email"})

        if CourseEnrollment.is_enrolled(teacher, course_key):
            can_add_without_consent = False

    return JsonResponse({"can_add_without_consent": can_add_without_consent})


@login_required
def archived_exams_page(request):
    """Handle Archived Exams Page."""
    archived_exams = TimedExamHide.objects.filter(user=request.user)
    return render_to_response(
        "timed_exam/archived_exams.html", {"archived_exams": archived_exams}
    )
