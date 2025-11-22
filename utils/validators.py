"""Input validation utilities"""
import re
from datetime import datetime
from typing import Optional
from email_validator import validate_email as email_validate, EmailNotValidError

def validate_email(email: str) -> bool:
    """
    Validate email address format

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        email_validate(email)
        return True
    except EmailNotValidError:
        return False

def validate_date(date_str: str, format: str = "%Y-%m-%d") -> Optional[datetime]:
    """
    Validate and parse date string

    Args:
        date_str: Date string to validate
        format: Expected date format

    Returns:
        datetime object if valid, None otherwise
    """
    try:
        return datetime.strptime(date_str, format)
    except ValueError:
        return None

def validate_url(url: str) -> bool:
    """
    Validate URL format

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format

    Args:
        phone: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    # Basic phone validation (can be enhanced)
    phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    return phone_pattern.match(clean_phone) is not None

def validate_currency(amount: str) -> Optional[float]:
    """
    Validate and parse currency amount

    Args:
        amount: Currency amount string

    Returns:
        Float value if valid, None otherwise
    """
    try:
        clean_amount = re.sub(r'[,$]', '', amount)
        return float(clean_amount)
    except ValueError:
        return None

def validate_hex_color(color: str) -> bool:
    """
    Validate hex color code

    Args:
        color: Hex color code

    Returns:
        True if valid, False otherwise
    """
    color_pattern = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')
    return color_pattern.match(color) is not None
