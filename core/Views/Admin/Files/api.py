from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import UserFile

from core.Utils.Logs.Decorators import log_activity


class IsSuperUser(BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


def full_name(user) -> str:
    name = f"{user.first_name} {user.last_name}".strip()
    return name or user.username


def humanize_bytes(total_bytes: int) -> str:
    size = float(total_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


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


class FilesListView(APIView):
    """
    Powers the Files tab: stat cards (Total Files / Hidden / Shared /
    Storage Used) plus the paginated "All Files" table.

    A file's displayed status is derived, not stored: "Shared" means it has
    at least one SharedFile row, "Hidden" means it doesn't (i.e. still
    private). That matches the two badge states the Files table shows.
    """

    permission_classes = [IsAuthenticated, IsSuperUser]

    @log_activity("admin.files.view", description="Admin viewed all-files list")
    def get(self, request):
        completed = UserFile.objects.all()

        total_files = completed.count()
        shared_ids = set(
            completed.filter(shares__isnull=False).distinct().values_list("id", flat=True)
        )
        shared_count = len(shared_ids)
        hidden_count = total_files - shared_count

        storage_bytes = 0
        for uf in completed.only("file"):
            try:
                storage_bytes += uf.file.size
            except (FileNotFoundError, ValueError):
                continue

        page, page_size = parse_pagination(request)
        offset = (page - 1) * page_size

        queryset = completed.select_related("user").order_by("-uploaded_at")
        page_items = queryset[offset : offset + page_size]

        results = []
        for uf in page_items:
            try:
                size_bytes = uf.file.size
            except (FileNotFoundError, ValueError):
                size_bytes = 0
            results.append({
                "id": uf.id,
                "name": uf.original_name or uf.file.name,
                "owner": full_name(uf.user),
                "size": humanize_bytes(size_bytes),
                "status": "Shared" if uf.id in shared_ids else "Hidden",
                "uploaded": uf.uploaded_at.strftime("%d %b %Y"),
            })

        total_pages = (total_files + page_size - 1) // page_size if page_size else 1

        return Response({
            "status": "success",
            "message": "Files retrieved",
            "data": {
                "stats": {
                    "total_files": total_files,
                    "hidden": hidden_count,
                    "shared": shared_count,
                    "storage_used_bytes": storage_bytes,
                    "storage_used_display": humanize_bytes(storage_bytes),
                },
                "files": results,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total_files,
                    "total_pages": total_pages,
                },
            },
        })