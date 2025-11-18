"""
NEXUS Video Conferencing Streamlit UI
Comprehensive interface for video conferencing, webinars, and meetings
"""

import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import asyncio

# Import NEXUS video modules
from .conference import (
    Conference,
    ConferenceManager,
    ConferenceSettings,
    ConferenceMode,
    ParticipantRole,
    ViewMode,
    SecuritySettings,
)
from .webrtc import WebRTCManager, MediaStreamConstraints
from .recording import RecordingManager, RecordingSettings, RecordingType, RecordingQuality
from .screen_share import ScreenShareManager, ScreenShareSettings
from .breakout_rooms import BreakoutRoomManager, BreakoutRoomSettings, AssignmentMethod
from .chat_overlay import Chat, ChatScope
from .reactions import ReactionManager, PollManager, QAManager, ReactionType
from .transcription import TranscriptionManager, TranscriptionLanguage


class VideoConferenceUI:
    """
    Streamlit UI for NEXUS Video Conferencing
    """

    def __init__(self):
        self.init_session_state()

    def init_session_state(self):
        """Initialize Streamlit session state"""
        if "conference_manager" not in st.session_state:
            st.session_state.conference_manager = ConferenceManager()

        if "recording_manager" not in st.session_state:
            st.session_state.recording_manager = RecordingManager()

        if "transcription_manager" not in st.session_state:
            st.session_state.transcription_manager = TranscriptionManager()

        if "current_conference" not in st.session_state:
            st.session_state.current_conference = None

        if "current_user" not in st.session_state:
            st.session_state.current_user = {
                "id": "user_001",
                "name": "Demo User",
                "role": ParticipantRole.HOST,
            }

        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []

    def render(self):
        """Render the main UI"""
        st.set_page_config(
            page_title="NEXUS Video Conferencing",
            page_icon="📹",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        st.title("📹 NEXUS Video Conferencing & Webinar Platform")

        # Sidebar navigation
        with st.sidebar:
            self.render_sidebar()

        # Main content area
        if st.session_state.current_conference:
            self.render_active_conference()
        else:
            self.render_conference_lobby()

    def render_sidebar(self):
        """Render sidebar navigation"""
        st.header("🎯 Navigation")

        menu = st.radio(
            "Select View",
            [
                "Conference Lobby",
                "Active Meetings",
                "Schedule Meeting",
                "Recordings",
                "Settings",
            ],
            key="sidebar_menu",
        )

        st.divider()

        # User info
        st.subheader("👤 User Profile")
        user = st.session_state.current_user
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Role:** {user['role'].value}")

        st.divider()

        # Quick actions
        st.subheader("⚡ Quick Actions")

        if st.button("🆕 New Meeting", use_container_width=True):
            self.create_instant_meeting()

        if st.button("📅 Schedule Meeting", use_container_width=True):
            st.session_state.sidebar_menu = "Schedule Meeting"

        if st.button("📊 View Statistics", use_container_width=True):
            self.show_statistics()

    def render_conference_lobby(self):
        """Render conference lobby (pre-meeting)"""
        st.header("🏠 Conference Lobby")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Start New Meeting")

            meeting_title = st.text_input(
                "Meeting Title",
                value=f"NEXUS Meeting - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            )

            meeting_mode = st.selectbox(
                "Meeting Mode",
                options=[mode.value for mode in ConferenceMode],
                format_func=lambda x: x.replace("_", " ").title(),
            )

            col_a, col_b = st.columns(2)

            with col_a:
                max_participants = st.number_input(
                    "Max Participants",
                    min_value=2,
                    max_value=10000,
                    value=100,
                )

            with col_b:
                enable_waiting_room = st.checkbox("Enable Waiting Room", value=True)

            # Security settings
            with st.expander("🔒 Security Settings"):
                require_password = st.checkbox("Require Password")
                meeting_password = ""
                if require_password:
                    meeting_password = st.text_input(
                        "Meeting Password",
                        type="password",
                    )

                encryption_enabled = st.checkbox("End-to-End Encryption", value=True)
                watermark_enabled = st.checkbox("Add Watermark to Video")

            # Features
            with st.expander("✨ Features"):
                enable_recording = st.checkbox("Enable Recording", value=True)
                enable_transcription = st.checkbox("Enable Live Transcription", value=True)
                enable_chat = st.checkbox("Enable Chat", value=True)
                enable_reactions = st.checkbox("Enable Reactions", value=True)
                enable_breakout_rooms = st.checkbox("Enable Breakout Rooms")
                enable_polls = st.checkbox("Enable Polls & Q&A", value=True)

            if st.button("🚀 Start Meeting", type="primary", use_container_width=True):
                self.start_new_conference(
                    title=meeting_title,
                    mode=ConferenceMode(meeting_mode),
                    max_participants=max_participants,
                    enable_waiting_room=enable_waiting_room,
                    enable_recording=enable_recording,
                    enable_transcription=enable_transcription,
                    enable_chat=enable_chat,
                    enable_reactions=enable_reactions,
                    enable_breakout_rooms=enable_breakout_rooms,
                    enable_polls=enable_polls,
                )

        with col2:
            st.subheader("Join Existing Meeting")

            conference_id = st.text_input("Enter Meeting ID or Link")

            participant_name = st.text_input(
                "Your Name",
                value=st.session_state.current_user["name"],
            )

            join_options = st.columns(2)

            with join_options[0]:
                join_with_video = st.checkbox("Join with Video", value=True)

            with join_options[1]:
                join_with_audio = st.checkbox("Join with Audio", value=True)

            if st.button("🎥 Join Meeting", type="primary", use_container_width=True):
                if conference_id:
                    self.join_conference(
                        conference_id,
                        participant_name,
                        join_with_video,
                        join_with_audio,
                    )
                else:
                    st.error("Please enter a meeting ID")

        # Active conferences
        st.divider()
        st.subheader("📋 Active Conferences")

        active_conferences = st.session_state.conference_manager.get_active_conferences()

        if active_conferences:
            for conf in active_conferences:
                with st.expander(f"📹 {conf.title}"):
                    col_a, col_b, col_c = st.columns(3)

                    with col_a:
                        st.metric("Participants", conf.get_participant_count())

                    with col_b:
                        duration = (datetime.now() - conf.started_at).total_seconds() if conf.started_at else 0
                        st.metric("Duration", f"{int(duration // 60)} min")

                    with col_c:
                        if st.button("Join", key=f"join_{conf.id}"):
                            st.session_state.current_conference = conf
                            st.rerun()
        else:
            st.info("No active conferences")

    def render_active_conference(self):
        """Render active conference interface"""
        conf = st.session_state.current_conference

        # Top bar with controls
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.header(f"📹 {conf.title}")

        with col2:
            duration = (datetime.now() - conf.started_at).total_seconds() if conf.started_at else 0
            st.metric("Duration", f"{int(duration // 60)}:{int(duration % 60):02d}")

        with col3:
            if st.button("🚪 Leave Meeting", type="secondary"):
                self.leave_conference()
                return

        st.divider()

        # Main conference area
        col_main, col_sidebar = st.columns([3, 1])

        with col_main:
            # Video grid
            self.render_video_grid(conf)

            # Bottom controls
            self.render_conference_controls(conf)

        with col_sidebar:
            # Tabs for different features
            tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "👥 Participants", "📊 Polls", "📝 Q&A"])

            with tab1:
                self.render_chat_panel(conf)

            with tab2:
                self.render_participants_panel(conf)

            with tab3:
                self.render_polls_panel(conf)

            with tab4:
                self.render_qa_panel(conf)

    def render_video_grid(self, conference: Conference):
        """Render video grid"""
        st.subheader("🎥 Video Grid")

        # View mode selector
        view_mode = st.radio(
            "View Mode",
            options=[mode.value for mode in ViewMode],
            format_func=lambda x: x.replace("_", " ").title(),
            horizontal=True,
        )

        # Simulate video tiles
        participants = list(conference.participants.values())

        if participants:
            # Display in grid
            cols_per_row = 3 if len(participants) > 4 else 2
            rows = (len(participants) + cols_per_row - 1) // cols_per_row

            for row in range(rows):
                cols = st.columns(cols_per_row)
                for col_idx in range(cols_per_row):
                    idx = row * cols_per_row + col_idx
                    if idx < len(participants):
                        participant = participants[idx]
                        with cols[col_idx]:
                            self.render_video_tile(participant)
        else:
            st.info("No participants in the meeting")

    def render_video_tile(self, participant):
        """Render individual video tile"""
        with st.container():
            # Placeholder for video
            st.image(
                "https://via.placeholder.com/300x200/1f1f1f/ffffff?text=Video",
                use_container_width=True,
            )

            # Participant info
            col1, col2 = st.columns([3, 1])

            with col1:
                status_icons = []
                if participant.is_muted:
                    status_icons.append("🔇")
                else:
                    status_icons.append("🎤")

                if participant.is_video_off:
                    status_icons.append("📷")

                if participant.is_hand_raised:
                    status_icons.append("✋")

                st.caption(f"{''.join(status_icons)} {participant.name}")

            with col2:
                st.caption(participant.role.value[:1].upper())

    def render_conference_controls(self, conference: Conference):
        """Render conference control buttons"""
        st.divider()

        cols = st.columns(8)

        with cols[0]:
            if st.button("🎤 Mute", use_container_width=True):
                st.success("Muted")

        with cols[1]:
            if st.button("📹 Video", use_container_width=True):
                st.success("Video toggled")

        with cols[2]:
            if st.button("🖥️ Share", use_container_width=True):
                st.info("Screen sharing started")

        with cols[3]:
            if st.button("✋ Raise Hand", use_container_width=True):
                user_id = st.session_state.current_user["id"]
                conference.raise_hand(user_id)
                st.success("Hand raised")

        with cols[4]:
            if st.button("👏 React", use_container_width=True):
                st.success("Reaction sent")

        with cols[5]:
            if st.button("⚙️ More", use_container_width=True):
                self.show_more_options(conference)

        with cols[6]:
            if st.button("🔴 Record", use_container_width=True):
                self.toggle_recording(conference)

        with cols[7]:
            if st.button("📊 Stats", use_container_width=True):
                self.show_conference_stats(conference)

    def render_chat_panel(self, conference: Conference):
        """Render chat panel"""
        st.subheader("💬 Chat")

        # Chat scope selector
        chat_scope = st.radio(
            "Chat Type",
            ["Public", "Private"],
            horizontal=True,
        )

        # Chat messages
        chat_container = st.container(height=400)

        with chat_container:
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.write(f"**{msg['name']}**")
                    st.write(msg["content"])
                    st.caption(msg["timestamp"])

        # Chat input
        chat_input = st.chat_input("Type a message...")

        if chat_input:
            msg = {
                "role": "user",
                "name": st.session_state.current_user["name"],
                "content": chat_input,
                "timestamp": datetime.now().strftime("%H:%M"),
            }
            st.session_state.chat_messages.append(msg)
            st.rerun()

    def render_participants_panel(self, conference: Conference):
        """Render participants panel"""
        st.subheader(f"👥 Participants ({conference.get_participant_count()})")

        # Participant list
        for participant in conference.participants.values():
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    icons = []
                    if participant.is_muted:
                        icons.append("🔇")
                    if participant.is_hand_raised:
                        icons.append("✋")

                    st.write(f"{''.join(icons)} {participant.name}")
                    st.caption(participant.role.value)

                with col2:
                    if st.session_state.current_user["role"] == ParticipantRole.HOST:
                        if st.button("⋮", key=f"menu_{participant.id}"):
                            self.show_participant_menu(participant)

                st.divider()

    def render_polls_panel(self, conference: Conference):
        """Render polls panel"""
        st.subheader("📊 Polls")

        if st.button("➕ Create Poll"):
            self.create_poll_dialog()

        # Show active polls
        st.write("*No active polls*")

    def render_qa_panel(self, conference: Conference):
        """Render Q&A panel"""
        st.subheader("📝 Q&A")

        # Ask question
        question = st.text_area("Ask a question...")

        if st.button("Submit Question"):
            if question:
                st.success("Question submitted!")
            else:
                st.error("Please enter a question")

        # Show questions
        st.divider()
        st.write("*No questions yet*")

    def create_instant_meeting(self):
        """Create and start an instant meeting"""
        settings = ConferenceSettings(
            mode=ConferenceMode.MEETING,
            max_participants=100,
            enable_recording=True,
            enable_chat=True,
        )

        conference = st.session_state.conference_manager.create_conference(
            title=f"Quick Meeting - {datetime.now().strftime('%H:%M')}",
            settings=settings,
        )

        conference.start()

        # Add current user as host
        conference.add_participant(
            name=st.session_state.current_user["name"],
            role=ParticipantRole.HOST,
            bypass_waiting_room=True,
        )

        st.session_state.current_conference = conference
        st.success(f"Meeting started! ID: {conference.id}")
        st.rerun()

    def start_new_conference(self, **kwargs):
        """Start a new conference with settings"""
        security = SecuritySettings(
            waiting_room_enabled=kwargs.get("enable_waiting_room", False),
            encryption_enabled=True,
        )

        settings = ConferenceSettings(
            mode=kwargs.get("mode", ConferenceMode.MEETING),
            max_participants=kwargs.get("max_participants", 100),
            enable_waiting_room=kwargs.get("enable_waiting_room", False),
            enable_recording=kwargs.get("enable_recording", True),
            enable_transcription=kwargs.get("enable_transcription", False),
            enable_chat=kwargs.get("enable_chat", True),
            enable_reactions=kwargs.get("enable_reactions", True),
            enable_breakout_rooms=kwargs.get("enable_breakout_rooms", False),
            enable_polls=kwargs.get("enable_polls", True),
            security=security,
        )

        conference = st.session_state.conference_manager.create_conference(
            title=kwargs.get("title", "New Meeting"),
            settings=settings,
        )

        conference.start()

        # Add current user
        conference.add_participant(
            name=st.session_state.current_user["name"],
            role=ParticipantRole.HOST,
            bypass_waiting_room=True,
        )

        st.session_state.current_conference = conference

        # Start transcription if enabled
        if kwargs.get("enable_transcription"):
            st.session_state.transcription_manager.start_transcription(
                conference.id,
                TranscriptionLanguage.ENGLISH,
            )

        st.success("Meeting started!")
        st.rerun()

    def join_conference(
        self,
        conference_id: str,
        participant_name: str,
        video_enabled: bool,
        audio_enabled: bool,
    ):
        """Join an existing conference"""
        conference = st.session_state.conference_manager.get_conference(conference_id)

        if conference:
            participant = conference.add_participant(
                name=participant_name,
                role=ParticipantRole.PARTICIPANT,
            )

            if participant:
                st.session_state.current_conference = conference
                st.success("Joined meeting!")
                st.rerun()
            else:
                st.error("Could not join meeting")
        else:
            st.error("Meeting not found")

    def leave_conference(self):
        """Leave the current conference"""
        if st.session_state.current_conference:
            conf = st.session_state.current_conference
            user_id = st.session_state.current_user["id"]

            # Find and remove participant
            for participant in conf.participants.values():
                if participant.name == st.session_state.current_user["name"]:
                    conf.remove_participant(participant.id)
                    break

            st.session_state.current_conference = None
            st.success("Left meeting")
            st.rerun()

    def toggle_recording(self, conference: Conference):
        """Toggle recording for conference"""
        if not conference.is_recording:
            # Start recording
            asyncio.run(
                st.session_state.recording_manager.start_recording(
                    conference.id,
                    conference.title,
                )
            )
            conference.is_recording = True
            st.success("Recording started")
        else:
            # Stop recording
            asyncio.run(
                st.session_state.recording_manager.stop_recording(conference.id)
            )
            conference.is_recording = False
            st.success("Recording stopped")

    def show_conference_stats(self, conference: Conference):
        """Show conference statistics"""
        stats = conference.get_conference_stats()

        with st.expander("📊 Conference Statistics", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Participants", stats["participant_count"])

            with col2:
                st.metric("Duration", f"{int(stats['duration_seconds'] // 60)} min")

            with col3:
                st.metric("Status", "Active" if stats["is_active"] else "Ended")

    def show_statistics(self):
        """Show overall statistics"""
        st.subheader("📊 Platform Statistics")

        manager = st.session_state.conference_manager

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Conferences",
                len(manager.get_all_conferences()),
            )

        with col2:
            st.metric(
                "Active Conferences",
                len(manager.get_active_conferences()),
            )

        with col3:
            recording_stats = st.session_state.recording_manager.get_storage_usage()
            st.metric(
                "Total Recordings",
                recording_stats["total_recordings"],
            )

    def show_more_options(self, conference: Conference):
        """Show more options menu"""
        with st.popover("⚙️ More Options"):
            if st.button("🎨 Virtual Background"):
                st.info("Virtual background settings")

            if st.button("🔊 Audio Settings"):
                st.info("Audio settings")

            if st.button("📹 Video Settings"):
                st.info("Video settings")

            if st.button("🌐 Network Stats"):
                st.info("Network statistics")

    def show_participant_menu(self, participant):
        """Show participant menu for hosts"""
        with st.popover(f"Options for {participant.name}"):
            if st.button("🔇 Mute"):
                st.success(f"Muted {participant.name}")

            if st.button("📹 Stop Video"):
                st.success(f"Stopped video for {participant.name}")

            if st.button("🚪 Remove"):
                st.warning(f"Removed {participant.name}")

    def create_poll_dialog(self):
        """Dialog to create a poll"""
        with st.dialog("Create Poll"):
            question = st.text_input("Poll Question")

            num_options = st.number_input("Number of Options", min_value=2, max_value=10, value=3)

            options = []
            for i in range(num_options):
                option = st.text_input(f"Option {i + 1}", key=f"poll_option_{i}")
                if option:
                    options.append(option)

            if st.button("Create Poll"):
                if question and len(options) >= 2:
                    st.success("Poll created!")
                else:
                    st.error("Please provide a question and at least 2 options")


def main():
    """Main entry point"""
    ui = VideoConferenceUI()
    ui.render()


if __name__ == "__main__":
    main()
