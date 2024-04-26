"""
Configuration for taleem Django app
"""


from django.apps import AppConfig


class TaleemConfig(AppConfig):
    """
    Configuration class for taleem Django app
    """
    name = 'openedx.custom.taleem'
    verbose_name = "Taleem"

    def ready(self):
        import openedx.custom.taleem.signals  # pylint: disable=unused-variable
        pass

