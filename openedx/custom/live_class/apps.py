"""
Configuration for live class app.
"""


from django.apps import AppConfig


class LiveClassConfig(AppConfig):
    """
    Configuration class for live class
    """
    name = 'openedx.custom.live_class'
    verbose_name = "Live Class"

    def ready(self):
        import openedx.custom.live_class.signals
