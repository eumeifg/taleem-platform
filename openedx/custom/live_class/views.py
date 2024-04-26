# -*- coding: UTF-8 -*-
"""
Meetings CRUD views.
"""
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.template.context_processors import csrf
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from edxmako.shortcuts import render_to_response
from six import text_type
from util.json_request import JsonResponse

from openedx.custom.live_class.forms import LiveClassForm, LiveClassReviewForm
from openedx.custom.live_class.models import (
    LiveClass,
    LiveClassAttendance,
    LiveClassBooking
)
from openedx.custom.live_class.utils import (
    can_browse_live_class,
    enroll_in_live_class,
    generate_jwt_token,
    get_class_url,
    get_class_settings,
)
from openedx.custom.live_class.tasks import start_live_class
from openedx.custom.payment_gateway.forms import VoucherRedemptionLiveClassForm
from openedx.custom.taleem.utils import user_is_ta3leem_admin, user_is_teacher
from openedx.custom.timed_exam.exceptions import InvalidCSVDataError, InvalidEmailError
from openedx.custom.taleem_search.utils import get_filters_data

log = logging.getLogger(__name__)


@ensure_csrf_cookie
def browse_classes(request):
    """
    Function responsible for showing the live classes for browsing.
    """
    live_classes = []
    if request.user.is_authenticated:
        live_class_qs = LiveClass.objects.prefetch_related('moderator').filter(
            stage__in=[LiveClass.SCHEDULED, LiveClass.RUNNING],
            class_type__in=[LiveClass.PUBLIC, LiveClass.PUBLIC_AT_INSTITUTION]
        )
        for live_class in live_class_qs.iterator():
            if can_browse_live_class(live_class, request.user):
                live_classes.append(live_class)
    else:
        live_classes = LiveClass.objects.filter(
            stage=LiveClass.SCHEDULED,
            class_type=LiveClass.PUBLIC,
        )

    return render_to_response('live_class/browse_classes.html', {
        'live_classes': live_classes,
        'filters_data': get_filters_data()
    })


@ensure_csrf_cookie
def class_about(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk)
    user = request.user

    return render_to_response('live_class/class_about.html', {
        'live_class': live_class,
        'has_booked': user.is_authenticated and live_class.has_booked(user),
    })


@login_required
@ensure_csrf_cookie
def book_class(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk)

    if not live_class.seats_left or live_class.is_paid:
        return HttpResponseForbidden("Action not allowed.")

    try:
        LiveClassBooking.objects.create(
            user=request.user,
            live_class=live_class,
        )
    except Exception as e:
        log.error(str(e))

    return redirect(reverse('dashboard'))


@login_required
@ensure_csrf_cookie
def create_meeting(request):
    user = request.user

    # Only teachers are allowed
    allowed_roles = [
        user_is_ta3leem_admin(user),
        user_is_teacher(user),
        user.is_superuser,
    ]
    if not any(allowed_roles):
        return HttpResponseForbidden("Action not allowed.")

    form = LiveClassForm()
    if request.method == 'POST':
        form = LiveClassForm(request.POST, request.FILES)
        if form.is_valid():
            live_class = form.save(commit=False)
            live_class.moderator = user.ta3leem_profile
            live_class.save()
            return redirect('live_classes_management')
    template_name = 'live_class/live_class_form.html'
    context = {'form': form, 'action': 'create'}
    return render_to_response(template_name, context)


@login_required
@ensure_csrf_cookie
def edit_meeting(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk)
    user = request.user
    is_admin = user.is_superuser or user_is_ta3leem_admin(user)

    # Only teachers/admins are allowed
    allowed_roles = [
        is_admin,
        user.ta3leem_profile == live_class.moderator,
    ]
    if not any(allowed_roles):
        return HttpResponseForbidden("Action not allowed.")

    form_class = is_admin and LiveClassReviewForm or LiveClassForm
    form = form_class(instance=live_class)
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=live_class)
        if form.is_valid():
            form.save()
            return redirect('live_classes_management')

    return render_to_response('live_class/live_class_form.html', {
        'form': form,
        'action': 'edit',
        'live_class': live_class,
    })


@login_required
@ensure_csrf_cookie
def cancel_meeting(request, pk):
    live_class = get_object_or_404(LiveClass, pk=pk)
    user = request.user
    is_admin = user.is_superuser or user_is_ta3leem_admin(user)

    # Only teachers/admins are allowed
    allowed_roles = [
        is_admin,
        user.ta3leem_profile == live_class.moderator,
    ]
    if not any(allowed_roles):
        return HttpResponseForbidden("Action not allowed.")

    if request.method == 'POST':
        live_class.delete()
        return redirect('live_classes_management')

    return render_to_response('live_class/confirm_delete.html',
        {'live_class': live_class
    })


@login_required
@ensure_csrf_cookie
def live_classes_management(request):
    '''
    Listing live class for the students or
    teacher.
    '''
    user = request.user
    template_name = 'live_class/list.html'
    is_admin = user.is_superuser or user_is_ta3leem_admin(user)

    # Only teachers/admins are allowed
    allowed_roles = [
        is_admin,
        user_is_teacher(user),
    ]
    if not any(allowed_roles):
        return HttpResponseForbidden("Action not allowed.")

    # Redirect to live management if teacher
    if is_admin:
        template_name = 'live_class/list_admin.html'
        live_classes = LiveClass.objects.all()
    else:
        live_classes = LiveClass.objects.filter(moderator=user.ta3leem_profile)
        template_name = 'live_class/list_teacher.html'

    return render_to_response(template_name, {
        'live_classes': live_classes,
    })


@login_required
@ensure_csrf_cookie
def go_to_class(request, class_id):
    live_class = get_object_or_404(LiveClass, id=class_id)
    user = request.user
    is_admin = user.is_superuser or user_is_ta3leem_admin(user)
    is_moderator = user.ta3leem_profile == live_class.moderator

    # Only teachers/admins are allowed
    allowed_roles = [
        is_admin,
        is_moderator,
        live_class.has_booked(user),
    ]
    if not any(allowed_roles):
        return HttpResponseForbidden("Action not allowed.")

    # Join jitsi if possible
    context = {
        'live_class': live_class,
        'is_teacher': is_moderator,
    }
    if live_class.can_join(user):
        context['join_url'] = get_class_url(live_class)
    else:
        # Can not join hence show the page with info
        expired = not(live_class.upcoming or live_class.running)
        minutes = (timezone.now() - live_class.scheduled_on).total_seconds() / 60.0
        threshold_period = 60 if live_class.duration > 60 else live_class.duration
        context.update({
            'expired': expired,
            'long_poll': -15 <= minutes <= threshold_period,
        })

    return render_to_response('live_class/jitsi_class.html', context)


@login_required
@ensure_csrf_cookie
def live_class_status(request, class_id):
    live_class = get_object_or_404(LiveClass, id=class_id)
    user = request.user
    is_admin = user.is_superuser or user_is_ta3leem_admin(user)
    is_moderator = user.ta3leem_profile == live_class.moderator

    # Only teachers/admins are allowed
    allowed_roles = [
        is_admin,
        is_moderator,
        live_class.has_booked(user),
    ]
    if not any(allowed_roles):
        return HttpResponseForbidden("Action not allowed.")

    join_url = ''
    if live_class.can_join(user):
        join_url = get_class_url(live_class)

    return JsonResponse({
        'continue_polling': not join_url,
        'join_url': join_url,
        'class_status': live_class.stage
    })


@login_required
@ensure_csrf_cookie
def end_class(request, class_id):
    '''
    When teacher ends the class change stage.
    '''
    live_class = get_object_or_404(LiveClass, id=class_id)
    class_end_time = timezone.now()
    user = request.user

    # If not moderator return error
    if user.ta3leem_profile != live_class.moderator:
        return HttpResponseForbidden("Action not allowed.")

    # mark as ended
    live_class.stage = LiveClass.ENDED
    live_class.save()

    attendances = LiveClassAttendance.objects.filter(live_class=live_class, left_at=None)
    for attendance in attendances:
        attendance.left_at = class_end_time
        attendance.save()

    # Redirect to live class page
    return JsonResponse({
        "class_ended": True
    }, status=200)


@login_required
@ensure_csrf_cookie
def running_class(request, class_id):
    live_class = get_object_or_404(LiveClass, id=class_id)
    user = request.user
    is_admin = user.is_superuser or user_is_ta3leem_admin(user)
    is_moderator = user.ta3leem_profile == live_class.moderator

    # Only teachers/admins are allowed
    allowed_roles = [
        is_admin,
        is_moderator,
        live_class.has_booked(user),
    ]
    if not any(allowed_roles):
        return HttpResponseForbidden("Action not allowed.")

    if not live_class.can_join(user):
        return redirect(reverse('dashboard'))

    # If teacher, mark the session running
    if is_moderator:
        # start the live class
        seconds = int((live_class.scheduled_on - timezone.now()).total_seconds())
        start_live_class.apply_async(
            args=(text_type(live_class.id),),
            countdown=seconds if seconds > 0 else 0
        )
    else:
        user_attendance = LiveClassAttendance(
            user=user,
            live_class=live_class,
            joined_at=timezone.now()
        )
        user_attendance.save()

    return render_to_response('live_class/running_class.html', {
        'live_class': live_class,
        'request': request,
        'is_teacher': is_moderator,
        'user_jwt_token': generate_jwt_token(user, is_moderator, live_class),
        'jitsi_server_url': settings.JITSI_SERVER_URL,
        'jitsi_server_domain': urlparse(settings.JITSI_SERVER_URL).netloc,
        'class_settings': get_class_settings(is_moderator, live_class),
    })


@login_required
@ensure_csrf_cookie
def mark_attendance(request, class_id):
    live_class = get_object_or_404(LiveClass, id=class_id)

    attendance_obj = LiveClassAttendance.objects.filter(
        user=request.user,
        live_class=live_class
    ).last()

    if not attendance_obj.left_at:
        attendance_obj.left_at = timezone.now()
        attendance_obj.save()

    return JsonResponse({
        'marked_attendance': True
    }, status=200)


@login_required
@ensure_csrf_cookie
def attendance_report(request, class_id):
    live_class = get_object_or_404(LiveClass, id=class_id)
    user = request.user
    is_admin = user.is_superuser or user_is_ta3leem_admin(user)
    is_moderator = user.ta3leem_profile == live_class.moderator

    # Only teachers/admins are allowed
    allowed_roles = [
        is_admin,
        is_moderator,
    ]
    if not any(allowed_roles):
        return HttpResponseForbidden("Action not allowed.")

    return render_to_response('live_class/attendance_report.html', {
        'class_attendance': LiveClassAttendance.objects.filter(
            live_class=live_class,
        ),
        'live_class': live_class
    })


@login_required
@ensure_csrf_cookie
def approve_class(request, class_id):
    if not request.user.is_superuser and not user_is_ta3leem_admin(request.user):
        return HttpResponseForbidden("Action not allowed.")

    live_class = get_object_or_404(LiveClass, id=class_id)
    live_class.stage = LiveClass.SCHEDULED
    live_class.save()

    return redirect(reverse('live_classes_management'))


@login_required
@ensure_csrf_cookie
def decline_class(request, class_id):
    if not request.user.is_superuser and not user_is_ta3leem_admin(request.user):
        return HttpResponseForbidden("Action not allowed.")

    live_class = get_object_or_404(LiveClass, id=class_id)
    live_class.stage = LiveClass.DECLINED
    live_class.save()

    return redirect(reverse('live_classes_management'))


@login_required
@ensure_csrf_cookie
@require_http_methods(('GET', 'POST'))
def payment_view(request, class_id):
    """
    View for handling vouchers for Live Classes.
    """
    live_class = get_object_or_404(LiveClass, id=class_id)

    if not live_class.has_booked(request.user) or not live_class.is_paid:
        return redirect(reverse('dashboard'))

    if live_class.is_fully_paid(request.user):
        return redirect(reverse('go_to_class', args=[text_type(live_class.id)]))

    remaining_amount = live_class.remaining_amount(request.user)

    context = {
        'live_class': live_class,
        'amount_to_pay': remaining_amount,
        'csrf_token': csrf(request)['csrf_token'],
    }

    if request.method == 'GET':
        return render_to_response('live_class/payment.html', context)
    else:
        # Handle the POST request.
        voucher_redemption_form = VoucherRedemptionLiveClassForm(request.POST)

        if voucher_redemption_form.is_valid():
            voucher_redemption_form.save(request.user, live_class)
            if not live_class.is_fully_paid(request.user):
                remaining_amount = live_class.remaining_amount(request.user)
                context = {
                    'payment_status': 'partial',
                    'live_class': live_class,
                    'amount_to_pay': remaining_amount,
                    'csrf_token': csrf(request)['csrf_token']
                }
                return render_to_response('live_class/payment.html', context)
        else:
            # Show error message to the user.
            context['form_errors'] = voucher_redemption_form.errors
            return render_to_response('live_class/payment.html', context)

    return redirect(reverse('go_to_class', args=[text_type(live_class.id)]))


@login_required
@ensure_csrf_cookie
@require_http_methods(('GET', 'POST'))
def class_bookings(request, class_id):
    live_class = get_object_or_404(LiveClass, id=class_id)
    user = request.user
    is_admin = user.is_superuser or user_is_ta3leem_admin(user)
    is_moderator = user.ta3leem_profile == live_class.moderator

    # Only teachers/admins are allowed
    allowed_roles = [
        is_admin,
        is_moderator,
    ]
    if not any(allowed_roles):
        return HttpResponseForbidden("Action not allowed.")

    error = None
    if request.method == 'POST':
        try:
            enroll_in_live_class(request, live_class)
        except (InvalidCSVDataError, ValidationError, InvalidEmailError) as exp:
            error = exp.message

    return render_to_response('live_class/bookings.html', {
        'bookings': LiveClassBooking.objects.filter(live_class=live_class),
        'seats_left': live_class.seats_left,
        'error': error,
    })
