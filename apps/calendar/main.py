"""Calendar Application with Day/Week/Month views, Events, Recurring, Reminders"""
import streamlit as st
from datetime import datetime, timedelta
import calendar as cal_module

# Lazy imports
pd = None
SessionLocal = None
CalendarEvent = None
settings = None
CALENDAR_EVENT_TYPES = None
RECURRENCE_PATTERNS = None
format_date = None
format_duration = None


def _lazy_imports():
    """Import all dependencies lazily"""
    global pd, SessionLocal, CalendarEvent, settings
    global CALENDAR_EVENT_TYPES, RECURRENCE_PATTERNS, format_date, format_duration

    import pandas as _pd
    from database import init_database, get_session
    from database.models import CalendarEvent as _CalendarEvent
    from config.settings import settings as _settings
    from config.constants import CALENDAR_EVENT_TYPES as _CALENDAR_EVENT_TYPES, RECURRENCE_PATTERNS as _RECURRENCE_PATTERNS
    from utils.formatters import format_date as _format_date, format_duration as _format_duration

    pd = _pd
    SessionLocal = get_session
    CalendarEvent = _CalendarEvent
    settings = _settings
    CALENDAR_EVENT_TYPES = _CALENDAR_EVENT_TYPES
    RECURRENCE_PATTERNS = _RECURRENCE_PATTERNS
    format_date = _format_date
    format_duration = _format_duration

    init_database()
    return get_session

def initialize_session_state():
    """Initialize session state variables"""
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'month'
    if 'current_date' not in st.session_state:
        st.session_state.current_date = datetime.now()
    if 'selected_event' not in st.session_state:
        st.session_state.selected_event = None

def render_sidebar():
    """Render sidebar with navigation and mini calendar"""
    st.sidebar.title("📅 Calendar")

    # View selector
    st.sidebar.subheader("View")
    views = ["Day", "Week", "Month"]
    for view in views:
        if st.sidebar.button(view, key=f"view_{view.lower()}", use_container_width=True):
            st.session_state.view_mode = view.lower()
            st.rerun()

    st.sidebar.divider()

    # Date navigation
    st.sidebar.subheader("Navigate")

    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        if st.button("◀️"):
            if st.session_state.view_mode == 'day':
                st.session_state.current_date -= timedelta(days=1)
            elif st.session_state.view_mode == 'week':
                st.session_state.current_date -= timedelta(weeks=1)
            else:  # month
                st.session_state.current_date -= timedelta(days=30)
            st.rerun()

    with col2:
        if st.button("Today"):
            st.session_state.current_date = datetime.now()
            st.rerun()

    with col3:
        if st.button("▶️"):
            if st.session_state.view_mode == 'day':
                st.session_state.current_date += timedelta(days=1)
            elif st.session_state.view_mode == 'week':
                st.session_state.current_date += timedelta(weeks=1)
            else:  # month
                st.session_state.current_date += timedelta(days=30)
            st.rerun()

    # Date picker
    selected_date = st.sidebar.date_input(
        "Jump to date",
        value=st.session_state.current_date.date()
    )
    if selected_date != st.session_state.current_date.date():
        st.session_state.current_date = datetime.combine(selected_date, datetime.min.time())
        st.rerun()

    st.sidebar.divider()

    # Quick add event
    with st.sidebar.expander("➕ Quick Add Event"):
        quick_title = st.text_input("Event Title")
        quick_date = st.date_input("Date", value=datetime.now().date())
        quick_time = st.time_input("Time", value=datetime.now().time())

        if st.button("Add", type="primary"):
            if quick_title:
                db = SessionLocal()
                event_dt = datetime.combine(quick_date, quick_time)
                event = CalendarEvent(
                    title=quick_title,
                    start_time=event_dt,
                    end_time=event_dt + timedelta(hours=1),
                    event_type='Meeting'
                )
                db.add(event)
                db.commit()
                db.close()
                st.success("Event added!")
                st.rerun()

    st.sidebar.divider()

    # Event types filter
    st.sidebar.subheader("Filter by Type")
    if 'filter_types' not in st.session_state:
        st.session_state.filter_types = CALENDAR_EVENT_TYPES

    for event_type in CALENDAR_EVENT_TYPES:
        checked = st.sidebar.checkbox(event_type, value=event_type in st.session_state.filter_types,
                                      key=f"filter_{event_type}")
        if checked and event_type not in st.session_state.filter_types:
            st.session_state.filter_types.append(event_type)
        elif not checked and event_type in st.session_state.filter_types:
            st.session_state.filter_types.remove(event_type)

def render_day_view(db):
    """Render day view"""
    current_date = st.session_state.current_date
    st.subheader(f"📅 {current_date.strftime('%A, %B %d, %Y')}")

    # Get events for the day
    start_of_day = current_date.replace(hour=0, minute=0, second=0)
    end_of_day = current_date.replace(hour=23, minute=59, second=59)

    events = db.query(CalendarEvent).filter(
        CalendarEvent.start_time >= start_of_day,
        CalendarEvent.start_time <= end_of_day,
        CalendarEvent.event_type.in_(st.session_state.filter_types)
    ).order_by(CalendarEvent.start_time).all()

    # Time slots
    for hour in range(24):
        with st.container():
            col1, col2 = st.columns([1, 5])

            with col1:
                st.caption(f"{hour:02d}:00")

            with col2:
                # Find events in this hour
                hour_events = [e for e in events if e.start_time.hour == hour]

                if hour_events:
                    for event in hour_events:
                        event_colors = {
                            'Meeting': '🔵',
                            'Call': '📞',
                            'Task': '✅',
                            'Reminder': '⏰',
                            'Appointment': '📋',
                            'Deadline': '🔴'
                        }
                        icon = event_colors.get(event.event_type, '📅')

                        if st.button(
                            f"{icon} {event.start_time.strftime('%H:%M')} - {event.title}",
                            key=f"event_{event.id}",
                            use_container_width=True
                        ):
                            st.session_state.selected_event = event.id
                            st.rerun()

            st.divider()

    if not events:
        st.info("No events scheduled for this day")

def render_week_view(db):
    """Render week view"""
    current_date = st.session_state.current_date

    # Get start of week (Monday)
    start_of_week = current_date - timedelta(days=current_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    st.subheader(f"📅 Week of {start_of_week.strftime('%B %d')} - {end_of_week.strftime('%B %d, %Y')}")

    # Create columns for each day
    days = [start_of_week + timedelta(days=i) for i in range(7)]
    cols = st.columns(7)

    for idx, day in enumerate(days):
        with cols[idx]:
            st.markdown(f"**{day.strftime('%a %d')}**")

            # Get events for this day
            start_of_day = day.replace(hour=0, minute=0, second=0)
            end_of_day = day.replace(hour=23, minute=59, second=59)

            events = db.query(CalendarEvent).filter(
                CalendarEvent.start_time >= start_of_day,
                CalendarEvent.start_time <= end_of_day,
                CalendarEvent.event_type.in_(st.session_state.filter_types)
            ).order_by(CalendarEvent.start_time).all()

            for event in events[:5]:  # Show max 5 events
                if st.button(
                    f"{event.start_time.strftime('%H:%M')} {event.title[:15]}...",
                    key=f"week_event_{event.id}",
                    use_container_width=True
                ):
                    st.session_state.selected_event = event.id
                    st.rerun()

            if len(events) > 5:
                st.caption(f"+ {len(events) - 5} more")

def render_month_view(db):
    """Render month view"""
    current_date = st.session_state.current_date
    year = current_date.year
    month = current_date.month

    st.subheader(f"📅 {current_date.strftime('%B %Y')}")

    # Get calendar for the month
    cal = cal_module.monthcalendar(year, month)

    # Day headers
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    cols = st.columns(7)
    for idx, day_name in enumerate(day_names):
        with cols[idx]:
            st.markdown(f"**{day_name}**")

    # Calendar grid
    for week in cal:
        cols = st.columns(7)
        for idx, day in enumerate(week):
            with cols[idx]:
                if day == 0:
                    st.write("")
                else:
                    # Get events for this day
                    day_date = datetime(year, month, day)
                    start_of_day = day_date.replace(hour=0, minute=0, second=0)
                    end_of_day = day_date.replace(hour=23, minute=59, second=59)

                    event_count = db.query(CalendarEvent).filter(
                        CalendarEvent.start_time >= start_of_day,
                        CalendarEvent.start_time <= end_of_day,
                        CalendarEvent.event_type.in_(st.session_state.filter_types)
                    ).count()

                    # Highlight today
                    if day == datetime.now().day and month == datetime.now().month and year == datetime.now().year:
                        st.markdown(f"**🔵 {day}**")
                    else:
                        st.markdown(f"{day}")

                    if event_count > 0:
                        if st.button(f"{event_count} event{'s' if event_count > 1 else ''}",
                                   key=f"month_day_{day}",
                                   use_container_width=True):
                            st.session_state.current_date = day_date
                            st.session_state.view_mode = 'day'
                            st.rerun()

def render_event_details(db, event_id):
    """Render event details and editor"""
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()

    if not event:
        st.error("Event not found")
        return

    st.subheader("📝 Event Details")

    # Back button
    if st.button("← Back"):
        st.session_state.selected_event = None
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        event.title = st.text_input("Title", value=event.title)
        event.description = st.text_area("Description", value=event.description or "", height=100)
        event.location = st.text_input("Location", value=event.location or "")

    with col2:
        event.event_type = st.selectbox("Event Type", CALENDAR_EVENT_TYPES,
                                       index=CALENDAR_EVENT_TYPES.index(event.event_type) if event.event_type in CALENDAR_EVENT_TYPES else 0)

        event.is_all_day = st.checkbox("All Day Event", value=event.is_all_day)

        event.recurrence_pattern = st.selectbox("Recurrence", RECURRENCE_PATTERNS,
                                               index=RECURRENCE_PATTERNS.index(event.recurrence_pattern) if event.recurrence_pattern in RECURRENCE_PATTERNS else 0)

    # Date and time
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", value=event.start_time.date())
        if not event.is_all_day:
            start_time = st.time_input("Start Time", value=event.start_time.time())
            event.start_time = datetime.combine(start_date, start_time)
        else:
            event.start_time = datetime.combine(start_date, datetime.min.time())

    with col2:
        end_date = st.date_input("End Date", value=event.end_time.date())
        if not event.is_all_day:
            end_time = st.time_input("End Time", value=event.end_time.time())
            event.end_time = datetime.combine(end_date, end_time)
        else:
            event.end_time = datetime.combine(end_date, datetime.max.time())

    # Attendees
    attendees_input = st.text_area("Attendees (one per line)",
                                   value='\n'.join(event.attendees or []) if event.attendees else "")
    event.attendees = [a.strip() for a in attendees_input.split('\n') if a.strip()]

    # Reminder
    event.reminder_minutes = st.number_input("Reminder (minutes before)", value=event.reminder_minutes or 15,
                                            min_value=0, max_value=1440)

    # Actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Save", type="primary"):
            db.commit()
            st.success("Event updated!")
            st.session_state.selected_event = None
            st.rerun()

    with col2:
        if st.button("📤 Export to ICS"):
            events_data = [{
                'title': event.title,
                'description': event.description,
                'start_time': event.start_time,
                'end_time': event.end_time,
                'location': event.location
            }]

            output_path = settings.EXPORTS_DIR / f"{event.title.replace(' ', '_')}.ics"
            export_to_ics(events_data, str(output_path))

            with open(output_path, 'rb') as f:
                st.download_button(
                    "⬇️ Download ICS",
                    f,
                    file_name=output_path.name,
                    mime="text/calendar"
                )

    with col3:
        if st.button("🗑️ Delete"):
            db.delete(event)
            db.commit()
            st.session_state.selected_event = None
            st.rerun()

    # AI Meeting Agenda
    if settings.ENABLE_AI_FEATURES and event.event_type == 'Meeting':
        with st.expander("🤖 AI Meeting Agenda"):
            duration = int((event.end_time - event.start_time).total_seconds() / 60)

            if st.button("Generate Agenda", type="primary"):
                try:
                    with st.spinner("Generating agenda..."):
                        ai_client = ClaudeClient()
                        agenda = ai_client.generate_meeting_agenda(event.title, duration)
                        st.text_area("Suggested Agenda", value=agenda, height=200)
                except Exception as e:
                    st.error(f"Error: {e}")

def render_add_event(db):
    """Render add event form"""
    st.subheader("➕ Add New Event")

    title = st.text_input("Event Title*")

    col1, col2 = st.columns(2)

    with col1:
        description = st.text_area("Description", height=100)
        location = st.text_input("Location")

    with col2:
        event_type = st.selectbox("Event Type", CALENDAR_EVENT_TYPES)
        is_all_day = st.checkbox("All Day Event")
        recurrence = st.selectbox("Recurrence", RECURRENCE_PATTERNS)

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().date())
        start_time = st.time_input("Start Time", value=datetime.now().time()) if not is_all_day else None

    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
        end_time = st.time_input("End Time", value=(datetime.now() + timedelta(hours=1)).time()) if not is_all_day else None

    attendees_input = st.text_area("Attendees (one per line)", height=80)
    reminder_minutes = st.number_input("Reminder (minutes before)", value=15, min_value=0, max_value=1440)

    if st.button("Add Event", type="primary"):
        if title:
            if is_all_day:
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.max.time())
            else:
                start_dt = datetime.combine(start_date, start_time)
                end_dt = datetime.combine(end_date, end_time)

            event = CalendarEvent(
                title=title,
                description=description,
                event_type=event_type,
                start_time=start_dt,
                end_time=end_dt,
                location=location,
                attendees=[a.strip() for a in attendees_input.split('\n') if a.strip()] if attendees_input else None,
                is_all_day=is_all_day,
                recurrence_pattern=recurrence,
                reminder_minutes=reminder_minutes,
                organizer=settings.SMTP_USER or "organizer@nexus.local"
            )

            db.add(event)
            db.commit()
            st.success("Event added!")
            st.rerun()
        else:
            st.error("Please enter an event title")

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Calendar - NEXUS",
        page_icon="📅",
        layout="wide"
    )

    try:
        # Lazy import all dependencies
        get_session = _lazy_imports()

        # Initialize session state
        initialize_session_state()

        # Render sidebar
        render_sidebar()

        # Render main content
        st.title("📅 Calendar")

        db = get_session()

        # Show event details if selected
        if st.session_state.selected_event:
            render_event_details(db, st.session_state.selected_event)
        else:
            # Render view based on mode
            if st.session_state.view_mode == 'day':
                render_day_view(db)
            elif st.session_state.view_mode == 'week':
                render_week_view(db)
            else:
                render_month_view(db)

            st.divider()

            # Add event section
            with st.expander("➕ Add New Event"):
                render_add_event(db)

        db.close()

    except Exception as e:
        st.error(f"Error in Calendar module: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
