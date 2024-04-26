"""
Configuration for taleem notifications Django app
"""


from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """
    Configuration class for taleem notifications Django app
    """
    name = 'openedx.custom.notifications'
    verbose_name = "Ta3leem Notifications"

    def ready(self):
        import openedx.custom.notifications.signals # pylint: disable=unused-import

