"""
Configuration for timed exam Django app
"""


from django.apps import AppConfig


class TimedExamConfig(AppConfig):
    """
    Configuration class for timed exam Django app
    """
    name = 'openedx.custom.timed_exam'
    verbose_name = "Timed Exam"

    def ready(self):
        import openedx.custom.timed_exam.signals  # pylint: disable=unused-import
