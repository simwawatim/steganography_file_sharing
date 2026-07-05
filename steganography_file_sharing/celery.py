import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "steganography_file_sharing.settings")

app = Celery("steganography_file_sharing")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()