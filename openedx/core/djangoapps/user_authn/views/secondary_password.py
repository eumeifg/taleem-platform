""" Password reset logic and views . """

import logging

from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from openedx.core.djangoapps.user_api.helpers import FormDescription
from openedx.custom.taleem.utils import validate_second_password
from openedx.custom.taleem.exceptions import SecondPasswordError


# Maintaining this naming for backwards compatibility.
log = logging.getLogger("edx.student")
AUDIT_LOG = logging.getLogger("audit")


def get_second_password_form():
    """
    Return a description of the secondary password form.

    This decouples clients from the API definition:
    if the API decides to modify the form, clients won't need
    to be updated.

    See `user_api.helpers.FormDescription` for examples
    of the JSON-encoded form description.

    Returns:
        HttpResponse

    """
    form_desc = FormDescription("post", reverse("second_password_request"))

    instructions = _(
        u"A secondary password has been sent through the email or SMS, Please enter that password here"
    )

    form_desc.add_field(
        'second_password',
        field_type='password',
        label=_('Second Password'),
        instructions=instructions,
        restrictions={
            "min_length": 4,
            "max_length": 6,
        }
    )

    return form_desc


@ensure_csrf_cookie
@require_POST
def second_password_request_handler(request):
    """
    Handle secondary password requests originating from the account page.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200 if the secondary password matches.
        HttpResponse: 400 if secondary password does not match.
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        POST /account/second-password

    """
    from openedx.core.djangoapps.user_authn.views.login import login_user
    user_post_data = request.session.get('USER_POST_DATA')

    if not user_post_data:
        return HttpResponse(
            _("Invalid Request. Please try again later. If problem persist, contact support."),
            status=400
        )

    try:
        validate_second_password(
            user_email=user_post_data.get('email'),
            second_password=request.POST.get('second_password'),
        )
    except SecondPasswordError as error:
        return HttpResponse(error.message, status=400)

    request.POST = user_post_data
    return login_user(request)
