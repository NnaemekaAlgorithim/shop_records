from rest_framework.pagination import PageNumberPagination
from user_management.apps.base.utils.response_structure import api_response


class CustomPagination(PageNumberPagination):
    page_size = 10  # Set the default page size
    page_size_query_param = 'page_size'  # Allow the client to control page size with a query parameter
    max_page_size = 100  # Set a limit to prevent large responses

    def get_paginated_response(self, data, description="Paginated results"):
        return api_response(
            response_status='success',
            response_description=description,
            response_data={
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "result": data
            }
        )
