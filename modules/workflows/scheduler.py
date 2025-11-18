"""
NEXUS Workflow Scheduler
Advanced scheduling system for workflows with cron support
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import uuid
from collections import defaultdict


class ScheduleType(Enum):
    """Types of schedules"""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    DELAYED = "delayed"


class ScheduleStatus(Enum):
    """Schedule status"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    EXPIRED = "expired"


@dataclass
class CronExpression:
    """Cron expression parser"""
    minute: str = "*"
    hour: str = "*"
    day: str = "*"
    month: str = "*"
    weekday: str = "*"

    @classmethod
    def from_string(cls, cron_string: str) -> 'CronExpression':
        """Parse cron string: minute hour day month weekday"""
        parts = cron_string.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_string}")

        return cls(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            weekday=parts[4]
        )

    def to_string(self) -> str:
        """Convert to cron string"""
        return f"{self.minute} {self.hour} {self.day} {self.month} {self.weekday}"


@dataclass
class Schedule:
    """Workflow schedule definition"""
    id: str
    workflow_id: str
    schedule_type: ScheduleType
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    timezone: str = "UTC"
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleExecution:
    """Record of a scheduled execution"""
    id: str
    schedule_id: str
    workflow_id: str
    scheduled_time: datetime
    actual_time: datetime
    execution_id: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None


class CronParser:
    """Parse and calculate cron expressions"""

    def __init__(self):
        self.special_strings = {
            '@yearly': '0 0 1 1 *',
            '@annually': '0 0 1 1 *',
            '@monthly': '0 0 1 * *',
            '@weekly': '0 0 * * 0',
            '@daily': '0 0 * * *',
            '@midnight': '0 0 * * *',
            '@hourly': '0 * * * *',
        }

    def parse(self, expression: str) -> CronExpression:
        """Parse cron expression"""
        # Handle special strings
        if expression.startswith('@'):
            expression = self.special_strings.get(expression.lower(), expression)

        return CronExpression.from_string(expression)

    def next_run(self, cron: CronExpression, from_time: Optional[datetime] = None) -> datetime:
        """Calculate next run time from cron expression"""
        if from_time is None:
            from_time = datetime.utcnow()

        # This is a simplified implementation
        # In production, use croniter library for accurate cron parsing

        current = from_time.replace(second=0, microsecond=0)

        # If using wildcards, add 1 minute and return
        if cron.minute == '*' and cron.hour == '*':
            return current + timedelta(minutes=1)

        # Try to find next match within next 24 hours
        for _ in range(1440):  # 24 hours * 60 minutes
            current += timedelta(minutes=1)

            if self._matches(cron, current):
                return current

        # If no match found, return 1 hour from now
        return from_time + timedelta(hours=1)

    def _matches(self, cron: CronExpression, dt: datetime) -> bool:
        """Check if datetime matches cron expression"""
        # Simplified matching - in production use croniter
        if cron.minute != '*' and str(dt.minute) != cron.minute:
            # Check if minute is in range or list
            if not self._matches_field(cron.minute, dt.minute, 0, 59):
                return False

        if cron.hour != '*' and str(dt.hour) != cron.hour:
            if not self._matches_field(cron.hour, dt.hour, 0, 23):
                return False

        if cron.day != '*' and str(dt.day) != cron.day:
            if not self._matches_field(cron.day, dt.day, 1, 31):
                return False

        if cron.month != '*' and str(dt.month) != cron.month:
            if not self._matches_field(cron.month, dt.month, 1, 12):
                return False

        if cron.weekday != '*':
            weekday = dt.weekday()  # 0 = Monday
            if not self._matches_field(cron.weekday, weekday, 0, 6):
                return False

        return True

    def _matches_field(self, pattern: str, value: int, min_val: int, max_val: int) -> bool:
        """Check if value matches cron field pattern"""
        # Handle wildcards
        if pattern == '*':
            return True

        # Handle lists (e.g., "1,3,5")
        if ',' in pattern:
            return str(value) in pattern.split(',')

        # Handle ranges (e.g., "1-5")
        if '-' in pattern:
            start, end = pattern.split('-')
            return int(start) <= value <= int(end)

        # Handle steps (e.g., "*/5")
        if '/' in pattern:
            parts = pattern.split('/')
            step = int(parts[1])
            if parts[0] == '*':
                return value % step == 0
            else:
                start = int(parts[0])
                return value >= start and (value - start) % step == 0

        # Exact match
        return str(value) == pattern


class WorkflowScheduler:
    """Main workflow scheduler"""

    def __init__(self):
        self.schedules: Dict[str, Schedule] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.cron_parser = CronParser()
        self.execution_callback: Optional[Callable] = None
        self.is_running = False

    def set_execution_callback(self, callback: Callable) -> None:
        """Set callback function for executing workflows"""
        self.execution_callback = callback

    def create_schedule(
        self,
        workflow_id: str,
        schedule_type: ScheduleType,
        **kwargs
    ) -> Schedule:
        """Create a new schedule"""
        schedule_id = kwargs.get('id', str(uuid.uuid4()))

        schedule = Schedule(
            id=schedule_id,
            workflow_id=workflow_id,
            schedule_type=schedule_type,
            status=ScheduleStatus.ACTIVE,
            cron_expression=kwargs.get('cron_expression'),
            interval_seconds=kwargs.get('interval_seconds'),
            start_time=kwargs.get('start_time'),
            end_time=kwargs.get('end_time'),
            max_runs=kwargs.get('max_runs'),
            timezone=kwargs.get('timezone', 'UTC'),
            config=kwargs.get('config', {}),
            metadata=kwargs.get('metadata', {})
        )

        # Calculate next run
        schedule.next_run = self._calculate_next_run(schedule)

        self.schedules[schedule_id] = schedule

        # Start schedule if scheduler is running
        if self.is_running:
            self._start_schedule_task(schedule)

        return schedule

    def update_schedule(self, schedule_id: str, **updates) -> Optional[Schedule]:
        """Update a schedule"""
        schedule = self.schedules.get(schedule_id)
        if not schedule:
            return None

        for key, value in updates.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)

        schedule.updated_at = datetime.utcnow()

        # Recalculate next run if schedule changed
        if any(k in updates for k in ['cron_expression', 'interval_seconds', 'start_time']):
            schedule.next_run = self._calculate_next_run(schedule)

        # Restart task if running
        if schedule_id in self.tasks:
            self.tasks[schedule_id].cancel()
            self._start_schedule_task(schedule)

        return schedule

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule"""
        if schedule_id in self.schedules:
            # Cancel task if running
            if schedule_id in self.tasks:
                self.tasks[schedule_id].cancel()
                del self.tasks[schedule_id]

            del self.schedules[schedule_id]
            return True

        return False

    def pause_schedule(self, schedule_id: str) -> bool:
        """Pause a schedule"""
        schedule = self.schedules.get(schedule_id)
        if schedule:
            schedule.status = ScheduleStatus.PAUSED

            # Cancel task
            if schedule_id in self.tasks:
                self.tasks[schedule_id].cancel()
                del self.tasks[schedule_id]

            return True

        return False

    def resume_schedule(self, schedule_id: str) -> bool:
        """Resume a paused schedule"""
        schedule = self.schedules.get(schedule_id)
        if schedule and schedule.status == ScheduleStatus.PAUSED:
            schedule.status = ScheduleStatus.ACTIVE
            schedule.next_run = self._calculate_next_run(schedule)

            if self.is_running:
                self._start_schedule_task(schedule)

            return True

        return False

    async def start(self) -> None:
        """Start the scheduler"""
        self.is_running = True

        # Start tasks for all active schedules
        for schedule in self.schedules.values():
            if schedule.status == ScheduleStatus.ACTIVE:
                self._start_schedule_task(schedule)

    async def stop(self) -> None:
        """Stop the scheduler"""
        self.is_running = False

        # Cancel all tasks
        for task in self.tasks.values():
            task.cancel()

        self.tasks.clear()

    def _start_schedule_task(self, schedule: Schedule) -> None:
        """Start monitoring task for a schedule"""
        task = asyncio.create_task(self._run_schedule(schedule))
        self.tasks[schedule.id] = task

    async def _run_schedule(self, schedule: Schedule) -> None:
        """Run a schedule continuously"""
        while self.is_running and schedule.status == ScheduleStatus.ACTIVE:
            try:
                # Check if expired
                if schedule.end_time and datetime.utcnow() > schedule.end_time:
                    schedule.status = ScheduleStatus.EXPIRED
                    break

                # Check if max runs reached
                if schedule.max_runs and schedule.run_count >= schedule.max_runs:
                    schedule.status = ScheduleStatus.EXPIRED
                    break

                # Wait until next run
                if schedule.next_run:
                    now = datetime.utcnow()
                    if schedule.next_run > now:
                        wait_seconds = (schedule.next_run - now).total_seconds()
                        await asyncio.sleep(wait_seconds)

                # Execute workflow
                await self._execute_schedule(schedule)

                # Calculate next run
                schedule.next_run = self._calculate_next_run(schedule)

                # For one-time schedules, mark as expired
                if schedule.schedule_type == ScheduleType.ONE_TIME:
                    schedule.status = ScheduleStatus.EXPIRED
                    break

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in schedule {schedule.id}: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _execute_schedule(self, schedule: Schedule) -> None:
        """Execute a scheduled workflow"""
        schedule.last_run = datetime.utcnow()
        schedule.run_count += 1

        if self.execution_callback:
            try:
                await self.execution_callback(schedule.workflow_id, {
                    "schedule_id": schedule.id,
                    "scheduled_time": schedule.next_run.isoformat() if schedule.next_run else None,
                    "run_count": schedule.run_count
                })
            except Exception as e:
                print(f"Error executing workflow {schedule.workflow_id}: {e}")

    def _calculate_next_run(self, schedule: Schedule) -> Optional[datetime]:
        """Calculate next run time for schedule"""
        now = datetime.utcnow()

        # Check start time
        if schedule.start_time and now < schedule.start_time:
            base_time = schedule.start_time
        else:
            base_time = now

        # Check end time
        if schedule.end_time and base_time >= schedule.end_time:
            return None

        # Calculate based on schedule type
        if schedule.schedule_type == ScheduleType.CRON:
            if schedule.cron_expression:
                cron = self.cron_parser.parse(schedule.cron_expression)
                return self.cron_parser.next_run(cron, base_time)

        elif schedule.schedule_type == ScheduleType.INTERVAL:
            if schedule.interval_seconds:
                if schedule.last_run:
                    return schedule.last_run + timedelta(seconds=schedule.interval_seconds)
                else:
                    return base_time + timedelta(seconds=schedule.interval_seconds)

        elif schedule.schedule_type == ScheduleType.ONE_TIME:
            if schedule.last_run:
                return None  # Already executed
            return base_time

        elif schedule.schedule_type == ScheduleType.DELAYED:
            delay_seconds = schedule.config.get('delay_seconds', 0)
            return base_time + timedelta(seconds=delay_seconds)

        return None

    def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get schedule by ID"""
        return self.schedules.get(schedule_id)

    def list_schedules(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[ScheduleStatus] = None
    ) -> List[Schedule]:
        """List schedules with optional filters"""
        schedules = list(self.schedules.values())

        if workflow_id:
            schedules = [s for s in schedules if s.workflow_id == workflow_id]

        if status:
            schedules = [s for s in schedules if s.status == status]

        return schedules

    def get_upcoming_executions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get upcoming scheduled executions"""
        now = datetime.utcnow()
        end_time = now + timedelta(hours=hours)

        upcoming = []
        for schedule in self.schedules.values():
            if schedule.status == ScheduleStatus.ACTIVE and schedule.next_run:
                if now <= schedule.next_run <= end_time:
                    upcoming.append({
                        "schedule_id": schedule.id,
                        "workflow_id": schedule.workflow_id,
                        "next_run": schedule.next_run,
                        "type": schedule.schedule_type.value
                    })

        # Sort by next_run
        upcoming.sort(key=lambda x: x['next_run'])

        return upcoming


# Global scheduler instance
workflow_scheduler = WorkflowScheduler()
