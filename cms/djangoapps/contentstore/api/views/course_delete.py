import six
import logging

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from xmodule.modulestore.django import modulestore
from contentstore.utils import delete_course
from contentstore.views.item import _delete_orphans

from .utils import course_author_access_required

log = logging.getLogger(__name__)


@view_auth_classes()
class CourseDeleteView(DeveloperErrorViewMixin, GenericAPIView):
    """
    **Use Case**

    **Example Requests**

        POST /api/courses/v1/delete/{course_id}/

    **GET Response Values**

        The HTTP 200 response has the following values.

        * success - whether the course is deleted.
        * error
            * whether the error in deleting the course.
    """
    @course_author_access_required
    def post(self, request, course_key):
        """
        Initiate the delete course.
        """
        status = False
        error = "Sorry, We are not able to find such course."

        if modulestore().get_course(course_key):
            try:
                _delete_orphans(course_key, request.user.id, True)
            except Exception as e:
                log.info("Failed to delete orphans, Skipping: {}".format(e))

            try:
                delete_course(course_key, request.user.id, True)
                status = True
                error = ''
            except Exception as e:
                error = str(e)

        return Response({
            'status': status,
            'error': error
        })
