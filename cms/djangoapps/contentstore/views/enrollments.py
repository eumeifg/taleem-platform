from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import ensure_csrf_cookie
from opaque_keys.edx.keys import CourseKey

from edxmako.shortcuts import render_to_response
from student.auth import has_course_author_access
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore

__all__ = ['enrollments_handler']


@login_required
@ensure_csrf_cookie
def enrollments_handler(request, course_key_string=None):
    '''
    The restful handler for course enrollments.
    It allows retrieval of the enrollments (as an HTML page).

    GET
        html: return an html page which will show course enrollments.
    '''
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    course_module = modulestore().get_course(course_key)
    enrollments = CourseEnrollment.objects.filter(
        course_id=course_key_string,
        is_active=True
    )
    return render_to_response('enrollments.html', {
        'language_code': request.LANGUAGE_CODE,
        'context_course': course_module,
        'enrollments': enrollments,
        'course_id': course_key_string,
    })
