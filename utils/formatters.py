"""Data formatting utilities"""
from datetime import datetime, timedelta
from typing import Optional

def format_date(dt: datetime, format: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format datetime object to string

    Args:
        dt: datetime object
        format: Desired format string

    Returns:
        Formatted date string
    """
    if not dt:
        return ""
    return dt.strftime(format)

def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format currency amount

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted currency string
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥",
        "INR": "₹"
    }
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"

def format_duration(minutes: int) -> str:
    """
    Format duration in minutes to readable string

    Args:
        minutes: Duration in minutes

    Returns:
        Formatted duration string (e.g., "2h 30m")
    """
    if minutes < 60:
        return f"{minutes}m"

    hours = minutes // 60
    mins = minutes % 60

    if mins == 0:
        return f"{hours}h"

    return f"{hours}h {mins}m"

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to readable string

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def format_relative_time(dt: datetime) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago")

    Args:
        dt: datetime object

    Returns:
        Relative time string
    """
    if not dt:
        return ""

    now = datetime.utcnow()
    diff = now - dt

    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format percentage value

    Args:
        value: Value (0-100)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"
