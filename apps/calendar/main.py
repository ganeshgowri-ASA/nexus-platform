"""Calendar Application with Day/Week/Month views"""


def main():
    import streamlit as st
    from datetime import datetime, timedelta
    import calendar as cal_module

    try:
        # Lazy import database
        from database import init_database
        init_database()

        st.set_page_config(
            page_title="Calendar - NEXUS",
            page_icon="📅",
            layout="wide"
        )

        st.title("📅 Calendar")

        # Session state
        if 'events' not in st.session_state:
            st.session_state.events = []
        if 'view_mode' not in st.session_state:
            st.session_state.view_mode = 'month'
        if 'current_date' not in st.session_state:
            st.session_state.current_date = datetime.now()

        # Sidebar
        st.sidebar.title("📅 Calendar")
        st.sidebar.subheader("View")

        for view in ["Day", "Week", "Month"]:
            if st.sidebar.button(view, key=f"view_{view.lower()}", use_container_width=True):
                st.session_state.view_mode = view.lower()
                st.rerun()

        st.sidebar.divider()

        col1, col2, col3 = st.sidebar.columns(3)
        with col1:
            if st.button("◀️"):
                if st.session_state.view_mode == 'day':
                    st.session_state.current_date -= timedelta(days=1)
                elif st.session_state.view_mode == 'week':
                    st.session_state.current_date -= timedelta(weeks=1)
                else:
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
                else:
                    st.session_state.current_date += timedelta(days=30)
                st.rerun()

        st.sidebar.divider()

        with st.sidebar.expander("➕ Quick Add Event"):
            quick_title = st.text_input("Event Title")
            quick_date = st.date_input("Date", value=datetime.now().date())
            quick_time = st.time_input("Time", value=datetime.now().time())
            event_type = st.selectbox("Type", ["Meeting", "Call", "Task", "Reminder"])

            if st.button("Add", type="primary"):
                if quick_title:
                    st.session_state.events.append({
                        'title': quick_title,
                        'date': str(quick_date),
                        'time': str(quick_time),
                        'type': event_type
                    })
                    st.success("Event added!")
                    st.rerun()

        # Main content
        current_date = st.session_state.current_date

        if st.session_state.view_mode == 'day':
            st.subheader(f"📅 {current_date.strftime('%A, %B %d, %Y')}")
            day_events = [e for e in st.session_state.events if e['date'] == str(current_date.date())]

            for hour in range(9, 18):
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.caption(f"{hour:02d}:00")
                with col2:
                    hour_events = [e for e in day_events if e['time'].startswith(f"{hour:02d}")]
                    for event in hour_events:
                        st.write(f"🔵 {event['title']}")
                st.divider()

        elif st.session_state.view_mode == 'week':
            start_of_week = current_date - timedelta(days=current_date.weekday())
            st.subheader(f"📅 Week of {start_of_week.strftime('%B %d, %Y')}")

            cols = st.columns(7)
            for i, col in enumerate(cols):
                day = start_of_week + timedelta(days=i)
                with col:
                    st.markdown(f"**{day.strftime('%a %d')}**")
                    day_events = [e for e in st.session_state.events if e['date'] == str(day.date())]
                    for event in day_events[:3]:
                        st.caption(f"• {event['title'][:15]}")

        else:  # month
            st.subheader(f"📅 {current_date.strftime('%B %Y')}")
            cal = cal_module.monthcalendar(current_date.year, current_date.month)

            day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            cols = st.columns(7)
            for idx, name in enumerate(day_names):
                with cols[idx]:
                    st.markdown(f"**{name}**")

            for week in cal:
                cols = st.columns(7)
                for idx, day in enumerate(week):
                    with cols[idx]:
                        if day == 0:
                            st.write("")
                        else:
                            is_today = day == datetime.now().day and current_date.month == datetime.now().month
                            st.markdown(f"{'**🔵 ' if is_today else ''}{day}{'**' if is_today else ''}")
                            day_date = datetime(current_date.year, current_date.month, day).date()
                            event_count = len([e for e in st.session_state.events if e['date'] == str(day_date)])
                            if event_count > 0:
                                st.caption(f"{event_count} event{'s' if event_count > 1 else ''}")

        st.divider()
        st.metric("Total Events", len(st.session_state.events))

    except Exception as e:
        import streamlit as st
        st.error(f"Error loading module: {str(e)}")
        with st.expander("Technical Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
