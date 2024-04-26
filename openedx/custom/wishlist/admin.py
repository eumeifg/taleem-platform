"""
Django admin page for Wishlist to manage at high level.
Usecase: Manage wishlist on behalf of users.
"""


from django.contrib import admin

from .models import Wishlist


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage user's
    favourite courses.
    """
    list_display = [
        'id',
        'user',
        'course_key',
        'created',
    ]

    search_fields = [
        'id',
        'user__user_name',
        'course_key'
    ]

