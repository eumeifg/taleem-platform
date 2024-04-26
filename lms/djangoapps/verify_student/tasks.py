"""
Django Celery tasks for service status app
"""

import logging

import requests
import simplejson
from celery import Task, task
from celery.states import FAILURE
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

from edx_ace import ace
from edx_ace.recipient import Recipient
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY


from .message_types import VerificationSuccessMessage, VerificationFailureMessage

ACE_ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)
SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = getattr(settings, 'SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY', None)
log = logging.getLogger(__name__)


class BaseSoftwareSecureTask(Task):
    """
    Base task class for use with Software Secure request.

    Permits updating information about user attempt in correspondence to submitting
    request to software secure.
    """
    abstract = True

    def on_success(self, retval, task_id, args, kwargs):
        """
        Update SoftwareSecurePhotoVerification object corresponding to this
        task with info about success.

        Updates user verification attempt to "submitted" if the response was ok otherwise
        set it to "must_retry".

        Assumes `retval` is a dict containing the task's result, with the following keys:
            'response_ok': boolean, indicating if the response was ok
            'response_text': string, indicating the response text in case of failure.
        """
        from .models import SoftwareSecurePhotoVerification

        user_verification = SoftwareSecurePhotoVerification.objects.get(id=kwargs['user_verification_id'])
        if retval['response_ok']:
            user_verification.mark_submit()
            log.info(
                'Sent request to Software Secure for user: %r and receipt ID %r.',
                user_verification.user.username,
                user_verification.receipt_id,
            )
            return user_verification

        user_verification.mark_must_retry(retval['response_text'])

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        If max retries have reached and task status is still failing, mark user submission
        with "must_retry" so that it can be retried latter.
        """
        if self.max_retries == self.request.retries and status == FAILURE:
            from .models import SoftwareSecurePhotoVerification

            user_verification_id = kwargs['user_verification_id']
            user_verification = SoftwareSecurePhotoVerification.objects.get(id=user_verification_id)
            user_verification.mark_must_retry()
            log.error(
                'Software Secure submission failed for user %r, setting status to must_retry',
                user_verification.user.username,
                exc_info=True
            )


@task(routing_key=ACE_ROUTING_KEY)
def send_verification_status_email(context):
    """
    Spins a task to send verification status email to the learner
    """
    from openedx.core.lib.celery.task_utils import emulate_http_request
    from openedx.core.djangoapps.user_api.preferences import api as preferences_api

    site = Site.objects.get_current()
    user_context = get_base_template_context(site)
    user_context.update(context.get('email_vars'))
    user = User.objects.get(id=context.get('user_id'))
    MessageType = VerificationSuccessMessage if context.get('status') else VerificationFailureMessage
    msg = MessageType().personalize(
        recipient=Recipient(user.username, user.email),
        language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
        user_context=user_context,
    )
    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    msg.options['from_address'] = from_address
    try:
        with emulate_http_request(site=site, user=user):
            ace.send(msg)
    except:  # pylint: disable=bare-except
        # We catch all exceptions and log them.
        # It would be much, much worse to roll back the transaction due to an uncaught
        # exception than to skip sending the notification email.
        log.exception(u"Could not send verification status email for user %s", user.id)


@task(
    base=BaseSoftwareSecureTask,
    bind=True,
    default_retry_delay=settings.SOFTWARE_SECURE_REQUEST_RETRY_DELAY,
    max_retries=settings.SOFTWARE_SECURE_RETRY_MAX_ATTEMPTS,
    routing_key=SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY,
)
def send_request_to_ss_for_user(self, user_verification_id, copy_id_photo_from):
    """
    Assembles a submission to Software Secure.

    Keyword Arguments:
        user_verification_id (int) SoftwareSecurePhotoVerification model object identifier.
        copy_id_photo_from (SoftwareSecurePhotoVerification): If provided, re-send the ID photo
                data from this attempt.  This is used for re-verification, in which new face photos
                are sent with previously-submitted ID photos.
    Returns:
        request.Response
    """
    from .models import SoftwareSecurePhotoVerification

    user_verification = SoftwareSecurePhotoVerification.objects.get(id=user_verification_id)
    log.info('=>New Verification Task Received %r', user_verification.user.username)
    try:
        headers, body = user_verification.create_request(copy_id_photo_from)
        # checkout PROD-1395 for detail why we are adding system certificate paths for verification.
        response = requests.post(
            settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["API_URL"],
            headers=headers,
            data=simplejson.dumps(body, indent=2, sort_keys=True, ensure_ascii=False).encode('utf-8'),
            verify=settings.VERIFY_STUDENT["SOFTWARE_SECURE"]['CERT_VERIFICATION_PATH']
        )
        return {
            'response_ok': getattr(response, 'ok', False),
            'response_text': getattr(response, 'text', '')
        }
    except Exception as exc:  # pylint: disable=broad-except
        log.error(
            (
                'Retrying sending request to Software Secure for user: %r, Receipt ID: %r '
                'attempt#: %s of %s'
            ),
            user_verification.user.username,
            user_verification.receipt_id,
            self.request.retries,
            settings.SOFTWARE_SECURE_RETRY_MAX_ATTEMPTS,
        )
        log.error(str(exc))
        self.retry()
