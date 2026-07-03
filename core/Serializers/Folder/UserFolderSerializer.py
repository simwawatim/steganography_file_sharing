from rest_framework import serializers
from core.models import UserFolder


class UserFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFolder
        fields = ["id", "folder_name", "created_at"]
        read_only_fields = ["id", "created_at"]