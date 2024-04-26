"""
Configuration for payment_gateway Django app
"""


from django.apps import AppConfig


class PaymentGatewayConfig(AppConfig):
    name = 'openedx.custom.payment_gateway'
    verbose_name = "Payment Gateway"

    def ready(self):
        # Import signals to activate signal handler which invalidates
        # the CourseOverview cache every time a course is published.
        # from . import signals  # pylint: disable=unused-variable
        from . import handlers
