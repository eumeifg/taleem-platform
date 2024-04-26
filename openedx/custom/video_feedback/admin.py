"""
Django admin page for video feedback app to manage it at high level.
"""


from django.contrib import admin

from .models import VideoRating, VideoLike


@admin.register(VideoRating)
class VideoRatingAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage user ratings on
    video in any course.
    """
    list_display = [
        'id',
        'user',
        'context_key',
        'block_key',
        'stars',
    ]

    search_fields = ['id', 'user__user_name',]


@admin.register(VideoLike)
class VideoLikeAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage user likes on
    video in any course.
    """
    list_display = [
        'id',
        'user',
        'context_key',
        'block_key',
        'like',
    ]

    search_fields = ['id', 'user__user_name',]

