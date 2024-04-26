"""
Miscellaneous utility functions.
"""


import re

from xmodule.annotator_mixin import html_to_text

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


def escape_invalid_characters(name, invalid_char_list, replace_with='_'):
    """
    Remove invalid characters from a variable and replace it with given character.
    Few chars are not allowed in asset displayname, during import/export
    Escape those chars with `replace_with` and return clean name

    Args:
        name (str): variable to escape chars from.
        invalid_char_list (list): Must be a list, and it should contain list of chars to be removed
            from name
        replace_with (str): Char used to replace invalid_char with.

    Returns:
        name (str): name without `invalid_char_list`.

    """

    for char in invalid_char_list:
        if char in name:
            name = name.replace(char, replace_with)
    return name


def escape_html_characters(content):
    """
    Remove HTML characters that shouldn't be indexed using ElasticSearch indexer
    This method is complementary to html_to_text method found in xmodule/annotator_mixin.py

    Args:
        content (str): variable to escape html characters from

    Returns:
        content (str): content ready to be index by ElasticSearch

    """

    # Removing HTML comments
    return re.sub(
        r"<!--.*-->",
        "",
        # Removing HTML CDATA
        re.sub(
            r"<!\[CDATA\[.*\]\]>",
            "",
            # Removing HTML-encoded non-breaking space characters
            re.sub(
                r"(\s|&nbsp;|//)+",
                " ",
                html_to_text(content)
            )
        )
    )


def get_short_labeler(prefix):
    """
    Returns a labeling function that prepends
    `prefix` to an assignment index.
    """
    def labeler(index):
        return u"{prefix} {index:02d}".format(prefix=prefix, index=index)
    return labeler


def get_default_short_labeler(course):
    """
    Returns a helper function that creates a default
    short_label for a subsection.
    """
    default_labelers = {}
    for grader, assignment_type, _ in course.grader.subgraders:
        default_labelers[assignment_type] = {
            'labeler': get_short_labeler(grader.short_label),
            'index': 1,
        }

    def default_labeler(assignment_type):
        """
        Given an assignment type, returns the next short_label
        for that assignment type.  For example, if the assignment_type
        is "Homework" and this is the 2nd time the function has been called
        for that assignment type, this function would return "Ex 02", assuming
        that "Ex" is the short_label assigned to a grader for Homework subsections.
        """
        if assignment_type not in default_labelers:
            return None
        labeler = default_labelers[assignment_type]['labeler']
        index = default_labelers[assignment_type]['index']
        default_labelers[assignment_type]['index'] += 1
        return labeler(index)
    return default_labeler


def get_optional_question_message(
    num_optional_questions, num_assigned_questions):
    """
    Given the number of questions assigned to the
    student and the number of questions marked as
    optional this function will return a readable
    message for the student to know how many questions
    can be skipped.
    """
    if num_optional_questions >= num_assigned_questions:
        return _("All questions in this section are optional.")
    elif num_optional_questions > 0:
        return _(
            "{x} out of {y} questions in this section are optional."
        ).format(x=num_optional_questions, y=num_assigned_questions)
    return _("All questions in this section are mandatory.")