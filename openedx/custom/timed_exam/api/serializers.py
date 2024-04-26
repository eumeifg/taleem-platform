"""
exam Serializers.
"""


from rest_framework import serializers
from django.utils import timezone

from opaque_keys.edx.keys import CourseKey

from openedx.custom.timed_exam.models import TimedExam


class ExamSerializer(serializers.ModelSerializer):  # pylint: disable=abstract-method
    """
    Serializer for timed exam objects.
    """
    duration = serializers.SerializerMethodField('duration_minutes')
    attempted = serializers.SerializerMethodField('has_attempted')
    attempted_on = serializers.SerializerMethodField('attempt_time')
    total_questions = serializers.SerializerMethodField('count_questions')
    tag = serializers.SerializerMethodField('attempt_status_tag')
    show_popup = serializers.SerializerMethodField('has_timedout_notice')

    def duration_minutes(self, exam):
        hh, mm = exam.allotted_time.split(":")
        return int(hh) * 60 + int(mm)

    def count_questions(self, exam):
        return sum(exam.count_questions)

    def has_attempted(self, exam):
        return exam.key in self.context['attempts']

    def attempt_time(self, exam):
        return self.context['attempts'].get(exam.key, '')

    def attempt_status_tag(self, exam):
        if self.context['requested_status'] == 'upcoming':
            return None
        attempted = self.context['attempts'].get(exam.key)
        if self.context['requested_status'] == 'ongoing':
            return attempted and 'completed' or None
        if self.context['requested_status'] == 'passed':
            return attempted and 'completed' or 'missed'
        else:
            return (
                attempted and 'completed' or \
                exam.due_date < timezone.now() and 'missed' or \
                None
            )

    def has_timedout_notice(self, exam):
        return exam.key in self.context['dangling']

    class Meta(object):
        """ Serializer metadata. """
        model = TimedExam
        fields = ('key', 'display_name', 'due_date', 'release_date',
            'duration', 'mode', 'attempted', 'attempted_on',
            'total_questions', 'tag', 'show_popup', 'exam_url', )

