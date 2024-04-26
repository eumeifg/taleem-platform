# -*- coding: UTF-8 -*-
"""
Views for Taleem Calendar App.
"""
import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.utils.timezone import make_aware
from django.views.decorators.http import require_http_methods
from util.json_request import JsonResponse

from openedx.custom.taleem_calendar.models import Ta3leemReminder, CalendarEvent
from openedx.custom.taleem_calendar.utils import (get_reminder_privacy, get_user_courses_between_dates,
                                                  get_user_exams_between_dates, get_user_live_classes_between_dates,
                                                  validate_reminder_params, get_user_custom_events)


@login_required
@require_http_methods(('GET', ))
def get_all_calendar_events(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Validations for date parameters
    if not from_date or not to_date:
        return JsonResponse({
            'error': 'Please pass valid `from_date` and `to_date` as a url parameter in iso format `YYYY-MM-DD`.'
        }, status=500)

    try:
        from_date = make_aware(datetime.strptime(from_date, '%Y-%m-%d'))
        to_date = make_aware(datetime.strptime(to_date, '%Y-%m-%d'))
    except Exception:
        return JsonResponse({
            'error': 'Please pass date in valid formats i.e: `YYYY-MM-DD`.'
        }, status=500)

    if not from_date <= to_date:
        return JsonResponse({
            'error': '`from_date` should be earlier than the `to_date`.'
        }, status=500)

    courses = get_user_courses_between_dates(from_date, to_date, request)
    exams = get_user_exams_between_dates(from_date, to_date, request.user)
    live_classes = get_user_live_classes_between_dates(from_date, to_date, request.user)
    custom_events = get_user_custom_events(from_date, to_date, request.user)

    return JsonResponse({
        'events': courses + exams + live_classes + custom_events
    }, status=200)


@login_required
@require_http_methods(('POST',))
def create_reminder(request):

    params = json.loads(request.body.decode("utf-8"))
    reminder_type = params.get('reminder_type')
    identifier = params.get('identifier')
    description = params.get('description')
    reminder_time = params.get('time')
    send_email = params.get('send_email', True)
    send_notification = params.get('send_notification', True)

    is_valid, error_message = validate_reminder_params(reminder_type, identifier, reminder_time, description)
    reminder_privacy = get_reminder_privacy(identifier, request, reminder_type)

    if not is_valid:
        return JsonResponse({
            'error': error_message
        }, status=500)

    reminder = Ta3leemReminder.objects.create(
        type=reminder_type,
        identifier=identifier,
        message=description,
        time=reminder_time,
        created_by=request.user,
        send_email=send_email,
        send_notification=send_notification,
        privacy=reminder_privacy
    )

    return JsonResponse({
        'reminder': reminder.id
    }, status=200)


@login_required
@require_http_methods(('POST',))
def create_event(request):

    params = json.loads(request.body.decode("utf-8"))
    title = params.get('event_title')
    description = params.get('event_description')
    time = params.get('event_time')

    reminder = CalendarEvent.objects.create(
        title=title,
        description=description,
        time=time,
        created_by=request.user
    )

    return JsonResponse({
        'reminder': reminder.id
    }, status=200)
