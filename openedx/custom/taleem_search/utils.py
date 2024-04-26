import collections
import math

from django.conf import settings
from django.db.models import Q, Count
from django.shortcuts import redirect
from six import text_type
from student.models import CourseEnrollment

from openedx.custom.taleem.utils import get_course_ratings
from openedx.custom.taleem_search.models import FilterCategory, FilterCategoryValue
from openedx.custom.wishlist.models import Wishlist


def apply_filters(courses, filters):
    """
    Works well for both courses and live courses
    Assumes that filters is a string and not empty.
    courses: Query set to be filtered.
    """
    filters_set = set(map(int, filters.split(',')))
    categories = collections.defaultdict(list)
    for fcv in FilterCategoryValue.objects.filter(
        id__in=filters_set
    ):
      categories[fcv.filter_category.id].append(fcv.id)


    def course_valid_for_filters(course):
        for category in categories:
            if not course.filters.filter(filter_value__id__in=categories[category]):
                return False
        return True

    filtered_courses = courses.filter(
        filters__filter_value__in=filters_set
    )

    return courses.filter(id__in=[
        course.id
        for course in filtered_courses
        if course_valid_for_filters(course)
    ])


def get_category_values(category_id):
    filters = []
    category_filters = FilterCategoryValue.objects.filter(filter_category__id=category_id)

    for category_filter in category_filters:
        filter = {
            'id': category_filter.id,
            'value': category_filter.value,
            'value_in_arabic': category_filter.value_in_arabic
        }
        filters.append(filter)

    return filters


def get_pagination_data(request, courses_list):
    current_page = 1
    is_pagination = False

    course_per_page = settings.COURSE_PER_PAGE or 8

    num_of_courses = len(courses_list)
    num_of_pages = max(math.ceil(num_of_courses/course_per_page), 1)

    if request.GET.get('page'):
        current_page = request.GET.get('page')

    try:
        current_page = int(current_page)
    except ValueError:
        return redirect('/courses')

    if num_of_courses > course_per_page:
        is_pagination = True

    if int(current_page) > num_of_pages:
        current_page = num_of_pages

    course_list_start = (current_page-1) * course_per_page
    course_list_end = current_page * course_per_page

    courses_list = courses_list[course_list_start:course_list_end]

    return is_pagination, num_of_pages, courses_list


def get_filters_data():
    filters_data = {}
    filter_categories = FilterCategory.objects.exclude(
        special=True).prefetch_related('filtercategoryvalue_set').all()

    for category in filter_categories:
        category_name = category.name
        category_filters = list(category.filtercategoryvalue_set.values('id', 'value', 'value_in_arabic'))
        for i in range(len(category_filters)):
            category_filters[i]['value_in_arabic'] = "" if category_filters[i]['value_in_arabic'] == None else category_filters[i]['value_in_arabic'].strip()

        filters_data[category_name] = {
            'category_name': category_name,
            'category_name_in_arabic': "" if category.name_in_arabic == None else category.name_in_arabic.strip(),
            'category_filters': category_filters
        }

    return filters_data


def get_recommended_courses(all_courses, filters):
    filters_set = set(map(int, filters.split(',')))
    categories = FilterCategory.objects.filter(
        filtercategoryvalue__in=filters_set
    ).order_by('weightage')

    for category in categories:
        category_values = category.filtercategoryvalue_set.all()
        courses = all_courses.filter(
            filters__filter_value__in=category_values,
        )
        if courses:
            return courses, category.name

    return all_courses.none(), ''


def get_courses_in_json(courses, user):
    json_courses = []

    course_ratings = get_course_ratings(user, courses)

    for course in courses:
        data = {
            'id': text_type(course.id),
            'display_name_with_default': course.display_name_with_default,
            'course_image_url': course.course_image_url,
            'display_number_with_default': course.display_number_with_default,
            'display_org_with_default': course.display_org_with_default,
            'course_date_string': course.start.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'advertised_start': course.advertised_start,
            'is_favorite': '' if user.is_anonymous else in_user_wishlist(course, user),
            'is_enrolled': CourseEnrollment.is_enrolled(user, course.id)
        }

        data.update(course_ratings[text_type(course.id)])
        json_courses.append(data)

    return json_courses


def in_user_wishlist(course, user):
    return Wishlist.objects.filter(user=user, course_key=text_type(course.id)).exists()


def is_course_valid_for_filters(filters_dict, course):
    for category in filters_dict:
        if not course.filters.filter(filter_value__id__in=filters_dict[category]):
            return False
    return True


def get_searched_courses(courses, search_term):
    """
    args:
        courses: Queryset to CourseOverview
        search_term: string
    returns: Queryset to CourseOverview
    """
    query1 = Q(display_name__icontains=search_term)
    query2 = Q(short_description__icontains=search_term)
    return courses.filter(query1 | query2)


def get_sorted_courses(courses, sort_type):
    sorting_supported = [
        'start_date',
        'atoz',
        'rating',
        'popular',
        'ztoa'
    ]

    if sort_type.lower() not in sorting_supported:
        return courses

    if sort_type == 'start_date':
        courses = courses.order_by("start")
    elif sort_type == 'atoz':
        courses.order_by('display_name')
    elif sort_type == 'ztoa':
        courses.order_by('-display_name')
    elif sort_type == 'rating':
        courses = courses.annotate(
            num_stars=Count('course_ratings')
        ).order_by('-num_stars')
    elif sort_type == 'popular':
        courses = courses.annotate(
            num_enrollments=Count('courseenrollment')
        ).order_by('-num_enrollments')

    return courses


def get_sorted_live_courses(courses, sort_type):
    """
    Sort the given courses.
    """
    sorting_supported = [
        'start_date',
        'atoz',
        'popular',
        'ztoa'
    ]

    if sort_type.lower() not in sorting_supported:
        return courses

    if sort_type == 'start_date':
        courses = courses.order_by('scheduled_on')
    elif sort_type == 'atoz':
        courses = courses.order_by('name')
    elif sort_type == 'ztoa':
        courses = courses.order_by('-name')
    elif sort_type == 'popular':
        courses = courses.annotate(
            num_bookings=Count('bookings')
        ).order_by('-num_bookings')

    return courses


def get_sorted_exams(exams, sort_type):
    """
    Sort the given exams.
    """
    sorting_supported = [
        'atoz',
        'ztoa'
        'start_date',
        'due_date',
    ]

    if sort_type.lower() not in sorting_supported:
        return exams

    if sort_type == 'start_date':
        exams = exams.order_by('release_date')
    elif sort_type == 'atoz':
        exams = exams.order_by('display_name')
    elif sort_type == 'ztoa':
        exams = exams.order_by('-display_name')
    elif sort_type == 'due_date':
        exams = exams.order_by('due_date')

    return exams
