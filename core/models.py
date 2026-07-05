from django.contrib.auth.models import User
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


def encrypt(data: str) -> str:
    f = Fernet(settings.FERNET_KEY)
    return f.encrypt(data.encode()).decode()


def decrypt(data: str) -> str:
    f = Fernet(settings.FERNET_KEY)
    return f.decrypt(data.encode()).decode()


def userFileUploadPath(instance, filename):
    return f"users/user_{instance.user.id}/folders/{instance.folder.id}/{filename}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    public_key = models.TextField(blank=True, null=True)

    _private_key = models.TextField(
        db_column="private_key",
        blank=True,
        null=True
    )

    def set_private_key(self, raw_key: str):
        self._private_key = encrypt(raw_key)

    def get_private_key(self):
        if self._private_key:
            return decrypt(self._private_key)
        return None

    def __str__(self):
        return self.user.username



class UserFolder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.folder_name} ({self.user.username})"
    





class UserFile(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(UserFolder, on_delete=models.CASCADE, related_name="files")

    file = models.FileField(upload_to=userFileUploadPath)
    original_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )


    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.original_name:
            self.original_name = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name or self.file.name
    



class SharedFile(models.Model):
    file = models.ForeignKey(UserFile, on_delete=models.CASCADE, related_name="shares")
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared_files_sent")
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared_files_received")

    can_download = models.BooleanField(default=True)
    encrypted_payload = models.TextField(blank=True, null=True)
    carrier_image = models.ImageField(upload_to="shared_files/secret_carriers/", blank=True, null=True)

    is_read = models.BooleanField(default=False)
    shared_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("file", "shared_with")

    def __str__(self):
        return f"{self.file.original_name} → {self.shared_with.username}"