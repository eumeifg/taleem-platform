"""
Configuration for enrollment dashboard app
"""


from django.apps import AppConfig


class EnrollmentDashboardConfig(AppConfig):
    """
    Configuration class for enrollment dashboard app.
    """
    name = 'openedx.custom.enrollment_dashboard'
    verbose_name = "Enrollment Dashboard"

    def ready(self):
        pass
