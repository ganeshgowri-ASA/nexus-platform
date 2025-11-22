"""
Streamlit UI for Calendar Module

Beautiful and intuitive Streamlit interface for the NEXUS Calendar system.
"""

import streamlit as st
from datetime import datetime, timedelta, time
from typing import Optional, List, Dict, Any
import calendar
import pandas as pd

from .calendar_engine import CalendarEngine, CalendarView, Calendar
from .event_manager import EventManager, Event, Attendee, AttendeeStatus
from .scheduling import Scheduler, SchedulingRequest
from .recurrence import RecurrenceEngine, RecurrencePattern, RecurrenceFrequency
from .reminders import ReminderManager, Reminder
from .invites import InviteManager
from .availability import AvailabilityManager
from .sync import SyncManager
from .timezones import TimezoneManager
from .conflicts import ConflictDetector
from .ai_scheduler import AIScheduler


class CalendarUI:
    """
    Streamlit UI for the Calendar system.

    Features:
    - Calendar grid views (month, week, day)
    - Event creation and management
    - Event details sidebar
    - Calendar list sidebar
    - Quick add functionality
    - Search and filters
    """

    def __init__(self):
        """Initialize the calendar UI."""
        self._initialize_session_state()
        self._initialize_managers()

    def _initialize_session_state(self):
        """Initialize Streamlit session state."""
        if 'current_date' not in st.session_state:
            st.session_state.current_date = datetime.now()

        if 'current_view' not in st.session_state:
            st.session_state.current_view = CalendarView.MONTH

        if 'selected_event' not in st.session_state:
            st.session_state.selected_event = None

        if 'show_event_modal' not in st.session_state:
            st.session_state.show_event_modal = False

        if 'selected_calendars' not in st.session_state:
            st.session_state.selected_calendars = []

    def _initialize_managers(self):
        """Initialize all calendar managers."""
        self.event_manager = EventManager()
        self.calendar_engine = CalendarEngine(event_manager=self.event_manager)
        self.recurrence_engine = RecurrenceEngine()
        self.scheduler = Scheduler(event_manager=self.event_manager)
        self.reminder_manager = ReminderManager(event_manager=self.event_manager)
        self.invite_manager = InviteManager(event_manager=self.event_manager)
        self.availability_manager = AvailabilityManager(event_manager=self.event_manager)
        self.sync_manager = SyncManager(
            event_manager=self.event_manager,
            calendar_engine=self.calendar_engine
        )
        self.timezone_manager = TimezoneManager()
        self.conflict_detector = ConflictDetector(event_manager=self.event_manager)
        self.ai_scheduler = AIScheduler(
            event_manager=self.event_manager,
            scheduler=self.scheduler,
            availability_manager=self.availability_manager,
            conflict_detector=self.conflict_detector,
        )

    def render(self):
        """Render the main calendar UI."""
        st.set_page_config(
            page_title="NEXUS Calendar",
            page_icon="📅",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Custom CSS
        self._apply_custom_css()

        # Header
        self._render_header()

        # Sidebar
        with st.sidebar:
            self._render_sidebar()

        # Main content
        col1, col2 = st.columns([3, 1])

        with col1:
            self._render_main_calendar()

        with col2:
            self._render_event_details_panel()

        # Modals
        if st.session_state.show_event_modal:
            self._render_event_modal()

    def _apply_custom_css(self):
        """Apply custom CSS styling."""
        st.markdown("""
            <style>
            .calendar-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 10px;
                color: white;
                margin-bottom: 2rem;
            }
            .calendar-day {
                border: 1px solid #e0e0e0;
                padding: 0.5rem;
                min-height: 100px;
                border-radius: 5px;
                background: white;
            }
            .calendar-day:hover {
                background: #f5f5f5;
                cursor: pointer;
            }
            .event-chip {
                background: #4285F4;
                color: white;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-size: 0.85rem;
                margin: 0.2rem 0;
                display: block;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .today {
                border: 2px solid #4285F4;
                background: #e3f2fd;
            }
            .sidebar-section {
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: 8px;
                background: #f8f9fa;
            }
            </style>
        """, unsafe_allow_html=True)

    def _render_header(self):
        """Render the calendar header."""
        col1, col2, col3 = st.columns([2, 3, 2])

        with col1:
            st.markdown(
                '<div class="calendar-header"><h1>📅 NEXUS Calendar</h1></div>',
                unsafe_allow_html=True
            )

        with col2:
            # View selector
            view_options = {
                "Month": CalendarView.MONTH,
                "Week": CalendarView.WEEK,
                "Day": CalendarView.DAY,
                "Agenda": CalendarView.AGENDA,
                "Year": CalendarView.YEAR,
            }

            selected_view = st.selectbox(
                "View",
                options=list(view_options.keys()),
                index=0,
                key="view_selector"
            )
            st.session_state.current_view = view_options[selected_view]

        with col3:
            # Quick actions
            col3_1, col3_2, col3_3 = st.columns(3)

            with col3_1:
                if st.button("← Prev"):
                    self._navigate_prev()

            with col3_2:
                if st.button("Today"):
                    st.session_state.current_date = datetime.now()
                    st.rerun()

            with col3_3:
                if st.button("Next →"):
                    self._navigate_next()

    def _render_sidebar(self):
        """Render the sidebar with calendars and quick add."""
        st.markdown("### Quick Add Event")

        # Quick add form
        with st.form("quick_add"):
            title = st.text_input("Event title")
            col1, col2 = st.columns(2)

            with col1:
                event_date = st.date_input("Date", value=datetime.now())

            with col2:
                event_time = st.time_input("Time", value=time(9, 0))

            duration = st.selectbox(
                "Duration",
                options=[15, 30, 45, 60, 90, 120],
                format_func=lambda x: f"{x} minutes",
                index=3
            )

            if st.form_submit_button("Add Event", use_container_width=True):
                start_time = datetime.combine(event_date, event_time)
                end_time = start_time + timedelta(minutes=duration)

                event = self.event_manager.create_event(
                    title=title,
                    start_time=start_time,
                    end_time=end_time,
                )

                st.success(f"Created: {title}")
                st.rerun()

        st.markdown("---")

        # Calendar list
        st.markdown("### My Calendars")

        calendars = self.calendar_engine.list_calendars()

        for cal in calendars:
            col1, col2 = st.columns([3, 1])

            with col1:
                is_selected = st.checkbox(
                    cal.name,
                    value=True,
                    key=f"cal_{cal.id}"
                )

                if is_selected and cal.id not in st.session_state.selected_calendars:
                    st.session_state.selected_calendars.append(cal.id)
                elif not is_selected and cal.id in st.session_state.selected_calendars:
                    st.session_state.selected_calendars.remove(cal.id)

            with col2:
                st.markdown(
                    f'<span style="color:{cal.color}">●</span>',
                    unsafe_allow_html=True
                )

        # Add calendar button
        if st.button("+ New Calendar", use_container_width=True):
            self._show_create_calendar_modal()

        st.markdown("---")

        # AI Suggestions
        st.markdown("### 🤖 AI Suggestions")

        # Get AI optimization suggestions
        suggestions = self.ai_scheduler.optimize_calendar(
            calendar_ids=st.session_state.selected_calendars or [calendars[0].id],
            start_date=datetime.now(),
            days=7,
        )

        if suggestions:
            for suggestion in suggestions[:3]:
                with st.expander(f"💡 {suggestion.title}"):
                    st.write(suggestion.description)
                    if st.button(f"Apply", key=f"apply_{suggestion.type}"):
                        st.info("Suggestion applied!")
        else:
            st.info("No suggestions at this time")

    def _render_main_calendar(self):
        """Render the main calendar view."""
        current_date = st.session_state.current_date

        if st.session_state.current_view == CalendarView.MONTH:
            self._render_month_view(current_date)
        elif st.session_state.current_view == CalendarView.WEEK:
            self._render_week_view(current_date)
        elif st.session_state.current_view == CalendarView.DAY:
            self._render_day_view(current_date)
        elif st.session_state.current_view == CalendarView.AGENDA:
            self._render_agenda_view(current_date)
        elif st.session_state.current_view == CalendarView.YEAR:
            self._render_year_view(current_date)

    def _render_month_view(self, current_date: datetime):
        """Render month view."""
        month_data = self.calendar_engine.get_month_view(
            year=current_date.year,
            month=current_date.month,
            calendar_ids=st.session_state.selected_calendars,
        )

        st.markdown(f"## {month_data['month_name']} {month_data['year']}")
        st.markdown(f"*{month_data['total_events']} events*")

        # Weekday headers
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        cols = st.columns(7)
        for i, day in enumerate(weekdays):
            cols[i].markdown(f"**{day}**")

        # Calendar grid
        for week in month_data['weeks']:
            cols = st.columns(7)

            for i, day_data in enumerate(week):
                with cols[i]:
                    if day_data['day'] is None:
                        st.markdown("")
                    else:
                        # Day number
                        day_class = "today" if day_data['is_today'] else ""
                        st.markdown(
                            f'<div class="calendar-day {day_class}">'
                            f'<strong>{day_data["day"]}</strong>',
                            unsafe_allow_html=True
                        )

                        # Events
                        for event in day_data['events'][:3]:  # Show max 3 events
                            event_html = f'<div class="event-chip" style="background:{event.color}">{event.title}</div>'
                            if st.button(
                                event.title,
                                key=f"event_{event.id}",
                                use_container_width=True
                            ):
                                st.session_state.selected_event = event
                                st.rerun()

                        # More events indicator
                        if len(day_data['events']) > 3:
                            st.caption(f"+{len(day_data['events']) - 3} more")

                        st.markdown('</div>', unsafe_allow_html=True)

    def _render_week_view(self, current_date: datetime):
        """Render week view."""
        week_num = current_date.isocalendar()[1]
        week_data = self.calendar_engine.get_week_view(
            year=current_date.year,
            week=week_num,
            calendar_ids=st.session_state.selected_calendars,
        )

        st.markdown(
            f"## Week {week_num}, {week_data['year']} "
            f"({week_data['start_date'].strftime('%b %d')} - "
            f"{week_data['end_date'].strftime('%b %d')})"
        )

        # Time slots
        for hour in range(8, 20):  # 8 AM to 8 PM
            cols = st.columns([1] + [2] * 7)

            with cols[0]:
                st.markdown(f"**{hour:02d}:00**")

            for i, day in enumerate(week_data['days']):
                with cols[i + 1]:
                    hour_start = day['date'].replace(hour=hour, minute=0)
                    hour_end = hour_start + timedelta(hours=1)

                    # Find events in this hour
                    hour_events = [
                        e for e in day['events']
                        if e.start_time <= hour_start < e.end_time or
                        hour_start <= e.start_time < hour_end
                    ]

                    for event in hour_events:
                        if st.button(
                            event.title,
                            key=f"week_event_{event.id}_{hour}",
                            use_container_width=True
                        ):
                            st.session_state.selected_event = event
                            st.rerun()

    def _render_day_view(self, current_date: datetime):
        """Render day view."""
        day_data = self.calendar_engine.get_day_view(
            date=current_date,
            calendar_ids=st.session_state.selected_calendars,
        )

        st.markdown(f"## {day_data['day_name']}")

        # All-day events
        if day_data['all_day_events']:
            st.markdown("### All-day Events")
            for event in day_data['all_day_events']:
                if st.button(
                    f"📅 {event.title}",
                    key=f"allday_{event.id}",
                    use_container_width=True
                ):
                    st.session_state.selected_event = event
                    st.rerun()

        st.markdown("---")

        # Hourly schedule
        for hour_data in day_data['hours']:
            if hour_data['events']:
                st.markdown(f"### {hour_data['time'].strftime('%I:%M %p')}")

                for event in hour_data['events']:
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        if st.button(
                            f"⏰ {event.title}",
                            key=f"day_event_{event.id}",
                            use_container_width=True
                        ):
                            st.session_state.selected_event = event
                            st.rerun()

                    with col2:
                        duration = int((event.end_time - event.start_time).total_seconds() / 60)
                        st.caption(f"{duration} min")

    def _render_agenda_view(self, current_date: datetime):
        """Render agenda view."""
        agenda_data = self.calendar_engine.get_agenda_view(
            start_date=current_date,
            days=14,
            calendar_ids=st.session_state.selected_calendars,
        )

        st.markdown("## Upcoming Events")

        for day_date, day_data in agenda_data['grouped_events'].items():
            st.markdown(f"### {day_data['day_name']}")

            for event in day_data['events']:
                col1, col2, col3 = st.columns([2, 3, 1])

                with col1:
                    st.markdown(f"**{event.start_time.strftime('%I:%M %p')}**")

                with col2:
                    if st.button(
                        event.title,
                        key=f"agenda_{event.id}",
                        use_container_width=True
                    ):
                        st.session_state.selected_event = event
                        st.rerun()

                with col3:
                    if event.location:
                        st.caption(f"📍 {event.location}")

            st.markdown("---")

    def _render_year_view(self, current_date: datetime):
        """Render year view."""
        year_data = self.calendar_engine.get_year_view(
            year=current_date.year,
            calendar_ids=st.session_state.selected_calendars,
        )

        st.markdown(f"## {year_data['year']}")
        st.markdown(f"*{year_data['total_events']} events this year*")

        # Display mini month calendars
        for i in range(0, 12, 3):
            cols = st.columns(3)

            for j in range(3):
                if i + j < 12:
                    month = year_data['months'][i + j]

                    with cols[j]:
                        st.markdown(f"### {month['month_name']}")
                        st.caption(f"{month['event_count']} events")

    def _render_event_details_panel(self):
        """Render event details panel."""
        st.markdown("### Event Details")

        if st.session_state.selected_event:
            event = st.session_state.selected_event

            st.markdown(f"## {event.title}")

            # Event info
            st.markdown(f"**📅 When:** {event.start_time.strftime('%A, %B %d, %Y')}")
            st.markdown(f"**⏰ Time:** {event.start_time.strftime('%I:%M %p')} - {event.end_time.strftime('%I:%M %p')}")

            if event.location:
                st.markdown(f"**📍 Location:** {event.location}")

            if event.video_link:
                st.markdown(f"**🎥 Video:** [{event.video_link}]({event.video_link})")

            if event.description:
                st.markdown(f"**📝 Description:**")
                st.write(event.description)

            # Attendees
            if event.attendees:
                st.markdown("**👥 Attendees:**")
                for attendee in event.attendees:
                    status_emoji = {
                        AttendeeStatus.ACCEPTED: "✅",
                        AttendeeStatus.DECLINED: "❌",
                        AttendeeStatus.TENTATIVE: "❓",
                        AttendeeStatus.NEEDS_ACTION: "⏳",
                    }.get(attendee.status, "⏳")

                    st.markdown(f"{status_emoji} {attendee.email}")

            # Actions
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✏️ Edit", use_container_width=True):
                    st.session_state.show_event_modal = True
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete", use_container_width=True):
                    self.event_manager.delete_event(event.id)
                    st.session_state.selected_event = None
                    st.success("Event deleted")
                    st.rerun()

        else:
            st.info("Select an event to view details")

    def _render_event_modal(self):
        """Render event creation/edit modal."""
        with st.form("event_form"):
            st.markdown("### Create/Edit Event")

            title = st.text_input("Title", value="")
            description = st.text_area("Description", value="")

            col1, col2 = st.columns(2)

            with col1:
                start_date = st.date_input("Start Date")
                start_time = st.time_input("Start Time")

            with col2:
                end_date = st.date_input("End Date")
                end_time = st.time_input("End Time")

            location = st.text_input("Location")
            video_link = st.text_input("Video Link")

            submitted = st.form_submit_button("Save Event")

            if submitted:
                start_datetime = datetime.combine(start_date, start_time)
                end_datetime = datetime.combine(end_date, end_time)

                self.event_manager.create_event(
                    title=title,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    description=description,
                    location=location,
                    video_link=video_link,
                )

                st.session_state.show_event_modal = False
                st.success("Event saved!")
                st.rerun()

    def _navigate_prev(self):
        """Navigate to previous period."""
        current = st.session_state.current_date
        view = st.session_state.current_view

        if view == CalendarView.MONTH:
            st.session_state.current_date = current - timedelta(days=30)
        elif view == CalendarView.WEEK:
            st.session_state.current_date = current - timedelta(weeks=1)
        elif view == CalendarView.DAY:
            st.session_state.current_date = current - timedelta(days=1)
        elif view == CalendarView.YEAR:
            st.session_state.current_date = current.replace(year=current.year - 1)

        st.rerun()

    def _navigate_next(self):
        """Navigate to next period."""
        current = st.session_state.current_date
        view = st.session_state.current_view

        if view == CalendarView.MONTH:
            st.session_state.current_date = current + timedelta(days=30)
        elif view == CalendarView.WEEK:
            st.session_state.current_date = current + timedelta(weeks=1)
        elif view == CalendarView.DAY:
            st.session_state.current_date = current + timedelta(days=1)
        elif view == CalendarView.YEAR:
            st.session_state.current_date = current.replace(year=current.year + 1)

        st.rerun()

    def _show_create_calendar_modal(self):
        """Show create calendar modal."""
        st.session_state.show_create_calendar = True


def main():
    """Main entry point for the calendar UI."""
    ui = CalendarUI()
    ui.render()


if __name__ == "__main__":
    main()
