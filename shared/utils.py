"""
NEXUS Platform - Shared Utilities

Common utility functions used across the platform.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TypeVar, Union

import pytz
from dateutil import parser

T = TypeVar("T")


def generate_uuid() -> str:
    """
    Generate a unique UUID v4.

    Returns:
        str: UUID string

    Example:
        >>> user_id = generate_uuid()
        >>> print(user_id)
        '550e8400-e29b-41d4-a716-446655440000'
    """
    return str(uuid.uuid4())


def generate_short_id(length: int = 16) -> str:
    """
    Generate a random short ID.

    Args:
        length: Length of the ID to generate

    Returns:
        str: Random alphanumeric string

    Example:
        >>> session_id = generate_short_id()
        >>> print(len(session_id))
        16
    """
    return secrets.token_urlsafe(length)[:length]


def hash_string(value: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using specified algorithm.

    Args:
        value: String to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)

    Returns:
        str: Hexadecimal hash string

    Example:
        >>> hashed = hash_string("user@example.com")
        >>> len(hashed)
        64
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(value.encode("utf-8"))
    return hash_obj.hexdigest()


def get_utc_now() -> datetime:
    """
    Get current UTC datetime.

    Returns:
        datetime: Current UTC datetime

    Example:
        >>> now = get_utc_now()
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def parse_datetime(
    dt_string: str, tz: Optional[str] = None
) -> datetime:
    """
    Parse datetime string with optional timezone.

    Args:
        dt_string: Datetime string to parse
        tz: Optional timezone name

    Returns:
        datetime: Parsed datetime object

    Example:
        >>> dt = parse_datetime("2024-01-15T10:30:00")
        >>> dt.year
        2024
    """
    dt = parser.parse(dt_string)

    if tz:
        timezone_obj = pytz.timezone(tz)
        if dt.tzinfo is None:
            dt = timezone_obj.localize(dt)
        else:
            dt = dt.astimezone(timezone_obj)

    return dt


def format_datetime(
    dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object
        fmt: Format string

    Returns:
        str: Formatted datetime string

    Example:
        >>> now = datetime.now()
        >>> formatted = format_datetime(now)
        >>> "2024" in formatted
        True
    """
    return dt.strftime(fmt)


def get_time_range(
    period: str, end_date: Optional[datetime] = None
) -> tuple[datetime, datetime]:
    """
    Get start and end datetime for a given period.

    Args:
        period: Period name (today, yesterday, last_7_days, last_30_days, etc.)
        end_date: Optional end date (defaults to now)

    Returns:
        tuple: Start and end datetime

    Example:
        >>> start, end = get_time_range("last_7_days")
        >>> (end - start).days
        7
    """
    if end_date is None:
        end_date = get_utc_now()

    period_map = {
        "today": timedelta(days=0),
        "yesterday": timedelta(days=1),
        "last_7_days": timedelta(days=7),
        "last_14_days": timedelta(days=14),
        "last_30_days": timedelta(days=30),
        "last_60_days": timedelta(days=60),
        "last_90_days": timedelta(days=90),
        "last_year": timedelta(days=365),
    }

    delta = period_map.get(period, timedelta(days=7))

    if period == "today":
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "yesterday":
        start_date = (end_date - delta).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = end_date - delta

    return start_date, end_date


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks of specified size.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List[List[T]]: List of chunks

    Example:
        >>> data = [1, 2, 3, 4, 5]
        >>> chunks = chunk_list(data, 2)
        >>> len(chunks)
        3
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(
    d: Dict[str, Any], parent_key: str = "", sep: str = "."
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys

    Returns:
        Dict[str, Any]: Flattened dictionary

    Example:
        >>> nested = {"a": {"b": {"c": 1}}}
        >>> flat = flatten_dict(nested)
        >>> flat
        {'a.b.c': 1}
    """
    items: List[tuple[str, Any]] = []

    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))

    return dict(items)


def unflatten_dict(
    d: Dict[str, Any], sep: str = "."
) -> Dict[str, Any]:
    """
    Unflatten a dictionary with dot-separated keys.

    Args:
        d: Flattened dictionary
        sep: Separator used in keys

    Returns:
        Dict[str, Any]: Nested dictionary

    Example:
        >>> flat = {"a.b.c": 1}
        >>> nested = unflatten_dict(flat)
        >>> nested
        {'a': {'b': {'c': 1}}}
    """
    result: Dict[str, Any] = {}

    for key, value in d.items():
        parts = key.split(sep)
        current = result

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string by removing control characters.

    Args:
        value: String to sanitize
        max_length: Optional maximum length

    Returns:
        str: Sanitized string

    Example:
        >>> sanitized = sanitize_string("hello\\nworld", max_length=10)
        >>> sanitized
        'hello worl'
    """
    # Remove control characters
    sanitized = "".join(char for char in value if ord(char) >= 32 or char in "\n\t")

    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized.strip()


def calculate_percentage(
    value: Union[int, float],
    total: Union[int, float],
    decimal_places: int = 2,
) -> float:
    """
    Calculate percentage with safe division.

    Args:
        value: Numerator value
        total: Denominator value
        decimal_places: Number of decimal places

    Returns:
        float: Percentage value

    Example:
        >>> calculate_percentage(25, 100)
        25.0
        >>> calculate_percentage(0, 0)
        0.0
    """
    if total == 0:
        return 0.0

    percentage = (value / total) * 100
    return round(percentage, decimal_places)


def format_number(
    value: Union[int, float],
    notation: str = "standard",
) -> str:
    """
    Format number with human-readable notation.

    Args:
        value: Number to format
        notation: Notation type (standard, compact, scientific)

    Returns:
        str: Formatted number string

    Example:
        >>> format_number(1000000)
        '1,000,000'
        >>> format_number(1000000, notation="compact")
        '1M'
    """
    if notation == "compact":
        if abs(value) >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B"
        elif abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{value / 1_000:.1f}K"
        else:
            return str(value)
    elif notation == "scientific":
        return f"{value:.2e}"
    else:
        return f"{value:,}"


def safe_divide(
    numerator: Union[int, float],
    denominator: Union[int, float],
    default: Union[int, float] = 0,
) -> float:
    """
    Perform safe division with default value for zero division.

    Args:
        numerator: Numerator value
        denominator: Denominator value
        default: Default value if denominator is zero

    Returns:
        float: Division result or default

    Example:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0, default=0)
        0
    """
    if denominator == 0:
        return float(default)
    return numerator / denominator


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries.

    Args:
        *dicts: Variable number of dictionaries to merge

    Returns:
        Dict[str, Any]: Merged dictionary

    Example:
        >>> d1 = {"a": 1}
        >>> d2 = {"b": 2}
        >>> merged = merge_dicts(d1, d2)
        >>> merged
        {'a': 1, 'b': 2}
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def remove_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from dictionary.

    Args:
        d: Dictionary to clean

    Returns:
        Dict[str, Any]: Dictionary without None values

    Example:
        >>> data = {"a": 1, "b": None, "c": 3}
        >>> clean = remove_none_values(data)
        >>> clean
        {'a': 1, 'c': 3}
    """
    return {k: v for k, v in d.items() if v is not None}


def truncate_string(value: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.

    Args:
        value: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated string

    Example:
        >>> truncate_string("Hello World", 8)
        'Hello...'
    """
    if len(value) <= max_length:
        return value

    return value[: max_length - len(suffix)] + suffix
