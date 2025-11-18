"""
Timezone Management Module

Handles timezone conversions, detection, and multi-timezone support for the calendar system.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from zoneinfo import ZoneInfo, available_timezones
import pytz


class TimezoneManager:
    """
    Manages timezone operations for the calendar system.

    Features:
    - Timezone detection
    - Timezone conversions
    - Multi-timezone support
    - Display in user timezone
    - DST handling
    """

    def __init__(self, default_timezone: str = "UTC"):
        """
        Initialize the timezone manager.

        Args:
            default_timezone: Default timezone to use (IANA timezone name)
        """
        self.default_timezone = default_timezone
        self._validate_timezone(default_timezone)

    def _validate_timezone(self, timezone_name: str) -> None:
        """
        Validate that a timezone name is valid.

        Args:
            timezone_name: IANA timezone name to validate

        Raises:
            ValueError: If timezone is invalid
        """
        try:
            ZoneInfo(timezone_name)
        except Exception as e:
            raise ValueError(f"Invalid timezone: {timezone_name}") from e

    def convert_time(
        self,
        dt: datetime,
        from_tz: str,
        to_tz: str
    ) -> datetime:
        """
        Convert datetime from one timezone to another.

        Args:
            dt: Datetime to convert
            from_tz: Source timezone
            to_tz: Target timezone

        Returns:
            Converted datetime in target timezone
        """
        self._validate_timezone(from_tz)
        self._validate_timezone(to_tz)

        # If datetime is naive, localize it first
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(from_tz))

        # Convert to target timezone
        target_tz = ZoneInfo(to_tz)
        return dt.astimezone(target_tz)

    def to_utc(self, dt: datetime, source_tz: str) -> datetime:
        """
        Convert datetime to UTC.

        Args:
            dt: Datetime to convert
            source_tz: Source timezone

        Returns:
            Datetime in UTC
        """
        return self.convert_time(dt, source_tz, "UTC")

    def from_utc(self, dt: datetime, target_tz: str) -> datetime:
        """
        Convert datetime from UTC to target timezone.

        Args:
            dt: UTC datetime
            target_tz: Target timezone

        Returns:
            Datetime in target timezone
        """
        return self.convert_time(dt, "UTC", target_tz)

    def get_timezone_offset(self, timezone_name: str, dt: Optional[datetime] = None) -> timedelta:
        """
        Get the UTC offset for a timezone at a specific time.

        Args:
            timezone_name: IANA timezone name
            dt: Datetime to check offset for (defaults to now)

        Returns:
            UTC offset as timedelta
        """
        self._validate_timezone(timezone_name)

        if dt is None:
            dt = datetime.now(ZoneInfo(timezone_name))
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(timezone_name))

        return dt.utcoffset() or timedelta(0)

    def get_timezone_name(self, timezone_name: str) -> str:
        """
        Get the full timezone name including abbreviation.

        Args:
            timezone_name: IANA timezone name

        Returns:
            Formatted timezone name with abbreviation
        """
        self._validate_timezone(timezone_name)
        tz = pytz.timezone(timezone_name)
        now = datetime.now(tz)
        return f"{timezone_name} ({now.strftime('%Z')})"

    def detect_timezone(self) -> str:
        """
        Attempt to detect the system timezone.

        Returns:
            Detected timezone name (falls back to default)
        """
        try:
            import tzlocal
            return str(tzlocal.get_localzone())
        except Exception:
            return self.default_timezone

    def list_timezones(self, filter_region: Optional[str] = None) -> List[str]:
        """
        List all available timezones, optionally filtered by region.

        Args:
            filter_region: Optional region to filter by (e.g., "America", "Europe")

        Returns:
            List of timezone names
        """
        zones = sorted(available_timezones())

        if filter_region:
            zones = [z for z in zones if z.startswith(filter_region)]

        return zones

    def get_common_timezones(self) -> List[Dict[str, str]]:
        """
        Get a list of commonly used timezones with display names.

        Returns:
            List of timezone dicts with name and display_name
        """
        common = [
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "America/Anchorage",
            "Pacific/Honolulu",
            "Europe/London",
            "Europe/Paris",
            "Europe/Berlin",
            "Asia/Dubai",
            "Asia/Kolkata",
            "Asia/Shanghai",
            "Asia/Tokyo",
            "Australia/Sydney",
            "Pacific/Auckland",
            "UTC",
        ]

        result = []
        for tz_name in common:
            try:
                result.append({
                    "name": tz_name,
                    "display_name": self.get_timezone_name(tz_name),
                })
            except Exception:
                continue

        return result

    def is_dst(self, timezone_name: str, dt: Optional[datetime] = None) -> bool:
        """
        Check if daylight saving time is active for a timezone.

        Args:
            timezone_name: IANA timezone name
            dt: Datetime to check (defaults to now)

        Returns:
            True if DST is active, False otherwise
        """
        self._validate_timezone(timezone_name)

        if dt is None:
            dt = datetime.now(ZoneInfo(timezone_name))
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo(timezone_name))

        return bool(dt.dst())

    def get_timezone_transitions(
        self,
        timezone_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, datetime]]:
        """
        Get timezone transitions (DST changes) within a date range.

        Args:
            timezone_name: IANA timezone name
            start_date: Start of range
            end_date: End of range

        Returns:
            List of transition dicts with date and offset
        """
        self._validate_timezone(timezone_name)

        transitions = []
        tz = pytz.timezone(timezone_name)

        # Sample dates to find transitions
        current = start_date
        prev_offset = None

        while current <= end_date:
            localized = tz.localize(current.replace(tzinfo=None))
            offset = localized.utcoffset()

            if prev_offset is not None and offset != prev_offset:
                transitions.append({
                    "date": current,
                    "old_offset": prev_offset,
                    "new_offset": offset,
                })

            prev_offset = offset
            current += timedelta(days=1)

        return transitions

    def format_timezone_offset(self, timezone_name: str) -> str:
        """
        Format timezone offset as string (e.g., "+05:30", "-08:00").

        Args:
            timezone_name: IANA timezone name

        Returns:
            Formatted offset string
        """
        offset = self.get_timezone_offset(timezone_name)
        total_seconds = int(offset.total_seconds())
        hours, remainder = divmod(abs(total_seconds), 3600)
        minutes = remainder // 60
        sign = "+" if total_seconds >= 0 else "-"
        return f"{sign}{hours:02d}:{minutes:02d}"

    def get_user_friendly_name(self, timezone_name: str) -> str:
        """
        Get a user-friendly display name for a timezone.

        Args:
            timezone_name: IANA timezone name

        Returns:
            Formatted display name
        """
        self._validate_timezone(timezone_name)

        # Convert timezone name to readable format
        # e.g., "America/New_York" -> "New York (EST)"
        city = timezone_name.split("/")[-1].replace("_", " ")
        offset = self.format_timezone_offset(timezone_name)

        tz = pytz.timezone(timezone_name)
        now = datetime.now(tz)
        abbr = now.strftime("%Z")

        return f"{city} ({abbr}, UTC{offset})"
