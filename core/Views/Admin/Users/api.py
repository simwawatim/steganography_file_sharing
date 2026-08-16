from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from core.Utils.Logs.Decorators import log_activity


class IsSuperUser(BasePermission):
    """Same admin-only gate used across the other admin endpoints."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


def full_name(user: User) -> str:
    name = f"{user.first_name} {user.last_name}".strip()
    return name or user.username


def derive_role(user: User) -> str:
    """
    Best-effort role label from what's actually on the User model today.
    There's no dedicated role/title field on UserProfile yet, so this can't
    reproduce job-title-style labels like "Developer" or "Squad Lead" - it
    only distinguishes admin / staff / regular user. Add a `role` or `title`
    CharField to UserProfile if you want the finer-grained labels shown in
    the mockup.
    """
    if user.is_superuser:
        return "Admin"
    if user.is_staff:
        return "Staff"
    return "User"


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


class UsersListView(APIView):
    """Powers the Users tab: stat cards plus the paginated "All Users" table."""

    permission_classes = [IsAuthenticated, IsSuperUser]

    @log_activity("admin.users.view", description="Admin viewed all-users list")
    def get(self, request):
        users_qs = User.objects.all()

        total_users = users_qs.count()
        active_users = users_qs.filter(is_active=True).count()
        admins = users_qs.filter(is_superuser=True).count()

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = users_qs.filter(date_joined__gte=month_start).count()

        page, page_size = parse_pagination(request)
        offset = (page - 1) * page_size
        page_items = users_qs.order_by("-date_joined")[offset : offset + page_size]

        results = [
            {
                "id": u.id,
                "name": full_name(u),
                "email": u.email,
                "role": derive_role(u),
                "status": "Active" if u.is_active else "Inactive",
                "joined": u.date_joined.strftime("%d %b %Y"),
            }
            for u in page_items
        ]

        total_pages = (total_users + page_size - 1) // page_size if page_size else 1

        return Response({
            "status": "success",
            "message": "Users retrieved",
            "data": {
                "stats": {
                    "total_users": total_users,
                    "active": active_users,
                    "admins": admins,
                    "new_this_month": new_this_month,
                },
                "users": results,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total_users,
                    "total_pages": total_pages,
                },
            },
        })