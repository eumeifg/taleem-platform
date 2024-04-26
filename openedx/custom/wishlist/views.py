# -*- coding: UTF-8 -*-
"""
API end-points for Wishlist management.
"""
import logging

from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView

from edx_rest_framework_extensions.paginators import DefaultPagination
from openedx.core.lib.api.view_utils import view_auth_classes
from opaque_keys.edx.keys import CourseKey

from .serializers import WishlistSerializer
from .models import Wishlist

log = logging.getLogger(__name__)


class WishlistPagination(DefaultPagination):
    """
    Paginator for wishlist API.
    """
    page_size = 10
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        response = super(WishlistPagination, self).get_paginated_response(data)

        # Add `current_page` value, it's needed for pagination footer.
        response.data["current_page"] = self.page.number

        # Add `start` value, it's needed for the pagination header.
        response.data["start"] = (self.page.number - 1) * self.get_page_size(self.request)

        return response


@view_auth_classes(is_authenticated=True)
class WishlistAPIView(ListAPIView):
    """REST endpoints for wishlist."""
    serializer_class = WishlistSerializer
    pagination_class = WishlistPagination

    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of wishlist for the current user.

        Each page in the list contains 10 wishlist courses by default. The page
        size can be altered by passing parameter "page_size=<page_size>".

        **Use Cases**

           Request the list of courses added to wishlist.

        **Example Requests**

            GET /api/wishlist/

        **Response Values**

            Body comprises a list of wishlist course objects.

        **Returns**

            * 200 on success, with a list of items in wishlist.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                    "id": 1,
                    "course": {
                        "id": "course-v1:ta3leem+d1008+2020_T2",
                        "name": "Mathematics",
                        "etc."
                    }
                    "created": "2021-06-30T14:46:11.793766+03:00"
                  }
                ]
        """
        return super(WishlistAPIView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of wishlist for the requesting user.
        """
        return Wishlist.objects.filter(user=self.request.user)


@view_auth_classes(is_authenticated=True)
class CreateWishlistAPIView(CreateAPIView):
    """This endpoint adds a course to wishlist"""
    serializer_class = WishlistSerializer

    def perform_create(self, serializer):
        user = self.request.user
        course_id = self.request.data.get('course_key')
        course_key = CourseKey.from_string(course_id)
        Wishlist.objects.get_or_create(
            user=user,
            course_key=course_key,
        )

    def get_queryset(self):
        """
        Returns queryset of wishlist for the requesting user.
        """
        return Wishlist.objects.filter(user=self.request.user)


@view_auth_classes(is_authenticated=True)
class DeleteWishlistAPIView(DestroyAPIView):
    """This endpoint allows for deletion of a specific course from the wishlist"""
    serializer_class = WishlistSerializer

    def get_object(self):
        course_id = self.request.data.get('course_key')
        course_key = CourseKey.from_string(course_id)
        return Wishlist.objects.get(
            user=self.request.user,
            course_key=course_key,
        )

    def get_queryset(self):
        """
        Returns queryset of wishlist for the requesting user.
        """
        return Wishlist.objects.filter(user=self.request.user)


