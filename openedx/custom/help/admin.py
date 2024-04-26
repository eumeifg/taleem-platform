"""
Django admin page to manage help topics
"""


from django.contrib import admin

from .models import HelpTopic


@admin.register(HelpTopic)
class HelpTopicAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage help topics.
    """
    list_display = [
        'role',
        'title_english',
        'created',
    ]

    search_fields = [
        'role',
        'title_english'
    ]

    list_filter = ['role']

