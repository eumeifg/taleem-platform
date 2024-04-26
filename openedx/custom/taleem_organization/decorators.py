"""
Decorators for Taleem Organization app.
"""
from functools import wraps

from django.http import JsonResponse

from openedx.custom.taleem_organization.utils import validate_tashgheel_access
from openedx.custom.taleem_organization.exceptions import TashgheelAPIError


def ensure_tashgheel_access(func):
    """
    Validate that the request has proper access rights.

    Note: this view is applicable only on django views.

    Request will be authorized, if any of the following conditions is satisfied.
        1. Auth token `TashgheelConfig.token` is present in the Authorization.
        2. Source IP Address is whitelisted in `TashgheelConfig.ip_addresses`
    """
    @wraps(func)
    def decorator(request, *args, **kwargs):
        try:
            validate_tashgheel_access(request)
        except TashgheelAPIError as error:
            return JsonResponse({
                'detail': error.message
            }, status=401)

        return func(request, *args, **kwargs)
    return decorator
