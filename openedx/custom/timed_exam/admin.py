"""
Admin definitions for timed exam.
"""
from django.contrib import admin
from django.conf.urls import url

from .models import (
    TimedExam, QuestionSet, TimedExamExtras,
    PendingTimedExamUser, TimedExamAttempt,
    TimedExamAlarms, TimedExamAlarmConfiguration,
    TimedExamHide, ExamTimedOutNotice
)
from .constants import TIMED_EXAM_ALARM_CONFIGURATION_URL_NAME
from .views import TimedExamAlarmConfigurationView


@admin.register(TimedExam)
class TimedExamAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage timed exams.
    """
    list_display = ('id', 'display_name', 'key',
        'release_date', 'due_date', 'allotted_time',
        'external_exam_id', )
    list_filter = ('exam_type', 'mode', )
    search_fields = ('id', 'display_name', 'key', 'external_exam_id', )


@admin.register(TimedExamExtras)
class TimedExamExtrasAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage timed exams extras.
    """
    list_display = ('id', 'timed_exam',)
    search_fields = ('id', 'timed_exam', )


@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    search_fields = ('id', 'course_id', 'user__username',)
    list_display = ('user_id', 'course_id', 'easy_questions',
        'moderate_questions', 'hard_questions',)
    list_filter = ('course_id', )
    autocomplete_fields  = ('user', )


@admin.register(PendingTimedExamUser)
class PendingTimedExamUserAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage pending timed exam users.
    """
    list_display = ('id', 'user_email', 'timed_exam')
    search_fields = ('id', 'user_email', )


@admin.register(TimedExamAttempt)
class TimedExamAttemptAdmin(admin.ModelAdmin):
    """
    Simple, admin page to view timed exam attempts.
    """
    list_display = ('id', 'user', 'timed_exam_id', 'created')
    search_fields = ('id', 'user__email', 'user__name', 'timed_exam_id', )


@admin.register(TimedExamAlarms)
class TimedExamAlarmsAdmin(admin.ModelAdmin):
    """
    Simple, admin page to view timed exam attempts.
    """
    list_display = ('id', 'user', 'timed_exam_id', 'created', 'alarm_time', 'remaining_time_message', 'is_active')
    search_fields = ('id', 'user__email', 'user__name', 'timed_exam_id', )
    autocomplete_fields  = ('user', )


@admin.register(TimedExamAlarmConfiguration)
class TimedExamAlarmConfigurationAdmin(admin.ModelAdmin):
    """
    Simple, admin page to view timed  exam alarm configurations.
    """
    list_display = ('id', 'user', 'alarm_time', 'is_active', 'created', 'modified')
    search_fields = ('id', 'user__email', 'user__name', 'alarm_time', )
    ordering = ('-is_active', 'alarm_time',)
    readonly_fields = ('user', )

    def get_urls(self):
        """
        Returns the additional urls used by the custom object tools.
        """
        additional_urls = [
            url(
                r"^([^/]+)/timed-exam-alarm-configuration$",
                self.admin_site.admin_view(TimedExamAlarmConfigurationView.as_view()),
                name=TIMED_EXAM_ALARM_CONFIGURATION_URL_NAME
            ),
        ]
        return additional_urls + super().get_urls()

    def add_view(self, request, form_url='', extra_context=None):
        return TimedExamAlarmConfigurationView.as_view()(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(TimedExamHide)
class TimedExamHideAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage timed exams hide.
    """
    list_display = ('user', 'timed_exam',)


@admin.register(ExamTimedOutNotice)
class ExamTimedOutNoticeAdmin(admin.ModelAdmin):
    """
    Admin interface to see user notices
    """
    list_display = ('key', 'user_id', )
    search_fields = ('key', 'user_id', )
