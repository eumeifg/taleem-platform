
import logging
import math
import random
from datetime import datetime

from course_modes.models import CourseMode
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404
from django.utils import timezone
from django.utils.translation import get_language, ugettext as _
from edx_ace.recipient import Recipient
from edx_django_utils.monitoring import function_trace
from edx_proctoring.models import ProctoredExamStudentAttempt
from edx_proctoring.statuses import ProctoredExamStudentAttemptStatus
from opaque_keys.edx.keys import CourseKey
from six import iteritems, text_type
from xmodule.modulestore.django import modulestore
from xmodule.tabs import InvalidTabsException

from common.djangoapps.util.json_request import expect_json
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.djangoapps.user_authn.utils import generate_random_enrollment_code
from openedx.custom.offline_exam.models import OfflineExamStudentAttempt
from openedx.custom.offline_exam.statuses import OfflineExamStudentAttemptStatus
from openedx.custom.question_bank.utils import get_question_bank
from openedx.custom.taleem_grades.models import PersistentExamGrade
from openedx.custom.timed_exam.constants import (
    EXCLUDE, GRADING_POLICY, INCLUDE
)
from openedx.custom.timed_exam.forms import TimedExamForm
from openedx.custom.timed_exam.message_types import (CourseEnrollmentMessage, PendingEnrollment, TimedExamEnrollment,
                                                     TimedExamUnEnrollment)
from openedx.custom.timed_exam.models import QuestionSet, TimedExam, TimedExamAttempt
from openedx.custom.utils import cmp_to_key, format_date_time, get_minutes_from_time_duration, \
    local_datetime_to_utc_datetime, to_lower, utc_datetime_to_local_datetime
from openedx.custom.utils import get_email_context

log = logging.getLogger(__name__)


def get_exam_status(exam, user):
    attempted = False
    live_status = ''
    course_key = CourseKey.from_string(exam.key)
    try:
        exam_score = PersistentExamGrade.objects.get(
            course_id=course_key,
            user_id=user.id,
        ).percent_grade
    except PersistentExamGrade.DoesNotExist:
        exam_score = 0

    if exam.mode == 'ON':
        attempted = ProctoredExamStudentAttempt.objects.filter(user=user,
                proctored_exam__course_id=course_key,
                status=ProctoredExamStudentAttemptStatus.submitted).exists()
        live_status = ProctoredExamStudentAttempt.live_status(user,
                text_type(course_key))
    else:
        attempted = OfflineExamStudentAttempt.objects.filter(user=user,
                timed_exam=exam,
                status=OfflineExamStudentAttemptStatus.submitted).exists()

    disable_link = True
    btn_text = _('Start Exam')
    score = '--'
    btn_link = 'javascript:void(0);'

    if attempted:
        attempt_status = _('Completed')
        attempt_class = 'badge-success'
        score = exam_score
    elif live_status and live_status == 'attempting':
        attempt_status = _('Attempting')
        attempt_class = 'badge-info'
        btn_link = exam.exam_url
        disable_link = False
        btn_text = _('Resume Exam')
    elif live_status and live_status == 'dangling':
        attempt_status = _('Timed out')
        attempt_class = 'badge-warning'
    elif exam.due_date <= timezone.now():
        attempt_status = _('Missed')
        attempt_class = 'badge-danger'
        score = 0
    else:
        attempt_status = _('Yet to start')
        attempt_class = 'badge-primary'
        if exam.release_date < timezone.now() < exam.due_date:
            disable_link = False
            if QuestionSet.objects.filter(user=user,
                    course_id=exam.key).exists():
                btn_link = exam.exam_url
            else:
                btn_text = _('Preparing question set')

    return (
        attempt_status,
        attempt_class,
        btn_link,
        btn_text,
        score,
    )


def delete_timed_exam(timed_exam_id, user):
    """
    timed_exam_id (str): Course id for timed exam.
    user(User Object): User who is deleting the timed exam.

    Delete the timed exam course from mongo, its corresponding
    course overview records and all its enrollments.
    """
    from contentstore.utils import delete_course

    # Removing from the mongo
    delete_course(CourseKey.from_string(timed_exam_id), user.id)

    # Removing the course mode
    delete_timed_exam_mode(timed_exam_id)

    # Remove Timed exam record
    TimedExam.objects.filter(key=timed_exam_id).delete()

    # We don't need to inactive enrollments now as we are deleting only those
    # Timed exam which have zero enrollments, just commenting the code not removing.
    # course_enrollments = CourseEnrollment.objects.filter(course_id=timed_exam_id)
    # for enrollment in course_enrollments:
    #     enrollment.update_enrollment(is_active=False, skip_refund=True)


def save_timed_exam(time_exam_id, form_data, num_questions_pulled, user):
    code = str(generate_random_enrollment_code()) if form_data['generate_enrollment_code'] else ''

    time_exam, __ = TimedExam.objects.update_or_create(
        key=time_exam_id,
        defaults=dict(
            user_id=user.id,
            display_name=form_data['display_name'],
            question_bank=form_data['question_bank'],
            due_date=form_data['timed_exam_due_date'],
            release_date=form_data['timed_exam_release_date'],
            allotted_time=form_data['timed_exam_allotted_time'],
            allowed_disconnection_window=form_data['allowed_disconnection_window'],
            is_randomized=form_data['is_randomized'],
            is_bidirectional=form_data['is_bidirectional'],
            mode=form_data['exam_mode'],
            skill=form_data['skill'],
            round=form_data['round'],
            exam_type=form_data['exam_type'],
            generate_enrollment_code=form_data['generate_enrollment_code'],
            enable_monitoring=form_data['enable_monitoring'],
            enrollment_code=code,
            easy_question_count=form_data['question_count_of_easy_difficulty'],
            optional_easy_question_count=form_data['optional_easy_question_count'],
            moderate_question_count=form_data['question_count_of_medium_difficulty'],
            optional_moderate_question_count=form_data['optional_medium_question_count'],
            hard_question_count=form_data['question_count_of_hard_difficulty'],
            optional_hard_question_count=form_data['optional_hard_question_count'],
            num_easy_questions_pulled=num_questions_pulled['easy'],
            num_moderate_questions_pulled=num_questions_pulled['moderate'],
            num_hard_questions_pulled=num_questions_pulled['hard'],
            chapters=','.join(form_data['chapters']),
            chapters_include_exclude=form_data['chapters_include_exclude'],
            topics=','.join(form_data['topics']),
            topics_include_exclude=form_data['topics_include_exclude'],
            learning_output=','.join(form_data['learning_output']),
            learning_output_include_exclude=form_data['learning_output_include_exclude'],
        ),
    )
    return time_exam


def create_timed_exam_mode(course_key):
    """
    Create the timed course mode in LMS.
    """

    CourseMode.objects.get_or_create(course_id=course_key, mode_display_name="Timed", mode_slug=CourseMode.TIMED)


def create_run():
    """
    Returns a course run to be used in timed exam.

    It would be of the following format
     `{current-year}T{current-quarter-of-the-year}`
    """
    now = datetime.now()
    return '{year}T{quarter}'.format(
        year=now.year,
        quarter=math.ceil(now.month/3)
    )


def create_course_xblock(user, parent_locator, display_name, category):
    """
    Create a course xblock, this could be a course section, sub section or a unit.

    Arguments:
        user (User): User object who would is the owner of the course.
        parent_locator (str): Locator of the parent xblock.
        display_name (str): Name of the Section
        category (str): Section category e.g. 'chapter'
    """
    # Import is placed here to avoid circular import
    from contentstore.views.helpers import create_xblock
    from contentstore.views.item import create_xblock_info

    created_block = create_xblock(
        parent_locator=parent_locator,
        user=user,
        category=category,
        display_name=display_name,
    )
    create_xblock_info(
        created_block,
        include_child_info=True,
        course_outline=True,
        include_children_predicate=lambda xblock: not xblock.category == 'vertical'
    )
    return created_block


def update_grading_for_timed_exam(user, course_key):
    """
    Update the grading policy for timed exam.

    Arguments:
        user (User): User object who is the owner of the course.
        course_key (str): Locator of the course.
    """
    from models.settings.course_grading import CourseGradingModel
    CourseGradingModel.update_from_json(course_key, GRADING_POLICY, user)


def create_units(user, question_bank, parent, form_data):
    """
    Create units for the timed exam.

    Each unit will contain the problem added in the question bank.

    Arguments:
        user (User): Course author making the request.
        question_bank (Library): A question bank, containing questions for the timed exam.
        parent (XBlock): Parent x-block, normally a sub section.
        form_data (dict): Data from the TimedExamForm.
    """
    # Import is placed here to avoid circular import
    from contentstore.views.item import _save_xblock

    problems = apply_filters(
        question_bank.get_children(),
        filters={
            # 'is_randomized': form_data['is_randomized'],
            # 'question_count_of_easy_difficulty': form_data['question_count_of_easy_difficulty'],
            # 'question_count_of_medium_difficulty': form_data['question_count_of_medium_difficulty'],
            # 'question_count_of_hard_difficulty': form_data['question_count_of_hard_difficulty'],
            'chapters': [to_lower(chapter) for chapter in form_data['chapters']],
            'chapters_include_exclude': form_data['chapters_include_exclude'],
            'topics': [to_lower(topic) for topic in form_data['topics']],
            'topics_include_exclude': form_data['topics_include_exclude'],
            'learning_output': [to_lower(learning_output) for learning_output in form_data['learning_output']],
            'learning_output_include_exclude': form_data['learning_output_include_exclude'],
        },
    )

    # Sort problems by difficulty level
    sorting_weight = {'easy': 1, 'moderate': 2, 'hard': 3}
    def difficulty_level_cmp(p1, p2):
        return sorting_weight[p1.difficulty_level] - sorting_weight[p2.difficulty_level]
    problems.sort(key=cmp_to_key(difficulty_level_cmp))

    num_questions_pulled = {'easy': 0, 'moderate': 0, 'hard': 0}
    for problem in problems:
        unit = create_course_xblock(
            user=user,
            parent_locator=text_type(parent.location),
            category='vertical',
            display_name='Question',
        )
        new_problem = create_course_xblock(
            user=user,
            parent_locator=text_type(unit.location),
            category=problem.category,
            display_name='Question',
        )

        fields = get_problem_metadata(problem)

        # If its an ORA2 xblock we need to save the
        # submission_due and submission_start explicitly.
        if problem.category in ['openassessment']:
            timed_exam_start_date = format_date_time(local_datetime_to_utc_datetime(form_data['timed_exam_release_date']))
            timed_exam_end_date = format_date_time(local_datetime_to_utc_datetime(form_data['timed_exam_due_date']))
            rubric_assessments = fields['rubric_assessments']

            # Changing the staff assessment dates so we don't get conflict in LMS side.
            for rubric_assessment in rubric_assessments:
                if rubric_assessment['name'] == 'staff-assessment':
                    rubric_assessment['start'] = timed_exam_start_date
                    rubric_assessment['end'] = timed_exam_end_date

            fields['submission_start'] = timed_exam_start_date
            fields['submission_due'] = timed_exam_end_date

        _save_xblock(
            user=user,
            xblock=new_problem,
            data=getattr(problem, 'data', None),
            fields=fields,
        )
        num_questions_pulled[problem.difficulty_level] += 1

    return num_questions_pulled


def get_problem_metadata(source):
    """
    Get problem metadata from source.

    Some fields need to be skipped.
    """
    fields_to_skip = {'parent'}
    fields = {}
    for field in source.fields.keys():
        if field not in fields_to_skip:
            fields[field] = getattr(source, field, None)

    return fields


def apply_filters(problems, filters):
    """
    Apply filters to the problems.
    """
    filter_funcs = {
        'chapters': create_include_exclude_filter(
            include_exclude=filters['chapters_include_exclude'],
            items_to_include_or_exclude=filters['chapters'],
            key=lambda item: to_lower(getattr(item, 'chapter', None)),
        ),
        'topics': create_include_exclude_filter(
            include_exclude=filters['topics_include_exclude'],
            items_to_include_or_exclude=filters['topics'],
            key=lambda item: to_lower(getattr(item, 'topic', None)),
        ),
        'learning_output': create_include_exclude_filter(
            include_exclude=filters['learning_output_include_exclude'],
            items_to_include_or_exclude=filters['learning_output'],
            key=lambda item: to_lower(getattr(item, 'learning_output', None)),
        ),
    }

    problems = filter(filter_funcs['chapters'], problems)
    problems = filter(filter_funcs['topics'], problems)
    problems = filter(filter_funcs['learning_output'], problems)
    problems = list(problems)

    # A temporary dict to hold filtered problems
    # filtered_problems = {
    #     'easy_problems': [],
    #     'medium_problems': [],
    #     'hard_problems': []
    # }
    # filtered_problems['easy_problems'].extend(apply_difficulty_level_filter(
    #     problems=problems,
    #     difficulty_level=DIFFICULTYLEVEL.EASY,
    #     count=filters['question_count_of_easy_difficulty'],
    #     is_randomized=filters['is_randomized']
    # ))
    # filtered_problems['medium_problems'].extend(apply_difficulty_level_filter(
    #     problems=problems,
    #     difficulty_level=DIFFICULTYLEVEL.MODERATE,
    #     count=filters['question_count_of_medium_difficulty'],
    #     is_randomized=filters['is_randomized'],
    # ))
    # filtered_problems['hard_problems'].extend(apply_difficulty_level_filter(
    #     problems=problems,
    #     difficulty_level=DIFFICULTYLEVEL.HARD,
    #     count=filters['question_count_of_hard_difficulty'],
    #     is_randomized=filters['is_randomized']
    # ))
    # problems = []
    # if filters['is_randomized']:
    #     # Randomization the difficulty levels
    #     difficult_level_list = list(filtered_problems.keys())
    #     random.shuffle(difficult_level_list)

    #     for difficult_level in difficult_level_list:
    #         questions = filtered_problems[difficult_level]
    #         # randomization within difficulty levels.
    #         random.shuffle(questions)
    #         problems.extend(questions)
    return problems


def create_include_exclude_filter(include_exclude, items_to_include_or_exclude, key=None):
    """
    Create a filter for fields.
    """
    key = key if key is not None else lambda item: item
    if include_exclude == INCLUDE:
        # Only add items then are present in the `items_to_include` argument.
        return lambda item: key(item) in items_to_include_or_exclude
    elif include_exclude == EXCLUDE:
        # Only add items then are NOT present in the `items_to_exclude` argument.
        return lambda item: key(item) not in items_to_include_or_exclude

    # Do not filter anything
    return lambda item: True


def apply_difficulty_level_filter(problems, difficulty_level, count, is_randomized):
    """
    Apply the filter for questions by difficulty level.
    """
    problems_to_return = []
    # Only add `count` number of easy questions.
    counter = 0
    from openedx.custom.question_bank.utils import get_difficulty_level_problems
    all_problems = get_difficulty_level_problems(problems, difficulty_level)

    if is_randomized:
        random.shuffle(all_problems)

    for problem in all_problems:
        if counter >= count:
            break
        problems_to_return.append(problem)
        counter += 1
    return problems_to_return


def update_advanced_settings(request, course, settings):
    """
    Update the advanced settings of the given course.

    Arguments:
        request (Request): HttpRequest object.
        course (modulestore().Course): Course object.
        settings (dict): A dictionary with keys mapping to setting name and value to setting value.
    """
    # Import is placed here to avoid circular imports
    from contentstore.views.course import _refresh_course_tabs
    from models.settings.course_metadata import CourseMetadata

    course_settings = CourseMetadata.fetch(course)
    for key, value in iteritems(settings):
        if key not in course_settings:
            raise KeyError("Invalid advanced setting: '{}' is not a known advanced setting.".format(key))
        course_settings[key].update({'value': value})

    is_valid, errors, updated_data = CourseMetadata.validate_and_update_from_json(
        course,
        course_settings,
        user=request.user,
    )

    if is_valid:
        try:
            # update the course tabs if required by any setting changes
            _refresh_course_tabs(request, course)
        except InvalidTabsException as err:
            log.exception(text_type(err))

        # now update mongo
        modulestore().update_item(course, request.user.id)


def convert_to_timed_exam(user, sub_section, grade_as, release_date, due_date, allotted_time):
    """
    Convert the course sub section to a timed exam.

    Arguments:
        user (User): User making the request.
        sub_section (XBlock): Course sub section x block containing all the problem units.
        grade_as (str): String showing how to grade this section e.g. `notgraded`, `Final Exam`
        release_date (datetime): A date time object pointing the release date.
        due_date (datetime): A date time object pointing the due date.
        allotted_time (str): Allotted time in minutes.
    """
    # Import is placed here to avoid circular imports
    from contentstore.views.item import _save_xblock
    from contentstore.views.item import create_xblock_info

    _save_xblock(
        user,
        sub_section,
        metadata={
            'start': format_date_time(release_date),
            'due': format_date_time(due_date),
            'default_time_limit_minutes': get_minutes_from_time_duration(allotted_time),
            'is_onboarding_exam': False,
            'show_correctness': 'never',
            'is_practice_exam': False,
            'is_proctored_enabled': False,
            'is_time_limited': True,
        },
        grader_type=grade_as,
    )
    create_xblock_info(
        sub_section,
        include_child_info=True,
        course_outline=True,
        include_children_predicate=lambda xblock: not xblock.category == 'vertical'
    )


def publish(xblock, user, release_date=None):
    """
    Publish x block a;ll its children.
    """
    # Import is placed here to avoid circular imports
    from contentstore.views.item import _save_xblock
    from contentstore.views.item import create_xblock_info

    _save_xblock(
        user,
        xblock,
        publish='make_public',
        metadata={'start': format_date_time(release_date)} if release_date else None
    )
    create_xblock_info(
        xblock,
        include_child_info=True,
        course_outline=True,
        include_children_predicate=lambda xblock: not xblock.category == 'vertical'
    )


def check_write_permission_or_raise(user, timed_exam_key):
    """
    Check whether given user has write permission for given
    timed exam key if not then raise the exception
    """
    from student.auth import has_studio_write_access

    if not has_studio_write_access(user, timed_exam_key):
        log.exception(
            u"User %s tried to update timed exam %s without permission",
            user.username, text_type(timed_exam_key)
        )
        raise PermissionDenied()


def check_read_permission_or_raise(user, timed_exam_key):
    """
    Check whether given user has read permission for given
    timed exam key if not then raise the exception
    """
    from student.auth import has_studio_read_access

    if not has_studio_read_access(user, timed_exam_key):
        log.exception(
            u"User %s tried to access timed exam %s without permission",
            user.username, text_type(timed_exam_key)
        )
        raise PermissionDenied()


def check_timed_exam_or_raise(timed_exam, timed_exam_key_string):
    """
    Check whether given timed exam exists in mongo
    and mysql if not then raise the exception
    """
    if timed_exam is None:
        log.exception(u"Timed Exam %s not found.", text_type(timed_exam_key_string))
        raise Http404

    if not TimedExam.objects.filter(key=timed_exam_key_string).exists():
        log.exception(u"Timed Exam Model Instance %s not found.", text_type(timed_exam_key_string))
        raise Http404


def delete_timed_exam_mode(course_key):
    """
    Delete the timed course mode in LMS.
    """

    CourseMode.objects.filter(course_id=course_key).delete()


def create_timed_exam_content(request, timed_exam, form_data):
    """
    Create the content of timed exam, section, subsection and units

    Arguments:
        request (HttpRequest): Http Request object.
        timed_exam (modulestore()): Timed exam object.
        form_data (dict): A dictionary containing validated timed exam data.
    """
    question_bank = get_question_bank(form_data['question_bank'])

    utc_release_date = local_datetime_to_utc_datetime(form_data['timed_exam_release_date'])
    utc_due_date = local_datetime_to_utc_datetime(form_data['timed_exam_due_date'])
    update_advanced_settings(
        request=request,
        course=timed_exam,
        settings={
            'display_name': form_data['display_name'],
            'enable_timed_exams': True,
            'enable_proctored_exams': True,
            'invitation_only': form_data['exam_type'] == TimedExam.INVITE_ONLY,
        }
    )

    # Add a section to the timed exam course
    section = create_course_xblock(
        user=request.user,
        parent_locator=text_type(timed_exam.location),
        display_name=question_bank.display_name,
        category='chapter',
    )

    # publishing the section
    publish(section, request.user, utc_release_date)

    # Add a sub-section to the timed exam course
    sub_section = create_course_xblock(
        user=request.user,
        parent_locator=text_type(section.location),
        display_name=question_bank.display_name,
        category='sequential',
    )

    # convert the sub-section into a Timed exam
    convert_to_timed_exam(
        user=request.user,
        sub_section=sub_section,
        grade_as='Final Exam',
        release_date=utc_release_date,
        due_date=utc_due_date,
        allotted_time=form_data['timed_exam_allotted_time'],
    )

    # Add units in the subsection
    num_questions_pulled = create_units(
        user=request.user,
        question_bank=question_bank,
        parent=sub_section,
        form_data=form_data,
    )

    # Again, publishing the section so everything in it also get publish.
    publish(section, request.user, utc_release_date)

    # save the timed exam field in mysql for edit
    save_timed_exam(timed_exam.id, form_data, num_questions_pulled, request.user)


@expect_json
def update_timed_exam_dates(request, timed_exam_key):
    """
    RESTful interface to the edit the course core fields.
    """
    form = TimedExamForm(request.json)
    if form.is_valid():
        fields = {
            'start_date': local_datetime_to_utc_datetime(form.cleaned_data['timed_exam_release_date']),
            'end_date': local_datetime_to_utc_datetime(form.cleaned_data['timed_exam_due_date']),
        }
        CourseDetails.update_from_json(timed_exam_key, fields, request.user)


def send_enrollment_email(user_id, mode="timed"):
    """
    Send an enrollment email to the user.

    Email will be sent via a celery task.

    Arguments:
        user_id (long): User ID to whom we need to send the email.
    """
    # Import is placed here to avoid circular imports
    from openedx.custom.timed_exam.tasks import send_email_task

    try:
        recipient = User.objects.get(id=user_id)
    except Exception as e:
        return str(e)

    if mode == CourseMode.TIMED:
        Message = TimedExamEnrollment
    else:
        Message = CourseEnrollmentMessage

    msg = Message().personalize(
        recipient=Recipient(recipient.username, recipient.email),
        language=preferences_api.get_user_preference(recipient, LANGUAGE_KEY),
        user_context=get_email_context(),
    )

    send_email_task.delay(str(msg))


def send_pending_enrollment_email(recipient_email):
    """
    Send an enrollment email to the user whose enrollment is pending registration.

    Email will be sent via a celery task.

    Arguments:
        recipient_email (str): User email where we need to send the email.
    """
    # Import is placed here to avoid circular imports
    from openedx.custom.timed_exam.tasks import send_email_task

    msg = PendingEnrollment().personalize(
        recipient=Recipient(username='', email_address=recipient_email),
        language=get_language(),
        user_context=get_email_context(),
    )

    msg.options.update({
        'output_file_path': '/edx/src/ace_messages/{recipient_email}-{date:%Y%m%d-%H%M%S}.html'.format(
            recipient_email=recipient_email,
            date=datetime.now()
        )
    })

    send_email_task.delay(str(msg))


def send_unenrolling_email(user_id, mode="timed"):
    # Import is placed here to avoid circular imports
    from openedx.custom.timed_exam.tasks import send_email_task

    try:
        recipient = User.objects.get(id=user_id)
    except Exception as e:
        return str(e)

    msg = TimedExamUnEnrollment().personalize(
        recipient=Recipient(recipient.username, recipient.email),
        language=preferences_api.get_user_preference(recipient, LANGUAGE_KEY),
        user_context=get_email_context(),
    )

    send_email_task.delay(str(msg))


def does_timed_exam_has_attempts(timed_exam_key_str):
    """
    Check if given timed exam has any enrollments.

    Arguments:
        timed_exam_key_str (str): Timed Exam key in string form.
    """
    return ProctoredExamStudentAttempt.objects.filter(
        proctored_exam__course_id=timed_exam_key_str,
    ).exists()


def get_users_verification_status(users):
    """
    Return the ID verification statuses of given students.
    """
    statuses = []
    for user in users:
        status = 'submitted'
        attempt = IDVerificationService.get_recent_verification_for_user(user)
        if attempt:
            status = attempt.status
        statuses.append(status)
    return statuses


def get_suspicion_level(num_session_violations, num_tab_violations,
    num_snapshots_taken, num_face_not_found,
    num_multiple_faces, num_unknown_face):
    """
    Calculate and return suspicion level based on
    the given number of violations and settings
    about the penalty weight.
    """
    penalty = settings.PROCTORING_VIOLATION_PENALTY
    percent_face_not_found = (
        num_face_not_found * 1.0 / num_snapshots_taken
    ) if num_snapshots_taken else 0

    points = 0
    if num_session_violations:
        points += penalty['session_disconnect']

    if num_tab_violations:
        points += penalty['tab_switch']

    if percent_face_not_found:
        points += penalty['face_not_found']

    if num_multiple_faces:
        points += penalty['multiple_faces']

    if num_unknown_face:
        points += penalty['unknown_face']

    suspicion_level = round(points * 100.0 / sum(penalty.values()), 2)

    # Bootstrap class to highlight
    if suspicion_level < settings.PROCTORING_VIOLATION_IGNORE_LIMIT:
        suspicion_class = 'success'
    elif suspicion_level >= settings.PROCTORING_VIOLATION_WARN_LIMIT:
        suspicion_class = 'danger'
    else:
        suspicion_class = 'warning'

    return suspicion_level, suspicion_class


def mark_timed_exam_attempt(user, timed_exam_id, ip_address):
    """
    Save user's attempt at the timed exam.

    Arguments:
       user (User): User attempting the timed exam.
       timed_exam_id (str): Key to the timed exam.
       ip_address (str): User's IP address.
    """
    TimedExamAttempt.objects.get_or_create(
        user=user,
        timed_exam_id=timed_exam_id,
        ip_address=ip_address,
    )


def get_timed_exam_attempt(timed_exam_id, user):
    try:
        attempt = ProctoredExamStudentAttempt.objects.get(proctored_exam__course_id=timed_exam_id, user=user)
    except ProctoredExamStudentAttempt.DoesNotExist:
        attempt = None
    return attempt


@function_trace('get_browsable_exams')
def get_browsable_exams():
    """
    Get public exams which are not yet expired.
    """
    return TimedExam.objects.filter(
        exam_type=TimedExam.PUBLIC,
        due_date__gt=timezone.now(),
    )


def get_attempted_at(exam_key, student):
    """
    Get the time of the attempted exam.
    """
    # Get the student attempt for the exam
    attempt = ProctoredExamStudentAttempt.objects.get(proctored_exam__course_id=exam_key, user=student)

    return utc_datetime_to_local_datetime(attempt.completed_at).isoformat()


def is_user_attempted_exam(student, exam):
    exam_key = CourseKey.from_string(exam.key)
    if exam.mode == 'ON':
        attempted = ProctoredExamStudentAttempt.objects.filter(
            user=student,
            proctored_exam__course_id=exam_key,
            status=ProctoredExamStudentAttemptStatus.submitted).exists()
    else:
        attempted = OfflineExamStudentAttempt.objects.filter(
            user=student,
            timed_exam=exam,
            status=OfflineExamStudentAttemptStatus.submitted
        ).exists()

    return attempted
