"""
NEXUS Video Conferencing & Webinar Module
==========================================

A comprehensive video conferencing system with the following features:

- HD Video Calls (1080p) with 100+ participants
- WebRTC-based peer-to-peer connections
- Cloud and local recording with auto-transcription
- Screen sharing with annotation tools
- Breakout rooms with auto/manual assignment
- In-meeting chat with private messaging
- Interactive reactions, polls, and Q&A
- AI-powered live transcription and translation
- Meeting summaries and action items
- Webinar mode for up to 10,000 viewers

Usage:
------
    from modules.video import ConferenceManager, RecordingManager

    # Create a conference
    manager = ConferenceManager()
    conference = manager.create_conference(title="Team Meeting")

    # Start the conference
    conference.start()

    # Add participants
    conference.add_participant(name="John Doe", role=ParticipantRole.HOST)

    # Start recording
    recording_manager = RecordingManager()
    await recording_manager.start_recording(conference.id, conference.title)

For Streamlit UI:
-----------------
    from modules.video.streamlit_ui import VideoConferenceUI

    ui = VideoConferenceUI()
    ui.render()
"""

__version__ = "1.0.0"
__author__ = "NEXUS Team"

# Conference management
from .conference import (
    Conference,
    ConferenceManager,
    ConferenceSettings,
    ConferenceMode,
    Participant,
    ParticipantRole,
    ViewMode,
    VideoQuality,
    SecuritySettings,
    MediaSettings,
)

# WebRTC functionality
from .webrtc import (
    WebRTCManager,
    PeerConnection,
    SignalingServer,
    MediaStream,
    SessionDescription,
    IceCandidate,
    PeerConnectionConfig,
    MediaStreamConstraints,
)

# Recording
from .recording import (
    RecordingManager,
    Recording,
    RecordingSettings,
    RecordingType,
    RecordingQuality,
    RecordingStatus,
    StorageType,
    RecordingMetadata,
)

# Screen sharing
from .screen_share import (
    ScreenShareManager,
    ScreenShare,
    ScreenShareSettings,
    ScreenShareType,
    ScreenShareQuality,
    AnnotationTool,
    Annotation,
    AnnotationType,
)

# Breakout rooms
from .breakout_rooms import (
    BreakoutRoomManager,
    BreakoutRoom,
    BreakoutRoomSettings,
    AssignmentMethod,
    RoomStatus,
)

# Chat
from .chat_overlay import (
    Chat,
    ChatHistory,
    ChatMessage,
    MessageType,
    ChatScope,
    FileAttachment,
)

# Reactions and engagement
from .reactions import (
    ReactionManager,
    PollManager,
    QAManager,
    Reaction,
    ReactionType,
    Poll,
    PollOption,
    PollStatus,
    Question,
    QuestionStatus,
)

# Transcription
from .transcription import (
    TranscriptionManager,
    LiveTranscription,
    MeetingSummarizer,
    TranscriptSegment,
    Translation,
    MeetingSummary,
    ActionItem,
    TranscriptionLanguage,
    TranscriptionQuality,
)

# UI (optional, requires streamlit)
try:
    from .streamlit_ui import VideoConferenceUI
    __all_ui__ = ["VideoConferenceUI"]
except ImportError:
    __all_ui__ = []

# Public API
__all__ = [
    # Conference
    "Conference",
    "ConferenceManager",
    "ConferenceSettings",
    "ConferenceMode",
    "Participant",
    "ParticipantRole",
    "ViewMode",
    "VideoQuality",
    "SecuritySettings",
    "MediaSettings",
    # WebRTC
    "WebRTCManager",
    "PeerConnection",
    "SignalingServer",
    "MediaStream",
    "SessionDescription",
    "IceCandidate",
    "PeerConnectionConfig",
    "MediaStreamConstraints",
    # Recording
    "RecordingManager",
    "Recording",
    "RecordingSettings",
    "RecordingType",
    "RecordingQuality",
    "RecordingStatus",
    "StorageType",
    "RecordingMetadata",
    # Screen Share
    "ScreenShareManager",
    "ScreenShare",
    "ScreenShareSettings",
    "ScreenShareType",
    "ScreenShareQuality",
    "AnnotationTool",
    "Annotation",
    "AnnotationType",
    # Breakout Rooms
    "BreakoutRoomManager",
    "BreakoutRoom",
    "BreakoutRoomSettings",
    "AssignmentMethod",
    "RoomStatus",
    # Chat
    "Chat",
    "ChatHistory",
    "ChatMessage",
    "MessageType",
    "ChatScope",
    "FileAttachment",
    # Reactions
    "ReactionManager",
    "PollManager",
    "QAManager",
    "Reaction",
    "ReactionType",
    "Poll",
    "PollOption",
    "PollStatus",
    "Question",
    "QuestionStatus",
    # Transcription
    "TranscriptionManager",
    "LiveTranscription",
    "MeetingSummarizer",
    "TranscriptSegment",
    "Translation",
    "MeetingSummary",
    "ActionItem",
    "TranscriptionLanguage",
    "TranscriptionQuality",
] + __all_ui__
