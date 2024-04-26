from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from student.models import Registration
from student.views import compose_and_send_activation_email
from openedx.custom.taleem.api.utils import (
    create_user_account,
    get_access_token,
    get_existing_user_if_exists,
    get_user_data,
    PerMinuteResendActivationEmailThrottle,
    validate_request_parameters,
)
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.custom.taleem.models import MobileApp

User = get_user_model()

@api_view(['GET'])
@view_auth_classes(is_authenticated=False)
def mobile_app_version(request):
    """
    Return the latest version number and
    download link.
    """
    mobile_app = MobileApp.objects.filter().order_by('-version').first()
    version = '0.0.0'
    android_version = '0.0.0'
    force_update = False
    android_force_update = False
    link = ''
    if mobile_app:
        version = '{}'.format(mobile_app.version)
        android_version = '{}'.format(mobile_app.android_version)
        force_update = mobile_app.force_update
        android_force_update = mobile_app.android_force_update
        link = '{}{}'.format(
            settings.LMS_ROOT_URL,
            reverse('taleem:download_app')
        )

    return JsonResponse({
        'version': version,
        'download_link': link,
        'force_update': force_update,
        'android_version': android_version,
        'android_force_update': android_force_update,
    })

@api_view(['POST'])
@throttle_classes([PerMinuteResendActivationEmailThrottle])
def re_send_activation_email(request):
    """
    View handler for re-sending activation email.
    """
    try:
        email = request.data.get('email')
        user = User.objects.filter(email=email).first()

        if not user:
            return JsonResponse({'success': False, "message": "User not found"})

        registration = Registration.objects.get(user=user)
        compose_and_send_activation_email(user, user.profile, registration)

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


class SocialSignIn(APIView):
    """
        **Use Cases**

            * Get access token for social app user.

        **Example Requests**

            POST api/taleem/social_signin/ {
                "socialID": "1435464234",
                "email": "edx@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "provider": "google,facebook,apple",
                "clientID": "Mobile App Client ID"
            }

            **POST Parameters**

              A POST request can include the following parameters.

              * social_id: Should be the RawID from the firebase user data.
              * email: Email of the user you want to sign_in.
              * first_name: First Name of the User will be used for the registration of the user.
              * last_name: Last Name of the User will be user for the registration of the user.
              * provider: Social App provider of the user.
              * clientID: Oauth2 Client_id used for getting the access token.

        **POST Response Values**

             It returns Access token and Refresh Token for the user.

        **POST Response Values**

            If the request is successful, an HTTP 200 "OK" response is
            returned along with Access Token.

            {
                "access_token": "token",
                "expires_in": 36000,
                "token_type": "Bearer",
                "refresh_token": "token",
                "scope": "read write email profile"
            }
    """

    def post(self, request):
        # pylint: disable=too-many-statements
        is_valid, error = validate_request_parameters(request)
        if not is_valid:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": error}
            )

        user = get_existing_user_if_exists(request)

        if not user:
            data = get_user_data(request)
            user = create_user_account(request, data)

        token = get_access_token(user, request.data.get('client_id'))

        return Response(
            status=status.HTTP_200_OK,
            data=token
        )
