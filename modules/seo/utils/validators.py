"""
Validation utilities.

Input validation functions for SEO data.
"""

import re
from typing import Optional

import validators as val

from .exceptions import ValidationException


def validate_domain(domain: str) -> str:
    """
    Validate and clean domain name.

    Args:
        domain: Domain to validate

    Returns:
        Cleaned domain name

    Raises:
        ValidationException: If domain is invalid

    Example:
        >>> validate_domain("example.com")
        "example.com"
    """
    if not domain:
        raise ValidationException("Domain cannot be empty", field="domain")

    # Remove protocol if present
    domain = re.sub(r'^https?://', '', domain)

    # Remove www prefix
    domain = re.sub(r'^www\.', '', domain)

    # Remove trailing slash
    domain = domain.rstrip('/')

    # Validate domain format
    if not val.domain(domain):
        raise ValidationException(
            f"Invalid domain format: {domain}",
            field="domain",
        )

    return domain.lower()


def validate_url(url: str) -> str:
    """
    Validate URL.

    Args:
        url: URL to validate

    Returns:
        Validated URL

    Raises:
        ValidationException: If URL is invalid

    Example:
        >>> validate_url("https://example.com")
        "https://example.com"
    """
    if not url:
        raise ValidationException("URL cannot be empty", field="url")

    # Add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Validate URL format
    if not val.url(url):
        raise ValidationException(
            f"Invalid URL format: {url}",
            field="url",
        )

    return url


def validate_keyword(keyword: str, max_length: int = 500) -> str:
    """
    Validate keyword.

    Args:
        keyword: Keyword to validate
        max_length: Maximum keyword length

    Returns:
        Validated keyword

    Raises:
        ValidationException: If keyword is invalid

    Example:
        >>> validate_keyword("seo tools")
        "seo tools"
    """
    if not keyword or not keyword.strip():
        raise ValidationException("Keyword cannot be empty", field="keyword")

    keyword = keyword.strip()

    if len(keyword) > max_length:
        raise ValidationException(
            f"Keyword too long (max {max_length} characters)",
            field="keyword",
        )

    # Check for invalid characters
    if re.search(r'[<>{}\\]', keyword):
        raise ValidationException(
            "Keyword contains invalid characters",
            field="keyword",
        )

    return keyword


def validate_email(email: str) -> str:
    """
    Validate email address.

    Args:
        email: Email to validate

    Returns:
        Validated email

    Raises:
        ValidationException: If email is invalid

    Example:
        >>> validate_email("test@example.com")
        "test@example.com"
    """
    if not email:
        raise ValidationException("Email cannot be empty", field="email")

    email = email.strip().lower()

    if not val.email(email):
        raise ValidationException(
            f"Invalid email format: {email}",
            field="email",
        )

    return email


def validate_port(port: int) -> int:
    """
    Validate port number.

    Args:
        port: Port number to validate

    Returns:
        Validated port

    Raises:
        ValidationException: If port is invalid
    """
    if not isinstance(port, int):
        raise ValidationException("Port must be an integer", field="port")

    if port < 1 or port > 65535:
        raise ValidationException(
            "Port must be between 1 and 65535",
            field="port",
        )

    return port


def validate_score(score: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """
    Validate score is within range.

    Args:
        score: Score to validate
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Validated score

    Raises:
        ValidationException: If score is out of range
    """
    if not isinstance(score, (int, float)):
        raise ValidationException("Score must be a number", field="score")

    if score < min_val or score > max_val:
        raise ValidationException(
            f"Score must be between {min_val} and {max_val}",
            field="score",
        )

    return float(score)
