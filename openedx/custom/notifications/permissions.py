"""
Permissions for notifications app
"""

from django.contrib.auth.models import User
from student.roles import (
    GlobalStaff,
    CourseStaffRole,
    CourseInstructorRole,
)
from .models import NotificationPreference

def can_send_course_notifications(user, course_key):
    """
    Staff and admin can send notifications for all courses.
    Teacher can send notifications for their own courses.
    """
    return is_staff_or_course_teacher(user, course_key)


def is_staff_or_course_teacher(user, course_key):
    return any((
        GlobalStaff().has_user(user),
        CourseStaffRole(course_key).has_user(user),
        CourseInstructorRole(course_key).has_user(user),
    ))

def get_course_teachers(course_key, preference_filter=False):
    teachers = User.objects.filter(
        courseaccessrole__role__in=('instructor', 'staff'),
        courseaccessrole__course_id=course_key
    )
    if preference_filter:
        teachers = teachers.exclude(
            notification_preferences__receive_on=NotificationPreference.NOWHERE,
        )
    return teachers

def get_course_students(course_key):
    return User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1,
    )
