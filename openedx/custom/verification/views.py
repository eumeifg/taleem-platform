"""
Views for the verification flow
"""


import json
import logging
import datetime

import six
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from edxmako.shortcuts import render_to_response
from util.json_request import JsonResponse

from lms.djangoapps.verify_student.views import PayAndVerifyView, SubmitPhotosView
from lms.djangoapps.verify_student.tasks import send_verification_status_email
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.custom.taleem.models import UserType
from openedx.custom.taleem_organization.models import OrganizationType
from openedx.custom.verification.models import CustomSoftwareSecurePhotoVerification, \
    StudentSoftwareSecurePhotoVerification, TeacherSoftwareSecurePhotoVerification

log = logging.getLogger(__name__)


class PayAndVerifyView(PayAndVerifyView):
    """
    The page will display different steps and requirements.
    """
    INTRO_STEP = 'intro-step'
    PAYMENT_CONFIRMATION_STEP = 'payment-confirmation-step'
    FACE_PHOTO_STEP = 'face-photo-step'
    ID_PHOTO_STEP = 'id-photo-step'
    REVIEW_PHOTOS_STEP = 'review-photos-step'
    ENROLLMENT_CONFIRMATION_STEP = 'enrollment-confirmation-step'

    ALL_STEPS = [
        INTRO_STEP,
        FACE_PHOTO_STEP,
        ID_PHOTO_STEP,
        REVIEW_PHOTOS_STEP,
        ENROLLMENT_CONFIRMATION_STEP
    ]

    @method_decorator(login_required)
    def get(self, request):
        """
        Render the verification flow.

        Arguments:
            request (HttpRequest): The request object.

        Returns:
            HttpResponse
        """

        user = request.user
        user_type = user.ta3leem_profile.user_type
        if self._check_already_verified(user):
            return redirect(reverse('verification:already_verified'))

        display_steps = [
            {
                'name': step,
                'title': six.text_type(self.STEP_TITLES[step]),
            }
            for step in self.ALL_STEPS
        ]
        # Override the actual value if account activation has been disabled
        # Also see the reference to this parameter in context dictionary further down
        user_is_active = self._get_user_active_status(user)
        requirements = self._requirements(display_steps, user_is_active)


        message = self.FIRST_TIME_VERIFY_MSG
        current_step = display_steps[0]['name']

        if request.GET.get('skip-first-step') and current_step in self.SKIP_STEPS:
            display_step_names = [step['name'] for step in display_steps]
            current_step_idx = display_step_names.index(current_step)
            if (current_step_idx + 1) < len(display_steps):
                current_step = display_steps[current_step_idx + 1]['name']

        full_name = (
            user.profile.name
            if user.profile.name
            else ""
        )

        # Render the top-level page
        context = {
            'checkpoint_location': request.GET.get('checkpoint'),
            'current_step': current_step,
            'disable_courseware_js': True,
            'display_steps': display_steps,
            'user_type': user_type,
            'is_active': json.dumps(user_is_active),
            'user_email': user.email,
            'message_key': message,
            'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
            'requirements': requirements,
            'user_full_name': full_name,
            'capture_sound': staticfiles_storage.url("audio/camera_capture.wav"),
            'nav_hidden': False,
        }

        return render_to_response("verification/pay_and_verify.html", context)


class HandlePhotosView(SubmitPhotosView):
    """
    End-point for submitting photos for verification.
    """

    @method_decorator(login_required)
    def post(self, request):
        """
        Submit photos for verification.

        This end-point is used for the following cases:

        * Initial verification through the pay-and-verify flow.

        POST Parameters:

            face_image (str): base64-encoded image data of the user's face.
            photo_id_image (str): base64-encoded image data of the user's photo ID.
            full_name (str): The user's full name, if the user is requesting a name change as well.
        """
        # If the user already has an initial verification attempt, we can re-use the photo ID
        # the user submitted with the initial attempt.
        initial_verification = CustomSoftwareSecurePhotoVerification.get_initial_verification(request.user)

        # Validate the POST parameters
        params, response = self._validate_parameters(request, bool(initial_verification))
        if response is not None:
            return response

        # If necessary, update the user's full name
        if "full_name" in params:
            response = self._update_full_name(request.user, params["full_name"])
            if response is not None:
                return response

        face_image = params["face_image"]
        photo_id_image = params["photo_id_image"]

        self._submit_attempt(request.user, face_image, photo_id_image, initial_verification)

        self._fire_event(request.user, "edx.bi.verify.submitted", {"category": "verification"})
        self._send_confirmation_email()
        return JsonResponse({})

    def _submit_attempt(self, user, face_image, photo_id_image=None, initial_verification=None):
        """
        Submit a verification attempt.

        Arguments:
            user (User): The user making the attempt.
            face_image (str): Decoded face image data.

        Keyword Arguments:
            photo_id_image (str or None): Decoded photo ID image data.
            initial_verification (SoftwareSecurePhotoVerification): The initial verification attempt.
        """
        attempt = CustomSoftwareSecurePhotoVerification(user=user)

        decode_face_image, decode_photo_id_image, _ = self._decode_image_data(face_image, photo_id_image)

        # We will always have face image data, so upload the face image
        attempt.upload_face_image(decode_face_image)

        # If an ID photo wasn't submitted, re-use the ID photo from the initial attempt.
        # Earlier validation rules ensure that at least one of these is available.
        if photo_id_image is not None:
            attempt.upload_photo_id_image(decode_photo_id_image)
        elif initial_verification is None:
            # Earlier validation should ensure that we never get here.
            log.error(
                "Neither a photo ID image or initial verification attempt provided. "
                "Parameter validation in the view should prevent this from happening!"
            )

        # Submit the attempt
        attempt.mark_ready()
        attempt.submit(face_image=face_image, photo_id_image=photo_id_image)

        return attempt


@login_required
def already_verified(request):
    template_name = 'verification/already_verified.html'
    response = render_to_response(template_name, {})
    return response


@require_http_methods(['GET'])
@login_required
def get_verifications_view(request, user_type):
    if not request.user.is_superuser and not request.user.groups.filter(name='Verification Specialist').exists():
        raise Http404

    try:
        user_type = UserType[user_type]
    except KeyError:
        raise Http404

    if user_type.name == 'student':
        model = StudentSoftwareSecurePhotoVerification
    else:
        model = TeacherSoftwareSecurePhotoVerification

    current_user = request.user
    current_user_profile = current_user.ta3leem_profile
    organization = current_user_profile.organization

    if organization.type == OrganizationType.SCHOOL.name:
        queryset = model.objects.select_related('user__ta3leem_profile__organization').filter(
            user__ta3leem_profile__organization=organization)
    else:
        department = current_user_profile.department.all()
        queryset = model.objects.select_related('user__ta3leem_profile').order_by('submitted_at').filter(
            user__ta3leem_profile__department__in=department).distinct()

    return render_to_response('verification/requests.html', {
        'verifications': queryset,
        'model_name': user_type.value
    })


@require_http_methods(['POST'])
@login_required
@ensure_csrf_cookie
def change_verification_status(request):
    allowed_status = ['approved', 'denied']

    params = json.loads(request.body.decode("utf-8"))
    status = params.get('status')
    verification_ids = params.get('verification_ids')

    if not status or not verification_ids or status not in allowed_status:
        raise Http404

    try:
        verifications = CustomSoftwareSecurePhotoVerification.objects.filter(id__in=verification_ids)
        for verification in verifications:
            verification.status = status
            verification.save()
            _send_status_email(verification.user, status)
    except Exception as ex:
        log.info(ex)
        return JsonResponse({'message': 'There is some error!!'}, status=500)

    return JsonResponse({
        'verifications': verification_ids,
        'updated': True
    }, status=200)


def _send_status_email(user, status):
    """
    Send the verification status email
    to the user where status can be
    approved or denied.
    """
    verification_status_email_vars = {
        'full_name': user.profile.name,
    }
    if status == 'approved':
        expiry_date = datetime.date.today() + datetime.timedelta(
            days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
        )
        verification_status_email_vars.update({
            'expiry_date': expiry_date.strftime("%m/%d/%Y"),
        })
    else:
        verification_status_email_vars.update({
            'verification_errors': [],
            'verify_link': "{}{}".format(
                settings.LMS_ROOT_URL,
                reverse('verification:verify_student_identification')
            )
        })

    send_verification_status_email.delay({
        'user_id': user.id,
        'status': 1 if status == 'approved' else 0,
        'email_vars': verification_status_email_vars,
    })
