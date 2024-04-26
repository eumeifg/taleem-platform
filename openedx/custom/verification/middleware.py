import re

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.custom.taleem.models import UserType


class SiteAccessMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if not self.should_process_request(request):
            return

        if request.user.is_authenticated:
            ta3leem_profile = request.user.ta3leem_profile

            if ta3leem_profile and ta3leem_profile.user_type == UserType.teacher.name:
                user_verified = IDVerificationService.user_is_verified(request.user)
                if not user_verified:
                    redirect_url = self.get_redirect_url(request)
                    return redirect(redirect_url)

    def should_process_request(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return False

        path = request.META['PATH_INFO']

        restricted_url_patterns = [
            # '/dashboard',
            # '/courses',
            # '/course',
            '/home',
            '/timed-exams',
            '/library',
            '/verification/requests',
            '/verification/status_change'
        ]
        for pattern in restricted_url_patterns:
            if re.match(pattern, path) or path.startswith(pattern):
                return True
        return False

    def get_redirect_url(self, request):
        if request.get_host() == settings.CMS_BASE:
            return settings.LMS_ROOT_URL + '/dashboard/?notverified=1'

        return reverse('verification:verify_student_identification')
