from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from core.models import ActivityLog
from core.Serializers.Logs.ActivityLogSerializer import (
    ActivityLogListSerializer,
    ActivityLogDetailSerializer,
)
from core.Utils.Logs.Decorators import log_activity


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


def parse_pagination(request, default_size=20, max_size=100):
    try:
        page = max(int(request.query_params.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        page_size = min(max(int(request.query_params.get("page_size", default_size)), 1), max_size)
    except ValueError:
        page_size = default_size
    return page, page_size


@extend_schema(
    tags=["Activity Logs"],
    parameters=[
        OpenApiParameter(name="page", type=int, description="Page number"),
        OpenApiParameter(name="page_size", type=int, description="Items per page"),
        OpenApiParameter(name="action", type=str, description="Filter by exact action code, e.g. file.upload"),
        OpenApiParameter(name="status", type=str, description="Filter by status: success or failure"),
        OpenApiParameter(name="user_id", type=int, description="Filter by user ID"),
    ],
    responses={200: ActivityLogListSerializer(many=True)},
    description="Paginated list of activity logs - basic info only. Use the detail endpoint for the full picture on a single entry.",
)
class ActivityLogListView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    @log_activity("admin.logs.list", description="Admin viewed activity log list")
    def get(self, request):
        logs_qs = ActivityLog.objects.select_related("user").all()

        action = request.query_params.get("action")
        if action:
            logs_qs = logs_qs.filter(action=action)

        status_filter = request.query_params.get("status")
        if status_filter in (ActivityLog.ActionStatus.SUCCESS, ActivityLog.ActionStatus.FAILURE):
            logs_qs = logs_qs.filter(status=status_filter)

        user_id = request.query_params.get("user_id")
        if user_id:
            logs_qs = logs_qs.filter(user_id=user_id)

        total = logs_qs.count()

        page, page_size = parse_pagination(request)
        offset = (page - 1) * page_size
        page_items = logs_qs[offset : offset + page_size]

        serializer = ActivityLogListSerializer(page_items, many=True)

        total_pages = (total + page_size - 1) // page_size if page_size else 1

        return Response({
            "status": "success",
            "message": "Activity logs retrieved successfully",
            "data": {
                "logs": serializer.data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                },
            },
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Activity Logs"],
    responses={200: ActivityLogDetailSerializer},
    description="Full detail for a single activity log entry - IP address, the generic-FK target object, and raw metadata.",
)
class ActivityLogDetailView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    @log_activity(
        "admin.logs.view",
        description=lambda req, res: f"Admin viewed activity log {req.parser_context['kwargs'].get('pk')}",
    )
    def get(self, request, pk):
        try:
            log = ActivityLog.objects.select_related("user", "content_type").get(pk=pk)
        except ActivityLog.DoesNotExist:
            return Response(
                {
                    "status": "fail",
                    "message": "Activity log not found",
                    "data": None,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ActivityLogDetailSerializer(log)

        return Response({
            "status": "success",
            "message": "Activity log retrieved successfully",
            "data": serializer.data,
        }, status=status.HTTP_200_OK)