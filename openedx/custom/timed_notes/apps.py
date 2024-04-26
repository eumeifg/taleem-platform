"""
Configuration for timed notes Django app
"""


from django.apps import AppConfig


class TimedNotesConfig(AppConfig):
    """
    Configuration class for timed notes Django app
    """
    name = 'openedx.custom.timed_notes'
    verbose_name = "Timed Notes"

    def ready(self):
        # Import signals to activate signal handler which invalidates
        # the CourseOverview cache every time a course is published.
        # from . import signals  # pylint: disable=unused-variable
        pass

