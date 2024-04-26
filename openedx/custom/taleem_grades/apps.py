"""
Configuration for ta3leem grades app
"""


from django.apps import AppConfig


class TaleemGradesConfig(AppConfig):
    """
    Configuration class for ta3leem grades
    """
    name = 'openedx.custom.taleem_grades'
    verbose_name = "Taleem Grades"

    def ready(self):
        """
        Connect handlers to recalculate grades.
        """
        from .signals import handlers  # pylint: disable=unused-import
