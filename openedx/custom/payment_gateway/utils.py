"""
Utility helpers for payment gateway.
"""
import hashlib
import logging
from functools import wraps
from datetime import datetime
from ipware.ip import get_ip

from django.urls import reverse
from django.utils.http import urlencode
from django.shortcuts import redirect

from openedx.custom.payment_gateway.models import IpAddressWhitelist, CoursePrice


LOGGER = logging.getLogger(__name__)


def ensure_user_ip_in_whitelist(**kw):

    def _ensure_user_ip_in_whitelist(view_func):
        """
        Decorator which makes a view method redirect to the home page if user's ip is not in the whitelist.
        """

        @wraps(view_func)
        def inner(request, course_id, *args, **kwargs):
            """
            Redirect to the consent page if the request.user must consent to data sharing before viewing course_id.

            Otherwise, just call the wrapped view function.
            """
            allow_non_logged_in_users = kw.get('allow_non_logged_in_users', None)
            is_for_course_outline = kw.get('is_for_course_outline', None)
            is_for_courseware = kw.get('is_for_courseware', None)
            querystring = urlencode({'original_path': request.build_absolute_uri(request.path),})
            redirect_url = reverse('payment_gateway:vouchers_page', args=(course_id, )) + '?' + querystring
            if not is_user_allowed_to_access_the_course(request, course_id, allow_non_logged_in_users, is_for_course_outline, is_for_courseware):
                return redirect(redirect_url)

            # Otherwise, drop through to wrapped view
            return view_func(request, course_id, *args, **kwargs)
        return inner
    return _ensure_user_ip_in_whitelist


def get_all_ip(request):
    return "1: [{}], 2: [{}], 3: [{}], 4: [{}]".format(
        get_ip(request),
        get_ip(request, real_ip_only=False, right_most_proxy=True),
        get_ip(request, real_ip_only=True, right_most_proxy=False),
        get_ip(request, real_ip_only=True, right_most_proxy=True),
    )


def is_user_allowed_to_access_the_course(request, course_id, allow_non_logged_in_users=False, is_for_course_outline=False,is_for_courseware=False):
    """
    Function to check if a user is allowed to access the course.

    Arguments:
        request (Request): A request object. the request must be authenticated.
        course_id (str | CourseKey): Course identifier in either string or CourseKey form.
    """
    # Anonymous users are not allowed to access the course.
    try:
        course_price = get_course_price(course_id)
    except CoursePrice.DoesNotExist:
        # No Course Price, user is allowed.
        return True

    # No restrictions if course price is zero.
    if course_price.price.is_zero():
        return True

    if not request.user.is_authenticated:
        if allow_non_logged_in_users:
            return True
        else:
            return False

    if request.user.is_staff or request.user.is_superuser:
        return True

    user_ip = get_ip(request)

    LOGGER.info(
        "[Payment Gateway] User [%s] 0: ip address [%s], %s",
        request.user.username,
        user_ip,
        get_all_ip(request)
    )
    if IpAddressWhitelist.is_ip_in_whitelist(user_ip):
        return True

    user_course_price = course_price.get_course_price_for_user(request.user)
    if user_course_price.is_zero():
        return True

    real_user = getattr(request.user, 'real_user', request.user)
    LOGGER.info(
        u'User %s cannot access the course %s because they have not been granted access with ip address %s.',
        real_user,
        course_id,
        user_ip,
    )

    if is_for_course_outline:
        return True

    if is_for_courseware:
        return True

    return False


def get_voucher_codes(number_of_codes=1):
    """
    Get a list of unique codes to be used in vouchers.

    Arguments:
        number_of_codes (int): Number of codes to generate.

    Returns:
        (list<str>): A list of 16 character codes in all caps.
    """
    return [get_voucher_code() for _ in range(number_of_codes)]


def get_voucher_code():
    """
    get a voucher code for use in voucher.

    Returns:
         (str): A 16 character code in all caps.
    """
    return hashlib.sha256(str(datetime.now()).encode('utf-8')).hexdigest()[:16].upper()


def get_course_price(course_id):
    """
    Get the price of the course.

    Arguments:
        course_id (str | CourseKey): Course identifier in either string or CourseKey form.

    Returns:
        (CoursePrice): Price of the course.
    """
    course_price = CoursePrice.get_course_price(course_id)
    return course_price


def get_course_price_for_user(course_id, user):
    """
    Get the price of the course.

    Arguments:
        course_id (str | CourseKey): Course identifier in either string or CourseKey form.
        user (User): User instance who is trying to chek price of the course.

    Returns:
        (Decimal): Price of the course subtracting the voucher prices that user has already applied.
    """
    course_price = get_course_price(course_id)
    return course_price.get_course_price_for_user(user)
