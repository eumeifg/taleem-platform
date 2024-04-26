"""
Functions for accessing and displaying live courses.
"""
from itertools import chain

from django.db.models import Func, DateTimeField
from django.utils import timezone
from openedx.custom.live_class.models import LiveClass


class EndDate(Func):
    """
    Filter expression to count end date of live course.
    """
    function = "DATE_ADD"
    template = "%(function)s(%(expressions)s, INTERVAL duration MINUTE)"
    output_field = DateTimeField()


def get_course_with_access(user, course_key):
    """
    Given a course_key, look up the corresponding LiveClass,
    check that the user has the access to view the course,
    and return the live course.

    Raises a 404 if the course_key is invalid, or the user doesn't have access.
    """
    try:
        live_class = LiveClass.objects.get(id=course_key)
    except LiveClass.DoesNotExist:
        raise Http404("Course not found.")
    # if live_class.class_type == LiveClass.PUBLIC_AT_INSTITUTION and \
    #     user.ta3leem_profile.university != live_class.university:
    #     raise Http404("Course not found.")
    return live_class


def get_live_courses(stage=None):
    """
    Given the stage look up the live classes
    queryset.
    """
    stages = [stage] if stage else [LiveClass.RUNNING, LiveClass.SCHEDULED]
    _filters = {
        'class_type': LiveClass.PUBLIC,
        'stage__in': stages,
    }

    if stage == LiveClass.SCHEDULED:
        _filters.update({'scheduled_on__gt': timezone.now()})
    elif stage == LiveClass.RUNNING:
        _filters.update({'scheduled_on__lte': timezone.now()})

    courses = LiveClass.objects.prefetch_related('moderator').filter(**_filters).distinct()

    if not stage or stage == LiveClass.RUNNING:
        courses = courses.annotate(
            end=EndDate('scheduled_on')
        ).filter(end__gte=timezone.now())

    return courses.order_by('scheduled_on')


def my_live_classes(user):
    at_the_moment = timezone.now()
    classes_teach = LiveClass.objects.filter(moderator=user.ta3leem_profile)
    classes_learn = LiveClass.objects.filter(bookings__user=user)
    return sorted(
        chain(classes_learn, classes_teach),
        key=lambda live_class: abs(live_class.scheduled_on - at_the_moment)
    )
