from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django.db.models import Q
from rest_framework import serializers, status

from core.models import UserFile, UserFolder, SharedFile


MAX_STORAGE_BYTES = 1 * 1024 * 1024 * 1024


def human_readable_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def file_icon_for(filename: str) -> str:
    ext = (filename or "").rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""

    mapping = {
        "mp4": "play", "mov": "play", "avi": "play", "mkv": "play",
        "jpg": "image", "jpeg": "image", "png": "image", "gif": "image", "webp": "image",
        "mp3": "musical-notes", "wav": "musical-notes", "aac": "musical-notes",
        "pdf": "document-text", "doc": "document-text", "docx": "document-text",
        "xls": "document-text", "xlsx": "document-text", "txt": "document-text",
        "zip": "archive", "rar": "archive", "7z": "archive",
    }

    return mapping.get(ext, "document")


class RecentFileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="original_name")
    size = serializers.SerializerMethodField()
    size_bytes = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    folder_id = serializers.IntegerField(source="folder.id")
    folder_name = serializers.CharField(source="folder.folder_name")

    class Meta:
        model = UserFile
        fields = [
            "id",
            "name",
            "size",
            "size_bytes",
            "icon",
            "status",
            "folder_id",
            "folder_name",
            "uploaded_at",
        ]

    def get_size(self, obj):
        try:
            return human_readable_size(obj.file.size)
        except (ValueError, OSError):
            return "0 B"

    def get_size_bytes(self, obj):
        try:
            return obj.file.size
        except (ValueError, OSError):
            return 0

    def get_icon(self, obj):
        return file_icon_for(obj.original_name or obj.file.name)


class StorageStatsSerializer(serializers.Serializer):
    used_bytes = serializers.IntegerField()
    used_readable = serializers.CharField()
    max_bytes = serializers.IntegerField()
    max_readable = serializers.CharField()
    percent_used = serializers.FloatField()


class DashboardStatsSerializer(serializers.Serializer):
    total_folders = serializers.IntegerField()
    total_files = serializers.IntegerField()
    shared_people = serializers.IntegerField()
    storage = StorageStatsSerializer()
    recent_files = RecentFileSerializer(many=True)


@extend_schema(
    tags=["Dashboard"],
    responses={200: DashboardStatsSerializer},
    description="Returns folder/file counts, shared-people count, storage usage, and the 5 most recent files for the logged-in user.",
)
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        print("User: ", user)

        total_folders = UserFolder.objects.filter(user=user).count()

        user_files = UserFile.objects.filter(user=user)
        total_files = user_files.count()

        shared_people = (
            User.objects.filter(
                Q(shared_files_received__file__user=user)
                | Q(shared_files_sent__shared_with__isnull=False, shared_files_sent__file__user=user)
            )
            .exclude(id=user.id)
            .distinct()
            .count()
        )

        used_bytes = 0
        for f in user_files.only("file"):
            try:
                used_bytes += f.file.size
            except (ValueError, OSError):
                continue

        percent_used = round((used_bytes / MAX_STORAGE_BYTES) * 100, 2) if MAX_STORAGE_BYTES else 0
        percent_used = min(percent_used, 100.0)

        recent_files = user_files.select_related("folder").order_by("-uploaded_at")[:5]

        data = {
            "total_folders": total_folders,
            "total_files": total_files,
            "shared_people": shared_people,
            "storage": {
                "used_bytes": used_bytes,
                "used_readable": human_readable_size(used_bytes),
                "max_bytes": MAX_STORAGE_BYTES,
                "max_readable": human_readable_size(MAX_STORAGE_BYTES),
                "percent_used": percent_used,
            },
            "recent_files": RecentFileSerializer(recent_files, many=True, context={"request": request}).data,
        }
        print("data: ", data)

        return Response({
            "status": "success",
            "message": "Dashboard stats retrieved successfully",
            "data": data,
        }, status=status.HTTP_200_OK)