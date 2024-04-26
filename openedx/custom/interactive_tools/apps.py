"""
Configuration for interactive tools App
"""


from django.apps import AppConfig


class InteractiveToolsConfig(AppConfig):
    """
    Configuration class for interactive tools app
    """
    name = 'openedx.custom.interactive_tools'
    verbose_name = "Interactive Tools"

    def ready(self):
        # Import signals to activate signal handler which invalidates
        # the CourseOverview cache every time a course is published.
        # from . import signals  # pylint: disable=unused-variable
        pass

