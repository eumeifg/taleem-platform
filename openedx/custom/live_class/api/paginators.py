"""
Paginators for the live course enrollment related views.
"""

from edx_rest_framework_extensions.paginators import DefaultPagination


class LiveCoursePagination(DefaultPagination):
    """
    Paginator for live course API.
    """
    page_size = 10
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        response = super(LiveCoursePagination, self).get_paginated_response(data)

        # Add `current_page` value, it's needed for pagination footer.
        response.data["current_page"] = self.page.number

        # Add `start` value, it's needed for the pagination header.
        response.data["start"] = (self.page.number - 1) * self.get_page_size(self.request)

        return response

