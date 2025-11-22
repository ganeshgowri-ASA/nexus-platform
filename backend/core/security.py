"""
Security utilities for NEXUS platform.

This module provides authentication, password hashing, JWT token generation,
and password validation functionality.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import get_settings
from backend.core.exceptions import (
    AuthenticationException,
    InvalidTokenException,
    TokenExpiredException,
    ValidationException,
)
from backend.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password

    Example:
        >>> hashed = hash_password("my_password")
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        bool: True if password matches, False otherwise

    Example:
        >>> is_valid = verify_password("my_password", hashed)
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("password_verification_failed", error=str(e))
        return False


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password strength against configured requirements.

    Args:
        password: Password to validate

    Returns:
        tuple[bool, list[str]]: (is_valid, list of error messages)

    Example:
        >>> is_valid, errors = validate_password_strength("MyP@ss123")
        >>> if not is_valid:
        ...     print(errors)
    """
    errors = []

    # Check minimum length
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        errors.append(
            f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
        )

    # Check for uppercase
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    # Check for lowercase
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")

    # Check for numbers
    if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r"\d", password):
        errors.append("Password must contain at least one number")

    # Check for special characters
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(
        r'[!@#$%^&*(),.?":{}|<>]', password
    ):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (defaults to configured value)

    Returns:
        str: Encoded JWT token

    Example:
        >>> token = create_access_token({"sub": "user@example.com"})
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    logger.debug(
        "access_token_created",
        subject=data.get("sub"),
        expires_at=expire.isoformat(),
    )

    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (defaults to configured value)

    Returns:
        str: Encoded JWT refresh token

    Example:
        >>> refresh_token = create_refresh_token({"sub": "user@example.com"})
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update(
        {"exp": expire, "iat": datetime.utcnow(), "type": "refresh"}
    )

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    logger.debug(
        "refresh_token_created",
        subject=data.get("sub"),
        expires_at=expire.isoformat(),
    )

    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Dict[str, Any]: Decoded token payload

    Raises:
        TokenExpiredException: If token has expired
        InvalidTokenException: If token is invalid

    Example:
        >>> payload = decode_token(token)
        >>> user_id = payload.get("sub")
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        logger.debug("token_decoded", subject=payload.get("sub"))

        return payload

    except jwt.ExpiredSignatureError as e:
        logger.warning("token_expired", error=str(e))
        raise TokenExpiredException()

    except JWTError as e:
        logger.warning("invalid_token", error=str(e))
        raise InvalidTokenException()


def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify a JWT token and check its type.

    Args:
        token: JWT token to verify
        token_type: Expected token type ('access' or 'refresh')

    Returns:
        Dict[str, Any]: Decoded token payload

    Raises:
        InvalidTokenException: If token type doesn't match or token is invalid

    Example:
        >>> payload = verify_token(token, "access")
    """
    payload = decode_token(token)

    # Check token type for refresh tokens
    if token_type == "refresh":
        if payload.get("type") != "refresh":
            raise InvalidTokenException("Invalid token type")

    return payload


def generate_password_reset_token(email: str) -> str:
    """
    Generate a password reset token.

    Args:
        email: User email address

    Returns:
        str: Password reset token

    Example:
        >>> reset_token = generate_password_reset_token("user@example.com")
    """
    expires_delta = timedelta(hours=1)  # Reset tokens expire in 1 hour
    data = {"sub": email, "type": "password_reset"}

    return create_access_token(data, expires_delta)


def verify_password_reset_token(token: str) -> str:
    """
    Verify a password reset token and extract email.

    Args:
        token: Password reset token

    Returns:
        str: Email address from token

    Raises:
        InvalidTokenException: If token is invalid or wrong type

    Example:
        >>> email = verify_password_reset_token(reset_token)
    """
    payload = decode_token(token)

    if payload.get("type") != "password_reset":
        raise InvalidTokenException("Invalid token type")

    email = payload.get("sub")
    if not email:
        raise InvalidTokenException("Invalid token payload")

    return email


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        str: Random API key

    Example:
        >>> api_key = generate_api_key()
    """
    import secrets

    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.

    Args:
        api_key: API key to hash

    Returns:
        str: Hashed API key

    Example:
        >>> hashed_key = hash_api_key(api_key)
    """
    return hash_password(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """
    Verify an API key against a hashed key.

    Args:
        plain_key: Plain API key
        hashed_key: Hashed API key

    Returns:
        bool: True if key matches

    Example:
        >>> is_valid = verify_api_key(api_key, hashed_key)
    """
    return verify_password(plain_key, hashed_key)


class PasswordValidator:
    """
    Password validation utility class.

    Provides comprehensive password validation with detailed feedback.
    """

    @staticmethod
    def validate(password: str, raise_exception: bool = True) -> bool:
        """
        Validate password strength.

        Args:
            password: Password to validate
            raise_exception: Whether to raise exception on failure

        Returns:
            bool: True if password is valid

        Raises:
            ValidationException: If password is invalid and raise_exception=True

        Example:
            >>> PasswordValidator.validate("MyP@ss123")
            True
        """
        is_valid, errors = validate_password_strength(password)

        if not is_valid and raise_exception:
            raise ValidationException(
                message="Password does not meet security requirements",
                errors={"password": errors},
            )

        return is_valid

    @staticmethod
    def get_requirements() -> Dict[str, Any]:
        """
        Get password requirements.

        Returns:
            Dict[str, Any]: Password requirements

        Example:
            >>> requirements = PasswordValidator.get_requirements()
        """
        return {
            "min_length": settings.PASSWORD_MIN_LENGTH,
            "require_uppercase": settings.PASSWORD_REQUIRE_UPPERCASE,
            "require_lowercase": settings.PASSWORD_REQUIRE_LOWERCASE,
            "require_numbers": settings.PASSWORD_REQUIRE_NUMBERS,
            "require_special": settings.PASSWORD_REQUIRE_SPECIAL,
        }
