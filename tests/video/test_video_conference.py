"""
Comprehensive tests for NEXUS Video Conferencing Module
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Import modules to test
from modules.video.conference import (
    Conference,
    ConferenceManager,
    ConferenceSettings,
    ConferenceMode,
    ParticipantRole,
    Participant,
)
from modules.video.webrtc import (
    WebRTCManager,
    PeerConnection,
    SignalingServer,
    SessionDescription,
)
from modules.video.recording import (
    RecordingManager,
    Recording,
    RecordingSettings,
    RecordingType,
)
from modules.video.screen_share import (
    ScreenShareManager,
    ScreenShare,
    AnnotationTool,
)
from modules.video.breakout_rooms import (
    BreakoutRoomManager,
    BreakoutRoom,
    AssignmentMethod,
)
from modules.video.chat_overlay import (
    Chat,
    ChatMessage,
    ChatScope,
)
from modules.video.reactions import (
    ReactionManager,
    PollManager,
    QAManager,
    ReactionType,
)
from modules.video.transcription import (
    TranscriptionManager,
    LiveTranscription,
    TranscriptionLanguage,
)


class TestConference:
    """Test Conference class"""

    def test_conference_creation(self):
        """Test creating a conference"""
        conf = Conference(title="Test Meeting")

        assert conf.title == "Test Meeting"
        assert conf.is_active is False
        assert len(conf.participants) == 0

    def test_conference_start_stop(self):
        """Test starting and stopping a conference"""
        conf = Conference(title="Test Meeting")

        assert conf.start() is True
        assert conf.is_active is True
        assert conf.started_at is not None

        assert conf.end() is True
        assert conf.is_active is False
        assert conf.ended_at is not None

    def test_add_participant(self):
        """Test adding participants"""
        conf = Conference(title="Test Meeting")
        conf.start()

        participant = conf.add_participant(
            name="John Doe",
            email="john@example.com",
            role=ParticipantRole.HOST,
        )

        assert participant is not None
        assert participant.name == "John Doe"
        assert conf.get_participant_count() == 1

    def test_participant_limit(self):
        """Test participant limit"""
        settings = ConferenceSettings(max_participants=2)
        conf = Conference(title="Test Meeting", settings=settings)
        conf.start()

        # Add max participants
        conf.add_participant("User 1")
        conf.add_participant("User 2")

        # Should fail to add more
        participant = conf.add_participant("User 3")
        assert participant is None
        assert conf.get_participant_count() == 2

    def test_mute_unmute_participant(self):
        """Test muting and unmuting participants"""
        conf = Conference(title="Test Meeting")
        conf.start()

        participant = conf.add_participant("John Doe")

        assert conf.mute_participant(participant.id) is True
        assert participant.is_muted is True

        assert conf.unmute_participant(participant.id) is True
        assert participant.is_muted is False

    def test_mute_all(self):
        """Test muting all participants"""
        conf = Conference(title="Test Meeting")
        conf.start()

        # Add participants
        conf.add_participant("User 1", role=ParticipantRole.HOST)
        conf.add_participant("User 2", role=ParticipantRole.PARTICIPANT)
        conf.add_participant("User 3", role=ParticipantRole.PARTICIPANT)

        # Mute all except hosts
        count = conf.mute_all(except_hosts=True)

        assert count == 2  # Only non-hosts muted

    def test_lock_unlock_conference(self):
        """Test locking and unlocking conference"""
        conf = Conference(title="Test Meeting")
        conf.start()

        assert conf.lock_conference() is True
        assert conf.is_locked is True

        # Should fail to add participant when locked
        participant = conf.add_participant("User 1")
        assert participant is None

        assert conf.unlock_conference() is True
        assert conf.is_locked is False

    def test_waiting_room(self):
        """Test waiting room functionality"""
        settings = ConferenceSettings(enable_waiting_room=True)
        settings.security.waiting_room_enabled = True
        conf = Conference(title="Test Meeting", settings=settings)
        conf.start()

        # Participant should go to waiting room
        participant = conf.add_participant("User 1")

        assert participant.in_waiting_room is True
        assert participant.id in conf.waiting_room

        # Admit from waiting room
        assert conf.admit_from_waiting_room(participant.id) is True
        assert participant.in_waiting_room is False


class TestConferenceManager:
    """Test ConferenceManager class"""

    def test_create_conference(self):
        """Test creating conferences"""
        manager = ConferenceManager()

        conf = manager.create_conference(title="Test Meeting")

        assert conf is not None
        assert conf.title == "Test Meeting"
        assert conf.id in manager.conferences

    def test_get_active_conferences(self):
        """Test getting active conferences"""
        manager = ConferenceManager()

        conf1 = manager.create_conference(title="Meeting 1")
        conf2 = manager.create_conference(title="Meeting 2")

        conf1.start()

        active = manager.get_active_conferences()

        assert len(active) == 1
        assert active[0] == conf1

    def test_schedule_conference(self):
        """Test scheduling a conference"""
        manager = ConferenceManager()

        future_time = datetime.now() + timedelta(hours=1)
        conf_id = manager.schedule_conference(
            title="Future Meeting",
            scheduled_time=future_time,
            duration_minutes=60,
        )

        assert conf_id is not None

        scheduled = manager.get_scheduled_conferences()
        assert len(scheduled) == 1


@pytest.mark.asyncio
class TestWebRTC:
    """Test WebRTC functionality"""

    async def test_peer_connection_creation(self):
        """Test creating a peer connection"""
        pc = PeerConnection(peer_id="peer1")

        assert pc.peer_id == "peer1"
        assert pc.connection_state.value == "new"

    async def test_create_offer_answer(self):
        """Test SDP offer/answer exchange"""
        pc1 = PeerConnection(peer_id="peer1", is_initiator=True)
        pc2 = PeerConnection(peer_id="peer2")

        # Create offer
        offer = await pc1.create_offer()
        assert offer.type == "offer"

        # Set remote description
        await pc2.set_remote_description(offer)

        # Create answer
        answer = await pc2.create_answer()
        assert answer.type == "answer"

        # Set remote description on peer1
        await pc1.set_remote_description(answer)

    async def test_webrtc_manager(self):
        """Test WebRTC manager"""
        manager = WebRTCManager(conference_id="conf1")

        # Add peers
        pc1 = await manager.add_peer("peer1")
        pc2 = await manager.add_peer("peer2")

        assert len(manager.peer_connections) == 2

        # Negotiate connection
        success = await manager.negotiate_connection("peer1", "peer2")
        assert success is True

    async def test_signaling_server(self):
        """Test signaling server"""
        server = SignalingServer()

        # Join room
        await server.join_room("room1", "peer1")
        await server.join_room("room1", "peer2")

        peers = server.get_room_peers("room1")
        assert len(peers) == 2

        # Leave room
        await server.leave_room("room1", "peer1")
        peers = server.get_room_peers("room1")
        assert len(peers) == 1


@pytest.mark.asyncio
class TestRecording:
    """Test recording functionality"""

    async def test_recording_creation(self):
        """Test creating a recording"""
        recording = Recording(
            conference_id="conf1",
            conference_title="Test Meeting",
        )

        assert recording.conference_id == "conf1"
        assert recording.status.value == "idle"

    async def test_recording_lifecycle(self):
        """Test recording start, pause, resume, stop"""
        recording = Recording(
            conference_id="conf1",
            conference_title="Test Meeting",
        )

        # Start
        await recording.start()
        assert recording.status.value == "recording"

        # Pause
        await recording.pause()
        assert recording.status.value == "paused"

        # Resume
        await recording.resume()
        assert recording.status.value == "recording"

        # Stop
        await recording.stop()
        assert recording.status.value in ["stopped", "processing", "completed"]

    async def test_recording_manager(self):
        """Test recording manager"""
        manager = RecordingManager()

        # Start recording
        recording = await manager.start_recording(
            conference_id="conf1",
            conference_title="Test Meeting",
        )

        assert recording is not None
        assert "conf1" in manager.active_recordings

        # Stop recording
        success = await manager.stop_recording("conf1")
        assert success is True
        assert "conf1" not in manager.active_recordings


class TestScreenShare:
    """Test screen sharing functionality"""

    def test_screen_share_creation(self):
        """Test creating a screen share"""
        share = ScreenShare(
            participant_id="user1",
            participant_name="John Doe",
        )

        assert share.participant_id == "user1"
        assert share.is_active is False

    def test_screen_share_lifecycle(self):
        """Test screen share start/stop"""
        share = ScreenShare(
            participant_id="user1",
            participant_name="John Doe",
        )

        # Start
        assert share.start() is True
        assert share.is_active is True

        # Stop
        assert share.stop() is True
        assert share.is_active is False

    def test_annotation_tool(self):
        """Test annotation tool"""
        tool = AnnotationTool()

        # Add annotation
        annotation = tool.add_annotation(
            user_id="user1",
            points=[(0, 0), (100, 100)],
        )

        assert annotation is not None
        assert len(tool.annotations) == 1

        # Update annotation
        success = tool.update_annotation(
            annotation.id,
            text="Test annotation",
        )
        assert success is True

        # Remove annotation
        success = tool.remove_annotation(annotation.id)
        assert success is True
        assert len(tool.annotations) == 0


@pytest.mark.asyncio
class TestBreakoutRooms:
    """Test breakout rooms functionality"""

    def test_breakout_room_creation(self):
        """Test creating a breakout room"""
        room = BreakoutRoom(room_number=1, name="Room 1")

        assert room.room_number == 1
        assert room.name == "Room 1"
        assert room.status.value == "created"

    def test_breakout_room_participants(self):
        """Test adding/removing participants"""
        room = BreakoutRoom(room_number=1)

        # Add participant
        assert room.add_participant("user1") is True
        assert len(room.participants) == 1

        # Remove participant
        assert room.remove_participant("user1") is True
        assert len(room.participants) == 0

    def test_breakout_room_manager(self):
        """Test breakout room manager"""
        manager = BreakoutRoomManager(conference_id="conf1")

        # Create rooms
        rooms = manager.create_rooms(num_rooms=3)

        assert len(rooms) == 3
        assert len(manager.rooms) == 3

    def test_participant_assignment(self):
        """Test automatic participant assignment"""
        manager = BreakoutRoomManager(conference_id="conf1")

        # Create rooms
        manager.create_rooms(num_rooms=2)

        # Assign participants
        participants = ["user1", "user2", "user3", "user4"]
        assignments = manager.assign_participants(participants)

        assert len(assignments) == 2  # 2 rooms

    async def test_room_timer(self):
        """Test room timer"""
        manager = BreakoutRoomManager(conference_id="conf1")

        # Create room
        rooms = manager.create_rooms(num_rooms=1)
        room = rooms[0]

        # Start timer (very short for testing)
        task = asyncio.create_task(room.start_timer(duration_minutes=0.01))

        # Wait for completion
        await asyncio.sleep(1)

        # Room should be closed
        assert room.status.value == "closed"


class TestChat:
    """Test chat functionality"""

    def test_chat_creation(self):
        """Test creating a chat"""
        chat = Chat(conference_id="conf1")

        assert chat.conference_id == "conf1"
        assert chat.enabled is True

    def test_send_message(self):
        """Test sending messages"""
        chat = Chat(conference_id="conf1")

        # Send public message
        message = chat.send_message(
            sender_id="user1",
            sender_name="John Doe",
            content="Hello, everyone!",
        )

        assert message is not None
        assert message.content == "Hello, everyone!"
        assert message.scope == ChatScope.PUBLIC

    def test_private_message(self):
        """Test private messages"""
        chat = Chat(conference_id="conf1")

        # Send private message
        message = chat.send_message(
            sender_id="user1",
            sender_name="John",
            content="Private message",
            scope=ChatScope.PRIVATE,
            recipient_id="user2",
            recipient_name="Jane",
        )

        assert message.scope == ChatScope.PRIVATE
        assert message.recipient_id == "user2"

    def test_edit_delete_message(self):
        """Test editing and deleting messages"""
        chat = Chat(conference_id="conf1")

        # Send message
        message = chat.send_message(
            sender_id="user1",
            sender_name="John",
            content="Original message",
        )

        # Edit message
        success = chat.edit_message(
            message.id,
            "Edited message",
            "user1",
        )
        assert success is True
        assert message.content == "Edited message"

        # Delete message
        success = chat.delete_message(message.id, "user1")
        assert success is True
        assert message.is_deleted is True


class TestReactions:
    """Test reactions functionality"""

    def test_reaction_manager(self):
        """Test reaction manager"""
        manager = ReactionManager(conference_id="conf1")

        # Send reaction
        reaction = manager.send_reaction(
            participant_id="user1",
            participant_name="John",
            reaction_type=ReactionType.THUMBS_UP,
        )

        assert reaction is not None
        assert len(manager.recent_reactions) == 1

    def test_poll_creation(self):
        """Test creating and running a poll"""
        manager = PollManager(conference_id="conf1")

        # Create poll
        poll = manager.create_poll(
            question="What is your favorite color?",
            options=["Red", "Blue", "Green"],
            created_by="host",
        )

        assert poll is not None
        assert poll.question == "What is your favorite color?"
        assert len(poll.options) == 3

        # Start poll
        assert manager.start_poll(poll.id) is True
        assert poll.status.value == "active"

        # Vote
        assert manager.vote(poll.id, "user1", poll.options[0].id) is True

        # Get results
        results = poll.get_results()
        assert results["total_voters"] == 1

        # End poll
        assert manager.end_poll(poll.id) is True
        assert poll.status.value == "closed"

    def test_qa_manager(self):
        """Test Q&A functionality"""
        manager = QAManager(conference_id="conf1")

        # Enable Q&A
        manager.enable()

        # Ask question
        question = manager.ask_question(
            participant_id="user1",
            participant_name="John",
            question_text="What is the project timeline?",
        )

        assert question is not None
        assert question.status.value == "pending"

        # Upvote question
        assert manager.upvote_question(question.id, "user2") is True
        assert question.get_upvote_count() == 1

        # Answer question
        assert manager.answer_question(
            question.id,
            "The timeline is 6 months",
            "host",
        ) is True

        assert question.status.value == "answered"


@pytest.mark.asyncio
class TestTranscription:
    """Test transcription functionality"""

    def test_transcription_creation(self):
        """Test creating a transcription"""
        transcription = LiveTranscription(
            conference_id="conf1",
            primary_language=TranscriptionLanguage.ENGLISH,
        )

        assert transcription.conference_id == "conf1"
        assert transcription.is_active is False

    def test_transcription_lifecycle(self):
        """Test transcription start/stop"""
        transcription = LiveTranscription(conference_id="conf1")

        # Start
        assert transcription.start() is True
        assert transcription.is_active is True

        # Stop
        assert transcription.stop() is True
        assert transcription.is_active is False

    def test_add_segment(self):
        """Test adding transcript segments"""
        transcription = LiveTranscription(conference_id="conf1")
        transcription.start()

        # Add segment
        segment = transcription.add_segment(
            speaker_id="user1",
            speaker_name="John",
            text="This is a test transcript",
            is_final=True,
        )

        assert segment is not None
        assert len(transcription.segments) == 1

    def test_export_transcript(self):
        """Test exporting transcript"""
        transcription = LiveTranscription(conference_id="conf1")
        transcription.start()

        # Add segments
        transcription.add_segment(
            speaker_id="user1",
            speaker_name="John",
            text="First message",
            is_final=True,
        )

        transcription.add_segment(
            speaker_id="user2",
            speaker_name="Jane",
            text="Second message",
            is_final=True,
        )

        # Export as text
        transcript = transcription.export_transcript(format="txt")
        assert "First message" in transcript
        assert "Second message" in transcript

    async def test_meeting_summarizer(self):
        """Test meeting summarizer"""
        from modules.video.transcription import MeetingSummarizer, TranscriptSegment

        summarizer = MeetingSummarizer()

        # Create transcript segments
        segments = [
            TranscriptSegment(
                speaker_id="user1",
                speaker_name="John",
                text="We need to discuss the project timeline and budget.",
            ),
            TranscriptSegment(
                speaker_id="user2",
                speaker_name="Jane",
                text="I agree, we should also talk about resource allocation.",
            ),
        ]

        # Generate summary
        summary = await summarizer.generate_summary(
            conference_id="conf1",
            transcript_segments=segments,
            participants=["John", "Jane"],
        )

        assert summary is not None
        assert len(summary.key_points) > 0
        assert len(summary.topics_discussed) > 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
