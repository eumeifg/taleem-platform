# -*- coding: UTF-8 -*-
"""
API end-points for the ebooks.
"""


import pytz
import logging
from datetime import datetime
from distutils import util

from rest_framework.generics import (
    ListAPIView, CreateAPIView,
    DestroyAPIView, UpdateAPIView,
    RetrieveAPIView,
)
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions
from rest_framework.parsers import FormParser, MultiPartParser

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.paginators import DefaultPagination
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.lib.api.authentication import BearerAuthentication

from .serializers import EBookCategorySerializer, EBookSerializer
from .models import EBookCategory, EBook
from .permissions import AuthorAllStaffAll

log = logging.getLogger(__name__)


class EBookPagination(DefaultPagination):
    """
    Paginator for ebooks API.
    """
    page_size = 10
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        response = super(EBookPagination, self).get_paginated_response(data)

        # Add `current_page` value, it's needed for pagination footer.
        response.data["current_page"] = self.page.number

        # Add `start` value, it's needed for the pagination header.
        response.data["start"] = (self.page.number - 1) * self.get_page_size(self.request)

        return response



@view_auth_classes(is_authenticated=False)
class EBookCategoryListView(ListAPIView):
    """REST endpoints for lists of ebook categories."""

    pagination_class = EBookPagination
    serializer_class = EBookCategorySerializer

    def get(self, request, *args, **kwargs):
        """
        Get a paginated list of ebook categories.

        The category names are always sorted in ascending order by name.

        Each page in the list contains 10 categories by default. The page
        size can be altered by passing parameter "page_size=<page_size>".

        **Use Cases**

           Request information on ebook categories.

        **Example Requests**

            GET /api/ebooks/categories/

        **Response Values**

            Body comprises a list of category names.

        **Returns**

            * 200 on success, with a list of ebook categories.
            * 400 if an invalid parameter was sent

            Example response:

                [
                  {
                    "id": 1,
                    "name": "Fiction",
                    "name_ar": "خيالي"
                  }
                ]
        """
        return super(EBookCategoryListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Returns queryset of ebook categories for GET requests.

        The results will only include ebook categories.
        """
        return EBookCategory.objects.all().order_by('name')


class ListEBookAPIView(ListAPIView):
    """This endpoint list all of the available EBooks from the database"""
    queryset = EBook.objects.all()
    serializer_class = EBookSerializer
    pagination_class = EBookPagination

    def get_queryset(self):
        """
        Optionally restricts the returned ebooks to a given author username,
        by filtering against a `author` query parameter in the URL.
        """
        queryset = EBook.objects.all()
        author = self.request.query_params.get('author')
        if author is not None:
            queryset = queryset.filter(author__user__username=author)
        return queryset


class CreateEBookAPIView(CreateAPIView):
    """This endpoint allows for creation of a EBook"""
    queryset = EBook.objects.all()
    authentication_classes = (
        JwtAuthentication, BearerAuthentication, SessionAuthentication
    )
    permission_classes = (AuthorAllStaffAll,)
    parser_classes = (MultiPartParser, FormParser,)
    serializer_class = EBookSerializer

    def perform_create(self, serializer):
        user = self.request.user
        published_on = None
        if util.strtobool(self.request.data.get('published', 'false')):
            published_on = datetime.now(tz=pytz.UTC)

        serializer.save(
            author=user.ta3leem_profile,
            published_on=published_on,
        )


class UpdateEBookAPIView(UpdateAPIView):
    """This endpoint allows for updating a specific EBook by passing in the id of the EBook to update"""
    queryset = EBook.objects.all()
    authentication_classes = (
        JwtAuthentication, BearerAuthentication, SessionAuthentication
    )
    permission_classes = (AuthorAllStaffAll,)
    parser_classes = (MultiPartParser, FormParser,)
    serializer_class = EBookSerializer

    def perform_update(self, serializer):
        user = self.request.user
        published_on = None
        if util.strtobool(self.request.data.get('published', 'false')):
            published_on = datetime.now(tz=pytz.UTC)

        serializer.save(
            author=user.ta3leem_profile,
            published_on=published_on,
        )


class DeleteEBookAPIView(DestroyAPIView):
    """This endpoint allows for deletion of a specific EBook from the database"""
    queryset = EBook.objects.all()
    authentication_classes = (
        JwtAuthentication, BearerAuthentication, SessionAuthentication
    )
    permission_classes = (AuthorAllStaffAll,)
    serializer_class = EBookSerializer


class RetrieveEBookAPIView(RetrieveAPIView):
    """This endpoint allows to retrieve a specific EBook from the database"""
    queryset = EBook.objects.all()
    authentication_classes = (
        JwtAuthentication, BearerAuthentication, SessionAuthentication
    )
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EBookSerializer
