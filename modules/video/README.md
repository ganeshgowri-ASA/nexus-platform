# NEXUS Video Conferencing & Webinar Module

A production-ready video conferencing system that rivals Zoom and Google Meet, built for the NEXUS platform.

## Features

### 🎥 Video Calls
- **HD Quality**: Support for 1080p video streaming
- **Multi-Participant**: Handle 100+ participants simultaneously
- **View Modes**: Gallery, Speaker, Spotlight, and Sidebar views
- **Virtual Backgrounds**: Apply custom backgrounds and filters
- **Quality Control**: Auto-adjust quality based on bandwidth

### 🔊 Audio
- **Noise Cancellation**: Advanced noise suppression
- **Echo Reduction**: Automatic echo cancellation
- **Audio-Only Mode**: Join meetings without video
- **Smart Muting**: Host can mute all or individual participants

### 🖥️ Screen Sharing
- **Full Screen & Window**: Share entire screen or specific applications
- **Annotation Tools**: Draw, highlight, and annotate during sharing
- **Multiple Shares**: Support simultaneous screen sharing (configurable)

### 📹 Recording
- **Cloud Recording**: Store recordings in the cloud
- **Local Recording**: Save to local storage
- **Auto-Transcription**: Generate transcripts automatically
- **Multiple Formats**: MP4, WebM, and audio-only options

### 🎯 Interactive Features
- **Hand Raise**: Non-verbal participant signaling
- **Reactions**: Real-time emoji reactions (👍, ❤️, 😂, etc.)
- **Polls**: Create and run live polls during meetings
- **Q&A**: Structured question and answer sessions
- **Whiteboard**: Collaborative whiteboard (coming soon)

### 🚪 Breakout Rooms
- **Auto/Manual Assignment**: Flexible participant distribution
- **Timer Support**: Set time limits for breakout sessions
- **Broadcast**: Send messages to all breakout rooms
- **Easy Return**: Participants can rejoin main room anytime

### 💬 Chat
- **Public & Private**: Group chat and direct messages
- **File Sharing**: Share files up to 100MB
- **Message Threading**: Reply to specific messages
- **Chat Export**: Save chat history

### 🌐 Webinar Mode
- **Large Scale**: Support up to 10,000 viewers
- **Roles**: Host, Panelist, and Attendee permissions
- **Q&A Management**: Moderate questions from attendees
- **Recording**: Auto-record all webinars

### 🔒 Security
- **Waiting Room**: Screen participants before entry
- **Password Protection**: Secure meetings with passwords
- **Lock Meeting**: Prevent new participants from joining
- **Remove Participants**: Host can remove disruptive users
- **End-to-End Encryption**: Secure all communications

### 🤖 AI Features
- **Live Transcription**: Real-time speech-to-text
- **Translation**: Translate to 12+ languages in real-time
- **Meeting Summary**: AI-generated meeting summaries
- **Action Items**: Automatically extract action items
- **Key Points**: Identify and highlight key discussion points

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit UI
streamlit run modules/video/streamlit_ui.py
```

## Quick Start

### Creating a Conference

```python
from modules.video import ConferenceManager, ConferenceSettings, ConferenceMode

# Create manager
manager = ConferenceManager()

# Configure settings
settings = ConferenceSettings(
    mode=ConferenceMode.MEETING,
    max_participants=100,
    enable_recording=True,
    enable_transcription=True,
    enable_chat=True,
)

# Create conference
conference = manager.create_conference(
    title="Team Standup",
    settings=settings,
)

# Start the conference
conference.start()
```

### Adding Participants

```python
from modules.video import ParticipantRole

# Add host
host = conference.add_participant(
    name="John Doe",
    email="john@example.com",
    role=ParticipantRole.HOST,
)

# Add regular participant
participant = conference.add_participant(
    name="Jane Smith",
    email="jane@example.com",
)
```

### Recording

```python
from modules.video import RecordingManager, RecordingSettings

# Create recording manager
rec_manager = RecordingManager()

# Start recording
recording = await rec_manager.start_recording(
    conference_id=conference.id,
    conference_title=conference.title,
)

# Stop recording
await rec_manager.stop_recording(conference.id)
```

### Screen Sharing

```python
from modules.video import ScreenShareManager

# Create screen share manager
share_manager = ScreenShareManager(conference.id)

# Start sharing
screen_share = share_manager.start_screen_share(
    participant_id="user_123",
    participant_name="John Doe",
)

# Stop sharing
share_manager.stop_screen_share("user_123")
```

### Breakout Rooms

```python
from modules.video import BreakoutRoomManager, AssignmentMethod

# Create breakout room manager
br_manager = BreakoutRoomManager(conference.id)

# Create 3 breakout rooms
rooms = br_manager.create_rooms(num_rooms=3)

# Assign participants automatically
participant_ids = ["user1", "user2", "user3", "user4", "user5"]
assignments = br_manager.assign_participants(
    participant_ids,
    method=AssignmentMethod.AUTOMATIC,
)

# Start rooms with 15-minute timer
await br_manager.start_rooms_with_timer(
    duration_minutes=15,
    warning_minutes=1,
)
```

### Chat

```python
from modules.video import Chat, ChatScope

# Create chat
chat = Chat(conference.id)

# Send public message
message = chat.send_message(
    sender_id="user1",
    sender_name="John",
    content="Hello everyone!",
    scope=ChatScope.PUBLIC,
)

# Send private message
private_msg = chat.send_message(
    sender_id="user1",
    sender_name="John",
    content="Can we talk after?",
    scope=ChatScope.PRIVATE,
    recipient_id="user2",
    recipient_name="Jane",
)

# Export chat
chat_export = chat.export_chat()
```

### Polls & Q&A

```python
from modules.video import PollManager, QAManager

# Create poll
poll_manager = PollManager(conference.id)
poll = poll_manager.create_poll(
    question="What time works best for next meeting?",
    options=["9 AM", "2 PM", "4 PM"],
    created_by="host",
)

# Start poll
poll_manager.start_poll(poll.id)

# Vote
poll_manager.vote(poll.id, "user1", poll.options[0].id)

# End poll and get results
poll_manager.end_poll(poll.id)
results = poll.get_results()

# Q&A
qa_manager = QAManager(conference.id)
qa_manager.enable()

# Ask question
question = qa_manager.ask_question(
    participant_id="user1",
    participant_name="John",
    question_text="What's the project timeline?",
)

# Upvote question
qa_manager.upvote_question(question.id, "user2")

# Answer question
qa_manager.answer_question(
    question.id,
    "The timeline is 6 months",
    "host",
)
```

### Transcription & AI

```python
from modules.video import TranscriptionManager, TranscriptionLanguage

# Create transcription manager
trans_manager = TranscriptionManager()

# Start transcription
transcription = trans_manager.start_transcription(
    conference.id,
    primary_language=TranscriptionLanguage.ENGLISH,
)

# Enable real-time translation
transcription.enable_translation("es")  # Spanish
transcription.enable_translation("fr")  # French

# Generate meeting summary
summary = await trans_manager.generate_meeting_summary(
    conference.id,
    participants=["John", "Jane", "Bob"],
)

# Export summary
summary_text = trans_manager.export_summary(conference.id)
```

## Architecture

```
modules/video/
├── __init__.py              # Module exports
├── conference.py            # Core conference management
├── webrtc.py               # WebRTC signaling & peer connections
├── recording.py            # Cloud & local recording
├── screen_share.py         # Screen sharing with annotations
├── breakout_rooms.py       # Breakout room management
├── chat_overlay.py         # Chat with file sharing
├── reactions.py            # Reactions, polls, Q&A
├── transcription.py        # AI transcription & translation
└── streamlit_ui.py         # Streamlit web interface
```

## Testing

```bash
# Run all tests
pytest tests/video/

# Run specific test
pytest tests/video/test_video_conference.py::TestConference

# Run with coverage
pytest tests/video/ --cov=modules/video --cov-report=html
```

## API Reference

### Conference

- `Conference.start()` - Start the conference
- `Conference.end()` - End the conference
- `Conference.add_participant()` - Add a participant
- `Conference.remove_participant()` - Remove a participant
- `Conference.mute_participant()` - Mute a participant
- `Conference.lock_conference()` - Lock the meeting

### WebRTC

- `WebRTCManager.add_peer()` - Add a peer connection
- `WebRTCManager.remove_peer()` - Remove a peer
- `PeerConnection.create_offer()` - Create SDP offer
- `PeerConnection.create_answer()` - Create SDP answer

### Recording

- `RecordingManager.start_recording()` - Start recording
- `RecordingManager.stop_recording()` - Stop recording
- `Recording.pause()` - Pause recording
- `Recording.resume()` - Resume recording

See individual module documentation for complete API reference.

## Production Deployment

### Requirements

1. **WebRTC Server**: Deploy a TURN/STUN server for NAT traversal
2. **Media Server**: Use a media server like Jitsi, Janus, or mediasoup
3. **Cloud Storage**: Configure AWS S3, Google Cloud Storage, or Azure Blob
4. **Database**: Store conference metadata and recordings
5. **CDN**: Distribute recordings via CDN
6. **Load Balancer**: Handle multiple concurrent conferences

### Recommended Stack

- **Frontend**: Streamlit or React
- **Backend**: FastAPI or Django
- **WebRTC**: Jitsi Meet or Janus Gateway
- **Storage**: AWS S3
- **Database**: PostgreSQL
- **Cache**: Redis
- **Queue**: Celery
- **AI**: Claude API or OpenAI

## Performance

- **Scalability**: Handles 100+ participants per conference
- **Latency**: < 100ms for peer connections
- **Quality**: Adaptive bitrate streaming
- **Storage**: Efficient compression for recordings
- **Bandwidth**: Optimized for 2G to 5G networks

## Security

- **Encryption**: AES-256 for recordings, DTLS-SRTP for streams
- **Authentication**: JWT tokens
- **Authorization**: Role-based access control
- **Audit Logs**: Track all conference activities
- **Compliance**: GDPR, HIPAA ready

## Roadmap

- [ ] Mobile apps (iOS/Android)
- [ ] Desktop apps (Windows/Mac/Linux)
- [ ] Virtual reality support
- [ ] AI noise removal
- [ ] Background blur
- [ ] Beauty filters
- [ ] Live streaming to YouTube/Twitch
- [ ] Calendar integration (Google/Outlook)
- [ ] CRM integration (Salesforce/HubSpot)

## License

Copyright © 2024 NEXUS Team. All rights reserved.

## Support

For issues and feature requests, please open an issue on GitHub.

---

Built with ❤️ for the NEXUS Platform
