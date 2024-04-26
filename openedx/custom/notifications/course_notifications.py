"""
Views to show a course's notifications.
"""


import six
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template.context_processors import csrf
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import View
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.courseware.courses import get_course_with_access
from openedx.features.course_experience import default_course_url_name
from util.views import ensure_valid_course_key
from student.models import CourseEnrollment
from util.json_request import JsonResponse

from .tasks import send_announcement_notification

class CourseNotificationsView(View):
    """
    View showing the interface to send notifications for a course.
    """
    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def get(self, request, course_id):
        """
        Displays the interface to send course notifications.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key)
        course_url_name = default_course_url_name(course.id)
        course_url = reverse(course_url_name, kwargs={'course_id': six.text_type(course.id)})

        # Render the course notifications page
        context = {
            'csrf': csrf(request)['csrf_token'],
            'course': course,
            'enrollments': CourseEnrollment.objects.filter(
                course_id=course_id,
                is_active=True
            ),
            'supports_preview_menu': False,
            'course_url': course_url,
            'disable_courseware_js': True,
            'uses_pattern_library': False,
        }
        return render_to_response('notifications/course-notifications.html', context)

    @method_decorator(login_required)
    @method_decorator(ensure_csrf_cookie)
    @method_decorator(cache_control(no_cache=True, no_store=True, must_revalidate=True))
    @method_decorator(ensure_valid_course_key)
    def post(self, request, course_id):
        """
        Store notification and send FCM.

        Arguments:
            request: HTTP request
            course_id (unicode): course id
            students (list): User IDs
            title (unicode): Notification title
            message (unicode): Notification message
        """
        teacher_name = request.user.profile.name
        title = "{{teacher_name:{teacher_name}}} made an announcement".format(
            teacher_name=teacher_name
        )
        course_key = CourseKey.from_string(course_id)
        params = json.loads(request.body.decode("utf-8"))
        send_announcement_notification.delay(
            title=title,
            message=params.get('message', ''),
            data={
                'type': 'teacher_announcement',
                'course_id': course_id,
                'teacher_name': teacher_name,
            },
            course_id=course_id,
            users=params.get('students', []),
            resolve_link=params.get('resolve_link'),
        )
        return JsonResponse({'success': True})

