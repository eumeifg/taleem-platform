"""
Views for payment gateway app.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.template.context_processors import csrf
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from six import text_type
from xmodule.modulestore.django import modulestore

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.payment_gateway.forms import VoucherRedemptionForm
from openedx.custom.payment_gateway.models import CoursePrice
from openedx.custom.payment_gateway.utils import is_user_allowed_to_access_the_course

log = logging.getLogger(__name__)


@login_required
@ensure_csrf_cookie
@require_http_methods(('GET', 'POST'))
def vouchers(request, course_id):
    """
    View for handling vouchers for Taleem students.
    """
    course_key = CourseKey.from_string(course_id)
    course_overview = get_object_or_404(CourseOverview, id=course_key)
    context = {
        'course_overview': course_overview,
        'csrf_token': csrf(request)['csrf_token'],
    }

    if request.method == 'GET':
        original_path = request.GET.get('original_path')
        if is_user_allowed_to_access_the_course(request, course_id):
            if original_path:
                return redirect(original_path)
            else:
                return redirect('courseware', text_type(course_overview.id))
        return render_to_response('payment_gateway/vouchers.html', context)
    else:
        # Handle the POST request.
        course_price = CoursePrice.objects.filter(course_key=course_key).first()
        if not course_price:
            log.error(
                '[VOUCHER_REDEMPTION]: Could not redeem a voucher because '
                'course price object does not exists for course "{}"'.format(course_id)
            )
            context['error'] = _(
                'Server Error: We could not redeem the course you specified, '
                'please try a different course or contact you administrator for more information.'
            )
            return render_to_response('payment_gateway/vouchers.html', context)

        voucher_redemption_form = VoucherRedemptionForm(request.POST)

        if voucher_redemption_form.is_valid():
            voucher_redemption_form.save(course_overview, request.user, course_price)
        else:
            # Show error message to the user.
            context['form_errors'] = voucher_redemption_form.errors
            return render_to_response('payment_gateway/vouchers.html', context)

    discounted_price = course_price.get_course_price_for_user(request.user)
    if discounted_price.is_zero():
        return redirect('about_course', text_type(course_overview.id))
    else:
        # if user still has some payment pending to access the course.
        return redirect('about_course', text_type(course_id))


@login_required
@ensure_csrf_cookie
def course_price_view(request, course_key_string):
    from contentstore.views.course import get_course_and_check_access
    if course_key_string is None:
        return redirect(reverse('home'))

    course_key = CourseKey.from_string(course_key_string)

    with modulestore().bulk_operations(course_key):
        course_module = get_course_and_check_access(course_key, request.user)
        course_price = CoursePrice.get_course_price(course_id=course_key)

    if request.method == 'POST':
        new_price = request.POST.get('course-price')
        course_price.price = new_price
        course_price.save()

    course_price = CoursePrice.get_course_price(course_id=course_key)

    return render_to_response('payment_gateway/course_price.html', {
        'language_code': request.LANGUAGE_CODE,
        'context_course': course_module,
        'course_price': course_price,
        'course_key': course_key_string
    })
