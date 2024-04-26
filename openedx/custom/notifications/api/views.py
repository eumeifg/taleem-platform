"""
HTTP end-points for the Notifications API.
"""


import logging
from uuid import uuid4

from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop

import edx_api_doc_tools as apidocs
from edx_rest_framework_extensions.paginators import DefaultPagination
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.mixins import CreateModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.custom.notifications.models import NotificationMessage, MutedPost, NotificationPreference
from fcm_django.api.rest_framework import FCMDeviceSerializer
from fcm_django.models import FCMDevice
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment

from .serializers import NotificationSerializer
from .mixins import DeviceViewSetMixin


log = logging.getLogger(__name__)


# Default error message for user
DEFAULT_USER_MESSAGE = ugettext_noop(u'An error has occurred. Please try again.')


class NotificationsPagination(DefaultPagination):
    """
    Paginator for notifications API.
    """
    page_size = 10
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        response = super(NotificationsPagination, self).get_paginated_response(data)

        # Add `current_page` value, it's needed for pagination footer.
        response.data["current_page"] = self.page.number

        # Add `start` value, it's needed for the pagination header.
        response.data["start"] = (self.page.number - 1) * self.get_page_size(self.request)

        return response


class NotificationsViewMixin(object):
    """
    Shared code for notifications views.
    """
    def error_response(self, developer_message, user_message=None, error_status=status.HTTP_400_BAD_REQUEST):
        """
        Create and return a Response.

        Arguments:
            message (string): The message to put in the developer_message
                and user_message fields.
            status: The status of the response. Default is HTTP_400_BAD_REQUEST.
        """
        if not user_message:
            user_message = developer_message

        return Response(
            {
                "developer_message": developer_message,
                "user_message": _(user_message)
            },
            status=error_status
        )


class NotificationsListView(ListAPIView, NotificationsViewMixin):
    """REST endpoints for lists of notifications."""

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    pagination_class = NotificationsPagination
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = NotificationSerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'course_key',
                apidocs.ParameterLocation.QUERY,
                description="Course key to get the list of notifications.",
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of notifications for a user.

        The notifications are always sorted in descending order by creation date.

        Each page in the list contains 10 notifications by default. The page
        size can be altered by passing parameter "page_size=<page_size>".

        **Use Cases**

           Request information on all live courses visible to the specified user.

        **Example Requests**

            GET /api/notifications/v1/notifications/
            GET /api/notifications/v1/notifications/?course_key=course-v1%3Ax%2Fy%2Fz

        **Parameters**

            course_key (optional, URL encoded):
                If specified, filters notifications by course they belong to.
                URL encode e.g. course-v1:x/y/z --> course-v1%3Ax%2Fy%2Fz

        **Response Values**

            Body comprises a list of objects.

        **Returns**

            * 200 on success, with a list of notification objects.
            * 400 if an invalid parameter was sent

            Example response:

                [
                    {
                      "title": "Announcement",
                      "message": "Mulit admin announcement",
                      "link": null,
                      "data": {
                        "type": "admin_announcement",
                        "id": "d0706c82-8122-43bb-bbc8-12095ec1aaad",
                        "created": "2022-09-29 11:07:27.522490+03:00",
                        "read": false
                      }
                    }
                ]
        """
        return super(NotificationsListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of notifications for GET requests.

        The results will only include notifications for the request's user.
        Note: It will exclude the records having `data` as empty JSON.
        """
        user = self.request.user
        receive_on = NotificationPreference.BOTH
        if hasattr(user, 'notification_preferences'):
            receive_on = user.notification_preferences.receive_on

        course_key = self.request.data.get('course_key')
        queryset = NotificationMessage.objects.filter(
            user=user,
        ).exclude(data={})
        if course_key:
            queryset = queryset.filter(course_key=course_key)

        if receive_on not in (NotificationPreference.BOTH,
            NotificationPreference.MOBILE):
            queryset = queryset.exclude(title="Discussion")
        return queryset

    @apidocs.schema()
    def post(self, request, *unused_args, **unused_kwargs):
        """
        To use this api admin role is required.
        **Use Cases**

            Add a notification for any user.

        **Example Requests**

            POST /api/notifications/v1/notifications/

        **Parameters**

            To be sent in body (JSON).

            * email: (string) user email to be notified
            * message: (string) notification message
            * course_key (string in course-v1:abc/abc/abc format): ID of the course

            To notify all the users in the course,
            skip sending email param and specify a valid course_key.

        **Response Values**

            Body comprises an object.

        **Returns**

            * 200 on success, with the notification object.
            * 400 if an invalid parameter was sent
            * 403 if user is not an admin

            Example response:

            {
              "status": "success"
            }
        """
        if not request.user.is_superuser:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": u"action not allowed."
                }
            )

        if not request.data:
            return self.error_response(
                ugettext_noop(u'No data provided.'),
                DEFAULT_USER_MESSAGE
            )

        email = request.data.get('email', None)
        course_key = request.data.get('course_key', None)
        if not (email or course_key):
            return self.error_response(
                ugettext_noop(u'Either email or course_key required.'),
                DEFAULT_USER_MESSAGE
            )

        course_key_obj = None
        if course_key:
            try:
                course_key_obj = CourseKey.from_string(course_key)
            except:
                return self.error_response(
                    ugettext_noop(u'Invalid course_key.'),
                    DEFAULT_USER_MESSAGE
                )

        message = request.data.get('message', None)
        if not message:
            return self.error_response(
                ugettext_noop(u'Parameter message not provided.'),
                DEFAULT_USER_MESSAGE
            )

        if course_key:
            teacher_name = request.user.profile.name
            title = "{} made an announcement".format(teacher_name)
            announcement_type = "teacher_announcement"
        else:
            title = "Announcement"
            announcement_type = "admin_announcement"

        notification_id = str(uuid4())
        data = {
            'id': notification_id,
            'created': str(timezone.localtime()),
            'read': False,
            'type': announcement_type,
        }
        if course_key:
            data['course_id'] = course_key
            data['teacher_name'] = request.user.profile.name

        if email:
            users = list(User.objects.filter(
                email=email,
            ).values_list('id', flat=True))
        else:
            users = list(CourseEnrollment.objects.filter(
                is_active=True,
                course_id=course_key_obj,
            ).values_list('user_id', flat=True))

        for user_id in users:
            notification = NotificationMessage.objects.create(
                user_id=user_id,
                course_key=course_key,
                title=title,
                message=message,
                notification_id=notification_id,
                data=data,
            )

        return Response(
            {"success": True},
            status=status.HTTP_200_OK
        )

    @apidocs.schema()
    def patch(self, request, *unused_args, **unused_kwargs):
        """Mark a notification as read for a user.

        The PATCH request only needs to contain one parameter "id".
            **Example Request**
            {'id': 1}
            To mark all notifications as read: {'id': '*'}

        Http404 is returned if the notification does not exists is not correct.

        **Example Requests**

        POST /api/notifications/v1/notifications/
        """
        if not request.data:
            return self.error_response(ugettext_noop(u'No data provided.'), DEFAULT_USER_MESSAGE)

        notification_id = request.data.get('id', None)
        if not notification_id:
            return self.error_response(ugettext_noop(u'Parameter id not provided.'), DEFAULT_USER_MESSAGE)

        user = self.request.user

        if notification_id == '*':
            NotificationMessage.mark_all_as_read(user)
        else:
            try:
                NotificationMessage.objects.get(
                    notification_id=notification_id,
                    user=user
                ).mark_as_read()
            except NotificationMessage.DoesNotExist:
                error_message = ugettext_noop(u'Invalid id: {notification_id}.').format(notification_id=notification_id)
                log.error(error_message)
                return self.error_response(error_message, DEFAULT_USER_MESSAGE)

        return Response(
            NotificationSerializer(
                self.get_queryset(),
                context={'request': request},
                many=True
            ).data,
            status=status.HTTP_200_OK
        )


class HasCourseNotifications(APIView):
    """
    REST endpoint to know if the user has
    course related unread notifications or not.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated,)

    @apidocs.schema()
    def get(self, request, *args, **kwargs):
        """
        Get a Boolean indicating if the user has course
        notifications or not.

        **Use Cases**

           Request information to show a mark in mobile app
           (red dot) on `My Courses` tab if the user has
           course related notifications.

        **Example Requests**

            GET /api/notifications/v1/courses/has_notifications/

        **Parameters**

            not required

        **Response Values**

            Body comprises a object having status.

        **Returns**

            * 200 on success, with a list of notification objects.
            * 403 if user is not logged in

            Example response: {
                "has_notifications": true
            }
        """
        return Response({
            "has_notifications": NotificationMessage.objects.filter(
                user=self.request.user,
                course_key__isnull=False,
                read=False,
            ).exclude(data={}).exists(),
        })


class MutePostView(APIView):
    """
    REST endpoint to opt out from the list of
    different types of notifications/alerts.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated,)

    @apidocs.schema()
    def post(self, request, *args, **kwargs):
        """
        Mute/Unmute the given post.

        **Use Cases**

           Request to mute or unmute the discussion post.

        **Example Requests**

            POST /api/notifications/v1/mute/post/

        **Parameters**

            * course_id: ID of the course
            * post_id: ID of the post
            * mute: true/false

        **Response Values**

            Body contains JSON object with muted boolean.

        **Returns**

            * 200 on success, with muted boolean.
            * 400 if params are not valid
            * 403 if user is not logged in

            Example response: {
                "muted": true
            }
        """
        user = request.user
        course_id = request.data.get('course_id')
        if not course_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Invalid Course ID."}
            )

        post_id = request.data.get('post_id')
        if not post_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Invalid Post ID."}
            )

        mute = request.data.get('mute', True)
        muted = MutedPost.objects.filter(
            user=user,
            course_id=course_id,
            post_id=post_id,
        ).exists()

        # Create if user wants to mute
        if not muted and mute:
            MutedPost.objects.create(
                user=user,
                course_id=course_id,
                post_id=post_id
            )

        # Delete if user wants to unmute
        if not mute and muted:
            MutedPost.objects.get(
                user=user,
                course_id=course_id,
                post_id=post_id
            ).delete()

        return Response({
            'muted': mute,
        })


class FCMDeviceCreateOnlyViewSet(DeviceViewSetMixin, CreateModelMixin, GenericViewSet):
    queryset = FCMDevice.objects.all()
    serializer_class = FCMDeviceSerializer
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )

    @apidocs.schema()
    def create(self, request, *args, **kwargs):
        """
        Register a device to receive push notifications.

        **Use Cases**

           To subscribe/register a mobile device to get push notifications.

        **Example Requests**

            POST /api/notifications/v1/subscribe/ {
                "type": "web|android|ios",
                "registration_id": "fcm token here"
            }

            POST /api/notifications/v1/subscribe/ {
                "type": "web|android|ios",
                "registration_id": "fcm token here",
                "name": "device name here",
                "device_id": "device id here",
            }

            `type` and `registration_id` are required fields.

        **Response Values**

            Body comprises an objects with details of the registered device.

        **Returns**

            * 200 on success, with an device object.
            * 400 if an invalid parameter was sent

            Example response:
                {
                    "id": 10,
                    "name": "Test device",
                    "registration_id": "atestingtokendonotconsiderthisasfinalokplskeephimtheremack",
                    "device_id": "TD001",
                    "active": true,
                    "date_created": "2022-08-05T07:26:03.647276+03:00",
                    "type": "web"
                }
        """
        # delete existing
        return super(FCMDeviceCreateOnlyViewSet, self).create(request, *args, **kwargs)


class NotificationPreferenceView(APIView):
    """
    REST endpoint to get and set notification
    preferences.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated,)

    @apidocs.schema()
    def get(self, request, *args, **kwargs):
        """
        Get notification preferences.

        **Use Cases**

           Request information to see the notification preferences
           set by the user.

        **Example Requests**

            GET /api/notifications/v1/preferences/

        **Parameters**

            not required

        **Response Values**

            Body comprises a object having preferences.

        **Returns**

            * 200 on success, with a list of notification objects.
            * 403 if user is not logged in

            Example response: {
                "receive_on": "web",
                "added_discussion_post": true,
                "added_discussion_comment": false,
                "asked_question": true,
                "replied_on_question": false,
                "asked_private_question": true,
                "replied_on_private_question": false
            }
        """
        user = request.user
        preference, _ = NotificationPreference.objects.get_or_create(user=user)
        return Response({
            "receive_on": preference.get_receive_on_display(),
            "added_discussion_post": preference.added_discussion_post,
            "added_discussion_comment": preference.added_discussion_comment,
            "asked_question": preference.asked_question,
            "replied_on_question": preference.replied_on_question,
            "asked_private_question": preference.asked_private_question,
            "replied_on_private_question": preference.replied_on_private_question,
        })

    @apidocs.schema()
    def post(self, request, *args, **kwargs):
        """
        Set notification preferences.

        **Use Cases**

           Request information to set the notification preferences
           set by the user.

        **Example Requests**

            POST /api/notifications/v1/preferences/

        **Parameters**

            * receive_on: String (Web-wb, Mobile-mb, Both-bt, Nowhere-nw)
            * added_discussion_post: Boolean
            * added_discussion_comment: Boolean
            * asked_question: Boolean
            * replied_on_question: Boolean
            * asked_private_question: Boolean
            * replied_on_private_question: Boolean

        **Response Values**

            Body comprises a object having preferences.

        **Returns**

            * 200 on success, with a list of notification objects.
            * 403 if user is not logged in
            * 400 if request is invalid

            Example response: {
                "receive_on": "web",
                "added_discussion_post": true,
                "added_discussion_comment": false,
                "asked_question": true,
                "replied_on_question": false,
                "asked_private_question": true,
                "replied_on_private_question": false
            }
        """
        user = request.user
        preference, _ = NotificationPreference.objects.get_or_create(user=user)

        if "receive_on" in request.data:
            if request.data.get('receive_on') not in ('wb', 'mb', 'bt', 'nw'):
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": "Invalid option for receive_on."}
                )
            preference.receive_on = request.data.get('receive_on')

        # set preferences
        bool_fields = (
            "added_discussion_post",
            "added_discussion_comment",
            "asked_question",
            "replied_on_question",
            "asked_private_question",
            "replied_on_private_question",
        )
        for field in bool_fields:
            if field in request.data:
                if not type(request.data.get(field)) == bool:
                    return Response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data={"message": "Invalid type for {}.".format(field)}
                    )
                setattr(preference, field, request.data.get(field))

        # Save preference
        preference.save()

        return Response({
            "receive_on": preference.get_receive_on_display(),
            "added_discussion_post": preference.added_discussion_post,
            "added_discussion_comment": preference.added_discussion_comment,
            "asked_question": preference.asked_question,
            "replied_on_question": preference.replied_on_question,
            "asked_private_question": preference.asked_private_question,
            "replied_on_private_question": preference.replied_on_private_question,
        })
