from django.contrib.auth.models import User
from django.db import models

def userFileUploadPath(instance, filename):
    return f"users/user_{instance.user.id}/folders/{instance.folder.id}/{filename}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.user.username



class UserFolder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.folder_name} ({self.user.username})"
    





class UserFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(UserFolder, on_delete=models.CASCADE, related_name="files")

    file = models.FileField(upload_to=userFileUploadPath)
    original_name = models.CharField(max_length=255, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.original_name:
            self.original_name = self.file.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.original_name or self.file.name