# -*- coding: UTF-8 -*-
"""
Ta3leem Insights helpers.
"""
import logging

from xmodule.modulestore.django import modulestore
from lms.djangoapps.course_api.blocks.api import get_blocks
from openedx.custom.taleem.models import Ta3leemUserProfile
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = logging.getLogger(__name__)

def context_for_insights(request):
    courses = CourseOverview.objects.exclude(is_timed_exam=True)
    num_videos = 0
    num_lessons = 0
    course_names = []
    course_lessons = []
    for course in courses:
        try:
            counts = get_blocks(
                request,
                modulestore().make_course_usage_key(course.id),
                block_types_filter=['course'],
                block_counts=['video', 'vertical'],
                requested_fields=['block_counts'],
                return_type='list',
            )[0]['block_counts']
        except:
            counts = {}

        course_names.append(course.display_name)
        course_lessons.append(counts.get('vertical', 0))
        num_lessons += counts.get('vertical', 0)
        num_videos += counts.get('video', 0)

    # return counts
    return {
        'num_learners': Ta3leemUserProfile.objects.filter(
            user_type='student'
        ).count(),
        'num_courses': courses.count(),
        'num_lessons': num_lessons,
        'num_videos': num_videos,
        'course_names': course_names,
        'course_lessons': course_lessons,
    }

