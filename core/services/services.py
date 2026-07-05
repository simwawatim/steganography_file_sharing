# core/services.py
from .crypto_utils import hybrid_encrypt, hybrid_decrypt, hide_data_in_image, extract_data_from_image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from core.models import SharedFile, UserFile
from PIL import Image
import io






def share_file_with_secret(sender: User, recipient_username: str, file_obj: UserFile,
                            message: str, carrier_image_file, can_download: bool = True) -> SharedFile:
    recipient = User.objects.get(username=recipient_username)

    encrypted_payload = hybrid_encrypt(message, recipient.userprofile.public_key)

    image = Image.open(carrier_image_file)
    stego_image = hide_data_in_image(image, encrypted_payload.encode())

    buffer = io.BytesIO()
    stego_image.save(buffer, format="PNG")  
    buffer.seek(0)

    shared_file = SharedFile(
        file=file_obj,
        shared_by=sender,
        shared_with=recipient,
        can_download=can_download,
        encrypted_payload=encrypted_payload,
    )
    shared_file.carrier_image.save(
        f"stego_{sender.id}_{recipient.id}_{file_obj.id}.png",
        ContentFile(buffer.read()),
        save=False,
    )
    shared_file.save()
    return shared_file


def read_shared_secret(shared_file: SharedFile, raw_private_key_pem: str) -> str:
    image = Image.open(shared_file.carrier_image.path)
    extracted = extract_data_from_image(image)
    message = hybrid_decrypt(extracted.decode(), raw_private_key_pem)
    shared_file.is_read = True
    shared_file.save(update_fields=["is_read"])
    return message