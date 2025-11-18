"""
Shared utility functions for NEXUS platform.

This module contains common utility functions used across multiple modules.
"""

import re
import uuid
import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlencode
import bleach


def generate_uuid() -> str:
    """
    Generate a UUID4 string.

    Returns:
        UUID string.
    """
    return str(uuid.uuid4())


def generate_slug(text: str, max_length: int = 50) -> str:
    """
    Generate URL-safe slug from text.

    Args:
        text: Input text.
        max_length: Maximum slug length.

    Returns:
        URL-safe slug.
    """
    # Convert to lowercase and remove special characters
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    # Replace spaces with hyphens
    slug = re.sub(r"[-\s]+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    # Limit length
    return slug[:max_length]


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate.

    Returns:
        True if valid, False otherwise.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate.

    Returns:
        True if valid, False otherwise.
    """
    # Remove common formatting characters
    cleaned = re.sub(r"[\s\-\(\)\.]", "", phone)
    # Check if it's a valid phone number (10-15 digits)
    pattern = r"^\+?[1-9]\d{9,14}$"
    return bool(re.match(pattern, cleaned))


def sanitize_input(text: str, allow_tags: Optional[list[str]] = None) -> str:
    """
    Sanitize user input to prevent XSS attacks.

    Args:
        text: Input text to sanitize.
        allow_tags: List of allowed HTML tags (default: none).

    Returns:
        Sanitized text.
    """
    if allow_tags is None:
        allow_tags = []
    return bleach.clean(text, tags=allow_tags, strip=True)


def generate_api_key() -> str:
    """
    Generate a secure API key.

    Returns:
        API key string.
    """
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    """
    Hash password using SHA-256.

    Args:
        password: Plain text password.

    Returns:
        Hashed password.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def generate_tracking_code(
    source: str,
    medium: str,
    campaign: str,
    content: Optional[str] = None,
) -> str:
    """
    Generate UTM tracking code.

    Args:
        source: Traffic source.
        medium: Marketing medium.
        campaign: Campaign name.
        content: Ad content identifier.

    Returns:
        UTM tracking code.
    """
    params = {
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
    }
    if content:
        params["utm_content"] = content
    return urlencode(params)


def parse_url(url: str) -> dict[str, str]:
    """
    Parse URL into components.

    Args:
        url: URL to parse.

    Returns:
        Dictionary with URL components.
    """
    parsed = urlparse(url)
    return {
        "scheme": parsed.scheme,
        "domain": parsed.netloc,
        "path": parsed.path,
        "params": parsed.params,
        "query": parsed.query,
        "fragment": parsed.fragment,
    }


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calculate percentage change between two values.

    Args:
        old_value: Original value.
        new_value: New value.

    Returns:
        Percentage change.
    """
    if old_value == 0:
        return 100.0 if new_value > 0 else 0.0
    return ((new_value - old_value) / old_value) * 100


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format amount as currency string.

    Args:
        amount: Amount to format.
        currency: Currency code.

    Returns:
        Formatted currency string.
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
    }
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate.
        max_length: Maximum length.
        suffix: Suffix to append if truncated.

    Returns:
        Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def get_date_range(period: str) -> tuple[datetime, datetime]:
    """
    Get date range for common periods.

    Args:
        period: Period name (today, yesterday, last_7_days, last_30_days, this_month).

    Returns:
        Tuple of (start_date, end_date).
    """
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "today":
        return today, now
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday, today
    elif period == "last_7_days":
        start = today - timedelta(days=7)
        return start, now
    elif period == "last_30_days":
        start = today - timedelta(days=30)
        return start, now
    elif period == "this_month":
        start = today.replace(day=1)
        return start, now
    else:
        raise ValueError(f"Unknown period: {period}")


def chunk_list(items: list, chunk_size: int) -> list[list]:
    """
    Split list into chunks.

    Args:
        items: List to chunk.
        chunk_size: Size of each chunk.

    Returns:
        List of chunks.
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Flatten nested dictionary.

    Args:
        d: Dictionary to flatten.
        parent_key: Parent key prefix.
        sep: Separator between keys.

    Returns:
        Flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
