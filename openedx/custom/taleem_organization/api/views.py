"""
HTTP end-points for the Ta3leem org API.
"""
import logging
from urllib.parse import urljoin

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop
from edx_rest_framework_extensions.paginators import DefaultPagination
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import NON_FIELD_ERRORS, PermissionDenied
from django.db import transaction
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.conf import settings

from student.models import (
    NonExistentCourseError, EnrollmentClosedError, CourseFullError,
    AlreadyEnrolledError,
)
from opaque_keys.edx.keys import CourseKey
from course_modes.models import CourseMode

from openedx.custom.taleem_organization.models import Skill
from .serializers import SkillSerializer

from openedx.core.djangoapps.user_api import accounts as accounts_settings
from openedx.core.djangoapps.user_authn.views import register
from util.json_request import JsonResponse
from django.core.validators import ValidationError
from six import text_type

from openedx.custom.taleem.models import UserType
from openedx.core.djangoapps.user_authn.utils import generate_password
from student.models import (
    email_exists_or_retired,
    username_exists_or_retired,
)
from student.helpers import (
    AccountValidationError,
)

from openedx.custom.taleem_organization import utils
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.custom.taleem_organization.models import Subject, TaleemOrganization, College
from openedx.custom.taleem_organization.decorators import ensure_tashgheel_access
from openedx.custom.utils import convert_comma_separated_string_to_list
from student.models import CourseEnrollment
from .serializers import SubjectSerializer, TaleemOrganizationSerializer, CollegeSerializer
from ..utils import skill_name_exists, get_tashgheel_user
from ...notifications.api.views import log
from ...taleem_grades.models import PersistentExamGrade
from ...timed_exam.models import TimedExam


log = logging.getLogger(__name__)


# Default error message for user
DEFAULT_USER_MESSAGE = ugettext_noop(u'An error has occurred. Please try again.')


class TaleemPagination(DefaultPagination):
    """
    Paginator for subjects API.
    """
    page_size = 10
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        response = super(TaleemPagination, self).get_paginated_response(data)

        # Add `current_page` value, it's needed for pagination footer.
        response.data["current_page"] = self.page.number

        # Add `start` value, it's needed for the pagination header.
        response.data["start"] = (self.page.number - 1) * self.get_page_size(self.request)

        return response


class TaleemViewMixin(object):
    """
    Shared code for app views.
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


@view_auth_classes(is_authenticated=False)
class SubjectListView(ListAPIView, TaleemViewMixin):
    """REST endpoints for lists of notifications."""

    pagination_class = TaleemPagination
    serializer_class = SubjectSerializer

    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of subjects.

        The subjects are always sorted in ascending order by name.

        Each page in the list contains 10 notifications by default. The page
        size can be altered by passing parameter "page_size=<page_size>".

        **Use Cases**

           Request information on all subjects.

        **Example Requests**

            GET /api/subjects/v1/subjects/

        **Response Values**

            Body comprises a list of objects.

        **Returns**

            * 200 on success, with a list of subject objects.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                    "id": 11,
                    "name": "Arabic Language"
                  }
                ]
        """
        return super(SubjectListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of subjects for GET requests.

        The results will only include subjects.
        """
        return Subject.objects.all().order_by('name')


@view_auth_classes(is_authenticated=False)
class OrganizationListView(ListAPIView, TaleemViewMixin):
    """REST endpoints for lists of Organizations."""

    pagination_class = TaleemPagination
    serializer_class = TaleemOrganizationSerializer

    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of Organizations.

        The organization are always sorted in ascending order by name.

        Each page in the list contains 10 notifications by default. The page
        size can be altered by passing parameter "page_size=<page_size>".

        **Use Cases**

           Request information on Organizations.

        **Example Requests**

            GET /api/organizations/v1/organizations/

        **Response Values**

            Body comprises a list of objects.

        **Returns**

            * 200 on success, with a list of university objects.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                    "id": 111,
                    "name": "Baghdad University",
                    "type": "University",
                    "poster": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/organizations/sukran.png",
                    "num_courses": 12
                  },
                  {
                    "id": 453,
                    "name": "Primary School",
                    "type": "School",
                    "poster": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/organizations/sukran.png",
                    "num_courses": 20
                  }

                ]
        """
        return super(OrganizationListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of Organizations for GET requests.

        The results will only include Organizations.
        """
        return TaleemOrganization.objects.all().order_by('name')


@view_auth_classes(is_authenticated=False)
class CollegeListView(ListAPIView, TaleemViewMixin):
    """REST endpoints for lists of colleges."""

    pagination_class = TaleemPagination
    serializer_class = CollegeSerializer

    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of Colleges.

        The colleges are always sorted in ascending order by name.

        Each page in the list contains 10 notifications by default. The page
        size can be altered by passing parameter "page_size=<page_size>".

        **Use Cases**

           Request information on Colleges.

        **Example Requests**

            GET /api/organizations/v1/colleges/

        **Response Values**

            Body comprises a list of objects.

        **Returns**

            * 200 on success, with a list of college objects.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                    "id": 201,
                    "name": "Baghdad College of Engineering",
                  },
                  {
                    "id": 764,
                    "name": "Babylon College of Arts",
                  }

                ]
        """
        return super(CollegeListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of Colleges for GET requests.

        The results will only include colleges.
        """
        return College.objects.all().order_by('name')


@view_auth_classes(is_authenticated=False)
class SkillListView(ListAPIView):
    """
    REST endpoints for lists of skills.
    """

    pagination_class = TaleemPagination
    serializer_class = SkillSerializer

    @method_decorator(ensure_tashgheel_access)
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of Organizations for GET requests.

        The results will only include skills that are associated with some timed exam.
        """
        skills = TimedExam.objects.values_list('skill', flat=True)
        return Skill.objects.filter(id__in=skills).order_by('-created').all()


class TashgheelRegistrationView(APIView):
    """
    HTTP end-points for creating a new user from Tashgeel.
    """

    # This end-point is available to anonymous users,
    # so do not require authentication.
    authentication_classes = []

    @method_decorator(transaction.non_atomic_requests)
    @method_decorator(ensure_tashgheel_access)
    def dispatch(self, request, *args, **kwargs):
        return super(TashgheelRegistrationView, self).dispatch(request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Create the user's account.

        You must send all required form fields with the request.

        Arguments:
            request (HTTPRequest)

        Returns:
            HttpResponse: 200 on success
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 409 if an account with the given username or email
                address already exists
            HttpResponse: 403 operation not allowed
        """
        data = request.POST.copy()

        skill = data.get('skill')
        temp_password = generate_password()
        data["password"] = temp_password
        data["user_type"] = UserType.student.name
        data["honor_code"] = 'true'
        data["country"] = 'IQ'

        data['organization'] = self._get_tashgeel_organization_id()
        data['org_type'] = 'university'
        data['grade'] = 'NA'

        self._handle_terms_of_service(data)

        response = self._handle_skill(request, data)

        if response:
            return response

        email = data.get('email')
        username = data.get('username')

        user = get_tashgheel_user(email, username)
        if not user:
            response = self._handle_duplicate_email_username(request, data)
            if response:
                return response

            response, user = self._create_account(request, data)
            if response:
                return response

            # Mark user as tashgeel user.
            user.ta3leem_profile.is_tashgheel_user = True
            user.ta3leem_profile.save()

            # Send registration email.
            # send_tashgheel_registration_email(user.email, temp_password)

        if skill:
            response = self._handle_timed_exam_enrollments(request, user, skill)
            if response:
                return response

        token = utils.create_token(user)
        login_url = urljoin(
            settings.LMS_ROOT_URL,
            reverse('taleem_organization:tashgeel_user_login', args=(str(token.token),))
        )

        response = self._create_response(request, {'login_url': login_url}, status_code=200)
        return response

    def _get_tashgeel_organization_id(self):
        """
        Get organization id for the tashgeel.
        """
        org, _ = TaleemOrganization.objects.get_or_create(name='Tashgheel', type='UNIVERSITY')
        return org.id

    def _handle_skill(self, request, data):
        """
        Handle skill validation.
        """
        errors = {}
        skill = data.get('skill', None)
        error_message = _(
            u"It looks like '{skill_name}' does not exist in the system. "
            u"Try again with correct skill. Note that skill names are case sensitive."
        )

        if skill and not utils.skill_name_exists(skill):
            errors["skill"] = [{"user_message": error_message.format(skill_name=skill)}]

        if errors:
            return self._create_response(request, errors, status_code=409)

    def _handle_terms_of_service(self, data):
        # Backwards compatibility: the student view expects both
        # terms of service and honor code values.  Since we're combining
        # these into a single checkbox, the only value we may get
        # from the new view is "honor_code".
        # Longer term, we will need to make this more flexible to support
        # open source installations that may have separate checkboxes
        # for TOS, privacy policy, etc.
        if data.get("honor_code") and "terms_of_service" not in data:
            data["terms_of_service"] = data["honor_code"]

    def _handle_duplicate_email_username(self, request, data):
        """
        Validate the user with the given email or user nome does already exist.
        """
        email = data.get('email')
        username = data.get('username')
        errors = {}

        if email is not None and email_exists_or_retired(email):
            errors["email"] = [{"user_message": accounts_settings.EMAIL_CONFLICT_MSG.format(email_address=email)}]

        if username is not None and username_exists_or_retired(username):
            errors["username"] = [{"user_message": accounts_settings.USERNAME_CONFLICT_MSG.format(username=username)}]

        if errors:
            return self._create_response(request, errors, status_code=409)

    def _create_account(self, request, data):
        response, user = None, None
        try:
            user = register.create_account_with_params(request, data)
        except AccountValidationError as err:
            errors = {
                err.field: [{"user_message": text_type(err)}]
            }
            response = self._create_response(request, errors, status_code=409)
        except ValidationError as err:
            # Should only get field errors from this exception
            assert NON_FIELD_ERRORS not in err.message_dict
            # Only return first error for each field
            errors = {
                field: [{"user_message": error} for error in error_list]
                for field, error_list in err.message_dict.items()
            }
            response = self._create_response(request, errors, status_code=400)
        except PermissionDenied:
            response = HttpResponseForbidden(_("Account creation not allowed."))

        return response, user

    def _create_response(self, request, response_dict, status_code):
        if status_code == 200:
            # keeping this `success` field in for now, as we have outstanding clients expecting this
            response_dict['success'] = True
        else:
            self._log_validation_errors(request, response_dict, status_code)

        return JsonResponse(response_dict, status=status_code)

    def _log_validation_errors(self, request, errors, status_code):
        try:
            for field_key, errors in errors.items():
                for error in errors:
                    log.info(
                        'message=registration_failed, status_code=%d, agent="%s", field="%s", error="%s"',
                        status_code,
                        request.META.get('HTTP_USER_AGENT', ''),
                        field_key,
                        error['user_message']
                    )
        except:  # pylint: disable=bare-except
            log.exception("Failed to log registration validation error")

    def _handle_timed_exam_enrollments(self, request, user, skill):
        """
        Handle timed exam enrollments of the new user.

        Argument:
            request (HttpRequest): Django Http Request object.
            user (User): Django user instance to that was just created.
            skill (str): Name of the skill whose timed exam user needs to be enrolled in.
        """
        timed_exams = TimedExam.objects.filter(skill__name=skill).all()
        errors = {}

        for timed_exam in timed_exams:
            try:
                if not CourseEnrollment.is_enrolled(user=user, course_key=CourseKey.from_string(timed_exam.key)):
                    CourseEnrollment.enroll(
                        user=user,
                        course_key=CourseKey.from_string(timed_exam.key),
                        mode=CourseMode.TIMED,
                    )
            except NonExistentCourseError:
                errors['enrollment'] = "User {} failed to enroll in non-existent course {}.".format(
                    user.username, text_type(timed_exam.key)
                )
            except EnrollmentClosedError:
                errors['enrollment'] = "User {} failed to enroll in course {} because enrollment is closed.".format(
                    user.username, text_type(timed_exam.key)
                )
            except CourseFullError:
                errors['enrollment'] = "Course {} has reached its maximum enrollment of learners. " \
                                       "User {} failed to enroll.".format(
                    text_type(timed_exam.key), user.username
                )
            except AlreadyEnrolledError:
                errors['enrollment'] = "User {} attempted to enroll in {}, but they were already enrolled.".format(
                    user.username, text_type(timed_exam.key)
                )
        if errors:
            return self._create_response(request, errors, status_code=409)


class TashgheelGradeView(APIView):
    """
    HTTP end-points for getting Tashgheel user's
    """

    # This end-point is available to anonymous users,
    # so do not require authentication.
    authentication_classes = []

    @method_decorator(ensure_tashgheel_access)
    def dispatch(self, request, *args, **kwargs):
        return super(TashgheelGradeView, self).dispatch(request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Send the grade.

        Arguments:
            request (HTTPRequest)

        Returns:
            HttpResponse: 200 on success
            HttpResponse: 400 if the request is not valid.
            HttpResponse: 409 if an account with the given username or email
                address already exists
            HttpResponse: 403 operation not allowed
        """
        data = request.POST.copy()

        response = self._handle_email(request, data)
        if response:
            return response

        response = self._handle_skill(request, data)
        if response:
            return response

        return self._handle_grades(request, data)

    def _handle_email(self, request, data):
        """
        Handle suer email validation.
        """
        errors = {}
        email = data.get('email', None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logging.error("[Tasgheel Integration] User with email: {} does not exist in our system".format(email))
            error_message = _(
                u"It looks like user with '{email}' does not exist in the system. "
                u"Try again with correct user email."
            )
            errors["email"] = [{"user_message": error_message.format(email=email)}]
        else:
            if not user.ta3leem_profile.is_tashgheel_user:
                logging.error("[Tasgheel Integration] User with email: {} is not a tashgheel user".format(email))
                error_message = _(
                    u"It looks like user with '{email}' is not a tashgheel user. "
                    u"Try again with correct user email."
                )

                errors["email"] = [{"user_message": error_message.format(email=email)}]

        if errors:
            return self._create_response(request, errors, status_code=409)

    def _handle_skill(self, request, data):
        """
        Handle skill validation.
        """
        errors = {}
        skill = data.get('skill', None)
        error_message = _(
            u"It looks like '{skill_name}' does not exist in the system. "
            u"Try again with correct skill. Note that skill names are case sensitive."
        )

        if skill and not utils.skill_name_exists(skill):
            errors["skill"] = [{"user_message": error_message.format(skill_name=skill)}]

        if errors:
            return self._create_response(request, errors, status_code=409)

    def _create_response(self, request, response_dict, status_code):
        if status_code == 200:
            # keeping this `success` field in for now, as we have outstanding clients expecting this
            response_dict['success'] = True
        else:
            self._log_validation_errors(request, response_dict, status_code)

        return JsonResponse(response_dict, status=status_code)

    def _log_validation_errors(self, request, errors, status_code):
        try:
            for field_key, errors in errors.items():
                for error in errors:
                    log.info(
                        '[Tasgheel Integration] message=grade_failed, status_code=%d, agent="%s", field="%s", error="%s"',
                        status_code,
                        request.META.get('HTTP_USER_AGENT', ''),
                        field_key,
                        error['user_message']
                    )
        except:  # pylint: disable=bare-except
            log.exception("Failed to log registration validation error")

    def _handle_grades(self, request, data):
        """
        Handle timed exam grades request.

        Argument:
            request (HttpRequest): Django Http Request object.
            data (dict): Dictionary containing the request data.
        """
        skill = data.get('skill', None)
        email = data.get('email', None)

        # error checking has already been performed, so at this point there must be a user with this email.
        user = User.objects.get(email=email)
        param = {
            'user': user,
            'is_active': 1,
            'course__is_timed_exam': True,
        }

        if skill:
            course_ids = TimedExam.objects.filter(skill__name=skill).values_list('key', flat=True)
            param['course__id__in'] = [CourseKey.from_string(course_id) for course_id in course_ids]

        errors = {}
        response = []

        enrollments = CourseEnrollment.objects.filter(**param)
        grades = PersistentExamGrade.objects.filter(
            user_id=user.id,
            course_id__in=[e.course.id for e in enrollments]
        )

        for grade in grades:
            time_exam = TimedExam.get_obj_by_course_id(grade.course_id)
            response.append(
                {
                    'skill': TimedExam.get_skill(grade.course_id),
                    'grade': grade.percent_grade,
                    'course_name': time_exam.display_name if time_exam else None
                }
            )

        if not response:
            logging.error("[Tasgheel Integration] No grade for user with email: {}".format(email))
            errors['grade'] = 'No grade for user with email: {}'.format(email)

        if errors:
            return self._create_response(request, errors, status_code=409)

        return JsonResponse({'grades': response})


class TashgheelSkillView(APIView):
    """
    HTTP end-points for posting the skills.
    """

    # This end-point is available to anonymous users,
    # so do not require authentication.
    authentication_classes = []

    @method_decorator(ensure_tashgheel_access)
    def dispatch(self, request, *args, **kwargs):
        return super(TashgheelSkillView, self).dispatch(request, *args, **kwargs)

    @method_decorator(csrf_exempt)
    def post(self, request):
        """
        Save the skills.

        Arguments:
            request (HTTPRequest)

        Returns:
            HttpResponse: 200 on success
            HttpResponse: 400 if the request is not valid.
        """
        data = request.POST.copy()
        skills = data.get('skill', '')
        skills = convert_comma_separated_string_to_list(skills)
        for skill in skills:
            if not skill_name_exists(skill):
                Skill.objects.create(name=skill)
            else:
                log.warning("[Tashgheel Integration] Tried to add the skill [{}] which already exists.".format(skill))
        return JsonResponse({'success': True}, status=201)
