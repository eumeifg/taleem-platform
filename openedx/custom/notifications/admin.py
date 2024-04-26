"""
Django admin page for notifications to manage at high level.
Usecase: Manage notifications on behalf of users.
"""


from django.contrib import admin

from .models import (
    NotificationMessage,
    EventReminderSettings,
    MutedPost,
    NotificationPreference,
)


@admin.register(NotificationMessage)
class NotificationMessageAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage user notifications.
    """
    list_display = [
        'id',
        'user',
        'message',
        'read',
        'modified',
    ]

    search_fields = ['id', 'title', 'message']


@admin.register(MutedPost)
class MutedPostAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage user optouts.
    """
    list_display = ('id', 'user', 'course_id', 'post_id', )
    list_filter = ('course_id', )
    autocomplete_fields  = ('user', )
    search_fields = ('id', 'user', 'course_id', 'post_id', )


@admin.register(EventReminderSettings)
class EventReminderSettingsAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage user notifications.
    """
    list_display = [
        'id',
        'course_reminder_time',
        'exam_reminder_time',
        'live_class_reminder_time',
        'enabled'
    ]


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage user optouts.
    """
    list_display = (
        'user', 'receive_on', 'added_discussion_post',
        'added_discussion_comment', 'asked_question',
        'replied_on_question', 'asked_private_question',
        'replied_on_private_question',
    )
    list_filter = (
        'receive_on', 'added_discussion_post',
        'added_discussion_comment', 'asked_question',
        'replied_on_question', 'asked_private_question',
        'replied_on_private_question',
    )
    autocomplete_fields  = ('user', )
    search_fields = ('id', 'user', )
