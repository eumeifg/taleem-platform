"""
Status enums for offline-exam
"""
from __future__ import absolute_import


class OfflineExamStudentAttemptStatus:
    """
    A class to enumerate the various status that an attempt can have

    IMPORTANT: Since these values are stored in a database, they are system
    constants and should not be language translated, since translations
    might change over time.
    """

    # the attempt record has been created, but the exam has not yet
    # been started
    created = 'created'

    # the attempt is ready to start but requires
    # user to acknowledge that he/she wants to start the exam
    ready_to_start = 'ready_to_start'

    # the student has started the exam and is
    # in the process of completing the exam
    started = 'started'

    #
    # The follow statuses below are considered in a 'completed' state
    # and we will not allow transitions to status above this mark
    #

    # the exam has timed out
    timed_out = 'timed_out'

    # the student has submitted the exam for proctoring review
    submitted = 'submitted'

    # the course end date has passed
    expired = 'expired'

    @classmethod
    def is_completed_status(cls, status):
        """
        Returns a boolean if the passed in status is in a "completed" state, meaning
        that it cannot go backwards in state
        """
        return status in [
            cls.timed_out, cls.submitted,
        ]

    @classmethod
    def is_incomplete_status(cls, status):
        """
        Returns a boolean if the passed in status is in an "incomplete" state.
        """
        return status in [
            cls.created, cls.ready_to_start, cls.started,
        ]

    @classmethod
    def is_valid_status(cls, status):
        """
        Makes sure that passed in status string is valid
        """
        return cls.is_completed_status(status) or cls.is_incomplete_status(status)

    @classmethod
    def is_pre_started_status(cls, status):
        """
        Returns a boolean if the status passed is prior to "started" state.
        """
        return status in [
            cls.created, cls.ready_to_start
        ]

    @classmethod
    def is_in_progress_status(cls, status):
        """
        Returns a boolean if the status passed is "in progress".
        """
        return status == cls.started
