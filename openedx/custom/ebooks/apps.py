"""
Configuration for eBooks App
"""


from django.apps import AppConfig


class EBooksConfig(AppConfig):
    """
    Configuration class for eBooks app
    """
    name = 'openedx.custom.ebooks'
    verbose_name = "eBooks"

    def ready(self):
        # Import signals to activate signal handler which invalidates
        # the CourseOverview cache every time a course is published.
        # from . import signals  # pylint: disable=unused-variable
        pass


