from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 10000

    def get_paginated_response(self, data):
        return Response({
            'total': self.page.paginator.count,
            'page_count': self.page.paginator.num_pages,
            'data': data
        })
