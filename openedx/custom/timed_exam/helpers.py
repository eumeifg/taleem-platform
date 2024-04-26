"""
Helper functions for timed exam app.
"""

import six
import json
import logging
import pytz
from datetime import datetime
from collections import defaultdict
from six import text_type

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from xmodule.modulestore.django import modulestore
from edx_user_state_client.interface import XBlockUserState
from lms.djangoapps.courseware.models import StudentModule
from submissions.models import Submission, ScoreSummary
from xblock.fields import Scope

from student.models import anonymous_id_for_user, user_by_anonymous_id
from lms.djangoapps.courseware.module_render import get_module_for_descriptor
from lms.djangoapps.courseware.model_data import FieldDataCache
from openedx.custom.timed_exam.models import QuestionSet
from openedx.custom.taleem_grades.models import PersistentExamGrade


log = logging.getLogger(__name__)

OPEN_ASSESSMENT = 'openassessment'
EDX_SGA = 'edx_sga'


def num_correct_answers(learner_group, scores):
    """
    Return number of learners who answered
    correctly from the given learner group.
    """
    correct = 0
    for learner_id in learner_group:
        if scores.get(learner_id, 0):
            correct += 1
    return correct


def form_learner_groups(course_id):
    """
    Divide the group into four equal parts.
    If not precisely divisible by four,
    the highest and lowest groups should be the same size and
    slightly bigger than the two middle groups.
    """
    # Arrange the test scores from the highest to the lowest value
    learners = tuple(
        PersistentExamGrade.objects.filter(
            course_id=course_id
        ).values_list('user_id', flat=True
        ).order_by('-percent_grade')
    )

    # proceed only if we have records
    num_learners = len(learners)
    if num_learners < 2:
        return (None, None, None, None)

    # if we have not enough records
    if num_learners < 4:
        return ((learners[0],), None, None, (learners[-1],))

    # calc size if the group
    group_size = int(num_learners / 4)

    # adjustment if not able to precisely divide
    extra = num_learners - group_size * 4
    group_1_size = \
    group_2_size = \
    group_3_size = \
    group_4_size = group_size

    if extra == 3:
        group_1_size += 1
        group_4_size += 1
        group_2_size += 1
    elif extra == 2:
        group_1_size += 1
        group_4_size += 1
    elif extra == 1:
        group_1_size +=1

    # Prepare 4 groups
    index = 0
    learner_group_1 = learners[index:group_1_size]
    index += group_1_size
    learner_group_2 = learners[index:index+group_2_size]
    index += group_2_size
    learner_group_3 = learners[index:index+group_3_size]
    index += group_3_size
    learner_group_4 = learners[index:index+group_4_size]

    return (
        learner_group_1,
        learner_group_2,
        learner_group_3,
        learner_group_4
    )


def calc_discrimination_index(learner_groups, scores):
    """
    The discrimination index can be described as the possibility
    that a specific item might distinguish or discriminate between
    students who possess the necessary knowledge to answer the question correctly,
    and others who lack such knowledge.

    Ref. https://e.itg.be/bangalore/MCQ/Discrimination%20index.html

    Arguments: scores (dict) {
        student_id: score
    }
    learner_groups: tuple of tuples (4 groups)
    """
    if not any(learner_groups):
        return None
    g1,g2,g3,g4 = learner_groups
    KH = num_correct_answers(g1, scores)
    KL = num_correct_answers(g4, scores)
    NH = len(g1)
    D = (KH - KL) / NH
    return round(D, 2)


def get_effectiveness_of_question(d_value):
    """
    Based on the discrimination value
    return the effectiveness of the question.
    """
    GOOD = 'green'
    FAIR = 'blue'
    BAD = 'red'
    NA = 'gray'

    if not d_value:
        return NA
    if -1 <= d_value <= 0.2:
        return BAD
    elif 0.2 < d_value <= 0.39:
        return FAIR
    else:
        return GOOD


def descriptor_to_module(request, course_key, descriptor):
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course_key,
        request.user,
        descriptor,
        read_only=False,
    )
    instance = get_module_for_descriptor(
        request.user,
        request,
        descriptor,
        field_data_cache,
        course_key,
        disable_staff_debug_info=True,
        course=None
    )
    return instance


def get_assigned_problems(request, user_id, course_key, shallow=False):
    # Get all problems
    problems = []
    for sequential in modulestore().get_items(
        course_key,
        qualifiers={'category': 'sequential'}
    ):
        for vert in sequential.get_children():
            problems += vert.get_children()

    # Filter assigned questions
    easy, moderate, hard = QuestionSet.get_question_numbers(user_id, course_key)

    # Shallow objects
    if shallow:
        return [
            problems[question_num]
            for question_num in easy + moderate + hard
        ]

    return [
        descriptor_to_module(request, course_key, problems[question_num])
        for question_num in easy + moderate + hard
    ]


def get_submissions(course_key):
    student_modules = StudentModule.objects.filter(
        course_id=course_key,
        module_type__in=['problem', 'drag-and-drop-v2', 'h5p'],
        student__is_staff=False
    )

    submissions = defaultdict(dict)
    for student_module in student_modules:
        submissions[
            six.text_type(student_module.module_state_key)
        ].update({student_module.student_id: student_module.grade or 0})

    score_summary = ScoreSummary.objects.filter(
        student_item__course_id=six.text_type(course_key),
        student_item__item_type__in=['openassessment', 'sga']
    )
    for score in score_summary:
        student_id = user_by_anonymous_id(score.student_item.student_id)
        if student_id.is_staff:
            continue
        submissions[
            score.student_item.item_id
        ].update({
            student_id: \
            score.latest and score.latest.points_earned or 0
        })

    return submissions


def analyze_questions(course_key):
    """
    Analyze Questions based on the submissions.
    """
    problems = []

    # Prepare scores
    submissions = get_submissions(course_key)

    # for d_value create 4 groups
    learner_groups = form_learner_groups(six.text_type(course_key))

    # Get all problems in the course
    for sequential in modulestore().get_items(
        course_key,
        qualifiers={'category': 'sequential'}
    ):
        for vert in sequential.get_children():
            for problem in vert.get_children():
                problem_id = six.text_type(problem.location)
                learner_score_map = submissions.get(problem_id, {})
                problem_scores = learner_score_map.values()
                respondents = len(problem_scores)
                avg_score = respondents and round(sum(problem_scores) / respondents, 2) or 0.0
                d_value = calc_discrimination_index(learner_groups, learner_score_map)
                effectiveness = get_effectiveness_of_question(d_value)
                problems.append({
                    "id": problem_id,
                    "display_name": problem.display_name,
                    "difficulty_level": problem.difficulty_level.capitalize(),
                    "respondents": respondents,
                    "d_value": d_value or '--',
                    "effectiveness": effectiveness,
                })

    # Sort problems by name
    return sorted(problems, key=lambda problem:problem["display_name"])


def get_problem_scores(student, course_key, exam_started_at):
    """
    Returns the list of dictionary containing
    score for each problem
    that has been assigned to the student.
    """
    def datetime_to_point(dt):
        return round((dt - exam_started_at).total_seconds())

    # Get all problems
    problems = []
    for sequential in modulestore().get_items(
        course_key,
        qualifiers={'category': 'sequential'}
    ):
        for vert in sequential.get_children():
            problems += vert.get_children()

    # Filter assigned questions
    easy, moderate, hard = QuestionSet.get_question_numbers(student.id, course_key)
    assigned_problems = {
        str(problems[question_num].location): problems[question_num]
        for question_num in easy + moderate + hard
    }

    # Get student modules
    user_anonymous_id = anonymous_id_for_user(student, course_key)

    student_modules = {}
    for sm in StudentModule.objects.filter(
        student=student,
        course_id=course_key,
        module_state_key__in=assigned_problems.keys(),
    ):
        state = json.loads(sm.state)
        last_submission_time = state.get("last_submission_time")

        if sm.module_type == EDX_SGA:
            sga_xblock = assigned_problems[six.text_type(sm.module_state_key)]
            submission = sga_xblock.get_submission(student_id=user_anonymous_id)

            # if submission is not finalized skip the problem
            if not submission.get("answer", {}).get("finalized", False):
                continue

            state = {
                "submission_uuid": submission.get("uuid") if submission else ""
            }

            last_submission_time = submission.get('submitted_at')
            submitted_at = last_submission_time

        if not last_submission_time:
            continue

        if not sm.module_type == EDX_SGA:
            submitted_at = pytz.utc.localize(
                datetime.strptime(last_submission_time, "%Y-%m-%dT%H:%M:%SZ"))

        student_modules[str(sm.module_state_key)] = {
            'sm': sm,
            'state': state,
            'submitted_at': submitted_at,
        }

    # Prepare report data
    problem_scores = []
    total_problem_count = len(student_modules.keys())
    prev_problem_submitted_at = exam_started_at
    max_score_show = round(100/total_problem_count) if total_problem_count > 0 else 0
    for problem_id, packet in sorted(
        student_modules.items(),
        key=lambda d: d[1]['submitted_at']
    ):
        problem = assigned_problems[problem_id]
        student_module = packet['sm']
        display_name = problem.display_name
        student_answer = _("Student answer not available")
        correct_answer = _("Correct answer not available")
        submitted_at = packet['submitted_at']
        earned = student_module.grade if student_module.grade is not None else 0.0
        is_openassessment_problem = student_module.module_type == OPEN_ASSESSMENT
        is_edx_sga_problem = student_module.module_type == EDX_SGA
        submission_uuid = ''
        attached_file = None
        attached_file_description = None
        max_score = problem.max_score()
        if hasattr(problem, "generate_report_data"):
            report_data = problem.generate_report_data([
                XBlockUserState(
                    student_module.student.username,
                    student_module.module_state_key,
                    packet['state'],
                    student_module.modified,
                    Scope.user_state
                )
            ])
            for username, readable_state in report_data:
                display_name = readable_state.get('Question', display_name)
                student_answer = readable_state.get('Answer', student_answer)
                correct_answer = readable_state.get('Correct Answer', correct_answer)

        # This is code block is only for openassessment xBlock.
        if is_openassessment_problem:
            submission_uuid = packet['state']['submission_uuid']
            student_answer, attached_file, attached_file_description = get_openassessment_data(submission_uuid)
            earned = get_openassessment_score_data(submission_uuid)

        # This is code block is only for edx_sga xBlock.
        if is_edx_sga_problem:
            submission_uuid = packet['state']['submission_uuid']
            attached_file = get_edx_sga_data(submission_uuid, problem)
            earned = get_openassessment_score_data(submission_uuid)

        problem_scores.append({
            "id": str(problem.location),
            "is_openassessment_problem": is_openassessment_problem,
            "is_edx_sga_problem": is_edx_sga_problem,
            "submission_uuid": submission_uuid,
            "attached_file": attached_file,
            "attached_file_description": attached_file_description,
            "display_name": display_name,
            "earned": earned,
            "earned_show": ((earned * max_score_show) / max_score) if max_score and max_score_show else earned,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "possible": max_score,
            "max_score_show": max_score_show,
            "submitted_at": submitted_at,
            "start_time_point": datetime_to_point(prev_problem_submitted_at),
            "finish_time_point": datetime_to_point(submitted_at),
            "attempted": True
        })
        # Current submission time becomes prev start time
        prev_problem_submitted_at = submitted_at

    # Append skipped questions
    skipped_problems = set(assigned_problems) - set(student_modules)
    for skipped_problem_id in skipped_problems:
        skipped_problem = assigned_problems[skipped_problem_id]
        problem_scores.append({
            "id": str(skipped_problem.location),
            "is_openassessment_problem": False,
            "is_edx_sga_problem": False,
            "submission_uuid": None,
            "attached_file": None,
            "attached_file_description": '',
            "display_name": skipped_problem.display_name,
            "earned": 0.0,
            "earned_show": 0.0,
            "student_answer": _("Student answer not available"),
            "correct_answer": _("Correct answer not available"),
            "possible": skipped_problem.max_score(),
            "max_score_show": 0.0,
            "submitted_at": None,
            "start_time_point": 0,
            "finish_time_point": 0,
            "attempted": False
        })

    return problem_scores


def get_openassessment_score_data(submission_uuid):
    """
    Return the earned scores for given submission of xblock.
    """
    score_earned = 0
    try:
        submission = Submission.objects.get(uuid=submission_uuid)
        score = ScoreSummary.objects.get(student_item=submission.student_item).latest
        score_earned = score.points_earned
    except (ScoreSummary.DoesNotExist, Submission.DoesNotExist):
        pass
    return score_earned


def get_openassessment_data(submission_uuid):
    """
    Return the attached file and its description associated with problem.
    """
    submission = Submission.objects.get(uuid=submission_uuid)
    submission_text = submission.answer.get('parts', [{'text': _("Student answer not available")}])[0]['text']
    attached_file = submission.answer.get('file_keys', "")
    attached_file_description = submission.answer.get('files_descriptions', "")
    if attached_file:
        attached_file = "{}/{}".format(settings.AWS_S3_ENDPOINT_URL, attached_file[0])
        attached_file_description = attached_file_description[0]
    return submission_text, attached_file, attached_file_description


def get_edx_sga_data(submission_uuid, problem):
    """
    Return the attached file and its description associated with problem.
    """
    submission = Submission.objects.get(uuid=submission_uuid)
    download_url = "/courses/{course_key}/xblock/{xblock_location}/handler/staff_download?student_id={student_anonymous_id}".format(
        course_key=six.text_type(problem.location.course_key),
        xblock_location=six.text_type(problem.location),
        student_anonymous_id=submission.student_item.student_id
    )
    return download_url
