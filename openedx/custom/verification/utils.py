import json
import logging

from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseBadRequest
from six import text_type

from lms.djangoapps.verify_student.services import IDVerificationService
from lms.djangoapps.verify_student.tasks import send_verification_status_email
from student.views.dashboard import get_verification_error_reasons_for_display
from openedx.custom.verification.tasks import send_request_to_ss_for_user

log = logging.getLogger(__name__)


def submit_request_to_ss(user_verification, face_image, photo_id_image):
    """
    Submit our verification attempt to Software Secure for validation.

    Submits the task to software secure and If the task creation fails,
    set the verification status to "must_retry".
    """
    try:
        send_request_to_ss_for_user.delay(
            user_verification_id=user_verification.id,
            face_image=face_image,
            photo_id_image=photo_id_image
        )
    except Exception as error:
        log.exception(
            "Software Secure submit request %r failed, result: %s", user_verification.user.username, text_type(error)
        )
        user_verification.mark_must_retry()


def handle_response(response, user_verification_id):
    """
    Handle the response got from AI Module.
    """
    from openedx.custom.verification.models import CustomSoftwareSecurePhotoVerification

    attempt = CustomSoftwareSecurePhotoVerification.objects.get(id=user_verification_id)
    receipt_id = attempt.receipt_id

    user = attempt.user
    result = response['result']
    verified = response['verified'] if 'verified' in response.keys() else False
    if result and verified:
        # If this verification is not an outdated version then make expiry date of previous approved verification NULL
        # Setting expiry date to NULL is important so that it does not get filtered in the management command
        # that sends email when verification expires : verify_student/send_verification_expiry_email
        if attempt.status != 'approved':
            verification = CustomSoftwareSecurePhotoVerification.objects.filter(
                status='approved', user_id=attempt.user_id)
            if verification:
                log.info(u'Making expiry date of previous approved verification NULL for {}'.format(attempt.user_id))
                # The updated_at field in sspv model has auto_now set to True, which means any time save() is called on
                # the model instance, `updated_at` will change. Some of the existing functionality of verification
                # (showing your verification has expired on dashboard) relies on updated_at.
                # In case the attempt.approve() fails for some reason and to not cause any inconsistencies in existing
                # functionality update() is called instead of save()
                previous_verification = verification.latest('updated_at')
                CustomSoftwareSecurePhotoVerification.objects.filter(pk=previous_verification.pk).update(
                    expiry_date=None, expiry_email_date=None)
        log.debug(u'AI Module Approving verification for {}'.format(receipt_id))
        attempt.mark_approved_by_ai()
    elif not response['result'] or ("verified" in response.keys() and not verified):
        log.debug(u"Denying verification for %s", receipt_id)
        reasons = _parse_reason(response, user)
        attempt.deny(json.dumps(reasons))
        send_verification_status_email.delay({
            'user_id': user.id,
            'status': 0, # indicates verification failed
            'email_vars': {
                'full_name': user.profile.name,
                'verification_errors': get_verification_error_reasons_for_display(
                    IDVerificationService.user_status(user)['error']
                ),
                'verify_link': "{}{}".format(
                    settings.LMS_ROOT_URL,
                    reverse('verification:verify_student_identification')
                )
            },
        })
    else:
        log.error(u"Software Secure returned unknown result %s", response)
        return HttpResponseBadRequest(
            u"Result {} not understood.".format(response)
        )

    return {
        'response_ok': getattr(response, 'ok', False),
        'response_text': getattr(response, 'text', '')
    }


def _parse_reason(response_dict, user):
    errors = []
    error = {"errors_dict": {}}
    user_type = user.ta3leem_profile.user_type
    id_name = "Photo" if user_type == 'student' else 'Teacher'
    response_keys = response_dict.keys()
    if "reason" in response_keys:
        reason = response_dict['reason']
        if 'no face found' in reason:
            if 'object_1' in reason:
                error['errors_dict']['Not provided'] = 'We are unable to detect the face from {id_name} ID.'.format(
                    id_name=id_name
                )
                error['errors_dict']['Text not clear'] = 'We are unable to detect the face from {id_name} ID.'.format(
                    id_name=id_name
                )
                error['errors_dict']['Invalid Id'] = 'We are unable to detect the face from {id_name} ID.'.format(
                    id_name=id_name
                )
            elif 'object' in reason:
                error['errors_dict']['Photo not provided'] = 'We are unable to detect the face from Face Image.'
                error['errors_dict']['Image not clear'] = 'We are unable to detect the face from Face Image.'
        elif 'multiple faces found' in reason or 'multiple people found' in reason:
            error['errors_dict']['Photo not provided'] = 'We are unable to detect the face from Face Image.'
            error['errors_dict']['Image not clear'] = 'We are unable to detect the face from Face Image.'
    elif "reason" not in response_keys and "verified" in response_keys and not response_dict['verified']:
        error['errors_dict']['Photo/ID Photo mismatch'] = 'We are unable to detect the face from {id_name} ID.'.format(
            id_name=id_name
        )
    else:
        error['errors_dict']['unknown_error'] = 'Unknown Reason. Please Try Again!!'

    errors.append(error)

    return errors
