"""Timezone conversion utilities"""
from datetime import datetime
from typing import Optional, List
import pytz
from zoneinfo import available_timezones


def get_available_timezones() -> List[str]:
    """Get list of all available timezones"""
    return sorted(pytz.all_timezones)


def get_common_timezones() -> dict:
    """Get commonly used timezones grouped by region"""
    return {
        "US": [
            "US/Eastern",
            "US/Central",
            "US/Mountain",
            "US/Pacific",
            "US/Alaska",
            "US/Hawaii"
        ],
        "Europe": [
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Europe/Madrid",
            "Europe/Rome",
            "Europe/Amsterdam",
            "Europe/Stockholm"
        ],
        "Asia": [
            "Asia/Tokyo",
            "Asia/Shanghai",
            "Asia/Hong_Kong",
            "Asia/Singapore",
            "Asia/Dubai",
            "Asia/Kolkata",
            "Asia/Seoul"
        ],
        "Australia": [
            "Australia/Sydney",
            "Australia/Melbourne",
            "Australia/Brisbane",
            "Australia/Perth"
        ],
        "Other": [
            "UTC",
            "GMT"
        ]
    }


def convert_timezone(
    dt: datetime,
    from_tz: str,
    to_tz: str
) -> datetime:
    """Convert datetime from one timezone to another"""
    try:
        from_timezone = pytz.timezone(from_tz)
        to_timezone = pytz.timezone(to_tz)

        # Localize if naive
        if dt.tzinfo is None:
            dt = from_timezone.localize(dt)
        else:
            dt = dt.astimezone(from_timezone)

        # Convert to target timezone
        return dt.astimezone(to_timezone)

    except Exception as e:
        raise ValueError(f"Timezone conversion failed: {str(e)}")


def get_current_time_in_timezone(timezone: str) -> datetime:
    """Get current time in specified timezone"""
    try:
        tz = pytz.timezone(timezone)
        return datetime.now(tz)
    except Exception as e:
        raise ValueError(f"Invalid timezone: {str(e)}")


def is_valid_timezone(timezone: str) -> bool:
    """Check if timezone string is valid"""
    try:
        pytz.timezone(timezone)
        return True
    except Exception:
        return False


def get_timezone_offset(timezone: str, dt: Optional[datetime] = None) -> str:
    """Get UTC offset for timezone"""
    try:
        tz = pytz.timezone(timezone)
        dt = dt or datetime.now()
        offset = tz.utcoffset(dt)

        if offset:
            total_seconds = int(offset.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours:+03d}:{minutes:02d}"

        return "+00:00"

    except Exception:
        return "+00:00"
