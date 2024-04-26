"""
Helpers for instructor app.
"""


from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.module_render import get_module
from xmodule.modulestore.django import modulestore


class DummyRequest(object):
    """Dummy request"""

    META = {}

    def __init__(self):
        self.session = {}
        self.user = None
        return

    def get_host(self):
        """Return a default host."""
        return 'edx.mit.edu'

    def is_secure(self):
        """Always insecure."""
        return False


def get_module_for_student(student, usage_key, request=None, course=None):
    """Return the module for the (student, location) using a DummyRequest."""
    if request is None:
        request = DummyRequest()
        request.user = student

    descriptor = modulestore().get_item(usage_key, depth=0)
    field_data_cache = FieldDataCache([descriptor], usage_key.course_key, student)
    return get_module(student, request, usage_key, field_data_cache, course=course)


def set_staff_score(course_id, item_id, earned_score, max_score, submission_uuid, reason=None):
    """
    Set a staff score for the workflow.

    Allows for staff scores to be set on a submission, with annotations to provide an audit trail if needed.
    This method can be used for both required staff grading, and staff overrides.

    Args:
        course_id (str): Course identifier.
        item_id (str): Xblock identifier.
        earned_score (int): Score which was earned by a learner.
        max_score (int): Maximum score which learner can earned.
        submission_uuid (uuid string): Respective submission object's uuid for xblock.
        reason (string): An optional parameter specifying the reason for the staff grade. A default value
            will be used in the event that this parameter is not provided.

    """
    from submissions import api as sub_api

    if reason is None:
        reason = "A staff member has defined the score for this submission"

    submission_data = sub_api.get_submission_and_student(submission_uuid)

    sub_api.reset_score(
        submission_data['student_item']['student_id'],
        course_id,
        item_id,
        emit_signal=False
    )

    sub_api.set_score(
        submission_uuid,
        earned_score,
        max_score,
        annotation_reason=reason
    )
