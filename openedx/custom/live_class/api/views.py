"""
Live course API views
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.throttling import UserRateThrottle
from rest_framework import permissions, status
from rest_framework.response import Response
import edx_api_doc_tools as apidocs

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.custom.live_class.models import LiveClass, LiveClassBooking, LiveClassAttendance
from openedx.custom.notifications.constants import NotificationTypes
from openedx.custom.notifications.utils import notify_user

from . import USE_RATE_LIMIT_2_FOR_LIVE_COURSE_LIST_API, USE_RATE_LIMIT_10_FOR_LIVE_COURSE_LIST_API
from .courses import get_course_with_access, get_live_courses, my_live_classes
from .forms import LiveCourseDetailGetForm, LiveCourseListGetForm
from .serializers import LiveCourseDetailSerializer, LiveCourseSerializer
from .paginators import LiveCoursePagination


@view_auth_classes(is_authenticated=False)
class LiveCourseDetailView(DeveloperErrorViewMixin, RetrieveAPIView):
    """
    **Use Cases**

        Request details for a live course

    **Example Requests**

        GET /api/live-courses/v1/courses/{course_key}/

    **Response Values**

        Body consists of the following fields:

        * course_id: A unique identifier of the live course
        * name: Name of the course
        * description: A possibly verbose HTML textual description of the course.
        * start: Date and Time the course begins, in ISO 8601 notation
        * stage: Current stage of the course Running, or  Scheduled (Upcoming)
        * duration: Duration of the live class in minutes
        * price: A number indicating the price of the live course
        * seats: Total number of seats to join the course
        * seats_left: Total number of seats left to join the course
        * instructor: Name of the teacher who owns the course
        * has_booked: Whether the user has booked the course or not
        * booking_url: Used to book the course
        * meeting_url: Used to go to the live class
            * Available only if the user has booked the course

    **Parameters:**

        No parameter required except the course key which is part of the URL.


    **Returns**

        * 200 on success with above fields.
        * 400 if an invalid parameter was sent or
          the course key was not provided.
        * 404 if the course is not available or cannot be seen by the user.

        Example response:

            {
                "course_id": "220041e0-df6c-4008-9de8-4235af96023f",
                "name": "Example Course",
                "subject": "Mathematics",
                "organization": {
                    "name": "Oxford University",
                    "logo": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/organizations/done-image.png"
                },
                "poster": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/live_classes/courses-img5.jpg",
                "description": "<p>An example course.</p>",
                "start": "2015-07-17T12:00:00Z",
                "stage": "Running",
                "visibility": "Private",
                "duration": "60 Minutes",
                "price": 100,
                "seats": 50,
                "seats_left": 10,
                "instructor": "Mr Teacher",
                "has_booked": false,
                "booking_url": "/api/live-courses/v1/courses/220041e0-df6c-4008-9de8-4235af96023f/book/",
                "meeting_url": "/api/live-courses/v1/courses/220041e0-df6c-4008-9de8-4235af96023f/meet/"
            }
    """

    serializer_class = LiveCourseDetailSerializer

    def get_object(self):
        """
        Return the requested live course object, if the user has appropriate
        permissions.
        """
        requested_params = self.request.query_params.copy()
        requested_params.update({'course_key': self.kwargs['course_key']})
        form = LiveCourseDetailGetForm(requested_params)
        if not form.is_valid():
            raise ValidationError(form.errors)

        return get_course_with_access(
            self.request.user,
            form.cleaned_data['course_key'],
        )

class LiveCourseListUserThrottle(UserRateThrottle):
    """Limit the number of requests users can make to the live course list API."""
    # The course list endpoint is likely being inefficient with how it's querying
    # various parts of the code and can take plaform down, it needs to be rate
    # limited until optimized. LEARNER-5527

    THROTTLE_RATES = {
        'user': '20/minute',
        'staff': '40/minute',
    }

    def check_for_switches(self):
        if USE_RATE_LIMIT_2_FOR_LIVE_COURSE_LIST_API.is_enabled():
            self.THROTTLE_RATES = {
                'user': '2/minute',
                'staff': '10/minute',
            }
        elif USE_RATE_LIMIT_10_FOR_LIVE_COURSE_LIST_API.is_enabled():
            self.THROTTLE_RATES = {
                'user': '10/minute',
                'staff': '20/minute',
            }

    def allow_request(self, request, view):
        self.check_for_switches()
        # Use a special scope for staff to allow for a separate throttle rate
        user = request.user
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            self.scope = 'staff'
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)

        return super(LiveCourseListUserThrottle, self).allow_request(request, view)


@view_auth_classes(is_authenticated=False)
class LiveCourseListView(DeveloperErrorViewMixin, ListAPIView):
    """REST endpoint to list live courses"""

    pagination_class = LiveCoursePagination
    serializer_class = LiveCourseSerializer
    throttle_classes = (LiveCourseListUserThrottle,)

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'stage',
                apidocs.ParameterLocation.QUERY,
                description="The stage of live course `sd (upcoming)`, `rg (on going)`. Skip this to get all stages.",
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        """
        **Use Cases**

            Request information on all live courses visible to the specified user.

       **Example Requests**

           GET /api/live-courses/v1/courses/

        **Response Values**

           Body comprises a list of objects as returned by `LiveCourseDetailView`.

        **Parameters**

            stage (optional):
                If specified, filters courses by stage they belong to.

        **Returns**

            * 200 on success, with a list of course discovery objects as returned
              by `LiveCourseDetailView`.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                      "course_id": "220041e0-df6c-4008-9de8-4235af96023f",
                      "name": "Example Course",
                      "subject": "Mathematics",
                      "organization": {
                          "name": "Oxford University",
                          "logo": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/organizations/done-image.png"
                      },
                      "grade": "Grade 1",
                      "language": "Arabic",
                      "poster": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/live_classes/courses-img5.jpg",
                      "start": "2015-07-17T12:00:00Z",
                      "stage": "Running",
                      "visibility": "Public",
                      "duration": "60 Minutes",
                      "price": 100,
                      "seats": 50,
                      "seats_left": 10,
                      "details_url": "/api/live-courses/v1/courses/220041e0-df6c-4008-9de8-4235af96023f/",
                  }
                ]
        """
        return super(LiveCourseListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Yield live courses visible to the user.
        """
        form = LiveCourseListGetForm(self.request.query_params)
        if not form.is_valid():
            raise ValidationError(form.errors)

        return get_live_courses(stage=form.cleaned_data['stage'])


class LiveCourseEnrollmentView(APIView):
    """
        **Use Cases**

            * Get a list of all live course enrollments for the currently signed in user.

            * Enroll the currently signed in user in a live course.

        **Example Requests**

            GET /api/live-courses/v1/courses/enrollment/

            POST /api/live-courses/v1/courses/enrollment/ {

                "course_id": "577caa7a-1388-46cb-9e38-c96868f4c7b1",
            }

            **POST Parameters**

              A POST request can include the following parameters.

              * course_id: The unique identifier for the course.

        **GET Response Values**

            If an unspecified error occurs when the user tries to obtain a
            learner's enrollments, the request returns an HTTP 400 "Bad
            Request" response.

        **POST Response Values**

             If the user does not specify a course ID, the specified course
             does not exist, the request
             returns an HTTP 400 "Bad Request" response.

             If the course is full and no seat left for the enrollment,
             or the course is not public,
             or the course is not yet approved for enrollments,
             the request return an HTTP 403 "Forbidden" response.

             If the course is paid, until we have payment flow integrated,
             the request will return 403 "Forbidden" response.

        **GET and POST Response Values**

            If the request is successful, an HTTP 200 "OK" response is
            returned along with a collection of course enrollments for the
            user or for the newly created enrollment.

            Example response.
                [
                  {
                      "course_id": "220041e0-df6c-4008-9de8-4235af96023f",
                      "name": "Example Course",
                      "subject": "Mathematics",
                      "organization": {
                          "name": "Oxford University",
                          "logo": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/organizations/done-image.png"
                      },
                      "grade": "Grade 1",
                      "language": "Arabic",
                      "poster": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/live_classes/courses-img5.jpg",
                      "start": "2015-07-17T12:00:00Z",
                      "stage": "Running",
                      "duration": "60 Minutes",
                      "price": 100,
                      "seats": 50,
                      "seats_left": 10,
                      "details_url": "/api/live-courses/v1/courses/220041e0-df6c-4008-9de8-4235af96023f/",
                  }
                ]
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        """Gets a list of all live course enrollments for a user.

        Returns a list for the currently logged in user.
        """
        qset = my_live_classes(self.request.user)
        enrollments = LiveCourseSerializer(qset, many=True,
            context={'request': self.request}).data
        return Response(enrollments)

    def post(self, request):
        # pylint: disable=too-many-statements
        """
        Enrolls the currently logged-in user in a course.
        """
        # Get the User, Course ID, and Mode from the request.

        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": u"Course ID must be specified to create a new enrollment."}
            )

        try:
            live_class = LiveClass.objects.get(id=course_id)
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"No course '{course_id}' found for enrollment".format(course_id=course_id)
                }
            )

        # Check that the course is free
        if live_class.is_paid:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": u"Course '{course_id}' is paid.".format(
                        course_id=course_id
                    )
                }
            )

        # Check that the course public
        if live_class.class_type != LiveClass.PUBLIC:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": u"Course '{course_id}' is not public.".format(
                        course_id=course_id
                    )
                }
            )

        # Check that the course is approved
        if live_class.stage not in [LiveClass.SCHEDULED, LiveClass.RUNNING]:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": u"Course '{course_id}' is not accepting enrollments.".format(
                        course_id=course_id
                    )
                }
            )

        # Check that the seat is available
        if not live_class.seats_left:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": u"Course '{course_id}' is full.".format(
                        course_id=course_id
                    )
                }
            )

        booking, created = LiveClassBooking.objects.get_or_create(
            user=user,
            live_class=live_class,
        )
        if created:
            notify_user(
                user=user,
                notification_type=NotificationTypes.LIVE_CLASS_BOOKED,
                notification_message="You have been enrolled in new live class {{live_class_name:{live_class_name}}}".format(
                    live_class_name=live_class.name,
                )
            )

        enrollment = LiveCourseSerializer(
            live_class,
            context={'request': self.request}
        ).data
        return Response(enrollment)


class LiveCourseJoinView(APIView):
    """
        **Use Cases**

            * Check if the user can join the class.

        **Example Requests**

            GET /api/live-courses/v1/class/can_join/{course_key}

        **GET Response Values**

            If an user can join the class it returns true else
            returns false

        **GET Response Values**

            If the request is successful, an HTTP 200 "OK" response is
            returned along with a boolean indicates whether the user
            can join the class now or not.

            Example response {
              "can_join": true
            }
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, course_id):
        """
        Check if the user can join the request class.
        """
        user = request.user

        try:
            live_class = LiveClass.objects.get(id=course_id)
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"course '{course_id}' not found".format(course_id=course_id)
                }
            )

        # check if the user has booked the class
        if not live_class.has_booked(user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": u"Not enrolled in a course '{course_id}'".format(course_id=course_id)
                }
            )

        # Check if the user can join now
        return Response({
            "can_join": live_class.can_join(user),
        })


class LiveCourseAttendanceUserThrottle(UserRateThrottle):
    """
    Limit the number of requests users can make to
    the live course attendance API.
    """
    # The endpoint is likely being inefficient with how it's querying
    # various parts of the code and can take plaform down, it needs to be rate
    # limited until optimized. LEARNER-5527

    THROTTLE_RATES = {
        'user': '6/minute',
        'staff': '10/minute',
    }


class LiveCourseAttendanceView(APIView):
    """
        **Use Cases**

            * Take attendance of the user for a given live class.

        **Example Requests**

            POST /api/live-courses/v1/class/attendance/ {
                "course_id": "asdb-878-JSDFJS",
                "punch": "in/out"
            }

        **POST Request Params**

            * course_id: ID of the live class
            * punch: string, possible values in/out

        **POST Response Values**

            If the request is successful, an HTTP 200 "OK" response is
            returned along with a boolean indicates whether the user's
            attendance logged or not.

            Example response {
              "success": true
            }
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated, )
    throttle_classes = (LiveCourseAttendanceUserThrottle,)

    def post(self, request):
        """
        Check if the user can join the request class.
        """
        punch_time = timezone.now()
        user = request.user
        punch = request.data.get('punch')
        course_id = request.data.get('course_id')

        try:
            live_class = LiveClass.objects.get(id=course_id)
        except ObjectDoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"course '{course_id}' not found".format(course_id=course_id)
                }
            )

        # check if the user has booked the class
        if not live_class.has_booked(user):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": u"Not enrolled in a course '{course_id}'".format(course_id=course_id)
                }
            )

        # check stage of the class
        if live_class.stage not in (
            LiveClass.RUNNING, LiveClass.ENDED
        ):
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    "message": u"Attendace at invalid stage '{stage}'".format(stage=live_class.stage)
                }
            )

        # check if the user has booked the class
        if punch not in ("in", "out", ):
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"Invalid punch"
                }
            )

        # For ended class, only punch out is allowed
        if live_class.stage == LiveClass.ENDED and punch == 'in':
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"Class ended, punch in not allowed"
                }
            )

        # Log the attendance
        attendance, created = LiveClassAttendance.objects.get_or_create(
            user=user,
            live_class=live_class,
        )

        # validate sequence
        if created and punch == 'out':
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"Punch out not allowed before punch in"
                }
            )

        if not created and punch == 'in':
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "message": u"Punch in is allowed only once"
                }
            )

        if punch == 'in':
            attendance.joined_at = punch_time
        else:
            grace_minutes = 5 # minutes
            end_dt = live_class.scheduled_on + timedelta(
                minutes=live_class.duration)
            if punch_time > end_dt + timedelta(minutes=grace_minutes):
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        "message": u"Punch out not within time duration"
                    }
                )
            attendance.left_at = min(punch_time, end_dt)

        # Save attendance
        attendance.save()

        # Check if the user can join now
        return Response({
            "success": True,
        })
