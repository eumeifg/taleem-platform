import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.dispatch import Signal
from django.utils.timezone import now, timedelta
from django.utils.translation import get_language
from ipware.ip import get_ip
from oauth2_provider.models import AccessToken, Application, RefreshToken
from oauth2_provider.settings import oauth2_settings
from oauthlib.common import generate_token
from rest_framework.throttling import AnonRateThrottle
from social_django.models import UserSocialAuth
from student.helpers import (
    create_or_set_user_attribute_created_on_site,
    do_create_account,
)
from student.models import (
    create_comments_service_user,
)

from lms.djangoapps.discussion.notification_prefs.views import enable_notifications
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.djangoapps.user_authn.utils import generate_password
from openedx.core.djangoapps.user_authn.views.registration_form import (AccountCreationForm,
                                                                        get_registration_extension_form)
from openedx.custom.taleem.forms import get_default_organization

REGISTER_USER = Signal(providing_args=["user", "registration"])

log = logging.getLogger("edx.student")


class PerMinuteResendActivationEmailThrottle(AnonRateThrottle):

    scope = 'resend_activation_email'

    def get_ident(self, request):
        client_ip = get_ip(request)
        return client_ip

    rate = '1/minute'


def validate_request_parameters(request):
    social_id = request.data.get('socialID')
    email = request.data.get('email')
    provider = request.data.get('provider')
    client_id = request.data.get('client_id')

    if not social_id:
        return False, 'Invalid/Missing Social ID'
    if not email:
        return False, 'Invalid/Missing Email Address'
    if not provider or provider not in ['google', 'facebook', 'apple']:
        return False, 'Invalid/Missing Provider. Supported Providers are: google, facebook, apple'
    if not client_id:
        return False, 'Invalid/Missing Client ID.'

    return True, ''


def get_existing_user_if_exists(request):
    # Check if email is already registered
    social_id = request.data.get('socialID')
    email = request.data.get('email')
    provider = request.data.get('provider')

    user = User.objects.filter(email=email)

    email_user = None
    if user.exists():
        email_user = user[0]

    # Check if social account is already linked with any account
    if provider == 'facebook' or provider == 'apple':
        uid = social_id
    elif provider == 'google':
        uid = email

    social_user = None
    social_account = UserSocialAuth.objects.filter(uid=uid)
    if social_account.exists():
        social_user = social_account[0].user

    user = None
    # Check if both of the user is same
    if social_user or email_user:
        if social_user and email_user and social_user.id == email_user.id:
            user = social_user
        elif social_user and email_user and social_user.id != email_user.id:
            user = social_user
        elif not social_user and email_user:
            user = email_user
            create_social_auth_for_user(user, uid, provider)
        elif social_user and not email_user:
            user = social_user

    return user


def create_social_auth_for_user(user, uid, provider):
    social_auth, _ = UserSocialAuth.objects.get_or_create(
        user=user,
        uid=uid,
        provider=provider
    )

    return social_auth


def get_user_data(request):
    return {
        "social_id": request.data.get('socialID'),
        "email": request.data.get('email'),
        "provider": request.data.get('provider'),
        "name": request.data.get("first_name") + " " + request.data.get("last_name"),
        "user_type": "student",
        "org_type": "school",
        "grade": "NA",
        "school": get_default_organization("school")
    }


def create_user_account(request, params):
    params["password"] = generate_password()

    form = AccountCreationForm(
        data=params,
        do_third_party_auth=False,
        tos_required=False,
    )

    custom_form = get_registration_extension_form(data=params)

    (user, profile, registration) = do_create_account(form, custom_form)

    registration.activate()

    # Perform operations that are non-critical parts of account creation
    create_or_set_user_attribute_created_on_site(user, request.site)

    preferences_api.set_user_preference(user, LANGUAGE_KEY, get_language())

    if settings.FEATURES.get('ENABLE_DISCUSSION_EMAIL_DIGEST'):
        try:
            enable_notifications(user)
        except Exception:  # pylint: disable=broad-except
            log.exception(u"Enable discussion notifications failed for user {id}.".format(id=user.id))

    # Announce registration
    REGISTER_USER.send(sender=None, user=user, registration=registration)

    create_comments_service_user(user)

    return user


def get_token_json(access_token):
    """
    Takes an AccessToken instance as an argument
    and returns a JsonResponse instance from that
    AccessToken
    """
    token = {
        'access_token': access_token.token,
        'expires_in': oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
        'token_type': 'Bearer',
        'refresh_token': access_token.refresh_token.token,
        'scope': access_token.scope
    }
    return token


def get_access_token(user, client_id):
    """
    Takes a user instance and return an access_token as a JsonResponse
    instance.
    """

    # our oauth2 app
    app = Application.objects.get(client_id=client_id)

    # We delete the old access_token and refresh_token
    try:
        old_access_token = AccessToken.objects.get(
            user=user, application=app)
        old_refresh_token = RefreshToken.objects.get(
            user=user, access_token=old_access_token
        )
    except:
        pass
    else:
        old_access_token.delete()
        old_refresh_token.delete()

    # we generate an access token
    token = generate_token()
    # we generate a refresh token
    refresh_token = generate_token()

    expires = now() + timedelta(seconds=oauth2_settings.
                                ACCESS_TOKEN_EXPIRE_SECONDS)
    scope = "read write email profile"

    # we create the access token
    access_token = AccessToken.objects.\
        create(user=user,
               application=app,
               expires=expires,
               token=token,
               scope=scope)

    # we create the refresh token
    RefreshToken.objects.\
        create(user=user,
               application=app,
               token=refresh_token,
               access_token=access_token)

    # we call get_token_json and returns the access token as json
    return get_token_json(access_token)
