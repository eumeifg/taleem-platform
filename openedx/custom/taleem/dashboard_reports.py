
import math
from six import text_type
from datetime import datetime


from pytz import UTC
from django.db.models import Avg
from django.urls import reverse
from django.conf import settings

from student.models import CourseEnrollment

from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.custom.wishlist.models import Wishlist
from openedx.custom.taleem_grades.models import PersistentExamGrade
from openedx.custom.timed_exam.models import TimedExam
from edx_proctoring.models import ProctoredExamStudentAttempt
from edx_proctoring.statuses import ProctoredExamStudentAttemptStatus
from lms.djangoapps.grades.models import PersistentSubsectionGrade
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey


TIMED_EXAM_PASS_CRITERIA = 50.0


def get_teacher_exam_report_data(user):
    """
    Return the teacher's exam related report data.
    """
    timed_exams = TimedExam.objects.filter(user_id=user.id)

    average_persistent_exam_grades = PersistentExamGrade.objects.filter(
        course_id__in=[timed_exam.key for timed_exam in timed_exams]
    ).values('course_id').annotate(average_score=Avg('percent_grade'))
    average_persistent_exam_grades = {
        str(item['course_id']): round(item['average_score'], 2) for item in average_persistent_exam_grades
    }

    timed_exam_report_data = []
    for timed_exam in timed_exams:
        timed_exam_report_data.append(
            {
                'timed_exam_key': timed_exam.key,
                'timed_exam_name': timed_exam.display_name,
                'average_percentage': average_persistent_exam_grades.get(timed_exam.key),
                'top_students': get_top_students(timed_exam),
                'absent_students': get_absent_students(timed_exam)
            }
        )
    return {
        'timed_exam_count': timed_exams.count(),
        'timed_exam_reports': timed_exam_report_data
    }


def get_top_students(timed_exam):
    """
    Get the report of top students in the timed exams.


    Arguments:
        timed_exam (TimedExam): timed exam whose top students we need to get.
    """
    scores = PersistentExamGrade.objects.filter(
        course_id=timed_exam.key
    ).order_by('-percent_grade').values_list('user_id', 'percent_grade')

    # Getting the top 10% student from the queryset.
    top_ten_percent = int(math.ceil(scores.count() * 0.1))
    scores = dict(scores[0:top_ten_percent])

    return [{
        'name': "{0} {1}".format(student.get('user__first_name'), student.get('user__last_name')).strip(),
        'email': student.get('user__email'),
        'username': student.get('user__username'),
        'grade_percentage': scores.get(student.get('user__id'), 0.0)
    } for student in timed_exam.enrolled_students if scores.get(student.get('user__id'), False)]


def get_absent_students(timed_exam):
    """
    Get absent students in a Timed exam.

    Arguments:
        timed_exam (TimedExam): timed exam whose absent students we need to get.
    """
    student_with_attempts = ProctoredExamStudentAttempt.objects.filter(
        proctored_exam__course_id=timed_exam.key
    ).values_list('user_id', flat=True)

    return [{
        'name': "{0} {1}".format(student.get('user__first_name'), student.get('user__last_name')).strip(),
        'email': student.get('user__email'),
        'username': student.get('user__username'),
    } for student in timed_exam.enrolled_students if student.get('user__id') not in student_with_attempts]


def get_student_timed_exam_report_data(user):
    """
    Return the student's timed exam related report data.
    """

    def _filter_timed_exam(user, time_exam_queryset):
        """
        Filter the queryset if proctored exam attempt record doesn't exist.
        """
        return [
            timed_exam for timed_exam in time_exam_queryset if not ProctoredExamStudentAttempt.objects.filter(
                proctored_exam__course_id=timed_exam.key,
                user__username=user.username
            ).exists()
        ]

    def _get_submitted_timed_exams_count(user, timed_exam_ids):
        """
        Return the count of all the submitted timed exams of the given user.
        """
        return ProctoredExamStudentAttempt.objects.filter(
            proctored_exam__course_id__in=timed_exam_ids,
            user__username=user.username,
            status=ProctoredExamStudentAttemptStatus.submitted
        ).count()

    def _get_missed_timed_exams_count(user, timed_exams):
        """
        Return the count of all the missed timed exams of the given user.
        """
        past_timed_exams = timed_exams.filter(due_date__lt=datetime.utcnow())
        return len(_filter_timed_exam(user, past_timed_exams))

    def _get_pending_timed_exams_count(user, timed_exams):
        """
        Return the count of all the pending timed exams of the given user.
        """
        future_time_exams = timed_exams.filter(due_date__gte=datetime.utcnow())
        return len(_filter_timed_exam(user, future_time_exams))

    missed_timed_exam_count = pending_timed_exam_count = submitted_timed_exam_count = 0
    passed_exams_count = failed_exams_count = timed_exam_average_grade = 0

    timed_exam_ids = [
        str(enrollment.course.id) for enrollment in CourseEnrollment.enrollments_for_user(user, timed_exam=True)
    ]

    if timed_exam_ids:
        all_timed_exams = TimedExam.objects.filter(key__in=timed_exam_ids)

        submitted_timed_exam_count = _get_submitted_timed_exams_count(user, timed_exam_ids)
        missed_timed_exam_count = _get_missed_timed_exams_count(user, all_timed_exams)
        pending_timed_exam_count = _get_pending_timed_exams_count(user, all_timed_exams)

        # Grade related report data
        timed_exam_grades = PersistentExamGrade.objects.filter(user_id=user.id, course_id__in=timed_exam_ids)
        if timed_exam_grades:
            passed_exams_count = timed_exam_grades.filter(percent_grade__gte=TIMED_EXAM_PASS_CRITERIA).count()
            failed_exams_count = timed_exam_grades.count() - passed_exams_count
            timed_exam_average_grade = round(
                sum([grade.percent_grade for grade in timed_exam_grades]) / timed_exam_grades.count(),
                2
            )

    return {
        'submitted_timed_exam_count': submitted_timed_exam_count,
        'missed_timed_exam_count': missed_timed_exam_count,
        'pending_timed_exam_count': pending_timed_exam_count,
        'passed_timed_exams_count': passed_exams_count,
        'failed_timed_exams_count': failed_exams_count,
        'timed_exam_average_grade': timed_exam_average_grade
    }


def get_student_course_report_data(user):
    """
    Return the student's course related report data.
    """

    def _get_finished_courses_count(user, course_ids):
        """
        Return the count of finished/graded courses of user.
        """
        from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
        finished_courses = 0
        course_keys = [CourseKey.from_string(course_id) for course_id in course_ids]
        courses = CourseOverview.get_from_ids(course_keys)
        for course in courses.values():
            if course.has_ended():
                finished_courses = finished_courses + 1
        return finished_courses

    course_enrollments = CourseEnrollment.enrollments_for_user(user)
    course_ids = [str(enrollment.course.id) for enrollment in course_enrollments]
    course_report_data = {
        'course_wish_list_count': len(Wishlist.get_favorite_courses(user)),
        'enroll_course_count': course_enrollments.count(),
        'finished_course_count': _get_finished_courses_count(user, course_ids),
        'certificate_count_report': GeneratedCertificate.eligible_certificates.filter(user=user).count(),
        'assignment_report': get_student_assignments_report_data(user, course_ids, course_enrollments)
    }
    return course_report_data


def get_student_assignments_report_data(user, course_ids, course_enrollments):
    """
    Get report of user's assignments report.
    """

    def _get_student_all_submitted_assignments(user, course_ids):
        """
        Return all the submitted assignments for given user and course ids.
        """
        return set([
            str(subsection['usage_key']) for subsection in PersistentSubsectionGrade.objects.filter(
                user_id=user.id,
                course_id__in=course_ids
            ).values('usage_key')
        ])

    assignment_report_data = []
    user_all_submitted_assignments = _get_student_all_submitted_assignments(user, course_ids)
    for course_enrollment in course_enrollments:
        course = course_enrollment.course
        course_missed_assignments, course_pending_assignments, course_submitted_assignments = get_course_assignments(
            str(course.id),
            user_all_submitted_assignments
        )
        assignment_report_data.append(
            {
                'course_display_name': course.display_name,
                'course_missed_assignments': course_missed_assignments,
                'course_pending_assignments': course_pending_assignments,
                'course_submitted_assignments': course_submitted_assignments,
            }
        )
    return assignment_report_data


def get_course_assignments(course_key, submitted_assignments):
    """
    Get a list of all course assignments.
    """

    def _get_subsection_url(course_key, block_id):
        """
        Return the full URL of the given block id.
        """
        return "{lms_url}{subsection_url}".format(
            lms_url=settings.LMS_ROOT_URL,
            subsection_url=reverse('jump_to_id', kwargs={'course_id': text_type(course_key), 'module_id': block_id})
        )

    def _get_visible_subsections(_course):
        """
        Returns a list of all visible subsections for a course.
        """
        _, visible_sections = _get_all_children(_course)
        visible_subsections = []
        for section in visible_sections:
            visible_subsections.extend(_get_visible_children(section))
        return visible_subsections

    def _get_all_children(parent):
        """
        Returns all child nodes of the given parent.
        """
        store = modulestore()
        children = [store.get_item(child_usage_key) for child_usage_key in _get_children(parent)]
        visible_children = [c for c in children if not c.visible_to_staff_only and not c.hide_from_toc]
        return children, visible_children

    def _get_visible_children(parent):
        """
        Returns only the visible children of the given parent.
        """
        _, visible_children = _get_all_children(parent)
        return visible_children

    def _get_children(parent):
        """
        Returns the value of the 'children' attribute of a node.
        """
        return [] if not hasattr(parent, 'children') else parent.children

    def _filter_subsections(course_key, submitted_assignments, subsections):
        """
        Filter the subsection on the base of submission and due date.
        """
        missed_assignment_list = []
        pending_assignment_list = []
        submitted_assignment_list = []
        for subsection in subsections:
            if subsection.graded:
                subsection_usage_key = str(subsection.location)
                subsection_data = {
                    'name': subsection.display_name,
                    'url': _get_subsection_url(course_key, subsection.location.block_id)
                }
                if subsection_usage_key in submitted_assignments:
                    submitted_assignment_list.append(subsection_data)
                elif subsection.due > datetime.now(tz=UTC):
                    pending_assignment_list.append(subsection_data)
                else:
                    missed_assignment_list.append(subsection_data)
        return missed_assignment_list, pending_assignment_list, submitted_assignment_list

    return _filter_subsections(
        course_key,
        submitted_assignments,
        _get_visible_subsections(modulestore().get_course(CourseKey.from_string(course_key)))
    )
