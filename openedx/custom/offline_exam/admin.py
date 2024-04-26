"""
Admin definitions for offline exam.
"""
from django.contrib import admin

from .models import OfflineExamStudentAttempt


@admin.register(OfflineExamStudentAttempt)
class OfflineExamStudentAttemptAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage offline exams.
    """
    list_display = ('id', 'user', 'timed_exam', 'started_at', 'completed_at', 'status')
    search_fields = ('id', 'user', 'timed_exam', )
    list_filter = ('timed_exam', 'status', )
    autocomplete_fields  = ('user', 'timed_exam', )

