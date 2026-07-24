from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet
from PIL import Image
import base64
import json


# =========================
# KEY HANDLING
# =========================

def load_public_key(pem_str: str):
    return serialization.load_pem_public_key(pem_str.encode())


def load_private_key(pem_str: str):
    return serialization.load_pem_private_key(pem_str.encode(), password=None)


# =========================
# HYBRID ENCRYPTION
# =========================

def hybrid_encrypt(message: str, recipient_public_key_pem: str) -> str:
    session_key = Fernet.generate_key()
    ciphertext = Fernet(session_key).encrypt(message.encode())

    public_key = load_public_key(recipient_public_key_pem)

    encrypted_session_key = public_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    packed = (
        len(encrypted_session_key).to_bytes(2, "big")
        + encrypted_session_key
        + ciphertext
    )

    return base64.b64encode(packed).decode()


def hybrid_decrypt(payload_b64: str, private_key_pem: str) -> str:
    print(f"Payload received for decryption: {payload_b64}")  # Debugging line
    packed = base64.b64decode(payload_b64.encode())

    key_len = int.from_bytes(packed[:2], "big")
    encrypted_session_key = packed[2:2 + key_len]
    ciphertext = packed[2 + key_len:]

    private_key = load_private_key(private_key_pem)

    session_key = private_key.decrypt(
        encrypted_session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return Fernet(session_key).decrypt(ciphertext).decode()


# =========================
# STEGANOGRAPHY CORE
# =========================

def _bytes_to_bits(data: bytes) -> str:
    return "".join(f"{byte:08b}" for byte in data)


def _bits_to_bytes(bits: str) -> bytes:
    return bytes(
        int(bits[i:i + 8], 2)
        for i in range(0, len(bits), 8)
    )


def hide_data_in_image(image: Image.Image, data: bytes) -> Image.Image:
    image = image.convert("RGB")

    payload = len(data).to_bytes(4, "big") + data
    bits = _bytes_to_bits(payload)

    pixels = list(image.getdata())
    capacity_bits = len(pixels) * 3

    if len(bits) > capacity_bits:
        raise ValueError("Carrier image too small for payload.")

    bit_index = 0
    new_pixels = []

    for pixel in pixels:
        r, g, b = pixel

        r = (r & ~1) | int(bits[bit_index]) if bit_index < len(bits) else r
        bit_index += 1

        g = (g & ~1) | int(bits[bit_index]) if bit_index < len(bits) else g
        bit_index += 1

        b = (b & ~1) | int(bits[bit_index]) if bit_index < len(bits) else b
        bit_index += 1

        new_pixels.append((r, g, b))

    stego = Image.new("RGB", image.size)
    stego.putdata(new_pixels)
    return stego


def extract_data_from_image(image: Image.Image) -> bytes:
    image = image.convert("RGB")

    bits = "".join(
        str(channel & 1)
        for pixel in image.getdata()
        for channel in pixel
    )

    data_len = int(bits[:32], 2)
    data_bits = bits[32:32 + data_len * 8]

    return _bits_to_bytes(data_bits)


# =========================
# NEW CLEAN SECRET LAYER
# =========================

def hide_secret_in_image(image: Image.Image, encrypted_secret: str) -> Image.Image:
    payload = {
        "secret": encrypted_secret
    }
    return hide_data_in_image(image, json.dumps(payload).encode("utf-8"))


def extract_secret_from_image(image: Image.Image) -> str:
    raw = extract_data_from_image(image)

    try:
        decoded = raw.decode("utf-8", errors="ignore")
        payload = json.loads(decoded)
    except Exception as e:
        raise ValueError(f"Stego decode failed: {str(e)}")

    secret = payload.get("secret")

    if not secret:
        raise ValueError("No secret key in payload")

    return secret