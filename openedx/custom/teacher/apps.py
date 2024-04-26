"""
Configuration for teacher app.
"""

from django.apps import AppConfig


class TeacherConfig(AppConfig):
    """
    Configuration class for teacher app
    """
    name = 'openedx.custom.teacher'
    verbose_name = "Teacher"

    def ready(self):
        """
        Connect handlers to sync profile data.
        """
        from . import signals  # pylint: disable=unused-import
