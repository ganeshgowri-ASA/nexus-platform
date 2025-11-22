# NEXUS Calendar & Scheduling Module

A world-class, full-featured calendar system for the NEXUS platform with comprehensive scheduling, event management, and AI-powered features.

## Features

### 📅 Calendar Views
- **Month View**: Traditional calendar grid with events
- **Week View**: Week-based schedule with hourly slots
- **Day View**: Detailed daily schedule
- **Agenda View**: List of upcoming events
- **Year View**: Annual overview with event counts

### 📝 Event Management
- Create, read, update, delete events
- All-day and multi-day events
- Event categories and colors
- Location and video meeting links
- Rich descriptions and notes
- File attachments
- Event tags

### 🔄 Recurring Events
- Daily, weekly, monthly, yearly patterns
- Custom recurrence rules (RFC 5545 compliant)
- Exception dates
- Edit single or all occurrences
- Complex patterns (e.g., "2nd Tuesday of every month")

### 👥 Invitations & Attendees
- Send meeting invitations
- RSVP responses (Accept/Decline/Maybe)
- Required and optional attendees
- Guest permissions
- Attendee tracking
- Invitation reminders

### ⏰ Reminders & Notifications
- Email reminders
- Pop-up notifications
- SMS reminders (with integration)
- Push notifications
- Multiple reminders per event
- Snooze functionality
- Custom reminder times

### 🔗 Calendar Synchronization
- Google Calendar sync
- Outlook/Exchange sync
- iCal import/export
- CalDAV support
- Two-way synchronization
- Sync status tracking

### 📊 Availability & Scheduling
- Free/busy time tracking
- Working hours configuration
- Booking links for easy scheduling
- Find available time slots
- Out-of-office management
- Vacation tracking

### 🔍 Conflict Detection
- Automatic conflict detection
- Severity levels (hard, soft, adjacent)
- Conflict resolution suggestions
- Travel time consideration
- Back-to-back meeting warnings

### 🌍 Multiple Calendars
- Create unlimited calendars
- Calendar visibility controls
- Calendar sharing with permissions
- Color coding
- Overlay multiple calendars

### 🌐 Timezone Support
- Multi-timezone support
- Automatic timezone detection
- Timezone conversions
- DST handling
- Display events in user's timezone

### 🤖 AI-Powered Features
- Smart scheduling suggestions
- Meeting time optimization
- Auto-categorize events
- Natural language event creation
- Travel time detection
- Conflict resolution
- Meeting pattern analysis
- Calendar optimization tips

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Event Creation

```python
from modules.calendar import EventManager
from datetime import datetime, timedelta

# Initialize event manager
event_manager = EventManager()

# Create an event
start = datetime.now() + timedelta(hours=1)
end = start + timedelta(hours=2)

event = event_manager.create_event(
    title="Team Meeting",
    start_time=start,
    end_time=end,
    description="Discuss Q4 goals",
    location="Conference Room A"
)
```

### Creating Recurring Events

```python
from modules.calendar import RecurrenceEngine

recurrence_engine = RecurrenceEngine()

# Create a weekly pattern
pattern = recurrence_engine.create_weekly_pattern(
    weekdays=["monday", "wednesday", "friday"],
    count=10
)

# Generate occurrences
occurrences = recurrence_engine.generate_occurrences(
    pattern=pattern,
    start_time=start,
    end_time=end_range
)
```

### AI-Powered Scheduling

```python
from modules.calendar import AIScheduler

ai_scheduler = AIScheduler()

# Parse natural language
event_data = ai_scheduler.parse_natural_language(
    "Meeting with Sarah tomorrow at 2pm for 1 hour"
)

# Get smart suggestions
suggestions = ai_scheduler.suggest_optimal_meeting_time(
    title="Strategy Meeting",
    duration_minutes=60,
    attendees=["alice@example.com", "bob@example.com"],
    calendar_ids=["default"]
)
```

### Running the Streamlit UI

```bash
streamlit run modules/calendar/streamlit_ui.py
```

## Architecture

### Module Structure

```
modules/calendar/
├── __init__.py              # Module initialization
├── calendar_engine.py       # Main calendar logic
├── event_manager.py         # Event CRUD operations
├── scheduling.py            # Scheduling algorithms
├── recurrence.py            # Recurring event logic
├── reminders.py             # Notification system
├── invites.py               # Meeting invitations
├── availability.py          # Free/busy tracking
├── sync.py                  # External calendar sync
├── timezones.py             # Timezone handling
├── conflicts.py             # Conflict detection
├── ai_scheduler.py          # AI features
├── streamlit_ui.py          # Streamlit interface
└── README.md                # This file
```

### Core Components

1. **EventManager**: Handles all event CRUD operations
2. **CalendarEngine**: Manages calendars and generates views
3. **RecurrenceEngine**: Processes recurring event patterns
4. **Scheduler**: Finds optimal meeting times
5. **ConflictDetector**: Identifies scheduling conflicts
6. **AIScheduler**: Provides AI-powered features
7. **SyncManager**: Syncs with external calendars

## API Reference

### EventManager

```python
# Create event
event = event_manager.create_event(
    title: str,
    start_time: datetime,
    end_time: datetime,
    **kwargs
) -> Event

# Get event
event = event_manager.get_event(event_id: str) -> Optional[Event]

# Update event
event = event_manager.update_event(event_id: str, **updates) -> Optional[Event]

# Delete event
success = event_manager.delete_event(event_id: str) -> bool

# List events
events = event_manager.list_events(
    calendar_id: Optional[str],
    start_date: Optional[datetime],
    end_date: Optional[datetime]
) -> List[Event]
```

### CalendarEngine

```python
# Create calendar
calendar = calendar_engine.create_calendar(
    name: str,
    description: Optional[str],
    color: Optional[str]
) -> Calendar

# Get month view
view = calendar_engine.get_month_view(
    year: int,
    month: int,
    calendar_ids: Optional[List[str]]
) -> Dict[str, Any]

# Get week view
view = calendar_engine.get_week_view(
    year: int,
    week: int,
    calendar_ids: Optional[List[str]]
) -> Dict[str, Any]
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/test_calendar.py -v

# Run with coverage
python -m pytest tests/test_calendar.py --cov=modules/calendar --cov-report=html
```

## Configuration

### Working Hours

```python
from modules.calendar.availability import AvailabilityManager, WorkingHours, DayOfWeek
from datetime import time

availability_manager = AvailabilityManager()

working_hours = [
    WorkingHours(DayOfWeek.MONDAY, time(9, 0), time(17, 0), True),
    WorkingHours(DayOfWeek.TUESDAY, time(9, 0), time(17, 0), True),
    # ... configure for all days
]

availability_manager.set_working_hours("user_id", working_hours)
```

### Calendar Sync

```python
from modules.calendar.sync import SyncManager, SyncConfig, SyncProvider, SyncDirection

sync_manager = SyncManager()

config = SyncConfig(
    calendar_id="my_calendar",
    provider=SyncProvider.GOOGLE,
    external_calendar_id="google_cal_id",
    direction=SyncDirection.TWO_WAY,
    credentials={"access_token": "..."}
)

sync_manager.add_sync_config(config)
result = sync_manager.sync_calendar("my_calendar")
```

## Integration Guide

### Email Integration

The calendar module is designed to integrate with the NEXUS email module for:
- Sending meeting invitations
- Email reminders
- RSVP notifications

### Video Meeting Integration

Supports integration with video conferencing platforms:
- Zoom
- Google Meet
- Microsoft Teams
- Custom video links

### Database Integration

For production use, integrate with PostgreSQL:

```python
# Configure database backend
event_manager = EventManager(storage_backend=db_connection)
```

## Performance

- Events are cached in memory for fast access
- Recurrence generation is optimized with limits
- Calendar views use efficient date calculations
- Conflict detection uses smart algorithms

## Security

- All event data can be encrypted at rest
- Calendar sharing uses permission-based access
- Invitation links can be secured with tokens
- User authentication integration ready

## Contributing

When contributing to this module:

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Write comprehensive docstrings
4. Add unit tests for new features
5. Update this README

## License

Part of the NEXUS Platform
Copyright (c) 2024

## Support

For issues or questions about the calendar module:
- Check the documentation
- Review the test files for examples
- Contact the NEXUS development team

---

Built with ❤️ for the NEXUS Platform
