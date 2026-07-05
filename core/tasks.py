from celery import shared_task
from PIL import Image
import os

from django.conf import settings
from core.models import UserFile


@shared_task
def processUploadedFile(file_id):
    try:
        file_obj = UserFile.objects.get(id=file_id)

        file_obj.status = UserFile.Status.PROCESSING
        file_obj.save(update_fields=["status"])

        file_path = file_obj.file.path
        ext = os.path.splitext(file_path)[1].lower()

        if ext in [".jpg", ".jpeg", ".png"]:
            img = Image.open(file_path)
            img.thumbnail((800, 800))
            img.save(file_path)

        elif ext == ".pdf":
            pass

        elif ext in [".mp4", ".mov"]:
            pass

        file_obj.status = UserFile.Status.COMPLETED
        file_obj.save(update_fields=["status"])

    except Exception as e:
        file_obj.status = UserFile.Status.FAILED
        file_obj.save(update_fields=["status"])
        raise e