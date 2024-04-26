"""
Admin panel to manage teachers.
"""
from django.contrib import admin

from .models import AccessRequest


@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    """
    Simple, admin page to manage teacher requests.
    """
    list_display = [
        'id',
        'first_name',
        'last_name',
        'email',
        'phone_number',
        'country',
    ]
    list_filter = ['stage',]
    search_fields = ['id', 'email', 'first_name', 'last_name']
