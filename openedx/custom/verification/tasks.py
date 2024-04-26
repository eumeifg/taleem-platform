import logging

from celery import task
from django.conf import settings

ACE_ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)
SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY = getattr(settings, 'SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY', None)
log = logging.getLogger(__name__)


@task(
    bind=True,
    default_retry_delay=settings.SOFTWARE_SECURE_REQUEST_RETRY_DELAY,
    max_retries=settings.SOFTWARE_SECURE_RETRY_MAX_ATTEMPTS,
    routing_key=SOFTWARE_SECURE_VERIFICATION_ROUTING_KEY,
)
def send_request_to_ss_for_user(self, user_verification_id, face_image, photo_id_image):
    """
    Assembles a submission to Software Secure.

    Keyword Arguments:
        user_verification_id (int) SoftwareSecurePhotoVerification model object identifier.
        face_image: Base64 Image to be send to SoftwareSecure for verification.
        photo_id_image: Base64 Image of ID to be send to SoftwareSecure for verification.
    Returns:
        request.Response
    """
    from openedx.custom.verification.models import CustomSoftwareSecurePhotoVerification
    from openedx.custom.verification.utils import handle_response
    from openedx.custom.timed_exam.image_verification_service import ImageVerificationService

    user_verification = CustomSoftwareSecurePhotoVerification.objects.get(id=user_verification_id)
    log.info('New Verification Task Received for User: %r', user_verification.user.username)
    try:
        image_verification_service = ImageVerificationService(false_on_multiple=True, crop=True)
        response = image_verification_service.direct_validate(face_image=face_image, photo_id_image=photo_id_image)
        user_verification.mark_submit()
        return handle_response(response, user_verification_id)
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
