"""
Teacher API views
"""

from rest_framework.generics import ListCreateAPIView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from openedx.custom.teacher.models import AccessRequest
from .serializers import AccessRequestSerializer


class AccessRequestView(ListCreateAPIView):
    """
        **Use Cases**

            * Get or Create teacher access request.

        **Example Requests**

            GET /api/teacher/access/request/?email=test@example.com

            POST /api/teacher/access/request/ {

                "first_name": "first name",
                "last_name": "last name",
                "email": "test@example.com",
                "email": "test@example.com",
                "country": "IQ",
                "phone_number": "+964712345678",
                "speciality": "Maths",
                "qualifications": "Ph.D",
                "course_title": "optional course title",
                "profile_photo": "<image>",
                "cv_file": "<pdf/doc file>"
            }

        **POST Response Values**

            If an unspecified error occurs when the user tries to
            create the request, returns an HTTP 400 "Bad
            Request" response.

            Else HTTP 200 "Success"
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = AccessRequestSerializer
    parser_classes = (MultiPartParser, FormParser, )

    def get_queryset(self):
        email = self.request.GET.get('email', '')
        return AccessRequest.objects.filter(email=email)

    def get(self, request, *args, **kwargs):
        """
        Get an existing access request if any.
        """
        return super(AccessRequestView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Create a teacher access request.
        """
        if 'profile_photo' not in request.FILES:
            return Response(
                {
                    "user_message": _(u"No file provided for profile image"),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        if 'cv_file' not in request.FILES:
            return Response(
                {
                    "user_message": _(u"No file provided for CV"),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get the request data
        # serializer = AccessRequestSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        # return Response(status=status.HTTP_201_CREATED)
        return super(AccessRequestView, self).post(request, *args, **kwargs)
