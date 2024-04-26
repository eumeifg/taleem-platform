"""
Models used for persisting exam grades.
"""


import logging

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField

from lms.djangoapps.courseware.fields import UnsignedBigIntAutoField
from openedx.core.lib.cache_utils import get_cache

log = logging.getLogger(__name__)


@python_2_unicode_compatible
class PersistentExamGrade(TimeStampedModel):
    """
    A django model tracking persistent exam grades.

    .. no_pii:
    """

    class Meta(object):
        app_label = "taleem_grades"
        # Indices:
        # (course_id, user_id) for individual grades
        # (course_id) for instructors to see all exam grades, implicitly created via the unique_together constraint
        # (user_id) for user dashboard; explicitly declared as an index below
        # (modified): find all the grades updated within a certain timespan
        # (modified, course_id): find all the grades updated within a certain timespan for a exam
        unique_together = [
            ('course_id', 'user_id'),
        ]
        index_together = [
            ('modified', 'course_id')
        ]

    # primary key will need to be large for this table
    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name
    user_id = models.IntegerField(blank=False, db_index=True)
    course_id = CourseKeyField(blank=False, max_length=255)

    # Information about the course grade itself
    percent_grade = models.FloatField(blank=False)

    _CACHE_NAMESPACE = u"taleem_grades.models.PersistentExamGrade"

    def __str__(self):
        """
        Returns a string representation of this model.
        """
        return u', '.join([
            u"{} user: {}".format(type(self).__name__, self.user_id),
            u"percent grade: {}%".format(self.percent_grade),
        ])

    @classmethod
    def prefetch(cls, course_id, users):
        """
        Prefetches grades for the given users for the given exam.
        """
        get_cache(cls._CACHE_NAMESPACE)[cls._cache_key(course_id)] = {
            grade.user_id: grade
            for grade in
            cls.objects.filter(user_id__in=[user.id for user in users], course_id=course_id)
        }

    @classmethod
    def clear_prefetched_data(cls, course_key):
        """
        Clears prefetched grades for this exam from the RequestCache.
        """
        get_cache(cls._CACHE_NAMESPACE).pop(cls._cache_key(course_key), None)

    @classmethod
    def read(cls, user_id, course_id):
        """
        Reads a grade from database

        Arguments:
            user_id: The user associated with the desired grade
            course_id: The id of the exam associated with the desired grade

        Raises PersistentExamGrade.DoesNotExist if applicable
        """
        try:
            prefetched_grades = get_cache(cls._CACHE_NAMESPACE)[cls._cache_key(course_id)]
            try:
                return prefetched_grades[user_id]
            except KeyError:
                # user's grade is not in the prefetched dict, so
                # assume they have no grade
                raise cls.DoesNotExist
        except KeyError:
            # grades were not prefetched for the course, so fetch it
            return cls.objects.get(user_id=user_id, course_id=course_id)

    @classmethod
    def bulk_read_grades(cls, course_id):
        """
        Reads all grades for the given exam.

        Arguments:
            course_id: The exam identifier for the desired grades
        """
        try:
            prefetched_grades = get_cache(cls._CACHE_NAMESPACE)[cls._cache_key(course_id)]
            return prefetched_grades or []
        except KeyError:
            # grades were not prefetched for the course, so fetch it
            return cls.objects.filter(course_id=course_id)

    @classmethod
    def update_or_create(cls, user_id, course_id, percent_grade):
        """
        Creates a course grade in the database.
        Returns a PersistedExamGrade object.
        """
        try:
            grade = cls.objects.get(
                user_id=user_id,
                course_id=course_id,
            )
            grade.percent_grade=percent_grade
            grade.save()
        except cls.DoesNotExist:
            grade = cls.objects.create(
                user_id=user_id,
                course_id=course_id,
                percent_grade=percent_grade,
            )
        cls._update_cache(course_id, user_id, grade)
        return grade

    @classmethod
    def _update_cache(cls, course_id, user_id, grade):
        exam_cache = get_cache(cls._CACHE_NAMESPACE).get(cls._cache_key(course_id))
        if exam_cache is not None:
            exam_cache[user_id] = grade

    @classmethod
    def _cache_key(cls, course_id):
        return u"taleem_grades_cache.{}".format(course_id)
