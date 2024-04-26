"""
ebook API permissions.
"""

from rest_framework import permissions
from openedx.custom.taleem.utils import user_is_teacher


class AuthorAllStaffAll(permissions.BasePermission):

    edit_methods = ("PUT", "PATCH")

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.is_staff:
            return True

        if user_is_teacher(request.user):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser or request.user.is_staff:
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        if obj.author.user == request.user:
            return True

        return False
