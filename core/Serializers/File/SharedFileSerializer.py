from rest_framework import serializers
from django.contrib.auth.models import User

from core.models import SharedFile, UserFile
from core.services.crypto_utils import extract_secret_from_image, hybrid_decrypt
from PIL import Image


class ShareFileWithSecretSerializer(serializers.Serializer):

    file = serializers.PrimaryKeyRelatedField(queryset=UserFile.objects.none())
    recipient_username = serializers.CharField()
    message = serializers.CharField()
    carrier_image = serializers.ImageField()
    can_download = serializers.BooleanField(required=False, default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get("request")
        if request:
            self.fields["file"].queryset = UserFile.objects.filter(user=request.user)

    def validate_recipient_username(self, value):
        try:
            recipient = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient does not exist.")

        request = self.context["request"]

        if recipient == request.user:
            raise serializers.ValidationError("You cannot share with yourself.")

        if not hasattr(recipient, "userprofile") or not recipient.userprofile.public_key:
            raise serializers.ValidationError("Recipient has no public key.")

        return value

    def validate(self, attrs):
        request = self.context["request"]

        file_obj = attrs["file"]

        if SharedFile.objects.filter(
            file=file_obj,
            shared_with__username=attrs["recipient_username"]
        ).exists():
            raise serializers.ValidationError("Already shared with this user.")

        return attrs
    



class SharedFileSerializer(serializers.ModelSerializer):

    file_name = serializers.CharField(source="file.original_name", read_only=True)
    shared_by_username = serializers.CharField(source="shared_by.username", read_only=True)
    shared_with_username = serializers.CharField(source="shared_with.username", read_only=True)

    class Meta:
        model = SharedFile
        fields = [
            "id",
            "file",
            "file_name",
            "shared_by",
            "shared_by_username",
            "shared_with",
            "shared_with_username",
            "can_download",
            "carrier_image",
            "is_read",
            "shared_at",
        ]
        read_only_fields = fields


    


class SharedFileDetailsSerializer(serializers.ModelSerializer):

    file_name = serializers.CharField(source="file.original_name", read_only=True)
    shared_by_username = serializers.CharField(source="shared_by.username", read_only=True)
    shared_with_username = serializers.CharField(source="shared_with.username", read_only=True)

    decrypted_message = serializers.SerializerMethodField()

    class Meta:
        model = SharedFile
        fields = [
            "id",
            "file",
            "file_name",
            "shared_by",
            "shared_by_username",
            "shared_with",
            "shared_with_username",
            "can_download",
            "carrier_image",
            "is_read",
            "shared_at",
            "decrypted_message",
        ]
    def get_decrypted_message(self, obj):
        request = self.context.get("request")

        if not request or not hasattr(request.user, "userprofile"):
            return None

        try:
            image = Image.open(obj.carrier_image.path)

            print(image.format, image.size, image.mode)  # Debugging line

            # 1. Extract encrypted secret from image
            encrypted_secret = extract_secret_from_image(image)
            print(f"Encrypted secret extracted: {encrypted_secret}")  # Debugging line

            # 2. Decrypt using private key
            private_key = request.user.userprofile.get_private_key()
            print(f"Private key used for decryption: {private_key}")  # Debugging line

            return hybrid_decrypt(encrypted_secret, private_key)
        

        except Exception:
            return None