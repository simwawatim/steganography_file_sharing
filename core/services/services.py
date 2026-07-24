from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from core.models import SharedFile, UserFile
from core.services.crypto_utils import (
    hybrid_encrypt,
    hybrid_decrypt,
    hide_secret_in_image,
    extract_secret_from_image,
)
from PIL import Image
import io


def share_file_with_secret(
    sender,
    recipient_username,
    file_obj,
    message,
    carrier_image_file,
    can_download=True
):
    recipient = User.objects.get(username=recipient_username)

    # 1. Encrypt message for recipient
    encrypted_secret = hybrid_encrypt(
        message,
        recipient.userprofile.public_key
    )

    # 2. Load image
    image = Image.open(carrier_image_file)

    # 3. Hide encrypted secret inside image (JSON-wrapped)
    stego_image = hide_secret_in_image(image, encrypted_secret)

    # 4. Save image into memory buffer
    buffer = io.BytesIO()
    stego_image.save(buffer, format="PNG")
    buffer.seek(0)

    # 5. Create DB record (NO encrypted_payload anymore)
    shared_file = SharedFile(
        file=file_obj,
        shared_by=sender,
        shared_with=recipient,
        can_download=can_download,
    )

    shared_file.carrier_image.save(
        f"stego_{sender.id}_{recipient.id}_{file_obj.id}.png",
        ContentFile(buffer.read()),
        save=False
    )

    shared_file.save()
    return shared_file



def read_shared_secret(shared_file: SharedFile, raw_private_key_pem: str) -> str:
    """
    Extracts hidden encrypted secret from image,
    then decrypts it for the recipient.
    """

    image = Image.open(shared_file.carrier_image.path)

    # 1. Extract encrypted secret from image
    encrypted_secret = extract_secret_from_image(image)

    # 2. Decrypt message
    message = hybrid_decrypt(encrypted_secret, raw_private_key_pem)

    # 3. Mark as read
    shared_file.is_read = True
    shared_file.save(update_fields=["is_read"])

    return message