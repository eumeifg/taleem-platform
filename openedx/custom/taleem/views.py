"""
Views for taleem app.
"""
import datetime

import pytz
import requests
from django.urls import reverse

import logging
import base64

from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.template.context_processors import csrf
from django.contrib import messages
from django.shortcuts import redirect
from django.core.validators import ValidationError
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.db.models import F, Q
from django.db import transaction
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.core.validators import validate_email as django_validate_email
from django.utils.translation import ugettext as _
from django.utils import translation

from rest_framework.decorators import api_view

from xmodule.modulestore.django import modulestore

from student.views import compose_and_send_activation_email
from student.models import Registration
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import set_user_preference
from openedx.core.djangoapps.user_authn.views.password_reset import request_password_change

from openedx.core.djangoapps.user_authn.utils import generate_password
from openedx.custom.utils import parse_csv

from edx_django_utils.cache import TieredCache, get_cache_key
from opaque_keys.edx.keys import CourseKey

from student.models import CourseEnrollment
from student.helpers import (
    AccountValidationError,
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.taleem.models import CourseRating, Ta3leemUserProfile
from openedx.custom.taleem.forms import CourseRatingForm
from openedx.custom.taleem.utils import (
    user_is_teacher, user_is_ta3leem_admin, create_random_captcha_text, clear_login_attempts,
)
from openedx.custom.taleem.exceptions import BulkRegistrationError
from openedx.custom.taleem_organization.models import TaleemOrganization, OrganizationType, Skill
from openedx.core.djangoapps.user_api import accounts as accounts_settings
from openedx.core.djangoapps.user_authn.views import register

from openedx.core.djangoapps.user_authn.cookies import standard_cookie_settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.custom.taleem.dashboard_reports import (
    get_teacher_exam_report_data,
    get_student_course_report_data,
    get_student_timed_exam_report_data,
)
from student.models import (
    email_exists_or_retired,
    username_exists_or_retired,
)

from edxmako.shortcuts import render_to_response, render_to_string
from captcha.image import ImageCaptcha
from openedx.custom.timed_exam.models import TimedExam
from .models import UserType, TeacherAccountRequest, MobileApp


log = logging.getLogger(__name__)


@ensure_csrf_cookie
@require_http_methods(('GET', 'POST'))
def course_rating(request, course_id):
    """
    View for handling course ratings.
    """
    course_key = CourseKey.from_string(course_id)
    course_overview = get_object_or_404(CourseOverview, id=course_key)
    context = {
        'course_overview': course_overview,
        'csrf_token': csrf(request)['csrf_token'],
    }

    if request.method == 'GET':
        avg_rating = CourseRating.avg_rating(course_key)
        review_count = CourseRating.num_reviews(course_key)
        user_rating = CourseRating.get_user_rating(user_id=request.user.id, course_id=course_id)

        return JsonResponse({
            'average': avg_rating,
            'count': review_count,
            'user_rating': user_rating,
        })
    else:
        if not request.user.is_authenticated or not CourseEnrollment.is_enrolled(request.user, course_overview.id):
            return JsonResponse(
                {'errors': ['User is not authenticated or is not enrolled in the course.']},
                status=403
            )
        course_rating_form = CourseRatingForm({
            'stars': request.POST.get('stars'), 'user': request.user.id, 'course': course_id
        })
        if course_rating_form.is_valid():
            courser_rating = course_rating_form.save()
            return JsonResponse({
                'id': courser_rating.id,
                'user': courser_rating.user.id,
                'course': course_id,
                'stars': courser_rating.stars,
                'avg': CourseRating.avg_rating(course_key),
                'count': CourseRating.num_reviews(course_key),
            }, status=200)
        else:
            # Show error message to the user.
            context['errors'] = course_rating_form.errors
            return JsonResponse(course_rating_form.errors, status=403)


@login_required
def dashboard_reports(request):
    try:
        # cache will expire after 300 seconds
        cache_timeout = 300
        cache_key = get_cache_key(
            name='dashboard_report',
            role=request.user.ta3leem_profile.user_type,
            username=request.user.username,
        )
        cache_item = TieredCache.get_cached_response(cache_key)

        if cache_item.is_found:
            return cache_item.value

        user = request.user
        has_teacher_access = user_is_teacher(user) or user_is_ta3leem_admin(user) or user.is_staff or user.is_superuser
        response = JsonResponse(
            get_teacher_reports(user) if has_teacher_access else get_student_reports(user),
            status=200
        )
        TieredCache.set_all_tiers(key=cache_key, value=response, django_cache_timeout=cache_timeout)
        return response
    except Exception as exe:
        log.error(
            "[Dashboard Report] Error: {error} for user [{username}]".format(
                error=str(exe),
                username=request.user.username
            )
        )
        return JsonResponse({"error": str(exe)}, status=500)


def get_teacher_reports(user):
    """
    Generate the dashboard report for Teacher.

    {
        "user_type": "teacher",
        "status_code": "200",
        "reports_data": {
            {
                "timed_exam_count":19
                "timed_exam_reports":[
                    {
                        "timed_exam_name":"Maths",
                        "timed_exam_key":"course-v1:Maths+90+2021T1",
                        "absent_students":
                            [
                                {
                                   "username":"username1",
                                   "last_name":"demo2l",
                                   "first_name":"demo2f",
                                   "email":"test1@example.com"
                                },
                                {
                                   "username":"username2",
                                   "last_name":"demo2l",
                                   "first_name":"demo2f",
                                   "email":"test2@example.com"
                                },
                            ],
                        "top_students":
                            [
                                {
                                    "username":"john123",
                                    "grade_percentage":42.0,
                                    "last_name":"joe2",
                                    "first_name":"kl",
                                    "email":"john@yopmail.com"
                                },
                                {
                                    "username":"john124",
                                    "grade_percentage":45.0,
                                    "last_name":"joe22",
                                    "first_name":"kl1",
                                    "email":"john2@yopmail.com"
                                },
                             ],
                        "average_percentage":"98",
                    },
                    {
                        "timed_exam_name":"Arabic",
                        "timed_exam_key":"course-v1:Arabic+90+2021T1",
                        "absent_students":
                            [
                                {
                                   "username":"username1",
                                   "last_name":"demo2l",
                                   "first_name":"demo2f",
                                   "email":"test1@example.com"
                                },
                                {
                                   "username":"username2",
                                   "last_name":"demo2l",
                                   "first_name":"demo2f",
                                   "email":"test2@example.com"
                                },
                            ],
                        "top_students":
                            [
                                {
                                    "username":"john123",
                                    "grade_percentage":42.0,
                                    "last_name":"joe2",
                                    "first_name":"kl",
                                    "email":"john@yopmail.com"
                                },
                                {
                                    "username":"john124",
                                    "grade_percentage":45.0,
                                    "last_name":"joe22",
                                    "first_name":"kl1",
                                    "email":"john2@yopmail.com"
                                },
                             ],
                        "average_percentage":"98",
                    },
               ],
            }
        }
    }
    """
    return {
        'status_code': 200,
        'user_type': 'teacher',
        'reports_data': get_teacher_exam_report_data(user)
    }


def get_student_reports(user):
    """
    Generate the dashboard report for Student.

    {
        "user_type": "student",
        "status_code": 200,
        "reports_data": {
            "failed_timed_exams_count": 5,
            "timed_exam_average_grade": 55.19,
            "enroll_course_count": 9,
            "passed_timed_exams_count": 8,
            "course_wish_list_count": 0,
            "submitted_timed_exam_count": 12,
            "pending_timed_exam_count": 1,
            "assignment_report": [
                {
                    "course_display_name": "Introduction to Computer Sciences with Taleem",
                    "course_submitted_assignments": [
                        {
                            "url": "https://lms.com/courses/course-v1:edx+cs+2021/jump_to_id/sjdhksjdhds91befd191e9d",
                            "name": "MidTerm"
                        },
                    ],
                    "course_pending_assignments": [
                        {
                            "url": "https://lms.com/courses/course-v1:edx+cs+2021/jump_to_id/khsdkjhkjdshjkhefd191e9d",
                            "name": "Final"
                        },
                    ],
                    "course_missed_assignments": [
                        {
                            "url": "https://lms.com/courses/course-v1:edx+cs+2021/jump_to_id/sdkdksjhsdkhjkhefd191e9d",
                            "name": "Homework"
                        },
                    ]
                }
            ],
            "certificate_count_report": 0,
            "finished_course_count": 0,
            "missed_timed_exam_count": 1
        },
    }
    """
    report_data = {}
    report_data.update(get_student_course_report_data(user))
    report_data.update(get_student_timed_exam_report_data(user))

    return {
        'status_code': 200,
        'user_type': 'student',
        'reports_data': report_data
    }


@require_http_methods(('GET',))
def update_ip_address_session(request):
    response = JsonResponse({})
    ip_address = request.GET.get('ip_address')

    cookie_settings = standard_cookie_settings(request)

    response.set_cookie(
        'ip_address',
        ip_address,
        **cookie_settings,
    )

    if not request.user.is_authenticated:
        return response

    prev_ip_address = request.user.ta3leem_profile.user_ip_address

    if prev_ip_address != ip_address:
        request.user.ta3leem_profile.update_ip_address(ip_address)

    return response


def set_ip_address_with_redirect(request):
    """
    Set user's ip address in the session.
    """
    redirect_url = request.GET.get('next') or reverse('signin_user')
    response = redirect(redirect_url)
    cookie_settings = standard_cookie_settings(request)

    response.set_cookie(
        'ip_address',
        request.GET.get('ip_address'),
        **cookie_settings,
    )

    return response


@ensure_csrf_cookie
@require_http_methods(('GET', 'POST',))
def taleem_captcha(request):
    """
    View to handle captcha for taleem login page.
    """
    if request.method == 'GET':
        captcha_text = create_random_captcha_text()
        # generate the image of the given text
        data = ImageCaptcha(width=280, height=90).generate(captcha_text)

        return render_to_response(
            'taleem/taleem_captcha.html', {
                'captcha': base64.b64encode(data.read()),
                'messages': messages.get_messages(request),
                'csrf_token': csrf(request)['csrf_token'],
                'captcha_text': captcha_text,
            }
        )
    else:
        captcha = request.POST.get('captcha')
        captcha_text = request.POST.get('captcha_text')

        # We need to perform case in sensitive check.
        if captcha.lower() != captcha_text.lower():
            messages.add_message(request, messages.ERROR, 'Please enter valid captcha.')
            return redirect(request.get_full_path())
        else:
            clear_login_attempts(request)

        return redirect(
            request.GET.get('next') or reverse('signin_user')
        )


@ensure_csrf_cookie
@require_http_methods(('POST',))
def taleem_allow_entrance(request):
    """
    View to handle captcha for taleem login page.
    """
    if request.method == 'POST':
        from edx_proctoring.models import ProctoredExam, ProctoredExamStudentAttempt
        from openedx.custom.timed_exam.models import TimedExam
        from django.utils.translation import ugettext as _

        exam_id = request.POST.get('exam_id')
        code = request.POST.get('code')
        response = {
            'status': 400,
            'text': _('You have entered the wrong code.')
        }
        if exam_id and code:
            exam = ProctoredExam.get_exam_by_id(exam_id)
            if exam:
                time_exam = TimedExam.get_obj_by_course_id(exam.course_id)
                if code == time_exam.enrollment_code:
                    attempt = ProctoredExamStudentAttempt.objects.get(proctored_exam_id=exam_id, user=request.user)
                    attempt.allow_entrance = True
                    attempt.save()
                    response['status'] = 200
                    response['text'] = _('success')
        return JsonResponse(response)


def tashgheel_skill_notification(timed_exam):
    # Default skill should not be notified to the tashgheel.
    if Skill.DEFAULT_SKILL_NAME == timed_exam.skill.name:
        return

    config = configuration_helpers.get_value('TASHGHEEL', {})
    skill_endpoint = config.get('SKILL_NOTIFICATION_URL') 
    if skill_endpoint and timed_exam.skill:
        log.info("[Tashgheel Integration] Sending skill notification")
        requests.get(
            skill_endpoint,
            params={
                'skill': timed_exam.skill.name,
                'course_name': timed_exam.display_name
            }
        )


def tashgheel_grade_notification(user, course_id):
    if not user.ta3leem_profile.is_tashgheel_user:
        return

    config = configuration_helpers.get_value('TASHGHEEL', {})
    grade_endpoint = config.get('GRADE_NOTIFICATION_URL') 

    if not grade_endpoint:
        return

    timed_exam = TimedExam.get_obj_by_course_id(course_id)
    if timed_exam.skill:
        log.info("[Tashgheel Integration] Sending grade notification")
        requests.get(
            grade_endpoint,
            params={
                'email': user.email,
                'skill': timed_exam.skill.name,
                'course_name': timed_exam.display_name
            }
        )


def validate_duplicate_email_username(data):
    """
    Validate the user with the given email or user nome does already exist.
    """
    email = data.get('email')
    username = data.get('username')

    if email is not None and email_exists_or_retired(email):
        raise BulkRegistrationError(accounts_settings.EMAIL_CONFLICT_MSG.format(email_address=email))

    if username is not None and username_exists_or_retired(username):
        raise BulkRegistrationError(accounts_settings.USERNAME_CONFLICT_MSG.format(username=username))


def create_account(request, data):
    try:
        return register.create_account_with_params(request, data, skip_login=True, skip_activation_email=True)
    except AccountValidationError as err:
        raise BulkRegistrationError('Error creating account: {}'.format(str(err)))
    except ValidationError as err:
        raise BulkRegistrationError('Error creating account: {}'.format(str(err)))
    except KeyError as err:
        raise BulkRegistrationError('Error creating account: {}'.format(str(err)))
    except PermissionDenied:
        raise BulkRegistrationError('Error creating account: Permission Denied')
    except Exception as err:
        raise BulkRegistrationError('Error creating account: {}'.format(str(err)))


def generate_placeholder_email(org_code, index):
    from django.contrib.auth.models import User
    return "stu{}@{}.iq".format(
        User.objects.last().id + index,
        org_code
    )


def validate_phone_number(number):
    number = str(number)
    is_valid = True
    valid_number = number
    if number[0] == '+' and len(number) == 14:
        pass
    elif number[0] == '0' and len(number) == 11:
        valid_number = '{}{}'.format('+964', number[1:])
    elif number[0] != '0' and len(number) == 10:
        valid_number = '{}{}'.format('+964', number)
    else:
        is_valid = False
    return is_valid, valid_number


def validate_email(email):
    is_valid = True

    try:
        django_validate_email(email)
    except ValidationError:
        is_valid = False
    return is_valid, email


def validate_data(request, without_email=True):
    index = 0
    errors = []
    users_data = []
    export_csv_data = [
        ['name', 'email', 'password']
    ]
    for data in parse_csv(request.FILES['csv']):
        index += 1

        name = data.get('name')
        if not name:
            errors.append("Row {}: [{}] is invalid name.".format(index, name))

        # Phone Number
        is_valid_number, phone_number = validate_phone_number(data.get('phone_number', ''))
        if not is_valid_number:
            errors.append("Row {}: [{}] is invalid phone number.".format(index, phone_number))

        # Organization
        organization = data.get('organization')
        if not organization:
            errors.append("Row {}: [{}] is invalid organization name.".format(index, organization))

        data['taleem_organization'], _ = TaleemOrganization.objects.get_or_create(
            name=organization,
            type=OrganizationType.SCHOOL.name
        )

        if without_email:
            # Email
            organization_code = data.get('org_code', None)
            if not organization_code or len(organization_code) <= 1:
                errors.append("Row {}: [{}] is invalid organization code.".format(index, organization_code))
            email = generate_placeholder_email(organization_code, index)
        else:
            is_valid_email, email = validate_email(data.get('email', ''))
            if not is_valid_email:
                errors.append("Row {}: [{}] is invalid email.".format(index, email))

        # Grade
        csv_grade = data.get('grade')
        grade = Ta3leemUserProfile.valid_grades_mapping().get(csv_grade)
        if not grade:
            errors.append("Row {}: [{}] is invalid grade.".format(index, csv_grade))

        if not User.objects.filter(email=email).exists():
            temp_password = generate_password(length=8, exclude_char='l').lower()
            data["password"] = temp_password
            data['email'] = email
            data["user_type"] = UserType.student.name
            data["honor_code"] = 'true'
            data["terms_of_service"] = 'true'
            data["country"] = 'IQ'
            data["grade"] = grade
            data['phone_number'] = phone_number
            users_data.append(data)
            export_csv_data.append(
                [name, email, temp_password]
            )
        else:
            errors.append("Row {}: [{}] already exists please remove from csv.".format(index, email))

    return users_data, export_csv_data, errors


def create_users(request, users_data, without_email=True):
    errors = []
    for index, data in enumerate(users_data, start=1):
        try:
            user = create_account(request, data)
            log.info('[Bulk Registration without email] Creating Taleem User Profile for user: {}'.format(user.email))
            Ta3leemUserProfile.objects.create(
                user=user,
                phone_number=data['phone_number'],
                organization=data['taleem_organization'],
                grade=data['grade']
            )
        except BulkRegistrationError as error:
            error_msg = "Row {}: {}".format(index, error.message)
            log.info('[Bulk Registration without email] {}'.format(error_msg))
            errors.append(error_msg)
        else:
            if not without_email:
                # We need this here to send emails via LMS and not CMS.
                # we were having issues BadSignature with clients on staging,
                # so we went without authentication.
                import requests
                _ = requests.get(
                    "{}/taleem/send-email/{}".format(settings.LMS_ROOT_URL, user.id),
                    params={'activation': True, 'password_reset': True}
                )
    return errors


@login_required
@ensure_csrf_cookie
@transaction.non_atomic_requests
def bulk_registration(request):
    """
    Bulk Registration for the admin.
    """
    # Only staff members have access to this page.
    if not request.user.is_staff:
        raise Http404

    if request.method == 'GET':
        return render_to_response(u'taleem/bulk_registration.html', {
            u'user': request.user,
        })

    errors = []
    users_data = []
    without_email = False
    export_csv_data = [
        ['name', 'email', 'password']
    ]
    if request.method == 'POST':
        without_email = request.POST.get('without_email', False)
        users_data, export_csv_data, errors = validate_data(request, without_email)

    response = {
        'status': 200,
        'url': reverse('home'),
        'errors': errors,
        'csvData': export_csv_data
    }

    if not errors:
        log.info('[Bulk Registration without email] Data is correct now creating users.')
        response['errors'] = create_users(request, users_data, without_email=without_email)

    if response['errors']:
        response['status'] = 400
    return JsonResponse(response)


@login_required
@ensure_csrf_cookie
@transaction.non_atomic_requests
def bulk_registration_deprecated(request):
    """
    Bulk Registration for the admin.
    """
    # Only staff members have access to this page.
    if not request.user.is_staff:
        raise Http404

    if request.method == 'GET':
        return render_to_response(u'taleem/bulk_registration.html', {
            u'user': request.user,
        })

    errors = []
    if request.method == 'POST':
        for data in parse_csv(request.FILES['csv']):
            email = data.get('email')
            username = data.get('username')
            organization = data.get('organization')
            organization_type = OrganizationType.get_type(data.get('organization_type'))
            if not organization_type:
                errors.append("'{}' is invalid organization type, correct values are '{}'.".format(
                    data.get('organization_type'),
                    ', '.join([org_type.value for org_type in OrganizationType])
                ))
                continue

            taleem_organization, _ = TaleemOrganization.objects.get_or_create(name=organization,
                                                                              type=organization_type.name)

            if not User.objects.filter(Q(email=email) | Q(username=username)).exists():
                temp_password = generate_password()
                data["password"] = temp_password
                data["user_type"] = UserType.student.name
                data["honor_code"] = 'true'
                data["terms_of_service"] = 'true'
                try:
                    user = create_account(request, data)
                    log.info('Creating Ta3leem User Profile for user: {}'.format(user.email))
                    Ta3leemUserProfile.objects.get_or_create(
                        user=user,
                        user_type=data["user_type"],
                        organization=taleem_organization
                    )
                except BulkRegistrationError as error:
                    errors.append(error.message)
                else:
                    # We need this here to send emails via LMS and not CMS.
                    # we were having issues BadSignature with clients on staging,
                    # so we went without authentication.
                    import requests
                    _ = requests.get(
                        "{}/taleem/send-email/{}".format(settings.LMS_ROOT_URL, user.id),
                        params={'activation': True, 'password_reset': True}
                    )
    if errors:
        return JsonResponse({'ErrMsg': '<br/>'.join(errors)})
    else:
        return JsonResponse({'url': reverse('home')})


@api_view(['GET'])
def send_email(request, user_id):
    """
    View handler for sending email.
    """
    user = User.objects.filter(id=user_id).first()

    if not user:
        # intentional sending success True.
        return JsonResponse({'success': True})

    if request.GET.get('activation'):
        registration = Registration.objects.get(user=user)
        compose_and_send_activation_email(user, user.profile, registration)
    if request.GET.get('password_reset'):
        set_user_preference(user, LANGUAGE_KEY, 'en')
        request_password_change(user.email, True)

    return JsonResponse({'success': True})


def archive_course(request, course_key_string):
    """
    Archive given course.
    """
    from openedx.core.djangoapps.models.course_details import CourseDetails
    from contentstore.views.course import get_course_and_check_access

    if course_key_string is None:
        return redirect(reverse('home'))

    course_key = CourseKey.from_string(course_key_string)

    with modulestore().bulk_operations(course_key):
        now = datetime.datetime.now(pytz.UTC)
        yesterday = now - datetime.timedelta(days=1)
        get_course_and_check_access(course_key, request.user)
        CourseDetails.update_from_json(course_key, {'start_date': yesterday}, request.user),
        CourseDetails.update_from_json(course_key, {'end_date': now}, request.user),

    return JsonResponse({'url': reverse('home')})


@login_required()
def apply_for_teacher_account(request):
    # Staff members are already have the teacher access
    user = request.user

    if user.is_staff or user.is_superuser or user_is_ta3leem_admin(user) or user_is_teacher(user):
        raise Http404

    account_request, _ = TeacherAccountRequest.objects.get_or_create(user=user)
    account_request.state = TeacherAccountRequest.APPLIED
    account_request.save()

    return JsonResponse({'status': 'applied'})


@login_required
@ensure_csrf_cookie
def teacher_account_request(request):
    """
        Listing teacher account requests
    """
    user = request.user
    template_name = 'taleem/teacher_account_request.html'

    if user.is_superuser or user_is_ta3leem_admin(user):
        teacher_account_requests = TeacherAccountRequest.objects.all()

    context = {
        'teacher_account_requests': teacher_account_requests,
    }
    return render_to_response(template_name, context)


@login_required
@ensure_csrf_cookie
def teacher_account_request_state_change(request, request_id, state):
    if not request.user.is_superuser and not user_is_ta3leem_admin(request.user):
        return HttpResponseForbidden("Action not allowed.")

    if state not in ['approve', 'decline']:
        return Http404('Invalid State')

    account_request = get_object_or_404(TeacherAccountRequest, id=request_id)

    if state == 'approve':
        account_request.state = TeacherAccountRequest.APPROVED
    else:
        account_request.state = TeacherAccountRequest.DECLINED

    account_request.save()

    return redirect(reverse('taleem:teacher_account_requests'))


@login_required
@ensure_csrf_cookie
def get_teachers(request):
    EMPTY_OPTION = {'id': '', 'name': _('Select Teacher'), 'email': ''}

    teachers_qs = Ta3leemUserProfile.objects.filter(user_type=UserType.teacher.name, user__is_active=True).values(
        'id', name=F('user__profile__name'), email=F('user__email')
    )

    teachers = [EMPTY_OPTION] + list(teachers_qs)

    return JsonResponse({
        'teachers': teachers
    }, status=200)


def download_app(request):
    """
    To download ios mobile app.
    """
    app = MobileApp.objects.filter().order_by('-version').first()
    if not app:
        raise Http404

    content = render_to_string("mobile/manifest.plist", {'app': app})
    response = HttpResponse(content, content_type='application/octet-stream')
    file_name = "Ta3leem-{}.plist".format(app.version)
    response['Content-Disposition'] = 'attachment; filename="'+file_name+'"'

    # return response as plist xml
    return response


def landing_page(request):
    return render_to_response('taleem/landing_page.html')


def arabic_privacy_policy_page(request):
    with translation.override('ar'):
        return render_to_response('static_templates/privacy.html')


def english_privacy_policy_page(request):
    with translation.override('en'):
        return render_to_response('static_templates/privacy.html')
