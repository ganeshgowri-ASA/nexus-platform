"""
Calendar Sync Module

Handles synchronization with external calendar services (Google Calendar, Outlook, iCal, CalDAV).
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from icalendar import Calendar as iCalendar, Event as iCalEvent, vDatetime
import base64

from .event_manager import Event, EventManager, Attendee
from .calendar_engine import Calendar, CalendarEngine


class SyncProvider(Enum):
    """External calendar provider."""
    GOOGLE = "google"
    OUTLOOK = "outlook"
    ICAL = "ical"
    CALDAV = "caldav"
    APPLE = "apple"


class SyncStatus(Enum):
    """Sync status."""
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"


class SyncDirection(Enum):
    """Sync direction."""
    IMPORT = "import"  # External -> Local
    EXPORT = "export"  # Local -> External
    TWO_WAY = "two_way"  # Bidirectional


@dataclass
class SyncConfig:
    """
    Sync configuration for a calendar.

    Attributes:
        calendar_id: Local calendar ID
        provider: External provider
        external_calendar_id: External calendar ID
        direction: Sync direction
        enabled: Whether sync is enabled
        auto_sync: Automatically sync on interval
        sync_interval_minutes: Sync interval
        last_sync: Last sync timestamp
        credentials: Provider credentials
    """
    calendar_id: str
    provider: SyncProvider
    external_calendar_id: str
    direction: SyncDirection = SyncDirection.TWO_WAY
    enabled: bool = True
    auto_sync: bool = True
    sync_interval_minutes: int = 15
    last_sync: Optional[datetime] = None
    credentials: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "calendar_id": self.calendar_id,
            "provider": self.provider.value,
            "external_calendar_id": self.external_calendar_id,
            "direction": self.direction.value,
            "enabled": self.enabled,
            "auto_sync": self.auto_sync,
            "sync_interval_minutes": self.sync_interval_minutes,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "credentials": self.credentials,
        }


@dataclass
class SyncResult:
    """
    Result of a sync operation.

    Attributes:
        config: Sync configuration
        status: Sync status
        events_imported: Number of events imported
        events_exported: Number of events exported
        events_updated: Number of events updated
        events_deleted: Number of events deleted
        errors: List of error messages
        started_at: Sync start time
        completed_at: Sync completion time
    """
    config: SyncConfig
    status: SyncStatus
    events_imported: int = 0
    events_exported: int = 0
    events_updated: int = 0
    events_deleted: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config": self.config.to_dict(),
            "status": self.status.value,
            "events_imported": self.events_imported,
            "events_exported": self.events_exported,
            "events_updated": self.events_updated,
            "events_deleted": self.events_deleted,
            "errors": self.errors,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": (self.completed_at - self.started_at).total_seconds()
                               if self.completed_at else None,
        }


class SyncManager:
    """
    Manages calendar synchronization with external services.

    Features:
    - Google Calendar sync
    - Outlook/Exchange sync
    - iCal import/export
    - CalDAV support
    - Two-way sync
    - Conflict resolution
    """

    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
        calendar_engine: Optional[CalendarEngine] = None,
    ):
        """
        Initialize the sync manager.

        Args:
            event_manager: Event manager instance
            calendar_engine: Calendar engine instance
        """
        self.event_manager = event_manager or EventManager()
        self.calendar_engine = calendar_engine or CalendarEngine()
        self._sync_configs: Dict[str, SyncConfig] = {}
        self._sync_history: List[SyncResult] = []

    def add_sync_config(
        self,
        config: SyncConfig,
    ) -> None:
        """
        Add a sync configuration.

        Args:
            config: Sync configuration
        """
        self._sync_configs[config.calendar_id] = config

    def remove_sync_config(
        self,
        calendar_id: str,
    ) -> bool:
        """
        Remove a sync configuration.

        Args:
            calendar_id: Calendar ID

        Returns:
            True if removed successfully
        """
        if calendar_id in self._sync_configs:
            del self._sync_configs[calendar_id]
            return True
        return False

    def sync_calendar(
        self,
        calendar_id: str,
    ) -> SyncResult:
        """
        Sync a calendar with its external provider.

        Args:
            calendar_id: Calendar ID to sync

        Returns:
            Sync result
        """
        config = self._sync_configs.get(calendar_id)
        if not config:
            result = SyncResult(
                config=SyncConfig(calendar_id, SyncProvider.GOOGLE, ""),
                status=SyncStatus.ERROR,
            )
            result.errors.append("No sync configuration found")
            return result

        if not config.enabled:
            result = SyncResult(
                config=config,
                status=SyncStatus.ERROR,
            )
            result.errors.append("Sync is disabled")
            return result

        # Create result
        result = SyncResult(
            config=config,
            status=SyncStatus.SYNCING,
        )

        try:
            # Perform sync based on provider
            if config.provider == SyncProvider.GOOGLE:
                self._sync_google_calendar(config, result)
            elif config.provider == SyncProvider.OUTLOOK:
                self._sync_outlook_calendar(config, result)
            elif config.provider == SyncProvider.ICAL:
                self._sync_ical_calendar(config, result)
            elif config.provider == SyncProvider.CALDAV:
                self._sync_caldav_calendar(config, result)
            else:
                result.errors.append(f"Unsupported provider: {config.provider}")
                result.status = SyncStatus.ERROR

            # Update sync status
            if not result.errors:
                result.status = SyncStatus.SUCCESS
                config.last_sync = datetime.now()
            else:
                result.status = SyncStatus.ERROR

        except Exception as e:
            result.status = SyncStatus.ERROR
            result.errors.append(f"Sync failed: {str(e)}")

        result.completed_at = datetime.now()
        self._sync_history.append(result)

        return result

    def _sync_google_calendar(
        self,
        config: SyncConfig,
        result: SyncResult,
    ) -> None:
        """
        Sync with Google Calendar.

        Args:
            config: Sync configuration
            result: Sync result to update
        """
        # TODO: Implement Google Calendar API integration
        # This would use the Google Calendar API v3

        # Placeholder implementation
        print(f"[GOOGLE SYNC] Syncing calendar {config.calendar_id}")

        # In a real implementation:
        # 1. Authenticate with Google OAuth2
        # 2. Fetch events from Google Calendar
        # 3. Compare with local events
        # 4. Import new/updated events
        # 5. Export local changes if two-way sync

        result.events_imported = 0
        result.events_exported = 0

    def _sync_outlook_calendar(
        self,
        config: SyncConfig,
        result: SyncResult,
    ) -> None:
        """
        Sync with Outlook/Exchange.

        Args:
            config: Sync configuration
            result: Sync result to update
        """
        # TODO: Implement Microsoft Graph API integration

        print(f"[OUTLOOK SYNC] Syncing calendar {config.calendar_id}")

        # In a real implementation:
        # 1. Authenticate with Microsoft Graph
        # 2. Fetch events from Outlook
        # 3. Sync events

        result.events_imported = 0
        result.events_exported = 0

    def _sync_ical_calendar(
        self,
        config: SyncConfig,
        result: SyncResult,
    ) -> None:
        """
        Sync with iCal feed.

        Args:
            config: Sync configuration
            result: Sync result to update
        """
        # iCal sync is typically one-way (import only)
        if config.direction == SyncDirection.EXPORT:
            result.errors.append("iCal sync only supports import")
            return

        # TODO: Fetch and parse iCal feed

        print(f"[ICAL SYNC] Syncing calendar {config.calendar_id}")

        result.events_imported = 0

    def _sync_caldav_calendar(
        self,
        config: SyncConfig,
        result: SyncResult,
    ) -> None:
        """
        Sync with CalDAV server.

        Args:
            config: Sync configuration
            result: Sync result to update
        """
        # TODO: Implement CalDAV protocol

        print(f"[CALDAV SYNC] Syncing calendar {config.calendar_id}")

        result.events_imported = 0
        result.events_exported = 0

    def export_to_ical(
        self,
        calendar_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        Export calendar to iCal format.

        Args:
            calendar_id: Calendar ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            iCal format string
        """
        # Get events
        events = self.event_manager.list_events(
            calendar_id=calendar_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Create iCalendar
        cal = iCalendar()
        cal.add('prodid', '-//NEXUS Calendar//nexus-platform//EN')
        cal.add('version', '2.0')

        # Get calendar info
        calendar = self.calendar_engine.get_calendar(calendar_id)
        if calendar:
            cal.add('x-wr-calname', calendar.name)
            cal.add('x-wr-timezone', calendar.timezone)

        # Add events
        for event in events:
            ical_event = self._event_to_ical(event)
            cal.add_component(ical_event)

        return cal.to_ical().decode('utf-8')

    def _event_to_ical(self, event: Event) -> iCalEvent:
        """
        Convert Event to iCal event.

        Args:
            event: Event to convert

        Returns:
            iCal event component
        """
        ical_event = iCalEvent()

        ical_event.add('uid', event.id)
        ical_event.add('summary', event.title)
        ical_event.add('dtstart', event.start_time)
        ical_event.add('dtend', event.end_time)

        if event.description:
            ical_event.add('description', event.description)

        if event.location:
            ical_event.add('location', event.location)

        if event.organizer:
            ical_event.add('organizer', f'mailto:{event.organizer}')

        # Add attendees
        for attendee in event.attendees:
            ical_event.add('attendee', f'mailto:{attendee.email}', parameters={
                'cn': attendee.name or attendee.email,
                'partstat': attendee.status.value.upper(),
                'role': 'OPT-PARTICIPANT' if attendee.optional else 'REQ-PARTICIPANT',
            })

        ical_event.add('status', event.status.value.upper())
        ical_event.add('created', event.created_at)
        ical_event.add('last-modified', event.updated_at)

        return ical_event

    def import_from_ical(
        self,
        calendar_id: str,
        ical_data: str,
    ) -> Dict[str, Any]:
        """
        Import events from iCal format.

        Args:
            calendar_id: Calendar ID to import into
            ical_data: iCal format string

        Returns:
            Import summary
        """
        try:
            cal = iCalendar.from_ical(ical_data)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse iCal data: {str(e)}",
                "events_imported": 0,
            }

        imported = 0
        errors = []

        for component in cal.walk():
            if component.name == "VEVENT":
                try:
                    event = self._ical_to_event(component, calendar_id)
                    self.event_manager.create_event(
                        title=event.title,
                        start_time=event.start_time,
                        end_time=event.end_time,
                        description=event.description,
                        location=event.location,
                        calendar_id=calendar_id,
                    )
                    imported += 1
                except Exception as e:
                    errors.append(f"Failed to import event: {str(e)}")

        return {
            "success": True,
            "events_imported": imported,
            "errors": errors,
        }

    def _ical_to_event(
        self,
        ical_event: iCalEvent,
        calendar_id: str,
    ) -> Event:
        """
        Convert iCal event to Event.

        Args:
            ical_event: iCal event component
            calendar_id: Calendar ID

        Returns:
            Event instance
        """
        title = str(ical_event.get('summary', 'Untitled Event'))
        start_time = ical_event.get('dtstart').dt
        end_time = ical_event.get('dtend').dt

        # Convert date to datetime if needed
        if isinstance(start_time, datetime):
            pass
        else:
            start_time = datetime.combine(start_time, datetime.min.time())
            end_time = datetime.combine(end_time, datetime.min.time())

        event = Event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=str(ical_event.get('description', '')),
            location=str(ical_event.get('location', '')),
            calendar_id=calendar_id,
        )

        return event

    def sync_all_calendars(self) -> List[SyncResult]:
        """
        Sync all configured calendars.

        Returns:
            List of sync results
        """
        results = []

        for calendar_id in self._sync_configs.keys():
            result = self.sync_calendar(calendar_id)
            results.append(result)

        return results

    def get_sync_status(
        self,
        calendar_id: str,
    ) -> Dict[str, Any]:
        """
        Get sync status for a calendar.

        Args:
            calendar_id: Calendar ID

        Returns:
            Sync status information
        """
        config = self._sync_configs.get(calendar_id)
        if not config:
            return {
                "synced": False,
                "error": "No sync configuration",
            }

        # Get latest sync result
        recent_results = [
            r for r in self._sync_history
            if r.config.calendar_id == calendar_id
        ]

        if recent_results:
            latest = max(recent_results, key=lambda r: r.started_at)
            return {
                "synced": True,
                "last_sync": config.last_sync.isoformat() if config.last_sync else None,
                "status": latest.status.value,
                "events_imported": latest.events_imported,
                "events_exported": latest.events_exported,
                "errors": latest.errors,
            }

        return {
            "synced": True,
            "last_sync": config.last_sync.isoformat() if config.last_sync else None,
            "status": "idle",
        }

    def get_sync_history(
        self,
        calendar_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get sync history.

        Args:
            calendar_id: Optional calendar ID filter
            limit: Maximum number of results

        Returns:
            List of sync results
        """
        results = self._sync_history

        if calendar_id:
            results = [r for r in results if r.config.calendar_id == calendar_id]

        # Sort by most recent first
        results.sort(key=lambda r: r.started_at, reverse=True)

        return [r.to_dict() for r in results[:limit]]
