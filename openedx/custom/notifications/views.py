# -*- coding: UTF-8 -*-
"""
Notification management views.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from edxmako.shortcuts import render_to_response
from util.json_request import JsonResponse

from openedx.custom.taleem.utils import user_is_teacher, user_is_ta3leem_admin
from openedx.custom.notifications.utils import (
    get_users,
    user_can_add_new_notification
)
from openedx.custom.notifications.serializers import NotificationMessageSerializer
from openedx.custom.timed_exam.models import TimedExamAlarms

from .models import NotificationMessage, NotificationPreference
from .forms import NotificationPreferenceForm

log = logging.getLogger(__name__)


@login_required
@ensure_csrf_cookie
def list_messages(request):
    user = request.user

    notifications = NotificationMessage.get_messages(user, include_read=True)
    context = {
        'notifications': notifications,
        'can_add_new_notification': user_can_add_new_notification(request)
    }
    return render_to_response('notifications/list.html', context)


@login_required
@ensure_csrf_cookie
def mark_as_read(request, id):
    user = request.user

    try:
        notification = NotificationMessage.objects.get(
            id=id,
            user=user,
        )
        notification.mark_as_read()
        success = True
    except Exception as e:
        success = False

    return JsonResponse({
        'success': success,
    })


@login_required
@ensure_csrf_cookie
def mark_all_as_read(request):
    user = request.user

    try:
        NotificationMessage.mark_all_as_read(user)
        success = True
    except Exception as e:
        success = False

    return JsonResponse({
        'success': success,
    })


@login_required
@ensure_csrf_cookie
def delete(request, id):
    user = request.user

    try:
        notification = Notification.objects.get(
            id=id,
            user=user,
        )
        notification.delete()
        success = True
    except:
        success = False

    return JsonResponse({
        'success': success,
    })


@login_required
@ensure_csrf_cookie
def delete_all(request):
    user = request.user

    try:
        Notification.objects.filter(
            user=user,
        ).delete()
        success = True
    except:
        success = False

    return JsonResponse({
        'success': success,
    })


@login_required
@ensure_csrf_cookie
def autocomplete_users(request):
    page_data, page_object = get_users(request)
    has_next = page_object.has_next()
    has_previous = page_object.has_previous()
    next,previous = None, None
    if has_next:
        next = page_object.next_page_number()
    if has_previous:
        previous = page_object.previous_page_number()

    return JsonResponse({
        'data': page_data,
        'has_next': has_next,
        'has_previous': has_previous,
        'next': next,
        'previous': previous,
    }, status=200)


@login_required
@ensure_csrf_cookie
def list_messages_in_json(request):
    user = request.user
    include_read = request.GET.get('include-read', False) in {'True', True, 'true'}

    notifications = NotificationMessage.get_messages(user, include_read=include_read)
    serializer = NotificationMessageSerializer(
        notifications,
        context={'language': request.LANGUAGE_CODE},
        many=True,
    )
    return JsonResponse(serializer.data)


@login_required
def timed_exam_alarms(request):
    """
    Endpoint to check whether there is some alarm to be scheduled for user.
    """
    alarm = TimedExamAlarms.check_alarm(request.user)
    response = {
        "message": '',
        "alarm": 0
    }
    if alarm:
        minutes, display_name = alarm.remaining_time_message.split(":")
        response['message'] = _(
            "There is only less than {minutes} minutes left for timed exam '{name}', please submit your answers before that.".format(
                minutes=minutes,
                name=display_name
            )
        )
        response['alarm'] = 1
    return JsonResponse(response)


@login_required
@ensure_csrf_cookie
def notification_preferences(request):
    """
    Notification preferences page with form.
    """
    user = request.user

    # Only teachers and admins are allowed
    if not any((
        user_is_ta3leem_admin(user),
        user_is_teacher(user),
        user.is_superuser,
        user.is_staff,
    )):
        return HttpResponseForbidden("Action not allowed.")

    preference, _ = NotificationPreference.objects.get_or_create(user=user)
    form = NotificationPreferenceForm(instance=preference)
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST)
        if form.is_valid():
            NotificationPreference.objects.update_or_create(user=user, defaults=form.cleaned_data)
            return redirect('notifications:notification_preferences')
    template_name = 'notifications/preferences.html'
    return render_to_response(template_name, {'form': form})
