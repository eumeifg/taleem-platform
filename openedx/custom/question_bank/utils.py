"""
Utility methods added for Question Bank.
"""
from operator import itemgetter

from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryUsageLocator

from openedx.custom.question_bank.models import QuestionTags
from openedx.custom.timed_exam.models import TimedExam
from openedx.custom.utils import convert_comma_separated_string_to_list, dedupe
from xmodule.capa_base import DIFFICULTYLEVEL
from xmodule.modulestore.django import modulestore
from openedx.custom.utils import to_lower


def add_question_tags(question):
    """
    Add tags for question problems.
    """
    question_bank = question.parent.library_key
    for tag_type in QuestionTags.TAG_TYPES:
        tag_value = getattr(question, tag_type, '')
        tag_value = tag_value.strip() if tag_value else tag_value
        if tag_value:
            handle_other_tag(question_bank, question, tag_type, tag_value) if not tag_type == QuestionTags.TOPIC else \
                handle_topic_tag(question_bank, question, convert_comma_separated_string_to_list(tag_value))
        else:
            QuestionTags.objects.filter(
                question_bank=question_bank,
                question=question.location,
                tag_type=tag_type
            ).delete()


def handle_other_tag(question_bank, question, tag_type, tag):
    """
    Update or create the tags (Chapter, Difficulty Level and Learning Output).
    """
    QuestionTags.objects.update_or_create(
        question_bank=question_bank,
        question=question.location,
        tag_type=tag_type,
        defaults={'tag': tag}
    )


def handle_topic_tag(question_bank, question, tags):
    """
    Add or delete the topic tag.
    """
    QuestionTags.objects.filter(
        question_bank=question_bank,
        question=question.location,
        tag_type=QuestionTags.TOPIC
    ).delete()

    for tag in tags:
        QuestionTags.objects.create(
            question_bank=question_bank,
            question=question.location,
            tag_type=QuestionTags.TOPIC,
            tag=tag
        )


def get_grouped_tags(question_bank_key_string):
    """
    Group tags by tag type in the form of a dictionary with tag type as the key.
    """
    grouped_tags = {tag_type: [] for tag_type in QuestionTags.TAG_TYPES}
    tags = QuestionTags.objects.filter(question_bank=question_bank_key_string)

    for tag in tags:
        grouped_tags[tag.tag_type].append({
            'id': tag.id,
            'text': tag.tag,
        })

    return _remove_duplicate_and_normalize_tag_values(grouped_tags)


def _remove_duplicate_and_normalize_tag_values(grouped_tags):
    """
    Normalize and remove duplicate tag values.
    """
    tags = {tag_type: [] for tag_type in QuestionTags.TAG_TYPES}
    tags['chapter'] = [
        {
            'id': chapter['text'],
            'text': 'Chapter {}'.format(chapter['text']),
        } for chapter in dedupe(grouped_tags['chapter'], key=itemgetter('text'))
    ]

    # remove duplicated learning output
    tags['learning_output'] = [
        {
            'id': learning_output['text'],
            'text': learning_output['text'],
        } for learning_output in dedupe(grouped_tags['learning_output'], key=itemgetter('text'))
    ]

    # remove duplicated difficulty level
    tags['difficulty_level'] = [
        {
            'id': difficulty_level['text'],
            'text': difficulty_level['text'],
        } for difficulty_level in dedupe(grouped_tags['difficulty_level'], key=itemgetter('text'))
    ]
    tags['topic'] = [
        {
            'id': topic['text'],
            'text': topic['text'],
        } for topic in dedupe(grouped_tags['topic'], key=itemgetter('text'))
    ]

    return tags


def get_question_bank_stats(quest_bank_key_string):
    """
    Helper method to get the stats of question bank.
    """
    question_bank_key = CourseKey.from_string(quest_bank_key_string)
    question_bank = modulestore().get_library(question_bank_key)
    stats = {
        DIFFICULTYLEVEL.EASY: 0,
        DIFFICULTYLEVEL.MODERATE: 0,
        DIFFICULTYLEVEL.HARD: 0,
        "has_same_weightage": False
    }

    if question_bank:
        problems = filter(lambda item: hasattr(item, 'weight'), question_bank.get_children())
        stats['has_same_weightage'] = len(
            # Remove duplicates.
            set(
                # Get Item weightage.
                map(lambda item: item.weight or 1, problems)
            )
        ) <= 1

        for problem in question_bank.get_children():
            if problem.difficulty_level:
                stats[problem.difficulty_level] += 1

    return stats


def get_question_bank(question_bank_key):
    """
    Get Question Bank (i.e. Library) from the question bank key (i.e. library key).

    Arguments:
        question_bank_key (str): Library key that points to a question bank (i.e. Library).
    """
    question_bank_key = CourseKey.from_string(question_bank_key)
    return modulestore().get_library(question_bank_key)


def get_question_bank_stats_with_tags(problems):
    """
    Return the timed exam's problem stats.
    """
    easy_problems = get_difficulty_level_problems(problems, DIFFICULTYLEVEL.EASY)
    moderate_problems = get_difficulty_level_problems(problems, DIFFICULTYLEVEL.MODERATE)
    hard_problems = get_difficulty_level_problems(problems, DIFFICULTYLEVEL.HARD)

    return {
        DIFFICULTYLEVEL.EASY: len(easy_problems),
        DIFFICULTYLEVEL.MODERATE: len(moderate_problems),
        DIFFICULTYLEVEL.HARD: len(hard_problems),
        'chapters': {
            DIFFICULTYLEVEL.EASY: [
                to_lower(getattr(problem, 'chapter', ''))
                for problem in easy_problems if getattr(problem, 'chapter', None)
            ],
            DIFFICULTYLEVEL.MODERATE:  [
                to_lower(getattr(problem, 'chapter', None))
                for problem in moderate_problems if getattr(problem, 'chapter', None)
            ],
            DIFFICULTYLEVEL.HARD:  [
                to_lower(getattr(problem, 'chapter', ''))
                for problem in hard_problems if getattr(problem, 'chapter', None)
            ],
        },
        'topics': {
            DIFFICULTYLEVEL.EASY:  [
                to_lower(getattr(problem, 'topic', ''))
                for problem in easy_problems if getattr(problem, 'topic', None)
            ],
            DIFFICULTYLEVEL.MODERATE: [
                to_lower(getattr(problem, 'topic', ''))
                for problem in moderate_problems if getattr(problem, 'topic', None)
            ],
            DIFFICULTYLEVEL.HARD: [
                to_lower(getattr(problem, 'topic', ''))
                for problem in hard_problems if getattr(problem, 'topic', None)
            ],
        },
        'learning_output': {
            DIFFICULTYLEVEL.EASY: [
                to_lower(getattr(problem, 'learning_output', ''))
                for problem in easy_problems if getattr(problem, 'learning_output', None)
            ],
            DIFFICULTYLEVEL.MODERATE: [
                to_lower(getattr(problem, 'learning_output', ''))
                for problem in moderate_problems if getattr(problem, 'learning_output', None)
            ],
            DIFFICULTYLEVEL.HARD: [
                to_lower(getattr(problem, 'learning_output', ''))
                for problem in hard_problems if getattr(problem, 'learning_output', None)
            ],
        },
    }


def get_difficulty_level_problems(problems, difficulty_level):
    """
    Return the list of all the problems of given difficulty_level.
    """
    return [problem for problem in problems if getattr(problem, 'difficulty_level', None) == difficulty_level]


def delete_question_bank_handler(question_bank_id, user):
    """
    question_bank_id (str): id for question bank.
    user(User Object): User who is deleting the timed exam.

    Delete the question bank from mongo.
    """
    from contentstore.utils import delete_course
    from openedx.custom.timed_exam.utils import delete_timed_exam

    # Removing from the mongo
    delete_course(CourseKey.from_string(question_bank_id), user.id)

    timed_exams = TimedExam.objects.filter(question_bank=question_bank_id)

    for timed_exam in timed_exams:
        delete_timed_exam(timed_exam.key, user)


def xblock_deletion_allow(usage_key):
    # Do not allow the deletion of last xblock from the question bank if the question bank is associated with any
    # TimedExam.
    if isinstance(usage_key, LibraryUsageLocator) and TimedExam.is_question_bank_associated(usage_key.library_key):
        library = modulestore().get_library(usage_key.library_key)
        if not len(library.get_children()) > 1:
            return False
    return True
