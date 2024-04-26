"""
Wishlist models.
"""

import logging

from django.contrib.auth.models import User
from django.db import models

from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import LearningContextKeyField

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


log = logging.getLogger(__name__)


# pylint: disable=model-has-unicode
class Wishlist(TimeStampedModel, models.Model):
    """
    Model for user wishlist/fav course.
    """
    id = models.BigAutoField(primary_key=True)  # pylint: disable=invalid-name
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wishlist"
    )
    course_key = LearningContextKeyField(
        max_length=255,
        db_column="course_key"
    )

    @property
    def course(self):
        try:
            return CourseOverview.get_from_id(self.course_key)
        except:
            return None

    @classmethod
    def get_favorite_courses(cls, user):
        """
        Returns the list of courses marked as favorite by
        the given user.
        """
        favorite_courses = []
        entries = cls.objects.filter(
            user=user,
        ).order_by('-created')
        for entry in entries:
            try:
                favorite_courses.append(CourseOverview.get_from_id(entry.course_key))
            except CourseOverview.DoesNotExist as e:
                continue
        return favorite_courses

    @classmethod
    def fav_course_id_list(cls, user):
        """
        Returns the list of course IDs marked as favorite by
        the given user.
        """
        return cls.objects.filter(
            user=user,
        ).values_list('course_key', flat=True)


    class Meta:
        app_label = 'wishlist'
        unique_together = ('user', 'course_key')
        ordering = ("-created",)

    def __unicode__(self):
        return 'Wishlist: {username}: {course_key}'.format(
            username=self.user.username,
            course_key=self.course_key,
        )

