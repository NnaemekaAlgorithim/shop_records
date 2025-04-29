from rest_framework.response import Response
from rest_framework import status


def api_response(response_status, response_description, response_data=None):
    """
    Format all responses to follow the given pattern.
    """
    return Response(
        {
            "response status": response_status,
            "response description": response_description,
            "response data": response_data or {}
        },
        status=status.HTTP_200_OK if response_status == "success" else status.HTTP_400_BAD_REQUEST,
    )
