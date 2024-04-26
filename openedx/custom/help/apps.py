"""
Configuration for help Django app
"""


from django.apps import AppConfig


class HelpAppConfig(AppConfig):
    """
    Configuration class for timed exam Django app
    """
    name = 'openedx.custom.help'
    verbose_name = "Help"

    def ready(self):
        pass
