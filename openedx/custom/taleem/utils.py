"""
Utility functions for taleem.
"""
import io
import logging
import random
from ipware.ip import get_ip

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files.storage import default_storage
from django.db.models import Q
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.core.files.storage import default_storage
from edx_ace import ace
from edx_ace.recipient import Recipient
from qr_code.qrcode.maker import _options_from_args, make_qr

from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.preferences import api as preferences_api
from openedx.core.djangoapps.waffle_utils import WaffleSwitch, WaffleSwitchNamespace
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.custom.taleem.message_types import SecondPasswordMessage, TashgheelRegistration
from openedx.custom.taleem.models import CourseRating, LoginAttempt, SecondPassword, Ta3leemUserProfile, \
    TeacherAccountRequest, UserType
from openedx.custom.taleem.twilio import SMSSender
from openedx.custom.utils import get_email_context, get_sms_body_for_login

log = logging.getLogger(__name__)

# Namespace for ta3leem waffle flags.
WAFFLE_SWITCH_NAMESPACE = WaffleSwitchNamespace(name=u'ta3leem')

TA3LEEM_CAPTCHA_DISABLE_SWITCH = WaffleSwitch(
    WAFFLE_SWITCH_NAMESPACE, 'disable_ta3leem_captcha'
)


def can_create_exam(user):
    return user.ta3leem_profile.can_create_exam


def user_is_teacher(user):
    return user.ta3leem_profile.user_type == UserType.teacher.name


def user_is_verified_teacher(user):
    if user.ta3leem_profile.user_type == UserType.teacher.name:
        return user.groups.filter(name='Ta3leem Teacher').exists()

    return False


def user_is_verification_specialist(user):
    if user.groups.filter(name='Verification Specialist').exists():
        return True
    return False


def user_is_ta3leem_admin(user):
    if user.groups.filter(name='Taleem Admin').exists():
        return True
    return False


def send_second_password_via_email(user, second_password):
    """
    Send secondary password to the specified email address and
    return a boolean whether email service was failed or not

    Arguments:
        user (User): User Object.
        second_password (str): 4 or 6 digit password.
    """
    # this flag is by default True, but it will False for dev server.
    if not settings.ENABLE_2FA_EMAIL:
        log.info("[Two Factor Authentication] email service is disable ")
        # if service is disable then treat it as a failure
        return True

    failed = False
    email_context = get_email_context()

    email_context.update({
        'second_password': second_password
    })

    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)

    msg = SecondPasswordMessage().personalize(
        recipient=Recipient(user.username, user.email),
        language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
        user_context=email_context,
    )

    msg.options['from_address'] = from_address

    site = Site.objects.get_current()

    log.info(
        u'[Two Factor Authentication]Sending a Second Password Email to User: "%s"',
        user.email
    )

    try:
        with emulate_http_request(site=site, user=user):
            ace.send(msg)
    except Exception:
        log.exception(
            '[Two Factor Authentication] Unable to send second password email to user "%s"',
            user.email,
        )
        failed = True
    return failed


def send_second_password_via_sms(user, second_password):
    """
    Send secondary password to the user's phone number via SMS and
    return a boolean whether SMS service was failed or not.

    Arguments:
        user (User): User Object.
        second_password (str): 4 or 6 digit password.
    """
    # This flag will be removed later once we will deploy the message feature successfully.
    if not settings.ENABLE_2FA_MESSAGE:
        log.info("[Two Factor Authentication] SMS service is disable.")
        # if service is disable then treat it as a failure
        return True

    failed = False
    user_phone_number = Ta3leemUserProfile.objects.get(user=user).phone_number
    if user_phone_number:
        message_string = get_sms_body_for_login(
            preferences_api.get_user_preference(user, LANGUAGE_KEY)
        ).format(code=second_password)
        try:
            SMSSender().send_message(user_phone_number.raw_input, message_string)
        except Exception as exe:
            log.exception(
                '[Two Factor Authentication] Unable to send second password via SMS to user: "%s", exe: "%s"',
                user.email,
                str(exe)
            )
            failed = True
    else:
        log.warning(
            "[Two Factor Authentication] User [%s] doesn't have phone number in his/her profile",
            user.email
        )
    return failed


def create_and_send_second_password(user_email):
    """
    Create a second password for the user with given email, and send it via email and SMS.

    Arguments:
        user_email (str): Email address of the user.

    Raises:
        (User.DoesNotExist): raised of no user could be found matching the given email.
        (Exception): if both email and SMS services failed to send the second password.
    """
    user = User.objects.get(email=user_email)
    instance = SecondPassword.create_new_password(user)
    sms_sending_service_failed = send_second_password_via_sms(user, instance.second_password)
    email_sending_service_failed = send_second_password_via_email(user, instance.second_password)
    if sms_sending_service_failed and email_sending_service_failed:
        raise Exception


def validate_second_password(user_email, second_password):
    """
    Validate Second password for the given user.

    Arguments:
        user_email (str): Email address of the user.
        second_password (str): 4 or 6 digit password.

    Raises:
        (User.DoesNotExist): raised of no user could be found matching the given email.
        (SecondPasswordValidationError): Raised if the given second password does not match any db record.
        (SecondPasswordExpiredError): Raised if the second password given has expired.
    """
    user = User.objects.get(email=user_email)
    return SecondPassword.validate_second_password(user, second_password)


def get_course_ratings(user, courses):
    """
    Given a list of courses get course ratings and serialize then in  a json serilizable dict.

    Arguments:
        user (User): User whose course rating should be returned alongside course rating and review count.
        courses (list<CourseOverview>): A list of course overview model instances.

    Returns:
        (dict<dict>):  A dictionary containing the following course_id: dict pairs of
            1. key: 'course', value: (str) course id
            2. key: 'avg_rating', value: (int) Average course rating
            3. key: 'num_reviews', value: (int) Count of the total reviews for the course.
            3. key: 'user_rating', value: (int) Rating given by the user.
    """
    ratings = CourseRating.get_course_ratings(courses=courses)
    for course in courses:
        course_id = str(course.id)
        if course_id in ratings:
            rating = ratings[course_id]
            if user.is_authenticated:
                rating['user_rating'] = CourseRating.get_user_rating(
                    user_id=user.id,
                    course_id=course_id
                )
            else:
                rating['user_rating'] = 0
        else:
            ratings[course_id] = {
                'course': course_id,
                'avg_rating': 0,
                'num_reviews': 0,
                'user_rating': 0,
            }
    return ratings


def number_already_exists(number):
    """
    Check whether given already attached to any user already or not
    """
    return Ta3leemUserProfile.objects.filter(phone_number=number).exists()


def update_user_calendar_settings(update, user):
    """
    Update the user calendar settings in Ta3leemUserProfile Model.
    """
    updated_calendar_settings = {}

    for key, value in update.items():
        if key.startswith('calendar'):
            updated_calendar_settings[key] = update[key]

    if updated_calendar_settings:
        user_ta3leem_profile = Ta3leemUserProfile.objects.get(user=user)
        for key, value in updated_calendar_settings.items():
            user_ta3leem_profile.extra_settings[key] = value
        user_ta3leem_profile.save()


def update_grade_if_needed(update, user):
    """
    Update the grade standard of the requesting user.
    """
    if 'grade' in update:
        try:
            user_ta3leem_profile = Ta3leemUserProfile.objects.get(user=user)
            user_ta3leem_profile.grade = update.get('grade', 'NA')
            user_ta3leem_profile.save()
        except:
            return


def update_phone_number(update, user):
    """
    Update the phone number of the user.
    """
    if 'phone_number' in update:
        try:
            user_ta3leem_profile = Ta3leemUserProfile.objects.get(user=user)
            user_ta3leem_profile.phone_number = update.get('phone_number', 'NA')
            user_ta3leem_profile.save()
        except:
            return

def update_sponsor_number(update, user):
    """
    Update the phone number of the sponsor.
    """
    if 'sponsor_mobile_number' in update:
        try:
            user_ta3leem_profile = Ta3leemUserProfile.objects.get(user=user)
            user_ta3leem_profile.sponsor_mobile_number = update.get('sponsor_mobile_number', 'NA')
            user_ta3leem_profile.save()
        except:
            return

def update_category_choice(update,user):
    """
    Update User Category Choice
    """
    if 'category_selection' in update:
        try:
            user_ta3leem_profile = Ta3leemUserProfile.objects.get(user=user)
            user_ta3leem_profile.category_selection = update.get('category_selection', 'NA')
            user_ta3leem_profile.save()
        except:
            return


def upload_course_qr_code(course_key):
    """
    Check whether the course QR code already exists or not.
    if not the upload the image on storage.
    """
    key_name = "qrcode/{course_key}.png".format(
        course_key=course_key
    )
    if not default_storage.exists(key_name):
        course_about_url = "{lms_url}{about_course}".format(
            lms_url=settings.LMS_ROOT_URL,
            about_course=reverse(
                'about_course',
                args=[str(course_key)]
            )
        )
        qr_code_options = _options_from_args(
            {
                "size": "6",
                "image_format": "png",
                "light_color": None
            }
        )
        qr = make_qr(course_about_url, qr_code_options)
        out = io.BytesIO()
        qr.save(out, **qr_code_options.kw_save())
        default_storage.save(key_name, out)
    image_url = default_storage.url(key_name)
    return image_url


def get_setting_from_extra_setting(setting_name, user):
    user_ta3leem_profile = user.ta3leem_profile
    extra_settings = user_ta3leem_profile.extra_settings
    return extra_settings.get(setting_name, '')


def get_attempt_count(request):
    """
    Get login attempt count of an ip address.

    Arguments:
        request (HttpRequest): HttpRequest object.
    """
    return LoginAttempt.get_attempt_count(get_ip(request))


def log_attempt(request):
    """
    Log user login attempt in the system.

    Arguments:
        request (HttpRequest): HttpRequest object.
    """
    LoginAttempt.log_attempt(get_ip(request))


def clear_login_attempts(request):
    """
    Clear user's login attempts.

    Arguments:
        request (HttpRequest): HttpRequest object.
    """
    LoginAttempt.clear_attempts(get_ip(request))


def create_random_captcha_text(captcha_string_size=7):
    # The number list, lower case character list and upper case character list are used to generate captcha text.
    alphabet_uppercase = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
        'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
    ]
    # This function will create a random captcha string text based on above three list.
    # The input parameter is the captcha text length.

    captcha_string_list = []
    base_char = alphabet_uppercase
    for i in range(captcha_string_size):
        # Select one character randomly.
        char = random.choice(base_char)
        # Append the character to the list.
        captcha_string_list.append(char)
    captcha_string = ''
    # Change the character list to string.
    for item in captcha_string_list:
        captcha_string += str(item)
    return captcha_string


def send_tashgheel_registration_email(email, temp_password="hello123"):
    failed = False
    user = User.objects.get(email=email)
    email_context = get_email_context()
    email_context.update({
        'password': temp_password,
        'username': user.first_name
    })

    msg = TashgheelRegistration().personalize(
        recipient=Recipient(user.username, user.email),
        language=preferences_api.get_user_preference(user, LANGUAGE_KEY),
        user_context=email_context,
    )
    msg.options['from_address'] = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    site = Site.objects.get_current()
    log.info(
        u'[Tashgheel Integration]Sending a Temporary Password Email to User: "%s"',
        user.email
    )
    try:
        with emulate_http_request(site=site, user=user):
            ace.send(msg)
    except Exception:
        log.exception(
            '[Tashgheel Integration] Unable to send temporary password email to user "%s"',
            user.email,
        )
        failed = True
    return failed


def get_ta3leem_designed_studio_component(component_templates):
    try:
        ta3leem_component_templates = []
        documents_dict = {
            'type': 'html',
            'display_name': _('Documents'),
            'templates': []
        }

        questions_dict = {
            'type': 'problem',
            'display_name': _('Questions'),
            'templates': []
        }

        for template in component_templates:
            if template['type'] == 'problem':
                questions_dict['templates'] = questions_dict['templates'] + template['templates']
                questions_dict['support_legend'] = template['support_legend']

            if template['type'] == 'advanced' or template['type'] == 'video' or template['type'] == 'html':
                documents_dict['templates'] = documents_dict['templates'] + template['templates']
                documents_dict['support_legend'] = template['support_legend']

        ta3leem_component_templates.append(documents_dict)
        ta3leem_component_templates.append(questions_dict)
    except:  # pylint: disable=bare-except
        log.error('Error while creating Ta3leem Designed Studio Component')
        return component_templates

    return ta3leem_component_templates


def get_translated_component_name(component_templates):
    for component_template in component_templates:
        for template in component_template['templates']:
            template['display_name'] = _(template['display_name'])

    return component_templates


def applied_for_teacher_account(user):
    return TeacherAccountRequest.objects.filter(
        Q(state=TeacherAccountRequest.APPLIED) | Q(state=TeacherAccountRequest.APPROVED), Q(user=user)
    ).exists()
