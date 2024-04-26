"""
Exceptions for Timed Exam.
"""


class InvalidCSVDataError(Exception):
    """
    This exception is raised if there is some error in the csv data
    """

    def __init__(self, message, *args):
        """
        Save message on the instance for future usage.
        """
        super(InvalidCSVDataError, self).__init__(*args)
        self.message = message


class InvalidEmailError(Exception):
    """
    This exception is raised if some/all of the email in CSV data are not valid.
    """

    def __init__(self, message, *args):
        """
        Save message on the instance for future usage.
        """
        super(InvalidEmailError, self).__init__(*args)
        self.message = message
