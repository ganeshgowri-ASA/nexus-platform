"""Cron expression utilities"""
from croniter import croniter
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import pytz
from modules.scheduler.models.schemas import JobType


def validate_cron_expression(expression: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate a cron expression
    Returns: (is_valid, description, error_message)
    """
    try:
        if not croniter.is_valid(expression):
            return False, None, "Invalid cron expression format"

        # Try to get description
        description = get_cron_description(expression)
        return True, description, None

    except Exception as e:
        return False, None, str(e)


def get_cron_description(expression: str) -> str:
    """Get human-readable description of cron expression"""
    try:
        parts = expression.split()
        if len(parts) != 5:
            return expression

        minute, hour, day, month, dow = parts

        desc_parts = []

        # Minute
        if minute == "*":
            desc_parts.append("every minute")
        elif minute.startswith("*/"):
            desc_parts.append(f"every {minute[2:]} minutes")
        else:
            desc_parts.append(f"at minute {minute}")

        # Hour
        if hour == "*":
            if minute != "*":
                desc_parts.append("of every hour")
        elif hour.startswith("*/"):
            desc_parts.append(f"every {hour[2:]} hours")
        else:
            desc_parts.append(f"at {hour}:00")

        # Day of month
        if day != "*":
            if day.startswith("*/"):
                desc_parts.append(f"every {day[2:]} days")
            else:
                desc_parts.append(f"on day {day}")

        # Month
        if month != "*":
            months = {
                "1": "January", "2": "February", "3": "March",
                "4": "April", "5": "May", "6": "June",
                "7": "July", "8": "August", "9": "September",
                "10": "October", "11": "November", "12": "December"
            }
            desc_parts.append(f"in {months.get(month, month)}")

        # Day of week
        if dow != "*":
            days = {
                "0": "Sunday", "1": "Monday", "2": "Tuesday",
                "3": "Wednesday", "4": "Thursday", "5": "Friday", "6": "Saturday"
            }
            if "," in dow:
                day_names = [days.get(d, d) for d in dow.split(",")]
                desc_parts.append(f"on {', '.join(day_names)}")
            elif "-" in dow:
                start, end = dow.split("-")
                desc_parts.append(f"on {days.get(start, start)} through {days.get(end, end)}")
            else:
                desc_parts.append(f"on {days.get(dow, dow)}")

        return " ".join(desc_parts).capitalize()

    except Exception:
        return expression


def get_next_run_times(
    expression: str,
    count: int = 5,
    timezone: str = "UTC",
    base_time: Optional[datetime] = None
) -> List[datetime]:
    """Get next N run times for a cron expression"""
    try:
        tz = pytz.timezone(timezone)
        base = base_time or datetime.now(tz)

        cron = croniter(expression, base)
        next_runs = []

        for _ in range(count):
            next_run = cron.get_next(datetime)
            next_runs.append(next_run)

        return next_runs

    except Exception:
        return []


def calculate_next_run(
    job_type: JobType,
    cron_expression: Optional[str] = None,
    interval_seconds: Optional[int] = None,
    scheduled_time: Optional[datetime] = None,
    timezone: str = "UTC",
    base_time: Optional[datetime] = None
) -> Optional[datetime]:
    """Calculate next run time based on job type"""
    try:
        tz = pytz.timezone(timezone)
        base = base_time or datetime.now(tz)

        if job_type == JobType.CRON and cron_expression:
            cron = croniter(cron_expression, base)
            return cron.get_next(datetime)

        elif job_type == JobType.INTERVAL and interval_seconds:
            return base + timedelta(seconds=interval_seconds)

        elif job_type == JobType.DATE and scheduled_time:
            # Ensure timezone-aware
            if scheduled_time.tzinfo is None:
                scheduled_time = tz.localize(scheduled_time)
            return scheduled_time

        elif job_type == JobType.CALENDAR:
            # Calendar-based scheduling handled separately
            return None

        return None

    except Exception:
        return None


def get_cron_schedule_description(job_type: str, **kwargs) -> str:
    """Get human-readable schedule description"""
    if job_type == "cron" and kwargs.get("cron_expression"):
        return get_cron_description(kwargs["cron_expression"])

    elif job_type == "interval" and kwargs.get("interval_seconds"):
        seconds = kwargs["interval_seconds"]
        if seconds < 60:
            return f"Every {seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"Every {minutes} minute(s)"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"Every {hours} hour(s)"
        else:
            days = seconds // 86400
            return f"Every {days} day(s)"

    elif job_type == "date" and kwargs.get("scheduled_time"):
        return f"Once at {kwargs['scheduled_time']}"

    elif job_type == "calendar":
        return "Calendar-based schedule"

    return "Unknown schedule"
