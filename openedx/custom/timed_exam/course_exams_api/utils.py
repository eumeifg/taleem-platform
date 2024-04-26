import json
import logging
import re

from django.http import Http404, HttpResponseBadRequest
from edx_proctoring.api import (
    create_exam_attempt,
    start_exam_attempt,
    stop_exam_attempt,
    update_attempt_status,
    get_exam_attempt_by_id,
)
from edx_proctoring.models import ProctoredExam
from edx_proctoring.models import ProctoredExamReview, ProctoredExamStudentAttempt
from edx_proctoring.statuses import ProctoredExamStudentAttemptStatus
from edx_proctoring.utils import get_time_remaining_for_attempt
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from six import text_type
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from openedx.core.lib.exceptions import CourseNotFoundError
from openedx.custom.timed_exam.models import TimedExam
from openedx.custom.timed_exam.utils import get_attempted_at

log = logging.getLogger(__name__)
VALID_QUESTION_TYPES = ["ProblemBlockWithMixins", "StaffGradedAssignmentXBlockWithMixins"]


def get_course_exams_for_user(request, course_key):
    exam_components = modulestore().get_items(
        course_key,
        qualifiers={'category': 'exams'}
    )

    exam_keys = [
        exam.exam_id
        for exam in exam_components
        if exam.exam_id and CourseEnrollment.is_enrolled(
            request.user,
            CourseKey.from_string(exam.exam_id),
        )
    ]

    return TimedExam.objects.filter(key__in=exam_keys)


def check_course_access(request, course_key):
    try:
        _ = get_course_with_access(request.user, 'load', course_key)
    except Http404:
        # Convert 404s into CourseNotFoundErrors.
        raise CourseNotFoundError("Course not found.")
    except CourseAccessRedirect:
        # Raise course not found if the user cannot access the course
        # since it doesn't make sense to redirect an API.
        raise CourseNotFoundError("Course not found.")


def get_review_status(course_id, student):
    # Get the course key
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    completed_at = get_attempted_at(course_key, student)

    status = {
        'course_id': course_id,
        'review_status': ProctoredExamReview.get_review_status(student, course_id),
        'submitted_at': completed_at
    }

    return status


def get_problem_json(problem, exam_key, for_report=False):
    problem_json = {}
    if type(problem).__name__ == "StaffGradedAssignmentXBlockWithMixins":
        problem_json = get_sga_question_json(problem, exam_key, for_report)
    elif type(problem).__name__ == "ProblemBlockWithMixins":
        if hasattr(problem, "problem_types") and list(problem.problem_types)[0] == "multiplechoiceresponse":
            problem_json = get_multiple_choice_question_json(problem, exam_key, for_report)

    return problem_json


def get_multiple_choice_question_json(problem, exam_key, for_report=False):
    response = {}
    question_type = "multi-choice"
    problem_markdown = problem.markdown

    try:
        problem_json = json.loads(problem_markdown)
    except json.JSONDecodeError:
        log.error("Error while parsing the markdown into JSON for problem_id: {}.".format(text_type(problem.location)))

        return {
            "error": "Problem is not edited by course staff yet."
        }

    problem_title = problem_json['config']['title']
    images_in_question = get_image_from_question_description(problem_json['config']['description'])

    if len(images_in_question):
        question_type = "multi-choice-image"
        response['images'] = images_in_question

    options = []
    problem_choices = problem_json['config']['options']

    for choice in problem_choices:
        choice_obj = {'value': choice['label'], 'id': 'choice_{id}'.format(id=choice['name'])}
        options.append(choice_obj)
        if for_report and choice['correct'] == 'true':
            response['correct_answer'] = 'choice_{id}'.format(id=choice['name'])

    input_state = ""
    if problem.input_state and type(problem.input_state) == dict and problem.input_state.keys():
        input_state = list(problem.input_state.keys())[0]
    else:
        input_state = "{problem_html_id}_2_1".format(problem_html_id=problem.location.html_id())

    student_answer = ""

    if problem.is_submitted():
        student_answer = problem.student_answers[input_state]

    input_state = "input_{}".format(input_state)

    block_id = text_type(problem.location)

    response.update({
        "title": problem_title,
        "choices": options,
        "problem_type": question_type,
        "attempted": problem.is_submitted(),
        "block_id": block_id,
        "student_answer": student_answer
    })

    if not for_report:
        response.update({
            "submit_key": input_state,
            "submit_url": "/courses/{exam_key}/xblock/{block_id}/handler/xmodule_handler/problem_check".format(
                exam_key=exam_key,
                block_id=block_id
            )
        })

    return response


def get_image_from_question_description(question_description):
    jpeg_images = re.findall("(?<=data:image/jpeg;base64,)[^\"]*", question_description)
    png_images = re.findall("(?<=data:image/png;base64,)[^\"]*", question_description)
    jpg_images = re.findall("(?<=data:image/jpg;base64,)[^\"]*", question_description)

    return jpeg_images + png_images + jpg_images


def get_sga_question_json(problem, exam_key, for_report=False):
    student_state = problem.student_state()
    block_id = text_type(problem.location)
    attempted = problem.has_attempted()

    file_uploaded_name = ""

    if attempted:
        uploaded = student_state.pop('uploaded')
        file_uploaded_name = uploaded['filename']

    question_json = {
        "title": student_state.pop('display_name'),
        "attempted": attempted,
        "problem_type": "descriptive-file-upload",
        "block_id": block_id,
        "file_uploaded_name": file_uploaded_name
    }

    if for_report and problem.has_attempted():
        student_score = ""
        if student_state['graded']:
            graded = student_state.pop('graded')
            if 'score' in graded.keys():
                student_score = graded['score']

        question_json.update({
            "student_score": student_score
        })

    if not for_report:
        question_json.update({
            "max_upload_size": problem.student_upload_max_size(),
            "upload_allowed": student_state.pop("upload_allowed"),
            "base_asset_url": student_state.pop("base_asset_url"),
            "file_upload_url": "/courses/{exam_key}/xblock/{block_id}/handler/upload_assignment".format(
                exam_key=exam_key,
                block_id=block_id
            ),
            "submit_url": "/courses/{exam_key}/xblock/{block_id}/handler/finalize_uploaded_assignment".format(
                exam_key=exam_key,
                block_id=block_id
            ),
        })

    return question_json


def is_valid_question_type(problem):
    is_valid = False
    if type(problem).__name__ == "StaffGradedAssignmentXBlockWithMixins":
        is_valid = True
    elif type(problem).__name__ == "ProblemBlockWithMixins":
        if (hasattr(problem, "problem_types") and problem.problem_types and
                list(problem.problem_types)[0] == "multiplechoiceresponse"):
            is_valid = True

    return is_valid


def get_total_number_of_question_in_exam(exam_key):
    """
    WARNING: DEPRECATED, use timed_exam.count_questions instead
    """
    total_question_count = 0
    for block in modulestore().get_items(
        exam_key,
        qualifiers={'category': 'problem'}
    ):
        if is_valid_question_type(block):
            total_question_count += 1

    for block in modulestore().get_items(
        exam_key,
        qualifiers={'category': 'edx_sga'}
    ):
        if is_valid_question_type(block):
            total_question_count += 1

    return total_question_count


def start_exam_for_user(exam_key, user):
    exam = ProctoredExam.objects.get(course_id=exam_key, is_active=True)
    attempt = ProctoredExamStudentAttempt.objects.filter(
        proctored_exam_id=exam.id,
        user=user,
    ).first()

    if not attempt:
        create_exam_attempt(exam.id, user.id)
        attempt_id = start_exam_attempt(
            exam.id,
            user.id
        )
    else:
        attempt_id = attempt.id

    return get_time_remaining_for_attempt(
        get_exam_attempt_by_id(attempt_id)
    )


def submit_exam_for_user(exam_key, user):
    is_attempt_available = False
    timed_out = False
    exam = ProctoredExam.objects.get(course_id=exam_key, is_active=True)
    try:
        attempt = ProctoredExamStudentAttempt.objects.get(
            proctored_exam_id=exam.id,
            user=user,
        )
    except:
        return is_attempt_available, timed_out

    is_attempt_available = True
    if not attempt.status == ProctoredExamStudentAttemptStatus.submitted:
        remaining_time = get_time_remaining_for_attempt({
            'started_at': attempt.started_at,
            'allowed_time_limit_mins': attempt.allowed_time_limit_mins,
        })
        timed_out = remaining_time == 0
        stop_exam_attempt(exam.id, user.id)
        update_attempt_status(
            exam.id,
            user.id,
            ProctoredExamStudentAttemptStatus.submitted
        )

    return is_attempt_available, timed_out
