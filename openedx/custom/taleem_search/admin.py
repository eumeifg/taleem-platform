"""
Admin registration for tags models
"""


from django.contrib import admin

from openedx.custom.taleem_search.models import (
    CourseFilters, FilterCategory,
    FilterCategoryValue, LiveCourseFilters,
    ExamFilters, AdvertisedCourse,
    PopularCourse,
)


@admin.register(FilterCategory)
class FilterCategoryAdmin(admin.ModelAdmin):
    """Admin for FilterCategory"""
    search_fields = ('name', )
    list_display = ('id', 'name', 'name_in_arabic',
        'weightage', 'web_only', 'special', 'highlight', )


@admin.register(FilterCategoryValue)
class FilterCategoryValueAdmin(admin.ModelAdmin):
    """Admin for FilterCategoryValue"""
    search_fields = ('value', )
    list_display = ('id', 'value', 'value_in_arabic')
    list_filter = ('filter_category', )


@admin.register(AdvertisedCourse)
class AdvertisedCourseAdmin(admin.ModelAdmin):
    """Admin for advertised courses"""
    search_fields = ('course__display_name', )
    list_display = ('id', 'course', 'priority')


@admin.register(PopularCourse)
class PopularCourseAdmin(admin.ModelAdmin):
    """Admin for popular courses"""
    search_fields = ('course__display_name', )
    list_display = ('id', 'course', 'priority')


@admin.register(CourseFilters)
class CourseFiltersAdmin(admin.ModelAdmin):
    """Admin for Courses Filters"""
    search_fields = ('course__display_name', 'filter_value__value')
    list_display = ('id', 'course', 'filter_value')
    list_filter = ('filter_value__filter_category', 'filter_value', )


@admin.register(LiveCourseFilters)
class LiveCourseFiltersAdmin(admin.ModelAdmin):
    """Admin for Live Courses Filters"""
    search_fields = ('course__name', 'filter_value__value')
    list_display = ('id', 'course', 'filter_value')
    list_filter = ('filter_value__filter_category', 'filter_value', )
    autocomplete_fields = ('course', )

@admin.register(ExamFilters)
class ExamFiltersAdmin(admin.ModelAdmin):
    """Admin for Exam Filters"""
    search_fields = ('exam__display_name', 'filter_value__value')
    list_display = ('id', 'exam', 'filter_value')
    list_filter = ('filter_value__filter_category', 'filter_value', )
    autocomplete_fields = ('exam', )
