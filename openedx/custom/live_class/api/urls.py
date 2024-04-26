"""
Course API URLs
"""


from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^v1/courses/$',
        views.LiveCourseListView.as_view(),
        name="live-course-list"
    ),
    url(
        r'^v1/courses/enrollment/$',
        views.LiveCourseEnrollmentView.as_view(),
        name="live-course-enrollments"
    ),
    url(
        r'^v1/courses/(?P<course_key>[0-9a-f-]+)',
        views.LiveCourseDetailView.as_view(),
        name="live-course-detail"
    ),
    url(
        r'^v1/class/can_join/(?P<course_id>[0-9a-f-]+)',
        views.LiveCourseJoinView.as_view(),
        name="live-course-join"
    ),
    url(
        r'^v1/class/attendance/',
        views.LiveCourseAttendanceView.as_view(),
        name="live-course-attendance"
    ),
]

