"""
Platform plugins to support course notifications.
"""


from django.urls import reverse
from django.utils.translation import ugettext as _

from openedx.features.course_experience.course_tools import CourseTool
from openedx.custom.notifications.permissions import can_send_course_notifications


class CourseNotificationsTool(CourseTool):
    """
    The course notifications tool.
    """
    @classmethod
    def analytics_id(cls):
        """
        Returns an id to uniquely identify this tool in analytics events.
        """
        return 'ta3leem.notifications'

    @classmethod
    def is_enabled(cls, request, course_key):
        """
        The notifications tool is only enabled for staff/teacher.
        """
        return can_send_course_notifications(request.user, course_key)

    @classmethod
    def title(cls):
        """
        Returns the title of this tool.
        """
        return _('Announcements')

    @classmethod
    def icon_classes(cls):
        """
        Returns the icon classes needed to represent this tool.
        """
        return 'fa fa-bullhorn'

    @classmethod
    def url(cls, course_key):
        """
        Returns the URL for this tool for the specified course key.
        """
        return reverse('notifications:course_notifications', args=[course_key])
