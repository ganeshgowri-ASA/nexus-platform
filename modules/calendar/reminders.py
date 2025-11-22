"""
Reminder Manager Module

Handles event reminders and notifications across multiple channels.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from collections import defaultdict

from .event_manager import Event, EventManager, Reminder


class ReminderMethod(Enum):
    """Reminder delivery method."""
    EMAIL = "email"
    POPUP = "popup"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class ReminderStatus(Enum):
    """Reminder status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SNOOZED = "snoozed"
    DISMISSED = "dismissed"


@dataclass
class ScheduledReminder:
    """
    Represents a scheduled reminder.

    Attributes:
        id: Unique reminder ID
        event_id: Associated event ID
        event_title: Event title
        event_start: Event start time
        reminder_time: When to send the reminder
        method: Delivery method
        status: Reminder status
        recipient: Recipient (email, phone, etc.)
        message: Reminder message
        snooze_until: If snoozed, when to remind again
        attempts: Number of delivery attempts
        created_at: Creation timestamp
    """
    id: str
    event_id: str
    event_title: str
    event_start: datetime
    reminder_time: datetime
    method: ReminderMethod
    recipient: str
    status: ReminderStatus = ReminderStatus.PENDING
    message: Optional[str] = None
    snooze_until: Optional[datetime] = None
    attempts: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "event_title": self.event_title,
            "event_start": self.event_start.isoformat(),
            "reminder_time": self.reminder_time.isoformat(),
            "method": self.method.value,
            "recipient": self.recipient,
            "status": self.status.value,
            "message": self.message,
            "snooze_until": self.snooze_until.isoformat() if self.snooze_until else None,
            "attempts": self.attempts,
            "created_at": self.created_at.isoformat(),
        }


class ReminderManager:
    """
    Manages event reminders and notifications.

    Features:
    - Schedule reminders
    - Multiple delivery methods
    - Snooze functionality
    - Retry failed reminders
    - Custom reminder messages
    """

    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
    ):
        """
        Initialize the reminder manager.

        Args:
            event_manager: Event manager instance
        """
        self.event_manager = event_manager or EventManager()
        self._scheduled_reminders: Dict[str, ScheduledReminder] = {}
        self._delivery_handlers: Dict[ReminderMethod, Callable] = {}
        self._running = False

    def schedule_reminders_for_event(
        self,
        event: Event,
        recipient: str,
    ) -> List[ScheduledReminder]:
        """
        Schedule all reminders for an event.

        Args:
            event: Event to create reminders for
            recipient: Reminder recipient

        Returns:
            List of scheduled reminders
        """
        scheduled = []

        for reminder in event.reminders:
            reminder_time = event.start_time - timedelta(minutes=reminder.minutes_before)

            # Don't schedule reminders in the past
            if reminder_time <= datetime.now():
                continue

            scheduled_reminder = ScheduledReminder(
                id=f"{event.id}_{reminder.minutes_before}_{reminder.method}",
                event_id=event.id,
                event_title=event.title,
                event_start=event.start_time,
                reminder_time=reminder_time,
                method=ReminderMethod(reminder.method),
                recipient=recipient,
                message=self._generate_reminder_message(event, reminder.minutes_before),
            )

            self._scheduled_reminders[scheduled_reminder.id] = scheduled_reminder
            scheduled.append(scheduled_reminder)

        return scheduled

    def _generate_reminder_message(
        self,
        event: Event,
        minutes_before: int,
    ) -> str:
        """
        Generate a reminder message for an event.

        Args:
            event: Event
            minutes_before: Minutes before event

        Returns:
            Formatted reminder message
        """
        if minutes_before == 0:
            time_text = "now"
        elif minutes_before < 60:
            time_text = f"in {minutes_before} minutes"
        elif minutes_before < 1440:  # Less than a day
            hours = minutes_before // 60
            time_text = f"in {hours} hour{'s' if hours > 1 else ''}"
        else:
            days = minutes_before // 1440
            time_text = f"in {days} day{'s' if days > 1 else ''}"

        message = f"Reminder: {event.title} starts {time_text}"

        if event.location:
            message += f" at {event.location}"

        message += f" on {event.start_time.strftime('%B %d, %Y at %I:%M %p')}"

        if event.description:
            message += f"\n\nDescription: {event.description}"

        return message

    def get_pending_reminders(
        self,
        before_time: Optional[datetime] = None,
    ) -> List[ScheduledReminder]:
        """
        Get pending reminders.

        Args:
            before_time: Get reminders due before this time (defaults to now)

        Returns:
            List of pending reminders
        """
        if before_time is None:
            before_time = datetime.now()

        pending = []

        for reminder in self._scheduled_reminders.values():
            # Check if reminder is due
            if reminder.status == ReminderStatus.PENDING:
                if reminder.reminder_time <= before_time:
                    pending.append(reminder)
            elif reminder.status == ReminderStatus.SNOOZED:
                if reminder.snooze_until and reminder.snooze_until <= before_time:
                    pending.append(reminder)

        return pending

    def send_reminder(
        self,
        reminder: ScheduledReminder,
    ) -> bool:
        """
        Send a reminder.

        Args:
            reminder: Reminder to send

        Returns:
            True if sent successfully
        """
        # Get delivery handler for this method
        handler = self._delivery_handlers.get(reminder.method)

        if not handler:
            # Default handlers
            if reminder.method == ReminderMethod.EMAIL:
                success = self._send_email_reminder(reminder)
            elif reminder.method == ReminderMethod.POPUP:
                success = self._send_popup_reminder(reminder)
            elif reminder.method == ReminderMethod.SMS:
                success = self._send_sms_reminder(reminder)
            elif reminder.method == ReminderMethod.PUSH:
                success = self._send_push_reminder(reminder)
            else:
                success = False
        else:
            success = handler(reminder)

        # Update reminder status
        reminder.attempts += 1

        if success:
            reminder.status = ReminderStatus.SENT
        else:
            reminder.status = ReminderStatus.FAILED

        return success

    def _send_email_reminder(self, reminder: ScheduledReminder) -> bool:
        """Send email reminder."""
        # TODO: Integrate with email module
        print(f"[EMAIL] To: {reminder.recipient}")
        print(f"Subject: Reminder: {reminder.event_title}")
        print(f"Body: {reminder.message}")
        return True

    def _send_popup_reminder(self, reminder: ScheduledReminder) -> bool:
        """Send popup reminder."""
        # TODO: Integrate with UI notification system
        print(f"[POPUP] {reminder.message}")
        return True

    def _send_sms_reminder(self, reminder: ScheduledReminder) -> bool:
        """Send SMS reminder."""
        # TODO: Integrate with SMS service (Twilio, etc.)
        print(f"[SMS] To: {reminder.recipient}")
        print(f"Message: {reminder.message}")
        return True

    def _send_push_reminder(self, reminder: ScheduledReminder) -> bool:
        """Send push notification."""
        # TODO: Integrate with push notification service
        print(f"[PUSH] To: {reminder.recipient}")
        print(f"Message: {reminder.message}")
        return True

    def register_delivery_handler(
        self,
        method: ReminderMethod,
        handler: Callable[[ScheduledReminder], bool],
    ) -> None:
        """
        Register a custom delivery handler.

        Args:
            method: Reminder method
            handler: Callable that takes a ScheduledReminder and returns success bool
        """
        self._delivery_handlers[method] = handler

    def snooze_reminder(
        self,
        reminder_id: str,
        minutes: int = 10,
    ) -> bool:
        """
        Snooze a reminder.

        Args:
            reminder_id: Reminder ID
            minutes: Minutes to snooze

        Returns:
            True if snoozed successfully
        """
        reminder = self._scheduled_reminders.get(reminder_id)
        if not reminder:
            return False

        reminder.status = ReminderStatus.SNOOZED
        reminder.snooze_until = datetime.now() + timedelta(minutes=minutes)

        return True

    def dismiss_reminder(
        self,
        reminder_id: str,
    ) -> bool:
        """
        Dismiss a reminder.

        Args:
            reminder_id: Reminder ID

        Returns:
            True if dismissed successfully
        """
        reminder = self._scheduled_reminders.get(reminder_id)
        if not reminder:
            return False

        reminder.status = ReminderStatus.DISMISSED
        return True

    def process_reminders(self) -> Dict[str, Any]:
        """
        Process all pending reminders.

        Returns:
            Summary of processed reminders
        """
        pending = self.get_pending_reminders()

        sent = 0
        failed = 0

        for reminder in pending:
            # Reset status if snoozed
            if reminder.status == ReminderStatus.SNOOZED:
                reminder.status = ReminderStatus.PENDING
                reminder.snooze_until = None

            # Send reminder
            if self.send_reminder(reminder):
                sent += 1
            else:
                failed += 1

        return {
            "processed": len(pending),
            "sent": sent,
            "failed": failed,
        }

    async def start_reminder_loop(
        self,
        check_interval_seconds: int = 60,
    ) -> None:
        """
        Start the reminder processing loop.

        Args:
            check_interval_seconds: How often to check for reminders
        """
        self._running = True

        while self._running:
            # Process reminders
            self.process_reminders()

            # Wait before next check
            await asyncio.sleep(check_interval_seconds)

    def stop_reminder_loop(self) -> None:
        """Stop the reminder processing loop."""
        self._running = False

    def get_upcoming_reminders(
        self,
        hours: int = 24,
    ) -> List[ScheduledReminder]:
        """
        Get upcoming reminders within a time window.

        Args:
            hours: Number of hours to look ahead

        Returns:
            List of upcoming reminders
        """
        cutoff = datetime.now() + timedelta(hours=hours)

        upcoming = []
        for reminder in self._scheduled_reminders.values():
            if reminder.status == ReminderStatus.PENDING:
                if datetime.now() <= reminder.reminder_time <= cutoff:
                    upcoming.append(reminder)

        # Sort by reminder time
        upcoming.sort(key=lambda r: r.reminder_time)

        return upcoming

    def get_reminder_statistics(self) -> Dict[str, Any]:
        """
        Get reminder statistics.

        Returns:
            Statistics about reminders
        """
        total = len(self._scheduled_reminders)
        status_counts = defaultdict(int)
        method_counts = defaultdict(int)

        for reminder in self._scheduled_reminders.values():
            status_counts[reminder.status.value] += 1
            method_counts[reminder.method.value] += 1

        return {
            "total_reminders": total,
            "by_status": dict(status_counts),
            "by_method": dict(method_counts),
            "pending": status_counts[ReminderStatus.PENDING.value],
            "sent": status_counts[ReminderStatus.SENT.value],
            "failed": status_counts[ReminderStatus.FAILED.value],
        }

    def retry_failed_reminders(
        self,
        max_attempts: int = 3,
    ) -> Dict[str, Any]:
        """
        Retry failed reminders.

        Args:
            max_attempts: Maximum delivery attempts

        Returns:
            Summary of retry results
        """
        failed = [
            r for r in self._scheduled_reminders.values()
            if r.status == ReminderStatus.FAILED and r.attempts < max_attempts
        ]

        retried = 0
        succeeded = 0

        for reminder in failed:
            reminder.status = ReminderStatus.PENDING
            if self.send_reminder(reminder):
                succeeded += 1
            retried += 1

        return {
            "retried": retried,
            "succeeded": succeeded,
            "still_failed": retried - succeeded,
        }
