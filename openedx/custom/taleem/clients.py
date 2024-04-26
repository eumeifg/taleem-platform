"""
Clients for taleem.
"""
from django.conf import settings
from django.contrib.auth.models import User
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user


class LMSApiClient(object):
    """
    Class for producing an LMS API client.
    """
    enterprise_worker = 'enterprise_worker'

    def __init__(self, user):
        """
        Initialize an authenticated LMS API client by using the provided user.
        """
        self.user = user
        jwt = create_jwt_for_user(user)
        self.client = EdxRestApiClient(
            settings.LMS_ROOT_URL,
            jwt=jwt
        )

    @classmethod
    def send_emails(cls, user, activation=True, password_reset=True):
        """
        Send user emails.
        """
        enterprise_worker_user = User.objects.get(username=cls.enterprise_worker)
        lms_client = LMSApiClient(enterprise_worker_user)
        endpoint = getattr(lms_client.client, 'taleem/send-email/')
        return endpoint(user.email).get(activation=activation, password_reset=password_reset)
