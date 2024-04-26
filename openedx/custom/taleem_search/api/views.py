# -*- coding: UTF-8 -*-
"""
API end-points for Ta3leem search.
"""

import logging
from pytz import UTC
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q
import edx_api_doc_tools as apidocs
from rest_framework.generics import ListAPIView
from rest_framework.authentication import SessionAuthentication
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination

from course_api.serializers import CourseSerializer
from openedx.custom.live_class.api.serializers import LiveCourseSerializer
from openedx.custom.live_class.api.courses import get_live_courses
from openedx.custom.timed_exam.utils import get_browsable_exams
from openedx.custom.timed_exam.api.serializers import ExamSerializer
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.custom.taleem_search.models import FilterCategory, FilterCategoryValue
from openedx.custom.taleem_search.utils import (
    apply_filters,
    get_sorted_courses,
    get_sorted_live_courses,
    get_sorted_exams,
)
from .serializers import (
    SearchCategorySerializer,
    SearchCategoryValueSerializer,
    AutoCompleteSerializer,
)

log = logging.getLogger(__name__)

class SearchPagination(DefaultPagination):
    """
    Paginator for search APIs.
    """
    page_size = 10
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        response = super(SearchPagination, self).get_paginated_response(data)

        # Add `current_page` value, it's needed for pagination footer.
        response.data["current_page"] = self.page.number

        # Add `start` value, it's needed for the pagination header.
        response.data["start"] = (self.page.number - 1) * self.get_page_size(self.request)

        return response


class SearchCategoryListView(ListAPIView):
    """REST endpoints for lists of search categories."""

    pagination_class = SearchPagination
    serializer_class = SearchCategorySerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'highlighted_only',
                apidocs.ParameterLocation.QUERY,
                description="List search category for discover screen",
            )
        ]
    )
    @method_decorator(cache_page(settings.API_CACHE_TIMEOUT))
    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of search categories with possible options.

        The category names are always sorted in descending order by weightage.

        Each page in the list contains 10 categories by default. The page
        size can be altered by passing parameter "page_size=<page_size>".

        **Use Cases**

           Request information on search categories.

        **Example Requests**

            GET /api/search/categories/
            GET /api/search/categories/?highlighted_only=true

        **Response Values**

            Body comprises a list of category names.

        **Returns**

            * 200 on success, with a list of search categories.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                    "id": 1,
                    "name": "Language",
                    "name_in_arabic": "لغة",
                    "description": "blah blha",
                    "weightage": 50.0,
                    "courses": 16,
                    "live_courses": 5,
                    "options": [
                      {
                        "id": 1,
                        "value": "Arabic",
                        "value_in_arabic": "العربية",
                        "logo": null,
                        "courses": 3,
                        "live_courses": 1
                      },
                      {
                        "id": 2,
                        "value": "English",
                        "value_in_arabic": "الإنجليزية",
                        "logo": null,
                        "courses": 1,
                        "live_courses": 3
                      },
                    ]
                  }
                ]
        """
        return super(SearchCategoryListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of search categories for GET requests.

        The results will only include search categories.
        """
        qs = FilterCategory.objects.exclude(web_only=True).order_by('-weightage')
        highlighted_only = self.request.query_params.get('highlighted_only', 'false')
        if highlighted_only.lower() == 'true':
            qs = qs.filter(highlight=True)
        return qs


class SearchCategoryValueListView(ListAPIView):
    """REST endpoints for lists of search category values."""

    pagination_class = SearchPagination
    serializer_class = SearchCategoryValueSerializer

    @method_decorator(cache_page(settings.API_CACHE_TIMEOUT))
    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of search category values.

        The category names are always sorted in ascending order by value alphabet.

        Each page in the list contains 10 categories by default. The page
        size can be altered by passing parameter "page_size=<page_size>".

        **Use Cases**

           Request information on search categories.

        **Example Requests**

            GET /api/search/category/<int:category_id>/values/

        **Response Values**

            Body comprises a list of values for the given category.

        **Returns**

            * 200 on success, with a list of category values.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                    "id": 1,
                    "value": "Arabic",
                    "value_in_arabic": "عربي",
                    "logo": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/taleem_search/sample-badge.png",
                    "courses": 10,
                    "live_courses": 3
                  }
                ]
        """
        return super(SearchCategoryValueListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of search categories for GET requests.

        The results will only include search categories.
        """
        category_id = self.kwargs['category_id']
        return FilterCategoryValue.objects.filter(filter_category=category_id).order_by('value')


class CourseSearchAutoCompleteView(ListAPIView):
    """REST endpoint for auto complete search term."""

    pagination_class = SearchPagination
    serializer_class = AutoCompleteSerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'search',
                apidocs.ParameterLocation.QUERY,
                description="Search term (At least 3 letters)",
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Get a list of course names for the given search term (auto complete).

        **Use Cases**

           Request course names for the given search term for auto completion.

        **Example Requests**

            GET /api/search/auto-complete/courses/?search=dare

        **Response Values**

            Body comprises a list of course names.

        **Returns**

            * 200 on success, with a list of course names matching search term.
            * 400 if an invalid parameter was sent

            Example response:

            {
              "results": [
                {
                  "id": "course-v1:ta3leem+d1008+2020_T2",
                  "name": "Dare to live"
                }
              ]
            }
        """
        return super(CourseSearchAutoCompleteView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of courses matching search term.
        """
        exclude_archived = {
            'end_date__isnull': False,
            'end_date__lte': datetime.now(UTC),
        }
        courses = CourseOverview.objects.filter(
            invitation_only=False,
        ).exclude(**exclude_archived).distinct()

        search_term = self.request.query_params.get('search')
        if search_term:
            query1 = Q(display_name__icontains=search_term)
            query2 = Q(short_description__icontains=search_term)
            courses = courses.filter(query1 | query2)

        return courses


class ExamSearchAutoCompleteView(ListAPIView):
    """REST endpoint for exam auto complete search term."""

    pagination_class = SearchPagination
    serializer_class = AutoCompleteSerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'search',
                apidocs.ParameterLocation.QUERY,
                description="Search term (At least 3 letters)",
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Get a list of exam names for the given search term (auto complete).

        **Use Cases**

           Request exam names for the given search term for auto completion.

        **Example Requests**

            GET /api/search/auto-complete/exams/?search=dare

        **Response Values**

            Body comprises a list of course names.

        **Returns**

            * 200 on success, with a list of course names matching search term.
            * 400 if an invalid parameter was sent

            Example response:

            {
              "results": [
                {
                  "id": "123",
                  "name": "Dare to live"
                }
              ]
            }
        """
        return super(ExamSearchAutoCompleteView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of courses matching search term.
        """
        exams = get_browsable_exams()
        search_term = self.request.query_params.get('search')
        if search_term:
            exams = exams.filter(
                display_name__icontains=search_term,
            )
        return exams


class LiveCourseSearchAutoCompleteView(ListAPIView):
    """REST endpoint for auto complete search term (live courses)."""

    pagination_class = SearchPagination
    serializer_class = AutoCompleteSerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'search',
                apidocs.ParameterLocation.QUERY,
                description="Search term (At least 3 letters)",
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Get a list of live course names for the given search term (auto complete).

        **Use Cases**

           Request course names for the given search term for auto completion.
        **Example Requests**

            GET /api/search/auto-complete/live/courses/?search=dare

        **Response Values**

            Body comprises a list of course names.

        **Returns**

            * 200 on success, with a list of course names matching search term.
            * 400 if an invalid parameter was sent

            Example response:

            {
              "results": [
                {
                  "id": "927d3fe5-0ccf-4f3d-b455-b19a70da1fae",
                  "name": "Dare to live"
                }
              ]
            }
        """
        return super(LiveCourseSearchAutoCompleteView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of courses matching search term.
        """
        live_courses = get_live_courses()
        search_term = self.request.query_params.get('search')
        if search_term:
            live_courses = live_courses.filter(
                name__icontains=search_term,
            )
        return live_courses


class AdvertisedCourseListView(ListAPIView):
    """REST endpoint to list the advertised courses"""

    authentication_classes = (
        JwtAuthentication, BearerAuthenticationAllowInactiveUser, SessionAuthentication
    )
    pagination_class = SearchPagination
    serializer_class = CourseSerializer

    @method_decorator(cache_page(settings.API_CACHE_TIMEOUT))
    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of advertised courses.

        **Use Cases**

           Request courses to show on mobile home screen.

        **Example Requests**

            GET /api/search/advertised/courses/

        **Response Values**

            Body comprises a list of courses.

        **Returns**

            * 200 on success, with a list of courses.
            * 400 if an invalid parameter was sent

            Example response:

            [
              {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                  "course_image": {
                    "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                    "name": "Course Image"
                  }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp"
              }
            ]
        """
        return super(AdvertisedCourseListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of courses set to be advertised.
        """
        exclude_archived = {
            'end_date__isnull': False,
            'end_date__lte': datetime.now(UTC),
        }
        courses = CourseOverview.objects.filter(
            invitation_only=False,
            advertised__isnull=False,
        ).exclude(**exclude_archived).distinct().order_by("popular__priority")

        return courses


class PopularCourseListView(ListAPIView):
    """REST endpoint to list the popular courses"""

    authentication_classes = (
        JwtAuthentication, BearerAuthenticationAllowInactiveUser, SessionAuthentication
    )
    pagination_class = SearchPagination
    serializer_class = CourseSerializer

    @method_decorator(cache_page(settings.API_CACHE_TIMEOUT))
    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of popular courses.

        **Use Cases**

           Request courses to show on mobile home screen.

        **Example Requests**

            GET /api/search/popular/courses/

        **Response Values**

            Body comprises a list of courses.

        **Returns**

            * 200 on success, with a list of courses.
            * 400 if an invalid parameter was sent

            Example response:

            [
              {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                  "course_image": {
                    "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                    "name": "Course Image"
                  }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp"
              }
            ]
        """
        return super(PopularCourseListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of courses set to be popular.
        """
        exclude_archived = {
            'end_date__isnull': False,
            'end_date__lte': datetime.now(UTC),
        }
        courses = CourseOverview.objects.filter(
            invitation_only=False,
            popular__isnull=False,
        ).exclude(**exclude_archived).distinct().order_by("popular__priority")

        return courses


class CourseSearchView(ListAPIView):
    """REST endpoint for search, sort and filter courses"""

    authentication_classes = (
        JwtAuthentication, BearerAuthenticationAllowInactiveUser, SessionAuthentication
    )
    pagination_class = SearchPagination
    serializer_class = CourseSerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'filters',
                apidocs.ParameterLocation.QUERY,
                description="Comma separated list of category `option` id which you get from /api/search/categories/",
            ),
            apidocs.string_parameter(
                'search',
                apidocs.ParameterLocation.QUERY,
                description="Search term",
            ),
            apidocs.string_parameter(
                'sort',
                apidocs.ParameterLocation.QUERY,
                description="atoz, start_date, rating, popular, ztoa",
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of courses for the given search term and filters.

        **Use Cases**

           Request courses belongs to the given filters and sort/serch.

        **Example Requests**

            GET /api/search/courses/

        **Response Values**

            Body comprises a list of courses.

        **Returns**

            * 200 on success, with a list of courses.
            * 400 if an invalid parameter was sent

            Example response:

            [
              {
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Fexample%2F2012_Fall",
                "media": {
                  "course_image": {
                    "uri": "/c4x/edX/example/asset/just_a_test.jpg",
                    "name": "Course Image"
                  }
                },
                "description": "An example course.",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "course_id": "edX/example/2012_Fall",
                "name": "Example Course",
                "number": "example",
                "org": "edX",
                "start": "2015-07-17T12:00:00Z",
                "start_display": "July 17, 2015",
                "start_type": "timestamp"
              }
            ]
        """
        return super(CourseSearchView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of courses matching search term and filters.

        The results will be then sorted based on the order given.
        """
        cache_key = "ta3leem.search.courses.qs"
        courses = cache.get(cache_key)
        if courses is None:
            exclude_archived = {
                'end_date__isnull': False,
                'end_date__lte': datetime.now(UTC),
            }
            courses = CourseOverview.objects.filter(
                filters__isnull=False,
                invitation_only=False,
            ).exclude(**exclude_archived).distinct()
            cache.set(cache_key, courses, settings.API_CACHE_TIMEOUT)

        filters = self.request.query_params.get('filters')
        if filters:
            courses = apply_filters(courses, filters)

        search_term = self.request.query_params.get('search')
        if search_term:
            query1 = Q(display_name__icontains=search_term)
            query2 = Q(short_description__icontains=search_term)
            courses = courses.filter(query1 | query2)

        sort_type = self.request.query_params.get('sort')
        if sort_type:
            courses = get_sorted_courses(courses, sort_type)

        return courses


class ExamSearchView(ListAPIView):
    """REST endpoint for search, sort and filter exams"""

    authentication_classes = (
        JwtAuthentication, BearerAuthenticationAllowInactiveUser, SessionAuthentication
    )
    pagination_class = SearchPagination
    serializer_class = ExamSerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'filters',
                apidocs.ParameterLocation.QUERY,
                description="Comma separated list of category `option` id which you get from /api/search/categories/",
            ),
            apidocs.string_parameter(
                'search',
                apidocs.ParameterLocation.QUERY,
                description="Search term",
            ),
            apidocs.string_parameter(
                'sort',
                apidocs.ParameterLocation.QUERY,
                description="atoz, start_date, popular, ztoa",
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of exams for the given search term and filters.

        **Use Cases**

           Request exams belongs to the given filters and sort/serch.

        **Example Requests**

            GET /api/search/exams/

        **Response Values**

            Body comprises a list of exams.

        **Returns**

            * 200 on success, with a list of exams.
            * 400 if an invalid parameter was sent

            Example response:

            [
              {
                "id": "927",
                "display_name": "Maths with Mack",
                "release_date": "2021-10-20T14:58:24+03:00",
                "due_date": "2021-10-30T14:58:24+03:00",
                "allotted_time": "01:00",
                "mode": "online",
                "exam_type": "public",
              }
            ]
        """
        return super(ExamSearchView, self).get(request, *args, **kwargs)

    def get_serializer_context(self):
        """
        Return the context for the serializer.
        """
        context = super(ExamSearchView, self).get_serializer_context()
        if self.request.method == 'GET':
            context.update({
                'requested_status': self.request.query_params.get('status'),
                'attempts': {},
                'dangling': [],
            })
        return context

    def get_queryset(self):
        """
        Returns queryset of exams matching search term and filters.
        The results will be then sorted based on the order given.
        """
        exams = get_browsable_exams()

        filters = self.request.query_params.get('filters')
        if filters:
            exams = apply_filters(exams, filters)

        search_term = self.request.query_params.get('search')
        if search_term:
            exams = exams.filter(display_name__icontains=search_term)

        sort_type = self.request.query_params.get('sort')
        if sort_type:
            exams = get_sorted_exams(exams, sort_type)

        return exams


class LiveCourseSearchView(ListAPIView):
    """REST endpoint for search, sort and filter live courses"""

    authentication_classes = (
        JwtAuthentication, BearerAuthenticationAllowInactiveUser, SessionAuthentication
    )
    pagination_class = SearchPagination
    serializer_class = LiveCourseSerializer

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                'filters',
                apidocs.ParameterLocation.QUERY,
                description="Comma separated list of category `option` id which you get from /api/search/categories/",
            ),
            apidocs.string_parameter(
                'search',
                apidocs.ParameterLocation.QUERY,
                description="Search term",
            ),
            apidocs.string_parameter(
                'sort',
                apidocs.ParameterLocation.QUERY,
                description="atoz, start_date, popular, ztoa",
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of live courses for the given search term and filters.

        **Use Cases**

           Request live courses belongs to the given filters and sort/serch.

        **Example Requests**

            GET /api/search/live/courses/

        **Response Values**

            Body comprises a list of live courses.

        **Returns**

            * 200 on success, with a list of live courses.
            * 400 if an invalid parameter was sent

            Example response:

            [
              {
                "course_id": "927d3fe5-0ccf-4f3d-b455-b19a70da1fae",
                "name": "Maths with Mack",
                "subject": null,
                "organization": {},
                "grade": null,
                "language": null,
                "poster": "https://storage-ta3leem.dev.env.creativeadvtech.com/media/live_classes/accounting.png",
                "start": "2021-10-20T14:58:24+03:00",
                "stage": "Scheduled",
                "duration": "60",
                "price": 0,
                "seats": 150,
                "seats_left": 150,
                "details_url": "https://lms-ta3leem.dev.env.creativeadvtech.com/api/live-courses/v1/courses/927d3fe5-0ccf-4f3d-b455-b19a70da1fae"
              }
            ]
        """
        return super(LiveCourseSearchView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of live courses matching search term and filters.

        The results will be then sorted based on the order given.
        """
        courses = get_live_courses()

        filters = self.request.query_params.get('filters')
        if filters:
            courses = apply_filters(courses, filters)

        search_term = self.request.query_params.get('search')
        if search_term:
            query = Q(name__icontains=search_term) | Q(description__icontains=search_term)
            courses = courses.filter(query)

        sort_type = self.request.query_params.get('sort')
        if sort_type:
            courses = get_sorted_live_courses(courses, sort_type)

        return courses
