# -*- coding: UTF-8 -*-
"""
Timed Notes management views.
"""
import logging
from datetime import time

from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from util.json_request import JsonResponse
from opaque_keys.edx.keys import CourseKey, UsageKey

from .models import TimedNote

log = logging.getLogger(__name__)


@login_required
@ensure_csrf_cookie
def list_notes(request):
    user = request.user
    course_id = request.GET.get('course_id')
    course_key = CourseKey.from_string(course_id)
    video_id = request.GET.get('video_id')
    block_key = UsageKey.from_string(video_id)

    notes = TimedNote.get_notes(user, course_key, block_key)

    return JsonResponse({
        'notes': notes,
    })


@login_required
@ensure_csrf_cookie
def add_note(request):
    user = request.user
    course_id = request.POST.get('course_id')
    course_key = CourseKey.from_string(course_id)
    video_id = request.POST.get('video_id')
    block_key = UsageKey.from_string(video_id)
    t_minutes,t_seconds = request.POST.get('taken_at', '0:00').split(':')
    taken_at = time(0, int(t_minutes), int(t_seconds))
    note = request.POST.get('note', '-')

    try:
        timed_note = TimedNote.objects.create(
            user=user,
            context_key=course_key,
            block_key=block_key,
            taken_at=taken_at,
            note=note,
        )
        note_id = timed_note.id
        message = _("Note created successfully.")
        success = True
    except:
        note_id = -1
        message = _("Couldn't create a note. Please try again after some time.")
        success = False

    return JsonResponse({
        'id': note_id,
        'success': success,
        'message': message,
    })


@login_required
@ensure_csrf_cookie
def save_note(request):
    user = request.user
    note_id = int(request.POST.get('id'))
    note = request.POST.get('note', '-')
    t_minutes,t_seconds = request.POST.get('taken_at', '0:00').split(':')
    taken_at = time(0, int(t_minutes), int(t_seconds))

    try:
        timed_note = TimedNote.objects.get(
            id=note_id,
            user=user,
        )
        timed_note.taken_at = taken_at
        timed_note.note = note
        timed_note.save()
        message = _("Note saved successfully.")
        success = True
    except:
        message = _("Couldn't save a note. Please try again after some time.")
        success = False

    return JsonResponse({
        'success': success,
        'message': message,
    })


@login_required
@ensure_csrf_cookie
def delete_note(request):
    user = request.user
    note_id = int(request.POST.get('id'))

    try:
        timed_note = TimedNote.objects.get(
            id=note_id,
            user=user,
        )
        timed_note.delete()
        message = _("Note deleted successfully.")
        success = True
    except:
        message = _("Couldn't delete a note. Please try again after some time.")
        success = False

    return JsonResponse({
        'success': success,
        'message': message,
    })
