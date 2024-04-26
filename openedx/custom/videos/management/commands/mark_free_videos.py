"""
Script to find free chapters and mark free chapter videos
as public videos.

python manage.py lms mark_free_videos
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from edxval.models import Video
from xmodule.modulestore.django import modulestore
from openedx.custom.videos.models import PublicVideo

class Command(BaseCommand):
    def confirm(self):
        answer = ""
        while answer not in ["y", "n"]:
            answer = input("Do you want to remove dangling blocks [Y/N]? ").lower()
        return answer == "y"

    def handle(self, *args, **options):
        admin = User.objects.filter(is_superuser=True).first()
        courses_summary = modulestore().get_course_summaries()
        count = 0
        dangling = []

        for course_summary in courses_summary:
            if course_summary.location.course == 'templates' or course_summary.is_timed_exam:
                continue
            print(".", end=" ")
            course_module = modulestore().get_course(course_summary.id, depth=None)
            for section in course_module.get_children()[:3]:
                for sub_section in section.get_children():
                    for unit in sub_section.get_children():
                        for block in unit.get_children():
                            if block.category == 'video' and block.edx_video_id:
                                try:
                                    video = Video.objects.get(edx_video_id=block.edx_video_id)
                                except Exception as e:
                                    dangling.append(block.location)
                                    continue
                                PublicVideo.objects.get_or_create(video=video, edx_video_id=block.edx_video_id)
                                count += 1

        print(".")
        print("Whooo! {} videos are now public, don't complain about them :)".format(count))
        print("\n")
        print("_" * 15)
        if dangling:
            print("{} dangling video blocks found !".format(len(dangling)))
            print("A dangling video block is the one which has reference to a video which doesn't exits")
            if self.confirm():
                for dangling_item in dangling:
                    try:
                        modulestore().delete_item(dangling_item, admin.id)
                    except:
                        continue
            else:
                print("Okay no worries, keep that garbage with you :)")
        print("Done! Enjoy.")
