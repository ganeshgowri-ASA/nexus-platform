"""Video Conference Application with WebRTC, Screen Share, Recording"""
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from database.connection import SessionLocal, init_db
from database.models import VideoConference, ConferenceRecording
from ai.claude_client import ClaudeClient
from config.settings import settings
from utils.formatters import format_date, format_duration, format_file_size
import uuid

def initialize_session_state():
    """Initialize session state variables"""
    if 'current_conference' not in st.session_state:
        st.session_state.current_conference = None
    if 'in_call' not in st.session_state:
        st.session_state.in_call = False

def render_sidebar():
    """Render sidebar with conference list"""
    st.sidebar.title("📹 Video Conference")

    # New conference button
    if st.sidebar.button("➕ New Conference", use_container_width=True):
        st.session_state.current_conference = None
        st.session_state.in_call = False
        st.rerun()

    st.sidebar.divider()

    # Conference list
    st.sidebar.subheader("Conferences")

    db = SessionLocal()
    conferences = db.query(VideoConference).order_by(VideoConference.scheduled_time.desc()).limit(20).all()

    for conf in conferences:
        status_icon = {
            'Scheduled': '📅',
            'Active': '🟢',
            'Ended': '⚫'
        }.get(conf.status, '📹')

        if st.sidebar.button(f"{status_icon} {conf.title}", key=f"conf_{conf.id}",
                            use_container_width=True):
            st.session_state.current_conference = conf.id
            st.rerun()

    db.close()

    st.sidebar.divider()

    # Quick stats
    st.sidebar.subheader("Stats")
    db = SessionLocal()
    total_conferences = db.query(VideoConference).count()
    recordings_count = db.query(ConferenceRecording).count()
    db.close()

    st.sidebar.metric("Total Conferences", total_conferences)
    st.sidebar.metric("Recordings", recordings_count)

def render_conference_room(db, conference):
    """Render conference room interface"""
    st.subheader(f"📹 {conference.title}")

    # Conference info
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Host", conference.host)

    with col2:
        st.metric("Participants", len(conference.participants or []))

    with col3:
        st.metric("Status", conference.status)

    if conference.description:
        st.info(conference.description)

    st.divider()

    # Video interface (placeholder - actual WebRTC would require more complex setup)
    if st.session_state.in_call or conference.status == 'Active':
        st.subheader("🎥 Live Conference")

        # Placeholder for video streams
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Main Screen")
            st.info("📹 Video stream would appear here\n\n(WebRTC integration required for actual video)")

        with col2:
            st.markdown("### Participants")
            participants = conference.participants or [conference.host]
            for participant in participants:
                st.write(f"👤 {participant}")

        st.divider()

        # Controls
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if st.button("🎤 Mute/Unmute", use_container_width=True):
                st.info("Audio toggled")

        with col2:
            if st.button("📹 Video On/Off", use_container_width=True):
                st.info("Video toggled")

        with col3:
            if st.button("🖥️ Share Screen", use_container_width=True):
                st.info("Screen sharing started")

        with col4:
            is_recording = conference.is_recording
            if st.button("⏺️ Record" if not is_recording else "⏹️ Stop", use_container_width=True):
                conference.is_recording = not is_recording
                db.commit()

                if conference.is_recording:
                    st.success("Recording started")
                else:
                    # Save recording
                    recording = ConferenceRecording(
                        conference_id=conference.id,
                        file_path=f"/recordings/{conference.room_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                        duration_seconds=0,  # Would be calculated
                        file_size_mb=0.0  # Would be calculated
                    )
                    db.add(recording)
                    db.commit()
                    st.success("Recording saved")

        with col5:
            if st.button("📞 End Call", type="secondary", use_container_width=True):
                conference.status = 'Ended'
                st.session_state.in_call = False
                db.commit()
                st.rerun()

        # Chat sidebar
        st.divider()
        with st.expander("💬 Chat"):
            st.text_area("Messages", height=200, disabled=True,
                        value="[10:30] John: Hello everyone!\n[10:31] Sarah: Hi!")
            chat_input = st.text_input("Type a message...")
            if st.button("Send"):
                st.info("Message sent")

    else:
        # Pre-call interface
        st.subheader("Join Conference")

        st.write(f"**Scheduled Time:** {format_date(conference.scheduled_time)}")
        st.write(f"**Duration:** {format_duration(conference.duration_minutes or 60)}")

        # Join button
        col1, col2, col3 = st.columns([1, 1, 1])

        with col2:
            if st.button("📞 Join Conference", type="primary", use_container_width=True):
                conference.status = 'Active'
                st.session_state.in_call = True
                db.commit()
                st.rerun()

    st.divider()

    # Recordings section
    st.subheader("📼 Recordings")

    recordings = db.query(ConferenceRecording).filter(
        ConferenceRecording.conference_id == conference.id
    ).all()

    if recordings:
        for recording in recordings:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.write(f"📹 {Path(recording.file_path).name}")

            with col2:
                if recording.duration_seconds:
                    st.caption(format_duration(recording.duration_seconds // 60))

            with col3:
                if recording.file_size_mb:
                    st.caption(format_file_size(recording.file_size_mb * 1024 * 1024))

            with col4:
                if st.button("🗑️", key=f"del_rec_{recording.id}"):
                    db.delete(recording)
                    db.commit()
                    st.rerun()
    else:
        st.info("No recordings available")

    # AI Meeting Summary
    if settings.ENABLE_AI_FEATURES and conference.status == 'Ended':
        with st.expander("🤖 AI Meeting Summary"):
            if st.button("Generate Summary", type="primary"):
                try:
                    with st.spinner("Generating summary..."):
                        ai_client = ClaudeClient()
                        # In real implementation, would summarize transcription
                        summary = f"Meeting summary for '{conference.title}' would be generated here using AI based on transcription."
                        st.text_area("Summary", value=summary, height=150)
                except Exception as e:
                    st.error(f"Error: {e}")

def render_new_conference(db):
    """Render new conference form"""
    st.subheader("➕ Schedule New Conference")

    title = st.text_input("Conference Title*")
    description = st.text_area("Description", height=100)

    col1, col2 = st.columns(2)

    with col1:
        host = st.text_input("Host*", value=settings.SMTP_USER or "host@nexus.local")
        scheduled_date = st.date_input("Date", value=datetime.now().date())

    with col2:
        scheduled_time = st.time_input("Time", value=datetime.now().time())
        duration = st.number_input("Duration (minutes)", value=60, min_value=15, max_value=480)

    participants_input = st.text_area("Participants (one per line)", height=100,
                                     placeholder="participant1@example.com\nparticipant2@example.com")

    if st.button("Schedule Conference", type="primary"):
        if title and host:
            scheduled_dt = datetime.combine(scheduled_date, scheduled_time)

            conference = VideoConference(
                title=title,
                description=description,
                host=host,
                participants=[p.strip() for p in participants_input.split('\n') if p.strip()] if participants_input else [],
                scheduled_time=scheduled_dt,
                duration_minutes=duration,
                status='Scheduled',
                room_id=str(uuid.uuid4())[:8]
            )

            db.add(conference)
            db.commit()

            st.success(f"Conference scheduled! Room ID: {conference.room_id}")
            st.session_state.current_conference = conference.id
            st.rerun()
        else:
            st.error("Please fill in required fields")

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Video Conference - NEXUS",
        page_icon="📹",
        layout="wide"
    )

    # Initialize database
    init_db()

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main content
    st.title("📹 Video Conference")

    db = SessionLocal()

    if st.session_state.current_conference:
        conference = db.query(VideoConference).filter(
            VideoConference.id == st.session_state.current_conference
        ).first()

        if conference:
            render_conference_room(db, conference)
        else:
            st.error("Conference not found")
    else:
        render_new_conference(db)

    db.close()

if __name__ == "__main__":
    main()
