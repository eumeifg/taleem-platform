"""
Django admin page for Timed Notes to manage at high level.
Usecase: Manage notes on behalf of users.
"""


from django.contrib import admin

from .models import TimedNote


@admin.register(TimedNote)
class TimedNoteAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage user notes on
    video play time in any course.
    """
    list_display = [
        'id',
        'user',
        'context_key',
        'block_key',
        'taken_at',
        'note',
    ]

    search_fields = ['id', 'user__user_name', 'note']

