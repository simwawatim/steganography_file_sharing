from rest_framework.views import exception_handler, APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenError,
)
import logging
logger = logging.getLogger(__name__)


def AuthExceptionHandler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        message = "An error occurred"

        if isinstance(exc, AuthenticationFailed):
            message = "Authentication credentials were not provided or are invalid."

        elif isinstance(exc, (InvalidToken, TokenError)):
            message = "Token is invalid or has expired."

        else:
            if isinstance(response.data, dict):
                if "detail" in response.data:
                    message = response.data["detail"]
                else:
                    first_key = next(iter(response.data))
                    error = response.data[first_key]
                    message = error[0] if isinstance(error, list) else str(error)

        response.data = {"status": "fail", "message": message, "data": None}

    return response


class BaseAPIView(APIView):

    def handle_exception_response(
        self,
        error,
        error_type="unknown",
        message=None,
        status_code=None,
        include_error=False,
    ):
        error_map = {
            "validation_error": {
                "message": "Validation failed",
                "status_code": status.HTTP_400_BAD_REQUEST,
            },
            "permission_error": {
                "message": "You do not have permission to perform this action",
                "status_code": status.HTTP_403_FORBIDDEN,
            },
            "not_found": {
                "message": "Resource not found",
                "status_code": status.HTTP_404_NOT_FOUND,
            },
            "server_error": {
                "message": "Internal server error",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
            "unknown": {
                "message": "An unexpected error occurred",
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
        }
        config = error_map.get(error_type, error_map["unknown"])

        final_message = message or config["message"]
        final_status = status_code or config["status_code"]

        logger.exception("API exception [%s]: %s", error_type, str(error))

        response_data = {
            "status": "fail",
            "message": final_message,
            "data": None,
            "error_type": error_type,
        }

        if include_error:
            response_data["error"] = str(error)

        return Response(response_data, status=final_status)