
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.util.json_request import JsonResponse, expect_json
from contentstore.views.helpers import usage_key_with_run
from openedx.custom.question_bank.utils import (
    delete_question_bank_handler,
    get_grouped_tags,
    get_question_bank,
    get_question_bank_stats,
    get_question_bank_stats_with_tags,
)
from student.auth import (
    STUDIO_EDIT_ROLES,
    STUDIO_VIEW_USERS,
    get_user_permissions,
)

from openedx.custom.timed_exam.forms import TimedExamForm
from openedx.custom.timed_exam.utils import apply_filters
from openedx.custom.utils import to_lower
from openedx.custom.timed_exam.constants import (
    EXCLUDE, INCLUDE
)
from openedx.custom.question_bank.utils import xblock_deletion_allow

from xmodule.capa_base import DIFFICULTYLEVEL
log = logging.getLogger(__name__)


@login_required
@require_http_methods(('GET', ))
def question_tags_handler(request, course_key_string):
    """
    RESTful interface to get question tags.
    """
    question_bank_key_string = course_key_string
    return JsonResponse(
        get_grouped_tags(question_bank_key_string)
    )


@login_required
@require_http_methods(('GET', ))
def get_question_bank_statistics(request, course_key_string):
    """
    RESTful interface to get question tags.
    """
    statistics = get_question_bank_stats(course_key_string)
    return JsonResponse(statistics)


@expect_json
@login_required
@require_http_methods(('POST', ))
def get_question_bank_statistic_with_tags(request):
    """
    RESTful interface to get timed exam's question stat.
    """
    form = TimedExamForm(request.json)
    statistics = {}
    if form.is_valid():
        form_data = form.cleaned_data
        question_bank = get_question_bank(form_data['question_bank'])
        selected_chapters = [to_lower(chapter) for chapter in form_data['chapters']]
        selected_topics = [to_lower(topic) for topic in form_data['topics']]
        selected_learning_output = [to_lower(learning_output) for learning_output in form_data['learning_output']]
        statistics = get_question_bank_stats_with_tags(
            apply_filters(
                question_bank.get_children(),
                filters={
                    'is_randomized': form_data['is_randomized'],
                    'question_count_of_easy_difficulty': form_data['question_count_of_easy_difficulty'],
                    'question_count_of_medium_difficulty': form_data['question_count_of_medium_difficulty'],
                    'question_count_of_hard_difficulty': form_data['question_count_of_hard_difficulty'],
                    'chapters': selected_chapters,
                    'chapters_include_exclude': form_data['chapters_include_exclude'],
                    'topics': selected_topics,
                    'topics_include_exclude': form_data['topics_include_exclude'],
                    'learning_output': selected_learning_output,
                    'learning_output_include_exclude': form_data['learning_output_include_exclude'],
                },
            )
        )
        available_easy_chapters = statistics['chapters'][DIFFICULTYLEVEL.EASY]
        available_moderate_chapters = statistics['chapters'][DIFFICULTYLEVEL.MODERATE]
        available_hard_chapters = statistics['chapters'][DIFFICULTYLEVEL.HARD]

        available_easy_topics = statistics['topics'][DIFFICULTYLEVEL.EASY]
        available_moderate_topics = statistics['topics'][DIFFICULTYLEVEL.MODERATE]
        available_hard_topics = statistics['topics'][DIFFICULTYLEVEL.HARD]

        available_easy_learning_output = statistics['learning_output'][DIFFICULTYLEVEL.EASY]
        available_moderate_learning_output = statistics['learning_output'][DIFFICULTYLEVEL.MODERATE]
        available_hard_learning_output = statistics['learning_output'][DIFFICULTYLEVEL.HARD]

        statistics['feedback'] = {
            'easy': {
                'chapters': '',
                'topics': '',
                'learning_output': ''
            },
            'moderate': {
                'chapters': '',
                'topics': '',
                'learning_output': ''
            },
            'hard': {
                'chapters': '',
                'topics': '',
                'learning_output': ''
            },

        }

        if form_data['chapters_include_exclude'] == INCLUDE:
            if len(set(selected_chapters) - set(available_easy_chapters)) > 0:
                statistics['feedback']['easy']['chapters'] = 'Chapters: ' + ', '.join(
                    ['Chapter {}'.format(item) for item in (set(selected_chapters) - set(available_easy_chapters))]
                )

            if len(set(selected_chapters) - set(available_moderate_chapters)) > 0:
                statistics['feedback']['moderate']['chapters'] = 'Chapters: ' + ', '.join(
                    ['Chapter {}'.format(item) for item in (set(selected_chapters) - set(available_moderate_chapters))]
                )
            if len(set(selected_chapters) - set(available_hard_chapters)) > 0:
                statistics['feedback']['hard']['chapters'] = 'Chapters: ' + ', '.join(
                    ['Chapter {}'.format(item) for item in (set(selected_chapters) - set(available_hard_chapters))]
                )
        elif form_data['chapters_include_exclude'] == EXCLUDE:
            if len(set(selected_chapters).intersection(available_easy_chapters)) > 0:
                statistics['feedback']['easy']['chapters'] = 'Chapters: ' + ', '.join(
                    ['Chapter {}'.format(item) for item in set(selected_chapters).intersection(available_easy_chapters)]
                )

            if len(set(selected_chapters).intersection(available_moderate_chapters)) > 0:
                statistics['feedback']['moderate']['chapters'] = 'Chapters: ' + ', '.join(
                    [
                        'Chapter {}'.format(item) for item in
                        set(selected_chapters).intersection(available_moderate_chapters)
                    ]
                )

            if len(set(selected_chapters).intersection(available_hard_chapters)) > 0:
                statistics['feedback']['hard']['chapters'] = 'Chapters: ' + ', '.join(
                    ['Chapter {}'.format(item) for item in set(selected_chapters).intersection(available_hard_chapters)]
                )

        if form_data['topics_include_exclude'] == INCLUDE:
            if len(set(selected_topics) - set(available_easy_topics)) > 0:
                statistics['feedback']['easy']['topics'] = 'Topics: ' + ', '.join(
                    set(selected_topics) - set(available_easy_topics)
                )

            if len(set(selected_topics) - set(available_moderate_topics)) > 0:
                statistics['feedback']['moderate']['topics'] = 'Topics: ' + ', '.join(
                    set(selected_topics) - set(available_moderate_topics)
                )

            if len(set(selected_topics) - set(available_hard_topics)) > 0:
                statistics['feedback']['hard']['topics'] = 'Topics: ' + ', '.join(
                    set(selected_topics) - set(available_hard_topics)
                )
        elif form_data['topics_include_exclude'] == EXCLUDE:
            if len(set(selected_topics).intersection(available_easy_topics)) > 0:
                statistics['feedback']['easy']['topics'] = 'Topics: ' + ', '.join(
                    set(selected_topics).intersection(available_easy_topics)
                )
            if len(set(selected_topics).intersection(available_moderate_topics)) > 0:
                statistics['feedback']['moderate']['topics'] = 'Topics: ' + ', '.join(
                    set(selected_topics).intersection(available_moderate_topics)
                )

            if len(set(selected_topics).intersection(available_hard_topics)) > 0:
                statistics['feedback']['hard']['topics'] = 'Topics: ' + ', '.join(
                    set(selected_topics).intersection(available_hard_topics)
                )

        if form_data['learning_output_include_exclude'] == INCLUDE:
            if len(set(selected_learning_output) - set(available_easy_learning_output)) > 0:
                statistics['feedback']['easy']['learning_output'] = 'Learning Output: ' + ', '.join(
                    set(selected_learning_output) - set(available_easy_learning_output)
                )

            if len(set(selected_learning_output) - set(available_moderate_learning_output)) > 0:
                statistics['feedback']['moderate']['learning_output'] = 'Learning Output: ' + ', '.join(
                    set(selected_learning_output) - set(available_moderate_learning_output)
                )

            if len(set(selected_learning_output) - set(available_hard_learning_output)) > 0:
                statistics['feedback']['hard']['learning_output'] = 'Learning Output: ' + ', '.join(
                    set(selected_learning_output) - set(available_hard_learning_output)
                )
        elif form_data['learning_output_include_exclude'] == EXCLUDE:
            if len(set(selected_learning_output).intersection(available_easy_learning_output)) > 0:
                statistics['feedback']['easy']['learning_output'] = 'Learning Output: ' + ', '.join(
                    set(selected_learning_output).intersection(available_easy_learning_output)
                )

            if len(set(selected_learning_output).intersection(available_moderate_learning_output)) > 0:
                statistics['feedback']['moderate']['learning_output'] = 'Learning Output: ' + ', '.join(
                    set(selected_learning_output).intersection(available_moderate_learning_output)
                )

            if len(set(selected_learning_output).intersection(available_hard_learning_output)) > 0:
                statistics['feedback']['hard']['learning_output'] = 'Learning Output: ' + ', '.join(
                    set(selected_learning_output).intersection(available_hard_learning_output)
                )
    return JsonResponse(statistics)


@login_required
@ensure_csrf_cookie
@require_http_methods(('POST', ))
def delete_question_bank(request, course_key_string):
    """
    Endpoint to delete the question bank.
    """
    user_perms = get_user_permissions(request.user, CourseKey.from_string(course_key_string))
    if (not user_perms & STUDIO_VIEW_USERS) or (not user_perms & STUDIO_EDIT_ROLES):
        raise PermissionDenied()

    delete_question_bank_handler(course_key_string, request.user)
    return JsonResponse({'url': reverse('home')})


@login_required
@ensure_csrf_cookie
@require_http_methods(("POST",))
def can_delete_xblock(request, usage_key_string):
    if usage_key_string:
        usage_key = usage_key_with_run(usage_key_string)
        if xblock_deletion_allow(usage_key):
            return JsonResponse({'can_delete': True}, status=200)
        return JsonResponse({'can_delete': False}, status=200)

    else:
        return HttpResponseBadRequest(
            'Usage Key is required for the deletion of xblock.',
            content_type='text/plain'
        )
