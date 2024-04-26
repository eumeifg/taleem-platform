"""
Script to measure the avg time the video permission
check API takes.

python manage.py lms avg_time_video_permission
"""

import time
from edxval.models import CourseVideo
from student.models import CourseEnrollment
from openedx.custom.videos.models import PublicVideo
from edxval.api import is_video_available

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        edx_video_id = "ddd35116-faed-443a-bfd0-13177ccc5883"
        rounds = 15
        total = 0.0

        for r in range(rounds):
            start_time = time.time()
            PublicVideo.objects.filter(edx_video_id=edx_video_id).exists()
            course_videos = CourseVideo.objects.filter(video__edx_video_id=edx_video_id)
            not CourseEnrollment.objects.filter(
                course_id__in=course_videos.values_list('course_id')
            ).exists()
            not is_video_available(edx_video_id)
            total += time.time() - start_time
            print("Round {}: {} seconds ---".format(r+1, time.time() - start_time))

        print("-" * 15)
        print("Average --- {} seconds ---".format(round(total/rounds, 4)))
