"""
Configuration for video feedback Django app
"""


from django.apps import AppConfig


class VideoFeedbackConfig(AppConfig):
    """
    Configuration class for video feedback Django app
    """
    name = 'openedx.custom.video_feedback'
    verbose_name = "Video Feedback"

    def ready(self):
        # Import signals to activate signal handler which invalidates
        # the CourseOverview cache every time a course is published.
        # from . import signals  # pylint: disable=unused-variable
        pass

