"""
Configuration for verification app
"""


from django.apps import AppConfig


class VerificationConfig(AppConfig):
    """
    Configuration class for verification app.
    """
    name = 'openedx.custom.verification'
    verbose_name = "Verification"

    def ready(self):
        import openedx.custom.verification.signals  # pylint: disable=unused-variable
        pass
