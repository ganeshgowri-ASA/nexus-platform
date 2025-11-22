"""Video Conference Application"""


def main():
    import streamlit as st
    from datetime import datetime
    import uuid

    try:
        # Lazy import database
        from database import init_database
        init_database()

        st.set_page_config(
            page_title="Video Conference - NEXUS",
            page_icon="📹",
            layout="wide"
        )

        st.title("📹 Video Conference")

        # Session state
        if 'conferences' not in st.session_state:
            st.session_state.conferences = []
        if 'current_conference' not in st.session_state:
            st.session_state.current_conference = None
        if 'in_call' not in st.session_state:
            st.session_state.in_call = False

        # Sidebar
        st.sidebar.title("📹 Video Conference")

        if st.sidebar.button("➕ New Conference", use_container_width=True):
            st.session_state.current_conference = None
            st.session_state.in_call = False
            st.rerun()

        st.sidebar.divider()
        st.sidebar.subheader("Conferences")

        for idx, conf in enumerate(st.session_state.conferences):
            status_icon = '📅' if conf.get('status') == 'Scheduled' else '🟢' if conf.get('status') == 'Active' else '⚫'
            if st.sidebar.button(f"{status_icon} {conf['title']}", key=f"conf_{idx}", use_container_width=True):
                st.session_state.current_conference = idx
                st.rerun()

        st.sidebar.divider()
        st.sidebar.metric("Total Conferences", len(st.session_state.conferences))

        # Main content
        if st.session_state.current_conference is not None and st.session_state.current_conference < len(st.session_state.conferences):
            conf = st.session_state.conferences[st.session_state.current_conference]
            st.subheader(f"📹 {conf['title']}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Host", conf.get('host', 'Unknown'))
            with col2:
                st.metric("Participants", len(conf.get('participants', [])))
            with col3:
                st.metric("Status", conf.get('status', 'Scheduled'))

            st.divider()

            if st.session_state.in_call:
                st.info("📹 Video conference in progress\n\n(WebRTC integration required for actual video)")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.button("🎤 Mute", use_container_width=True)
                with col2:
                    st.button("📹 Video", use_container_width=True)
                with col3:
                    st.button("🖥️ Share", use_container_width=True)
                with col4:
                    if st.button("📞 End", type="secondary", use_container_width=True):
                        conf['status'] = 'Ended'
                        st.session_state.in_call = False
                        st.rerun()
            else:
                st.write(f"**Scheduled:** {conf.get('scheduled_time', 'Not set')}")
                if st.button("📞 Join Conference", type="primary"):
                    conf['status'] = 'Active'
                    st.session_state.in_call = True
                    st.rerun()
        else:
            st.subheader("➕ Schedule New Conference")
            title = st.text_input("Conference Title")
            description = st.text_area("Description", height=100)

            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host", value="host@nexus.local")
                scheduled_date = st.date_input("Date", value=datetime.now().date())
            with col2:
                scheduled_time = st.time_input("Time", value=datetime.now().time())
                duration = st.number_input("Duration (min)", value=60, min_value=15)

            participants = st.text_area("Participants (one per line)", height=100)

            if st.button("Schedule Conference", type="primary"):
                if title and host:
                    st.session_state.conferences.append({
                        'title': title, 'description': description, 'host': host,
                        'scheduled_time': f"{scheduled_date} {scheduled_time}", 'duration': duration,
                        'participants': [p.strip() for p in participants.split('\n') if p.strip()],
                        'status': 'Scheduled', 'room_id': str(uuid.uuid4())[:8]
                    })
                    st.success("Conference scheduled!")
                    st.session_state.current_conference = len(st.session_state.conferences) - 1
                    st.rerun()

    except Exception as e:
        import streamlit as st
        st.error(f"Error loading module: {str(e)}")
        with st.expander("Technical Details"):
            import traceback
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
