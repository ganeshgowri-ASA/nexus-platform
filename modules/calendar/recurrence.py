"""
Recurrence Engine Module

Handles recurring event patterns, generation, and exception management.
Supports RFC 5545 (iCalendar) recurrence rules.
"""

from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Set, Any
from enum import Enum
from dateutil import rrule
from dateutil.rrule import rrule as DateUtilRRule, DAILY, WEEKLY, MONTHLY, YEARLY


class RecurrenceFrequency(Enum):
    """Frequency of recurrence."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    HOURLY = "hourly"


class RecurrenceEndType(Enum):
    """How the recurrence ends."""
    NEVER = "never"
    DATE = "date"
    COUNT = "count"


class Weekday(Enum):
    """Days of the week."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class RecurrencePattern:
    """
    Represents a recurrence pattern for events.

    Supports complex patterns including:
    - Daily, weekly, monthly, yearly recurrence
    - Custom intervals
    - Specific days of week
    - End by date or count
    - Exception dates
    """

    def __init__(
        self,
        frequency: RecurrenceFrequency,
        interval: int = 1,
        end_type: RecurrenceEndType = RecurrenceEndType.NEVER,
        end_date: Optional[datetime] = None,
        count: Optional[int] = None,
        by_weekday: Optional[List[Weekday]] = None,
        by_monthday: Optional[List[int]] = None,
        by_month: Optional[List[int]] = None,
        by_setpos: Optional[List[int]] = None,
    ):
        """
        Initialize a recurrence pattern.

        Args:
            frequency: How often the event recurs
            interval: Interval between recurrences (e.g., every 2 weeks)
            end_type: How the recurrence ends
            end_date: End date for recurrence (if end_type is DATE)
            count: Number of occurrences (if end_type is COUNT)
            by_weekday: Specific days of week (for weekly recurrence)
            by_monthday: Specific days of month (for monthly recurrence)
            by_month: Specific months (for yearly recurrence)
            by_setpos: Nth occurrence (e.g., 1st Monday, last Friday)
        """
        self.frequency = frequency
        self.interval = interval
        self.end_type = end_type
        self.end_date = end_date
        self.count = count
        self.by_weekday = by_weekday or []
        self.by_monthday = by_monthday or []
        self.by_month = by_month or []
        self.by_setpos = by_setpos or []

        self._validate()

    def _validate(self) -> None:
        """Validate the recurrence pattern."""
        if self.interval < 1:
            raise ValueError("Interval must be at least 1")

        if self.end_type == RecurrenceEndType.DATE and not self.end_date:
            raise ValueError("end_date required when end_type is DATE")

        if self.end_type == RecurrenceEndType.COUNT and not self.count:
            raise ValueError("count required when end_type is COUNT")

        if self.count and self.count < 1:
            raise ValueError("count must be at least 1")

    def to_dict(self) -> Dict[str, Any]:
        """Convert pattern to dictionary."""
        return {
            "frequency": self.frequency.value,
            "interval": self.interval,
            "end_type": self.end_type.value,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "count": self.count,
            "by_weekday": [d.value for d in self.by_weekday],
            "by_monthday": self.by_monthday,
            "by_month": self.by_month,
            "by_setpos": self.by_setpos,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecurrencePattern":
        """Create pattern from dictionary."""
        return cls(
            frequency=RecurrenceFrequency(data["frequency"]),
            interval=data.get("interval", 1),
            end_type=RecurrenceEndType(data.get("end_type", "never")),
            end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            count=data.get("count"),
            by_weekday=[Weekday(d) for d in data.get("by_weekday", [])],
            by_monthday=data.get("by_monthday", []),
            by_month=data.get("by_month", []),
            by_setpos=data.get("by_setpos", []),
        )

    def to_rrule_string(self) -> str:
        """Convert to RFC 5545 RRULE string."""
        parts = []

        # Frequency
        freq_map = {
            RecurrenceFrequency.DAILY: "DAILY",
            RecurrenceFrequency.WEEKLY: "WEEKLY",
            RecurrenceFrequency.MONTHLY: "MONTHLY",
            RecurrenceFrequency.YEARLY: "YEARLY",
            RecurrenceFrequency.HOURLY: "HOURLY",
        }
        parts.append(f"FREQ={freq_map[self.frequency]}")

        # Interval
        if self.interval > 1:
            parts.append(f"INTERVAL={self.interval}")

        # End condition
        if self.end_type == RecurrenceEndType.DATE and self.end_date:
            parts.append(f"UNTIL={self.end_date.strftime('%Y%m%dT%H%M%SZ')}")
        elif self.end_type == RecurrenceEndType.COUNT and self.count:
            parts.append(f"COUNT={self.count}")

        # By weekday
        if self.by_weekday:
            days = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
            weekdays = ",".join(days[d.value] for d in self.by_weekday)
            parts.append(f"BYDAY={weekdays}")

        # By monthday
        if self.by_monthday:
            parts.append(f"BYMONTHDAY={','.join(map(str, self.by_monthday))}")

        # By month
        if self.by_month:
            parts.append(f"BYMONTH={','.join(map(str, self.by_month))}")

        # By setpos
        if self.by_setpos:
            parts.append(f"BYSETPOS={','.join(map(str, self.by_setpos))}")

        return "RRULE:" + ";".join(parts)


class RecurrenceEngine:
    """
    Engine for generating and managing recurring events.

    Features:
    - Generate event occurrences from patterns
    - Handle exception dates
    - Edit single/all occurrences
    - Validate recurrence patterns
    """

    def __init__(self):
        """Initialize the recurrence engine."""
        pass

    def generate_occurrences(
        self,
        pattern: RecurrencePattern,
        start_time: datetime,
        end_time: datetime,
        exceptions: Optional[Set[datetime]] = None,
        limit: int = 1000,
    ) -> List[datetime]:
        """
        Generate event occurrences based on recurrence pattern.

        Args:
            pattern: Recurrence pattern
            start_time: Start time of the recurring event
            end_time: End time of range to generate occurrences
            exceptions: Set of exception dates to exclude
            limit: Maximum number of occurrences to generate

        Returns:
            List of occurrence datetimes
        """
        exceptions = exceptions or set()

        # Map frequency to dateutil rrule frequency
        freq_map = {
            RecurrenceFrequency.HOURLY: rrule.HOURLY,
            RecurrenceFrequency.DAILY: DAILY,
            RecurrenceFrequency.WEEKLY: WEEKLY,
            RecurrenceFrequency.MONTHLY: MONTHLY,
            RecurrenceFrequency.YEARLY: YEARLY,
        }

        # Build rrule parameters
        rrule_params = {
            "freq": freq_map[pattern.frequency],
            "interval": pattern.interval,
            "dtstart": start_time,
        }

        # End condition
        if pattern.end_type == RecurrenceEndType.DATE and pattern.end_date:
            rrule_params["until"] = min(pattern.end_date, end_time)
        elif pattern.end_type == RecurrenceEndType.COUNT and pattern.count:
            rrule_params["count"] = min(pattern.count, limit)
        else:
            rrule_params["until"] = end_time

        # By weekday
        if pattern.by_weekday:
            weekday_map = {
                Weekday.MONDAY: rrule.MO,
                Weekday.TUESDAY: rrule.TU,
                Weekday.WEDNESDAY: rrule.WE,
                Weekday.THURSDAY: rrule.TH,
                Weekday.FRIDAY: rrule.FR,
                Weekday.SATURDAY: rrule.SA,
                Weekday.SUNDAY: rrule.SU,
            }
            rrule_params["byweekday"] = [weekday_map[d] for d in pattern.by_weekday]

        # By monthday
        if pattern.by_monthday:
            rrule_params["bymonthday"] = pattern.by_monthday

        # By month
        if pattern.by_month:
            rrule_params["bymonth"] = pattern.by_month

        # By setpos
        if pattern.by_setpos:
            rrule_params["bysetpos"] = pattern.by_setpos

        # Generate occurrences
        rule = DateUtilRRule(**rrule_params)
        occurrences = list(rule[:limit])

        # Filter by end_time and exceptions
        result = [
            dt for dt in occurrences
            if dt <= end_time and dt not in exceptions
        ]

        return result

    def get_next_occurrence(
        self,
        pattern: RecurrencePattern,
        start_time: datetime,
        after: datetime,
        exceptions: Optional[Set[datetime]] = None,
    ) -> Optional[datetime]:
        """
        Get the next occurrence after a specific datetime.

        Args:
            pattern: Recurrence pattern
            start_time: Start time of the recurring event
            after: Find next occurrence after this datetime
            exceptions: Exception dates to exclude

        Returns:
            Next occurrence datetime, or None if no more occurrences
        """
        # Generate occurrences up to a year from 'after'
        end_range = after + timedelta(days=365)

        occurrences = self.generate_occurrences(
            pattern=pattern,
            start_time=start_time,
            end_time=end_range,
            exceptions=exceptions,
            limit=100,
        )

        # Find first occurrence after 'after'
        for occurrence in occurrences:
            if occurrence > after:
                return occurrence

        return None

    def get_occurrence_count(
        self,
        pattern: RecurrencePattern,
        start_time: datetime,
        end_time: datetime,
        exceptions: Optional[Set[datetime]] = None,
    ) -> int:
        """
        Count the number of occurrences in a date range.

        Args:
            pattern: Recurrence pattern
            start_time: Start time of the recurring event
            end_time: End of range
            exceptions: Exception dates to exclude

        Returns:
            Number of occurrences
        """
        occurrences = self.generate_occurrences(
            pattern=pattern,
            start_time=start_time,
            end_time=end_time,
            exceptions=exceptions,
        )
        return len(occurrences)

    def is_valid_pattern(self, pattern: RecurrencePattern) -> bool:
        """
        Validate a recurrence pattern.

        Args:
            pattern: Pattern to validate

        Returns:
            True if pattern is valid
        """
        try:
            pattern._validate()
            return True
        except ValueError:
            return False

    def create_simple_pattern(
        self,
        frequency: str,
        interval: int = 1,
        end_date: Optional[datetime] = None,
        count: Optional[int] = None,
    ) -> RecurrencePattern:
        """
        Create a simple recurrence pattern.

        Args:
            frequency: "daily", "weekly", "monthly", or "yearly"
            interval: Interval between recurrences
            end_date: Optional end date
            count: Optional occurrence count

        Returns:
            RecurrencePattern instance
        """
        freq = RecurrenceFrequency(frequency.lower())

        if end_date:
            end_type = RecurrenceEndType.DATE
        elif count:
            end_type = RecurrenceEndType.COUNT
        else:
            end_type = RecurrenceEndType.NEVER

        return RecurrencePattern(
            frequency=freq,
            interval=interval,
            end_type=end_type,
            end_date=end_date,
            count=count,
        )

    def create_weekly_pattern(
        self,
        weekdays: List[str],
        interval: int = 1,
        end_date: Optional[datetime] = None,
        count: Optional[int] = None,
    ) -> RecurrencePattern:
        """
        Create a weekly recurrence pattern.

        Args:
            weekdays: List of weekday names (e.g., ["monday", "wednesday", "friday"])
            interval: Interval in weeks
            end_date: Optional end date
            count: Optional occurrence count

        Returns:
            RecurrencePattern instance
        """
        weekday_map = {
            "monday": Weekday.MONDAY,
            "tuesday": Weekday.TUESDAY,
            "wednesday": Weekday.WEDNESDAY,
            "thursday": Weekday.THURSDAY,
            "friday": Weekday.FRIDAY,
            "saturday": Weekday.SATURDAY,
            "sunday": Weekday.SUNDAY,
        }

        by_weekday = [weekday_map[day.lower()] for day in weekdays]

        if end_date:
            end_type = RecurrenceEndType.DATE
        elif count:
            end_type = RecurrenceEndType.COUNT
        else:
            end_type = RecurrenceEndType.NEVER

        return RecurrencePattern(
            frequency=RecurrenceFrequency.WEEKLY,
            interval=interval,
            by_weekday=by_weekday,
            end_type=end_type,
            end_date=end_date,
            count=count,
        )

    def create_monthly_pattern(
        self,
        day_of_month: Optional[int] = None,
        weekday: Optional[str] = None,
        week_number: Optional[int] = None,
        interval: int = 1,
        end_date: Optional[datetime] = None,
        count: Optional[int] = None,
    ) -> RecurrencePattern:
        """
        Create a monthly recurrence pattern.

        Args:
            day_of_month: Specific day of month (e.g., 15 for the 15th)
            weekday: Weekday name (for patterns like "2nd Tuesday")
            week_number: Week number (1-4 for 1st-4th, -1 for last)
            interval: Interval in months
            end_date: Optional end date
            count: Optional occurrence count

        Returns:
            RecurrencePattern instance
        """
        by_monthday = [day_of_month] if day_of_month else []
        by_weekday = []
        by_setpos = []

        if weekday and week_number:
            weekday_map = {
                "monday": Weekday.MONDAY,
                "tuesday": Weekday.TUESDAY,
                "wednesday": Weekday.WEDNESDAY,
                "thursday": Weekday.THURSDAY,
                "friday": Weekday.FRIDAY,
                "saturday": Weekday.SATURDAY,
                "sunday": Weekday.SUNDAY,
            }
            by_weekday = [weekday_map[weekday.lower()]]
            by_setpos = [week_number]

        if end_date:
            end_type = RecurrenceEndType.DATE
        elif count:
            end_type = RecurrenceEndType.COUNT
        else:
            end_type = RecurrenceEndType.NEVER

        return RecurrencePattern(
            frequency=RecurrenceFrequency.MONTHLY,
            interval=interval,
            by_monthday=by_monthday,
            by_weekday=by_weekday,
            by_setpos=by_setpos,
            end_type=end_type,
            end_date=end_date,
            count=count,
        )
