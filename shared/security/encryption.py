"""Data encryption utilities."""
from cryptography.fernet import Fernet
from shared.config import get_settings
import base64

settings = get_settings()


def _get_cipher():
    """Get Fernet cipher instance."""
    # Ensure key is 32 bytes for Fernet
    key = settings.OAUTH_ENCRYPTION_KEY.encode()
    if len(key) < 32:
        key = key.ljust(32, b"0")
    else:
        key = key[:32]
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_data(data: str) -> str:
    """Encrypt sensitive data."""
    cipher = _get_cipher()
    encrypted = cipher.encrypt(data.encode())
    return encrypted.decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    cipher = _get_cipher()
    decrypted = cipher.decrypt(encrypted_data.encode())
    return decrypted.decode()
