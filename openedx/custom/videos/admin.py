"""
Django admin page to manage Videos
"""

from django.contrib import admin
from .models import PublicVideo

@admin.register(PublicVideo)
class PublicVideoAdmin(admin.ModelAdmin):
    list_display = ('edx_video_id', 'created',)
    search_fields = ('edx_video_id',)
    autocomplete_fields = ('video',)

