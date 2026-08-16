from rest_framework import serializers
from core.models import ActivityLog


class ActivityLogListSerializer(serializers.ModelSerializer):
    """
    Basic info only - powers the Activity Log list/table view.
    Deliberately excludes ip_address, target, and metadata;
    use ActivityLogDetailSerializer for the full picture on one entry.
    """
    user = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "user",
            "action",
            "description",
            "status",
            "created_at",
        ]

    def get_user(self, obj):
        if not obj.user:
            return None
        name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "name": name or obj.user.username,
        }


class ActivityLogDetailSerializer(serializers.ModelSerializer):
    """Full detail for a single log entry - IP, generic-FK target, raw metadata."""
    user = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "user",
            "action",
            "description",
            "status",
            "ip_address",
            "target",
            "metadata",
            "created_at",
        ]

    def get_user(self, obj):
        if not obj.user:
            return None
        name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return {
            "id": obj.user.id,
            "username": obj.user.username,
            "email": obj.user.email,
            "name": name or obj.user.username,
        }

    def get_target(self, obj):
        if not obj.content_type or not obj.object_id:
            return None
        return {
            "type": obj.content_type.model,
            "id": obj.object_id,
            "display": str(obj.target) if obj.target else None,
        }