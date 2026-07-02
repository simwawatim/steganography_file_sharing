from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import serializers
from core.models import UserProfile


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )

        UserProfile.objects.create(
            user=user
        )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"]
        )

        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile_picture",
        ]

    def get_profile_picture(self, obj):
        request = self.context.get("request")

        try:
            if obj.userprofile.profile_picture:
                return request.build_absolute_uri(
                    obj.userprofile.profile_picture.url
                )
        except UserProfile.DoesNotExist:
            pass

        return None