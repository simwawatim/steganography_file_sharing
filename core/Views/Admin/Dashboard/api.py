from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import UserFile, SharedFile

from core.Utils.Logs.Decorators import log_activity


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


def full_name(user: User) -> str:
    name = f"{user.first_name} {user.last_name}".strip()
    return name or user.username


def humanize_when(moment) -> str:
    """
    Compact relative time - '2h ago', '1d ago', 'just now' - matching the
    dashboard's WHEN column. Django's own timesince() gives longer output
    like '2 hours, 15 minutes', which doesn't fit this UI.
    """
    seconds = int((timezone.now() - moment).total_seconds())

    if seconds < 60:
        return "just now"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 30:
        return f"{days}d ago"
    months = days // 30
    if months < 12:
        return f"{months}mo ago"
    years = days // 365
    return f"{years}y ago"


def humanize_bytes(total_bytes: int) -> str:
    """Binary units, one decimal - matches the dashboard's '2.4 GB' style."""
    size = float(total_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


class AdminDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    @log_activity("admin.dashboard.view", description="Admin viewed platform dashboard stats")
    def get(self, request):
        completed_files = UserFile.objects.all()

        files_hidden = completed_files.count()
        active_shares = SharedFile.objects.filter(can_download=True).count()
        extractions = SharedFile.objects.filter(is_read=True).count()
        storage_bytes = 0
        for uf in completed_files.only("file"):
            try:
                storage_bytes += uf.file.size
            except (FileNotFoundError, ValueError):
                continue

        recent_activity = []

        for uf in completed_files.select_related("user").order_by("-uploaded_at")[:10]:
            recent_activity.append({
                "file": uf.original_name or uf.file.name,
                "action": "Hidden",
                "by": full_name(uf.user),
                "when": humanize_when(uf.uploaded_at),
                "_ts": uf.uploaded_at,
            })

        for sf in (
            SharedFile.objects.select_related("shared_by", "shared_with", "file")
            .order_by("-shared_at")[:10]
        ):
            recent_activity.append({
                "file": sf.file.original_name or sf.file.file.name,
                "action": "Shared",
                "by": full_name(sf.shared_by),
                "when": humanize_when(sf.shared_at),
                "_ts": sf.shared_at,
            })

        for sf in (
            SharedFile.objects.filter(is_read=True)
            .select_related("shared_with", "file")
            .order_by("-shared_at")[:10]
        ):
            ts = getattr(sf, "read_at", None) or sf.shared_at
            recent_activity.append({
                "file": sf.file.original_name or sf.file.file.name,
                "action": "Extracted",
                "by": full_name(sf.shared_with),
                "when": humanize_when(ts),
                "_ts": ts,
            })

        recent_activity.sort(key=lambda row: row["_ts"], reverse=True)
        for row in recent_activity:
            del row["_ts"]

        return Response({
            "status": "success",
            "message": "Dashboard stats retrieved",
            "data": {
                "stats": {
                    "files_hidden": files_hidden,
                    "active_shares": active_shares,
                    "extractions": extractions,
                    "storage_used_bytes": storage_bytes,
                    "storage_used_display": humanize_bytes(storage_bytes),
                },
                "recent_activity": recent_activity[:10],
            },
        })