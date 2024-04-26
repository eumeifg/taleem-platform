"""
Configuration for wishlist Django app
"""


from django.apps import AppConfig


class WishlistConfig(AppConfig):
    """
    Configuration class for timed notes Django app
    """
    name = 'openedx.custom.wishlist'
    verbose_name = "Wishlist"

    def ready(self):
        """
        Connect handlers to signals.
        """
        from . import handlers  # pylint: disable=unused-variable

