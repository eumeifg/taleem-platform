"""
Ta3leem search views functions
"""

from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.taleem.utils import user_is_teacher
from openedx.custom.taleem_search.models import CourseFilters, FilterCategory, FilterCategoryValue
from openedx.custom.taleem_search.utils import (
    apply_filters, get_category_values, get_courses_in_json,
    get_pagination_data, get_searched_courses, get_sorted_courses,
    get_recommended_courses,
)


@login_required
@ensure_csrf_cookie
def course_filters_view(request, course_key_string):
    from contentstore.views.course import get_course_and_check_access

    if course_key_string is None:
        return redirect(reverse('home'))

    course_key = CourseKey.from_string(course_key_string)

    with modulestore().bulk_operations(course_key):
        course_module = get_course_and_check_access(course_key, request.user)
        course_overview = get_object_or_404(CourseOverview, id=course_key)
        filter_categories = FilterCategory.objects.all()

    if request.method == 'POST':
        filter_category = request.POST.get('filter-category')
        filter_value = request.POST.get('filter-value')
        new_filter = request.POST.get('new-filter')
        new_arabic_filter = request.POST.get('new-arabic-filter')
        category = FilterCategory.objects.get(id=filter_category)

        if new_filter:
            value, created = FilterCategoryValue.objects.get_or_create(
                filter_category=category, value=new_filter.capitalize(), value_in_arabic=new_arabic_filter)
        else:
            value = FilterCategoryValue.objects.get(id=filter_value)

        _, created = CourseFilters.objects.get_or_create(course=course_overview, filter_value=value)

    course_filters = CourseFilters.objects.filter(course=course_overview)

    return render_to_response('taleem_search/course_filters.html', {
        'language_code': request.LANGUAGE_CODE,
        'context_course': course_module,
        'filter_categories': filter_categories,
        'course_filters': course_filters,
        'course_key': course_key_string
    })


@login_required
@ensure_csrf_cookie
def get_category_filters(request, category_id):
    if not request.user.is_superuser:
        if not request.user.is_staff:
            if not user_is_teacher(request.user):
                return HttpResponseForbidden()

    filters = get_category_values(category_id)

    return JsonResponse({'filters': filters})


def get_filtered_courses(request, type='courses'):
    """
    args:
        type: 'exams' or 'courses'
    """
    exclude_archived = {
        'end_date__isnull': False,
        'end_date__lte': datetime.now(UTC),
    }
    if type == 'courses':
        all_courses = CourseOverview.objects.filter(
            invitation_only=False,
        ).exclude(**exclude_archived).distinct()
    else:
        all_courses = get_timed_exams()

    courses = all_courses
    is_recommended_courses = False
    weightage_category = ''

    filters = request.GET.get('filters')
    if filters:
        courses = apply_filters(courses, filters)
        if not courses:
            is_recommended_courses = True
            courses, weightage_category = get_recommended_courses(
                all_courses, filters
            )

    search_term = request.GET.get('search')
    if search_term:
        courses = get_searched_courses(courses, search_term)

    sort_type = request.GET.get('sort')
    if sort_type:
        courses = get_sorted_courses(courses, sort_type)

    is_pagination, total_num_of_pages, courses_list = get_pagination_data(request, courses)
    courses_list = get_courses_in_json(courses_list, request.user)

    return JsonResponse({
        'courses': courses_list,
        'is_pagination': is_pagination,
        'total_num_of_pages': total_num_of_pages,
        'is_recommened_courses': is_recommended_courses,
        'weightage_category': weightage_category
    }, status=200)

