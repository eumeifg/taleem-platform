"""
Exceptions for taleem.
"""


class SecondPasswordError(Exception):
    """
    Base class for exceptions related to the second password.
    """
    def __init__(self, message, *args):
        """
        Save human readable message as an attribute.
        """
        super(SecondPasswordError, self).__init__(message, *args)
        self.message = message


class SecondPasswordExpiredError(SecondPasswordError):
    """
    This exception is raised if second password has expired.
    """
    def __init__(self, *args):
        """
        Save human readable message as an attribute.
        """
        message = 'Second Password you entered has expired, please resend a new password and try again.'
        super(SecondPasswordExpiredError, self).__init__(message, *args)


class SecondPasswordValidationError(SecondPasswordError):
    """
    This exception is raised if second password does not match.
    """
    def __init__(self, *args):
        """
        Save human readable message as an attribute.
        """
        message = 'Second Password you entered does not match the one sent to you, ' \
                  'please send a new password and try again.'
        super(SecondPasswordValidationError, self).__init__(message, *args)


class BulkRegistrationError(Exception):
    def __init__(self, message, *args):
        super(BulkRegistrationError, self).__init__(*args)
        self.message = message
