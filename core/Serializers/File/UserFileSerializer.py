from rest_framework import serializers
from core.models import UserFile


class UserFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFile
        fields = ["id", "file", "original_name", "uploaded_at", "folder"]
        read_only_fields = ["id", "uploaded_at", "original_name"]