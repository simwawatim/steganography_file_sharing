from cryptography.fernet import Fernet
from django.conf import settings
from stegano import lsb
from PIL import Image
import hashlib
import base64
import uuid
import os
import io


class SteganographyManager:
    BASE_IMAGE_PATH = os.path.join(
        settings.BASE_DIR, "core", "Utils", "Encryption", "base-image.jpg"
    )

    def password_to_key(self, password: str) -> bytes:
        digest = hashlib.sha256(password.encode()).digest()
        return base64.urlsafe_b64encode(digest)

    def encrypt(self, message: str, password: str) -> dict:
        if not message:
            raise ValueError("message must not be empty")
        if not password:
            raise ValueError("password must not be empty")
        if not os.path.exists(self.BASE_IMAGE_PATH):
            raise FileNotFoundError(
                f"Base carrier image not found at {self.BASE_IMAGE_PATH}"
            )

        key = self.password_to_key(password)
        cipher = Fernet(key)
        encrypted_message = cipher.encrypt(message.encode()).decode()

        secret_image = lsb.hide(self.BASE_IMAGE_PATH, encrypted_message)

        buffer = io.BytesIO()
        secret_image.save(buffer, format="PNG")
        buffer.seek(0)

        return {
            "encrypted_payload": encrypted_message,
            "carrier_filename": f"{uuid.uuid4().hex}.png",
            "carrier_buffer": buffer,
        }

    def decrypt(self, carrier_image, password: str) -> str:
        if isinstance(carrier_image, str):
            image_source = carrier_image
        else:
            image_source = Image.open(carrier_image)

        hidden_ciphertext = lsb.reveal(image_source)
        if hidden_ciphertext is None:
            raise ValueError("No hidden message found in carrier image")

        key = self.password_to_key(password)
        cipher = Fernet(key)

        try:
            return cipher.decrypt(hidden_ciphertext.encode()).decode()
        except Exception as exc:
            raise ValueError(
                "Failed to decrypt message — wrong password or corrupted payload"
            ) from exc