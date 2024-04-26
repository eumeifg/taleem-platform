# -*- coding: UTF-8 -*-
"""
Video views.
"""

import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.conf import settings

from openedx.core.lib.api.view_utils import view_auth_classes
from rest_framework.views import APIView
from edxval.api import is_video_available
from edxval.models import CourseVideo

from student.models import CourseEnrollment
from .models import PublicVideo

log = logging.getLogger(__name__)


@view_auth_classes(is_authenticated=False)
class VideoPermissionView(APIView):
    """
    **Use Cases**

        Request to check if the user is allowed to play the video

    **Example Requests**

       GET /videos/permission/<video_id>/
       Headers: {
        "Authorization": "Bearer <token_here>"
       }

    **Response Values**

       This request won't return anything in response body,
       VDS to check the response status code.

    **Parameters**

        video_id (embed in URL):
            UUID of the video to check permission for.

    **Returns**

        * 200 on success, If the user is allowed to play the video.
        * 400 if an invalid parameter was sent.
        * 403 If the user is not allowed to play the video.
        * 404 if the requested video doesn't exists.
    """
    @method_decorator(cache_page(settings.API_CACHE_TIMEOUT))
    @method_decorator(vary_on_headers("Authorization",))
    def get(self, request, edx_video_id):
        """
        Check if the user can access the course video.
        """
        # if the requested video is public
        if PublicVideo.objects.only('id').filter(edx_video_id=edx_video_id).exists():
            return JsonResponse(data={}, status=200)

        if not request.user.is_authenticated:
            raise PermissionDenied("NotAuthenticated")

        user = request.user
        course_videos = CourseVideo.objects.only(
            'course_id',
        ).filter(video__edx_video_id=edx_video_id)
        # Only users with access to course can access video
        if not CourseEnrollment.objects.only('id').filter(
            user=user,
            is_active=True,
            course_id__in=course_videos.values_list('course_id')
        ).exists():
            log.info("{} is not allowed and tried to play {}".format(
                user.email,
                edx_video_id
            ))
            raise PermissionDenied("NotEnrolled")

        # Make sure the video exists
        if not is_video_available(edx_video_id):
            log.info("Video not found: {}.".format(edx_video_id))
            raise Http404(u"Video not found: {}.".format(edx_video_id))

        # return response
        return JsonResponse(data={}, status=200)

