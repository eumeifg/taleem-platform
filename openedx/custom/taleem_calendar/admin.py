"""
Django admin page for taleem calendar to manage at high level.
"""


from django.contrib import admin

from openedx.custom.taleem_calendar.models import Ta3leemReminder, CalendarEvent


@admin.register(Ta3leemReminder)
class Ta3leemReminderAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage ta3leem reminders.
    """
    list_display = [
        'id',
        'type',
        'identifier',
        'message',
        'time'
    ]

    search_fields = ['id', 'identifier', 'message']


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage ta3leem reminders.
    """
    list_display = [
        'title',
        'time',
        'created_by'
    ]

    search_fields = ['title', 'time', 'created_by']
