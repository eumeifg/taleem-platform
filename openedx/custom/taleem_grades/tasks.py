# -*- coding: UTF-8 -*-
"""
Background tasks for Ta3leem exam grade calculations.
"""

import logging

from opaque_keys.edx.keys import CourseKey
from celery.task import task  # pylint: disable=no-name-in-module, import-error
from django.contrib.auth.models import User

from student.models import CourseEnrollment

from openedx.custom.taleem_grades.grades import calc_and_persist_exam_grade

log = logging.getLogger(__name__)


@task(bind=True)
def calculate_exam_grade(self, student_id, course_id):
    """
    Calculate exam grade for the given student and
    exam
    """
    # Get course key and student
    course_key = CourseKey.from_string(course_id)
    student = User.objects.get(id=student_id)

    # Safe to calc and persist grade
    calc_and_persist_exam_grade(
        student,
        course_key
    )

@task(bind=True)
def calculate_exam_grades(self, course_id):
    """
    Calculate exam grade for the given exam
    """
    # Get course key
    course_key = CourseKey.from_string(course_id)

    # Get enrollements
    enrollments = CourseEnrollment.objects.filter(course__id=course_key)
    for enrollment in enrollments:
        # If the course is missing or broken, log an error and skip it.
        course_overview = enrollment.course_overview
        if not course_overview:
            log.error(
                "User %s enrolled in broken or non-existent course %s",
                enrollment.user.username,
                enrollment.course_id
            )
            continue
        # Safe to calc and persist grade
        calc_and_persist_exam_grade(
            enrollment.user,
            course_key
        )
