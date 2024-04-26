""" Middleware for seb_openedx """

import logging

from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from opaque_keys.edx.keys import CourseKey
from student.models import CourseAccessRole
from lms.djangoapps.courseware.access import has_access
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from .permissions import can_proceed

LOG = logging.getLogger(__name__)


class SecureBrowserMiddleware(MiddlewareMixin):
    """ Middleware for Ta3leem Browser """

    # pylint: disable=too-many-locals
    def process_view(self, request, view_func, view_args, view_kwargs):
        """ Start point """

        # Allow studio
        if settings.SERVICE_VARIANT == 'cms':
            return None

        user = request.user
        if user.is_authenticated:
            # Allow admin, staff and white listed users
            if any((
                user.is_superuser,
                request.user.is_staff,
                user.ta3leem_profile.can_use_normal_browser,
            )):
                return None

            course_id = view_kwargs.get('course_key_string') or view_kwargs.get('course_id')
            if course_id:
                course_key = CourseKey.from_string(course_id)
                # Allow course teacher
                if bool(has_access(user, 'instructor', course_key)) or \
                    bool(has_access(user, 'staff', course_key)):
                    return None
            else:
                # Allow teacher
                if CourseAccessRole.objects.filter(
                    user=user,
                    role__in=['staff', 'instructor']
                ).exists():
                    return None

        # Allow non blocked pages
        tb_config = configuration_helpers.get_value('TA3LEEM_BROWSER', {})
        if view_func.__name__ not in tb_config.get('BLOCKED_VIEWS', []):
            return None

        # Match the secret keys
        if can_proceed(request, tb_config):
            return None

        return redirect('apps_landing_page')
