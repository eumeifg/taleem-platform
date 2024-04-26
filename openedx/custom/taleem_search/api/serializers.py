"""
search Serializers.
"""

from pytz import UTC
from datetime import datetime
from rest_framework import serializers

from openedx.custom.taleem_search.models import (
    FilterCategory, FilterCategoryValue,
    CourseFilters, LiveCourseFilters,
)
from openedx.custom.live_class.models import LiveClass


class SearchCategorySerializer(serializers.ModelSerializer):  # pylint: disable=abstract-method
    """
    Serializer for search category objects.
    """

    courses = serializers.SerializerMethodField()
    live_courses = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()

    def get_courses(self, filter_category):
        exclude_archived = {
            'course__end_date__isnull': False,
            'course__end_date__lte': datetime.now(UTC),
        }
        return CourseFilters.objects.filter(
            filter_value__filter_category=filter_category,
        ).exclude(**exclude_archived).count()

    def get_live_courses(self, filter_category):
        return LiveCourseFilters.objects.filter(
            filter_value__filter_category=filter_category,
            course__class_type=LiveClass.PUBLIC,
            course__stage__in=[LiveClass.RUNNING, LiveClass.SCHEDULED],
        ).count()

    def get_options(self, filter_category):
        return SearchCategoryValueSerializer(
            filter_category.filtercategoryvalue_set.all(),
            many=True
        ).data

    class Meta(object):
        """ Serializer metadata. """
        model = FilterCategory
        fields = ('id', 'name', 'special', 'web_only', 'highlight', 'name_in_arabic', 'description',
            'weightage', 'options', 'courses', 'live_courses', )


class SearchCategoryValueSerializer(serializers.ModelSerializer):  # pylint: disable=abstract-method
    """
    Serializer for search category value objects.
    """
    courses = serializers.SerializerMethodField()
    live_courses = serializers.SerializerMethodField()

    def get_courses(self, filter_value):
        exclude_archived = {
            'course__end_date__isnull': False,
            'course__end_date__lte': datetime.now(UTC),
        }
        return filter_value.course_filters.exclude(**exclude_archived).count()

    def get_live_courses(self, filter_value):
        return filter_value.live_course_filters.filter(
            course__class_type=LiveClass.PUBLIC,
            course__stage__in=[LiveClass.RUNNING, LiveClass.SCHEDULED],
        ).count()

    class Meta(object):
        """ Serializer metadata. """
        model = FilterCategoryValue
        fields = ('id', 'value', 'value_in_arabic', 'logo',
            'courses', 'live_courses', )


class AutoCompleteSerializer(serializers.Serializer):
    """
    Serializer for all kind of search.
    item here refers to a course, live class and exam.
    """
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(source='display_name')
