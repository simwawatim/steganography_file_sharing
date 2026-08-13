import uuid

from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from core.models import SharedFile
from core.Utils.Encryption.Main import SteganographyManager


def share_file_with_secret(sender, recipient_username, file_obj, message, can_download=True):

    recipient = User.objects.filter(username=recipient_username).first()
    if recipient is None:
        raise ValueError(f"No user found with username '{recipient_username}'")

    if recipient == sender:
        raise ValueError("You cannot share a file with yourself")

    if SharedFile.objects.filter(file=file_obj, shared_with=recipient).exists():
        raise ValueError("This file has already been shared with this user")

    passphrase = "12345"

    stego_manager = SteganographyManager()
    result = stego_manager.encrypt(message=message, password=passphrase)

    shared_file = SharedFile(
        file=file_obj,
        shared_by=sender,
        shared_with=recipient,
        can_download=can_download,
        encrypted_payload=result["encrypted_payload"],
    )
    shared_file.carrier_image.save(
        result["carrier_filename"],
        ContentFile(result["carrier_buffer"].read()),
        save=False,
    )
    shared_file.save()

    return shared_file, passphrase


def reveal_shared_secret(shared_file: SharedFile, passphrase: str) -> str:
    if not shared_file.carrier_image:
        raise ValueError("This shared file has no carrier image")

    stego_manager = SteganographyManager()
    shared_file.carrier_image.open("rb")
    try:
        message = stego_manager.decrypt(shared_file.carrier_image, passphrase)
    finally:
        shared_file.carrier_image.close()

    shared_file.is_read = True
    shared_file.save(update_fields=["is_read"])

    return message