"""
Automation Scheduler - Handles scheduled automation executions
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from croniter import croniter
import pytz

from src.database.models import Schedule, Automation
from src.utils.logger import get_logger
from src.utils.helpers import generate_id, current_timestamp

logger = get_logger(__name__)


class AutomationScheduler:
    """Manages automation scheduling"""

    def __init__(self, db: Session):
        self.db = db

    def create_schedule(
        self,
        automation_id: str,
        name: str,
        cron_expression: str,
        timezone: str = "UTC",
        input_data: dict = None,
        created_by: str = None,
    ) -> Schedule:
        """
        Create a new schedule

        Args:
            automation_id: ID of the automation to schedule
            name: Name for the schedule
            cron_expression: Cron expression for scheduling
            timezone: Timezone for the schedule
            input_data: Default input data for scheduled runs
            created_by: User who created the schedule

        Returns:
            Schedule object
        """
        # Validate cron expression
        if not croniter.is_valid(cron_expression):
            raise ValueError(f"Invalid cron expression: {cron_expression}")

        # Validate timezone
        try:
            tz = pytz.timezone(timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Invalid timezone: {timezone}")

        # Calculate next run time
        next_run_at = self._calculate_next_run(cron_expression, timezone)

        schedule = Schedule(
            id=generate_id(),
            automation_id=automation_id,
            name=name,
            cron_expression=cron_expression,
            timezone=timezone,
            is_active=True,
            input_data=input_data or {},
            next_run_at=next_run_at,
            created_at=current_timestamp(),
            created_by=created_by,
        )

        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)

        logger.info(
            f"Created schedule {schedule.id} for automation {automation_id}"
        )
        return schedule

    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID"""
        return (
            self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
        )

    def list_schedules(
        self,
        automation_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Schedule]:
        """List schedules with optional filtering"""
        query = self.db.query(Schedule)

        if automation_id:
            query = query.filter(Schedule.automation_id == automation_id)

        if is_active is not None:
            query = query.filter(Schedule.is_active == is_active)

        return query.offset(skip).limit(limit).all()

    def update_schedule(
        self,
        schedule_id: str,
        name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        timezone: Optional[str] = None,
        is_active: Optional[bool] = None,
        input_data: Optional[dict] = None,
    ) -> Schedule:
        """Update a schedule"""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        if name is not None:
            schedule.name = name

        if cron_expression is not None:
            if not croniter.is_valid(cron_expression):
                raise ValueError(f"Invalid cron expression: {cron_expression}")
            schedule.cron_expression = cron_expression

        if timezone is not None:
            try:
                pytz.timezone(timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                raise ValueError(f"Invalid timezone: {timezone}")
            schedule.timezone = timezone

        if is_active is not None:
            schedule.is_active = is_active

        if input_data is not None:
            schedule.input_data = input_data

        # Recalculate next run time if cron or timezone changed
        if cron_expression is not None or timezone is not None:
            schedule.next_run_at = self._calculate_next_run(
                schedule.cron_expression, schedule.timezone
            )

        schedule.updated_at = current_timestamp()
        self.db.commit()
        self.db.refresh(schedule)

        logger.info(f"Updated schedule {schedule_id}")
        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule"""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            return False

        self.db.delete(schedule)
        self.db.commit()

        logger.info(f"Deleted schedule {schedule_id}")
        return True

    def get_due_schedules(self) -> List[Schedule]:
        """Get all schedules that are due to run"""
        now = current_timestamp()
        schedules = (
            self.db.query(Schedule)
            .filter(Schedule.is_active == True)
            .filter(Schedule.next_run_at <= now)
            .all()
        )

        return schedules

    def mark_schedule_executed(self, schedule_id: str):
        """Mark a schedule as executed and calculate next run time"""
        schedule = self.get_schedule(schedule_id)
        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        schedule.last_run_at = current_timestamp()
        schedule.run_count += 1
        schedule.next_run_at = self._calculate_next_run(
            schedule.cron_expression, schedule.timezone
        )

        self.db.commit()
        self.db.refresh(schedule)

        logger.info(
            f"Schedule {schedule_id} executed, next run at {schedule.next_run_at}"
        )

    def _calculate_next_run(
        self, cron_expression: str, timezone: str = "UTC"
    ) -> datetime:
        """Calculate the next run time based on cron expression"""
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        cron = croniter(cron_expression, now)
        next_run = cron.get_next(datetime)

        # Convert to UTC for storage
        next_run_utc = next_run.astimezone(pytz.UTC).replace(tzinfo=None)

        return next_run_utc

    def validate_cron_expression(self, cron_expression: str) -> bool:
        """Validate a cron expression"""
        return croniter.is_valid(cron_expression)
