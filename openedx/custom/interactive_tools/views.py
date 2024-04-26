"""
Views for interactive tools app.
"""

import json
import logging

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.http import HttpResponseForbidden, HttpResponseBadRequest, JsonResponse

from opaque_keys.edx.keys import CourseKey

from edxmako.shortcuts import render_to_response
from lms.djangoapps.courseware.access import has_access
from student.roles import CourseStaffRole
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from lms.djangoapps.courseware.models import StudentModule
from openedx.core.djangoapps.credit.utils import get_course_blocks

log = logging.getLogger(__name__)

# Name of the XBlock
INTERACTIVE_BLOCK_NAME = 'h5p'


@login_required
@ensure_csrf_cookie
def interactive_tools_list(request, course_id):
    """
    Render the list of the interactive tools in a
    given course for the teachers.

    Returns 404 if the given course does not exist.
    Returns 403 if the user has no access.
    """
    # Get the course key
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    # Get the course
    course = get_object_or_404(CourseOverview, id=course_key)

    # Only teacher can access the reports
    if not has_access(request.user, CourseStaffRole.ROLE, course_key):
        return HttpResponseForbidden()

    # render response
    return render_to_response("interactive_tools/list.html", {
        'course': course,
        'blocks': get_course_blocks(course_key, INTERACTIVE_BLOCK_NAME),
    })


@login_required
@ensure_csrf_cookie
@require_POST
def interactive_tools_report(request, course_id):
    """
    Return JSON response containing the state data
    of each student interacted with the given block.

    User must have course staff role at least else
    returns 403.
    Returns 404 is the course or module doesn't exist.
    Returns 400 is the module_id is missing in params.

    Request Method: POST only

    Params: module_id

    Response JSON: [{
        "student": {
            "student_id": 12,
            "username": "learnerx",
            "email": "learnerx@ta3leem.iq"
        },
        "state": {
            "success_status": "passed",
            "lesson_status": "completed",
            "lesson_score": 0.7,
            "h5p_data": {
                "statement": {
                    "duration": 'PT78.53s',
                    "id": "url..",
                    "score": {"max": 10, "scaled": 0.7, "min": 0, "raw": 7},
                    "details": [...]
                }
            }
        }
    }]
    """
    # Get the course key
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        return HttpResponseBadRequest()

    # Get the course
    course = get_object_or_404(CourseOverview, id=course_key)

    # Only teacher can access the reports
    if not has_access(request.user, CourseStaffRole.ROLE, course_key):
        return HttpResponseForbidden()

    # Get module id from request
    module_id = request.POST.get('module_id')
    if not module_id:
        return HttpResponseBadRequest()

    # Get StudentModule records
    student_modules = StudentModule.objects.filter(
        course_id=course_key,
        module_type=INTERACTIVE_BLOCK_NAME,
        module_state_key=module_id,
    )

    # Get students in one query
    students = {
        user.id: {
            'student_id': int(user.id),
            'username': user.username,
            'email': user.email,
        }
        for user in User.objects.filter(
            id__in=student_modules.values_list('student_id', flat=True),
        )
    }

    # Prepare list of records
    interactions = [
        {
            "student": students.get(student_module.student_id, {}),
            "state": json.loads(student_module.state)
        }
        for student_module in student_modules
    ]

    # Return JSON
    return JsonResponse({'interactions': interactions})
