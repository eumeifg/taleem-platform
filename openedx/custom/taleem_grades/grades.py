# -*- coding: UTF-8 -*-
"""
Grade calculations for the Ta3leem exams.
"""

import logging
import statistics
from six import text_type

from celery.task import task  # pylint: disable=no-name-in-module, import-error

from openedx.custom.timed_exam.models import TimedExam, QuestionSet
from xmodule.modulestore.django import modulestore
from lms.djangoapps.grades.api import SubsectionGradeFactory
from lms.djangoapps.course_blocks.api import get_course_blocks

from openedx.custom.taleem_grades.models import PersistentExamGrade

log = logging.getLogger(__name__)


def calc_and_persist_exam_grade(student, course_key):
    """
    Calculate exam grade for the given student
    and course key.
    """
    course_id = text_type(course_key)

    # Fetch timed exam, if does not exists, don't proceed
    timed_exam = TimedExam.get_obj_by_course_id(course_id)
    if not timed_exam:
        log.error("TimedExam id {} does not exists to calc grades for user {}".format(
            course_id, student.id))
        return 0

    sequentials = modulestore().get_items(
        course_key,
        qualifiers={'category': 'sequential'}
    )
    if not sequentials:
        log.error("TimedExam id {} does not have subsection to calc grades for user {}".format(
            course_id, student.id))
        return 0

    sequential = sequentials[0]
    try:
        problem_scores = SubsectionGradeFactory(
            student,
            course_structure=get_course_blocks(student, sequential.location)
        ).create(sequential, read_only=True).problem_scores
    except Exception as e:
        log.error("Could not calculate grades for id {}, exception: {}".format(
            course_id, str(e)))
        return 0

    # Assigned questions and scores
    easy_scores, moderate_scores, hard_scores = [], [], []
    easy, moderate, hard = QuestionSet.get_question_numbers(
        student.id, course_key)
    for index, problem_score in enumerate(problem_scores.values()):
        score = 0.0
        if problem_score.possible:
            score = problem_score.earned / problem_score.possible
        if index in easy:
            easy_scores.append(score)
        elif index in moderate:
            moderate_scores.append(score)
        elif index in hard:
            hard_scores.append(score)

    final_scores = (
        sorted(easy_scores, reverse=True)[:timed_exam.easy_question_count] +
        sorted(moderate_scores, reverse=True)[:timed_exam.moderate_question_count] +
        sorted(hard_scores, reverse=True)[:timed_exam.hard_question_count]
    )

    # Update or create persisted grade
    if final_scores:
        percent_grade = round(statistics.mean(final_scores) * 100, 2)
        PersistentExamGrade.update_or_create(student.id, course_id, percent_grade)
