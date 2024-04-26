"""
Exceptions for taleem organization.
"""


class TashgheelAPIError(Exception):
    """
    Exception for tashgheel API Error.
    """

    def __init__(self, message):
        super(TashgheelAPIError, self).__init__()
        self.message = message
