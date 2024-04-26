"""
Offline exam exceptions.
"""


class OfflineExamBaseException(Exception):
    """
    A common base class for all exceptions
    """


class StudentExamAttemptAlreadyExistsException(OfflineExamBaseException):
    """
    Raised when trying to start an exam when an Exam Attempt already exists.
    """


class StudentExamAttemptDoesNotExistsException(OfflineExamBaseException):
    """
    Raised when trying to stop an exam attempt where the Exam Attempt doesn't exist.
    """


class StudentExamAttemptedAlreadyStarted(OfflineExamBaseException):
    """
    Raised when the same exam attempt is being started twice
    """


class UserNotFoundException(OfflineExamBaseException):
    """
    Raised when the user not found.
    """


class OfflineExamPermissionDenied(OfflineExamBaseException):
    """
    Raised when the calling user does not have access to the requested object.
    """


class OfflineExamSuspiciousLookup(OfflineExamBaseException):
    """
    Raised when a lookup on the student attempt table does not fully match
    all expected security keys
    """


class OfflineExamIllegalStatusTransition(OfflineExamBaseException):
    """
    Raised if a state transition is not allowed, e.g. going from submitted to started
    """

