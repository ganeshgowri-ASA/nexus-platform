"""
Security Utilities

Provides authentication, password hashing, and encryption utilities.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from config.settings import settings
from config.logging import get_logger
from nexus.core.exceptions import AuthenticationError

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password

    Example:
        >>> hashed = get_password_hash("my_password")
        >>> print(hashed)
        $2b$12$...
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = get_password_hash("my_password")
        >>> verify_password("my_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token

    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    logger.debug("Access token created", user=data.get("sub"))
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Data to encode in the token

    Returns:
        Encoded JWT refresh token

    Example:
        >>> token = create_refresh_token({"sub": "user@example.com"})
    """
    expires_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(data, expires_delta)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        AuthenticationError: If token is invalid or expired

    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
        >>> payload = decode_access_token(token)
        >>> print(payload["sub"])
        user@example.com
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.error(f"Token decode error: {e}")
        raise AuthenticationError("Invalid or expired token")


def validate_password_strength(password: str) -> bool:
    """
    Validate password meets minimum security requirements.

    Args:
        password: Password to validate

    Returns:
        True if password is strong enough

    Example:
        >>> validate_password_strength("weak")
        False
        >>> validate_password_strength("StrongPass123!")
        True
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False

    # Check for at least one uppercase, lowercase, digit, and special character
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    return has_upper and has_lower and has_digit and has_special


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        Random API key string

    Example:
        >>> api_key = generate_api_key()
        >>> len(api_key) == 64
        True
    """
    import secrets
    return secrets.token_urlsafe(32)


def encrypt_data(data: str, key: Optional[str] = None) -> str:
    """
    Encrypt sensitive data.

    Args:
        data: Data to encrypt
        key: Encryption key (uses SECRET_KEY if not provided)

    Returns:
        Encrypted data

    Example:
        >>> encrypted = encrypt_data("sensitive info")
        >>> print(encrypted)
        gAAAAA...
    """
    from cryptography.fernet import Fernet
    import base64

    if key is None:
        # Use SECRET_KEY, padded/truncated to 32 bytes
        key = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
        key = base64.urlsafe_b64encode(key)

    cipher = Fernet(key)
    encrypted = cipher.encrypt(data.encode())
    return encrypted.decode()


def decrypt_data(encrypted_data: str, key: Optional[str] = None) -> str:
    """
    Decrypt encrypted data.

    Args:
        encrypted_data: Encrypted data
        key: Decryption key (uses SECRET_KEY if not provided)

    Returns:
        Decrypted data

    Example:
        >>> encrypted = encrypt_data("sensitive info")
        >>> decrypted = decrypt_data(encrypted)
        >>> print(decrypted)
        sensitive info
    """
    from cryptography.fernet import Fernet
    import base64

    if key is None:
        # Use SECRET_KEY, padded/truncated to 32 bytes
        key = settings.SECRET_KEY.encode()[:32].ljust(32, b'0')
        key = base64.urlsafe_b64encode(key)

    cipher = Fernet(key)
    decrypted = cipher.decrypt(encrypted_data.encode())
    return decrypted.decode()


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Example:
        >>> sanitize_input("<script>alert('xss')</script>")
        "&lt;script&gt;alert('xss')&lt;/script&gt;"
    """
    import html

    # Truncate to max length
    text = text[:max_length]

    # HTML escape
    text = html.escape(text)

    return text
