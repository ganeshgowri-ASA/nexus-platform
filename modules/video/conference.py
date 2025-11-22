"""
NEXUS Video Conference Module - Core Conference Management
Supports 100+ participants, HD video (1080p), gallery/speaker view, virtual backgrounds
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Callable
from uuid import uuid4
import asyncio
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ParticipantRole(Enum):
    """Participant roles in a conference"""
    HOST = "host"
    CO_HOST = "co_host"
    PANELIST = "panelist"  # For webinar mode
    ATTENDEE = "attendee"  # For webinar mode
    PARTICIPANT = "participant"  # Regular meetings


class VideoQuality(Enum):
    """Video quality settings"""
    SD_360P = "360p"
    SD_480P = "480p"
    HD_720P = "720p"
    HD_1080P = "1080p"
    AUTO = "auto"


class ViewMode(Enum):
    """Conference view modes"""
    GALLERY = "gallery"
    SPEAKER = "speaker"
    SPOTLIGHT = "spotlight"
    SIDEBAR = "sidebar"


class ConferenceMode(Enum):
    """Conference mode types"""
    MEETING = "meeting"  # Regular meeting (up to 100)
    WEBINAR = "webinar"  # Webinar (up to 10,000 viewers)
    BROADCAST = "broadcast"  # One-way broadcast


@dataclass
class MediaSettings:
    """Media settings for a participant"""
    video_enabled: bool = True
    audio_enabled: bool = True
    screen_sharing: bool = False
    video_quality: VideoQuality = VideoQuality.HD_1080P
    virtual_background: Optional[str] = None
    video_filter: Optional[str] = None
    noise_cancellation: bool = True
    echo_reduction: bool = True
    audio_only_mode: bool = False


@dataclass
class Participant:
    """Represents a participant in a video conference"""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    email: str = ""
    role: ParticipantRole = ParticipantRole.PARTICIPANT
    media_settings: MediaSettings = field(default_factory=MediaSettings)
    joined_at: datetime = field(default_factory=datetime.now)
    is_muted: bool = False
    is_video_off: bool = False
    is_hand_raised: bool = False
    in_waiting_room: bool = False
    is_speaking: bool = False
    audio_level: float = 0.0
    connection_quality: str = "good"  # poor, fair, good, excellent
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert participant to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "is_muted": self.is_muted,
            "is_video_off": self.is_video_off,
            "is_hand_raised": self.is_hand_raised,
            "is_speaking": self.is_speaking,
            "audio_level": self.audio_level,
            "connection_quality": self.connection_quality,
            "joined_at": self.joined_at.isoformat(),
        }


@dataclass
class SecuritySettings:
    """Security settings for a conference"""
    password: Optional[str] = None
    waiting_room_enabled: bool = False
    lock_meeting: bool = False
    allow_screen_sharing: bool = True
    allow_recording: bool = True
    allow_chat: bool = True
    require_authentication: bool = False
    encryption_enabled: bool = True
    watermark_enabled: bool = False


@dataclass
class ConferenceSettings:
    """Settings for a video conference"""
    mode: ConferenceMode = ConferenceMode.MEETING
    max_participants: int = 100
    enable_waiting_room: bool = False
    enable_recording: bool = True
    enable_transcription: bool = False
    enable_chat: bool = True
    enable_reactions: bool = True
    enable_breakout_rooms: bool = False
    enable_polls: bool = True
    enable_qa: bool = False
    enable_whiteboard: bool = True
    auto_recording: bool = False
    auto_transcription: bool = False
    default_view_mode: ViewMode = ViewMode.GALLERY
    security: SecuritySettings = field(default_factory=SecuritySettings)


class Conference:
    """
    Core video conference manager
    Handles participant management, security, and conference lifecycle
    """

    def __init__(
        self,
        conference_id: Optional[str] = None,
        title: str = "NEXUS Conference",
        settings: Optional[ConferenceSettings] = None,
    ):
        self.id = conference_id or str(uuid4())
        self.title = title
        self.settings = settings or ConferenceSettings()
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None

        # Participant management
        self.participants: Dict[str, Participant] = {}
        self.waiting_room: Set[str] = set()
        self.kicked_participants: Set[str] = set()

        # Conference state
        self.is_active = False
        self.is_locked = False
        self.is_recording = False

        # Event callbacks
        self.event_handlers: Dict[str, List[Callable]] = {
            "participant_joined": [],
            "participant_left": [],
            "participant_muted": [],
            "participant_unmuted": [],
            "recording_started": [],
            "recording_stopped": [],
            "conference_started": [],
            "conference_ended": [],
            "hand_raised": [],
            "chat_message": [],
        }

        logger.info(f"Conference created: {self.id} - {self.title}")

    def start(self) -> bool:
        """Start the conference"""
        if self.is_active:
            logger.warning(f"Conference {self.id} already active")
            return False

        self.is_active = True
        self.started_at = datetime.now()
        self._trigger_event("conference_started", {"conference_id": self.id})
        logger.info(f"Conference started: {self.id}")
        return True

    def end(self) -> bool:
        """End the conference"""
        if not self.is_active:
            logger.warning(f"Conference {self.id} not active")
            return False

        self.is_active = False
        self.ended_at = datetime.now()

        # Remove all participants
        for participant_id in list(self.participants.keys()):
            self.remove_participant(participant_id)

        self._trigger_event("conference_ended", {"conference_id": self.id})
        logger.info(f"Conference ended: {self.id}")
        return True

    def add_participant(
        self,
        name: str,
        email: str = "",
        role: ParticipantRole = ParticipantRole.PARTICIPANT,
        bypass_waiting_room: bool = False,
    ) -> Optional[Participant]:
        """Add a participant to the conference"""

        # Check if conference is locked
        if self.is_locked and role == ParticipantRole.PARTICIPANT:
            logger.warning(f"Conference {self.id} is locked")
            return None

        # Check max participants
        if len(self.participants) >= self.settings.max_participants:
            logger.warning(f"Conference {self.id} at max capacity")
            return None

        # Check password if required
        if self.settings.security.password and not bypass_waiting_room:
            # Password check would be done before calling this method
            pass

        participant = Participant(
            name=name,
            email=email,
            role=role,
        )

        # Handle waiting room
        if self.settings.security.waiting_room_enabled and not bypass_waiting_room:
            if role == ParticipantRole.PARTICIPANT:
                participant.in_waiting_room = True
                self.waiting_room.add(participant.id)
                logger.info(f"Participant {participant.id} added to waiting room")
                return participant

        self.participants[participant.id] = participant
        self._trigger_event("participant_joined", participant.to_dict())
        logger.info(f"Participant joined: {participant.id} - {participant.name}")
        return participant

    def admit_from_waiting_room(self, participant_id: str) -> bool:
        """Admit a participant from the waiting room"""
        if participant_id not in self.waiting_room:
            return False

        self.waiting_room.remove(participant_id)

        # Find participant and update status
        for p in self.participants.values():
            if p.id == participant_id:
                p.in_waiting_room = False
                self._trigger_event("participant_joined", p.to_dict())
                logger.info(f"Participant admitted: {participant_id}")
                return True

        return False

    def remove_participant(self, participant_id: str, kick: bool = False) -> bool:
        """Remove a participant from the conference"""
        if participant_id not in self.participants:
            return False

        participant = self.participants.pop(participant_id)

        if kick:
            self.kicked_participants.add(participant_id)

        self._trigger_event("participant_left", participant.to_dict())
        logger.info(f"Participant left: {participant_id} - {participant.name}")
        return True

    def mute_participant(self, participant_id: str) -> bool:
        """Mute a participant"""
        if participant_id not in self.participants:
            return False

        participant = self.participants[participant_id]
        participant.is_muted = True
        participant.media_settings.audio_enabled = False

        self._trigger_event("participant_muted", participant.to_dict())
        logger.info(f"Participant muted: {participant_id}")
        return True

    def unmute_participant(self, participant_id: str) -> bool:
        """Unmute a participant"""
        if participant_id not in self.participants:
            return False

        participant = self.participants[participant_id]
        participant.is_muted = False
        participant.media_settings.audio_enabled = True

        self._trigger_event("participant_unmuted", participant.to_dict())
        logger.info(f"Participant unmuted: {participant_id}")
        return True

    def mute_all(self, except_hosts: bool = True) -> int:
        """Mute all participants"""
        count = 0
        for participant in self.participants.values():
            if except_hosts and participant.role in [ParticipantRole.HOST, ParticipantRole.CO_HOST]:
                continue
            if self.mute_participant(participant.id):
                count += 1

        logger.info(f"Muted {count} participants")
        return count

    def toggle_video(self, participant_id: str, enabled: bool) -> bool:
        """Toggle video for a participant"""
        if participant_id not in self.participants:
            return False

        participant = self.participants[participant_id]
        participant.is_video_off = not enabled
        participant.media_settings.video_enabled = enabled

        logger.info(f"Participant video toggled: {participant_id} - {enabled}")
        return True

    def raise_hand(self, participant_id: str) -> bool:
        """Raise hand for a participant"""
        if participant_id not in self.participants:
            return False

        participant = self.participants[participant_id]
        participant.is_hand_raised = True

        self._trigger_event("hand_raised", participant.to_dict())
        logger.info(f"Hand raised: {participant_id}")
        return True

    def lower_hand(self, participant_id: str) -> bool:
        """Lower hand for a participant"""
        if participant_id not in self.participants:
            return False

        participant = self.participants[participant_id]
        participant.is_hand_raised = False

        logger.info(f"Hand lowered: {participant_id}")
        return True

    def lower_all_hands(self) -> int:
        """Lower all raised hands"""
        count = 0
        for participant in self.participants.values():
            if participant.is_hand_raised:
                self.lower_hand(participant.id)
                count += 1

        logger.info(f"Lowered {count} hands")
        return count

    def lock_conference(self) -> bool:
        """Lock the conference to prevent new participants"""
        self.is_locked = True
        logger.info(f"Conference locked: {self.id}")
        return True

    def unlock_conference(self) -> bool:
        """Unlock the conference"""
        self.is_locked = False
        logger.info(f"Conference unlocked: {self.id}")
        return True

    def update_participant_role(
        self,
        participant_id: str,
        new_role: ParticipantRole
    ) -> bool:
        """Update a participant's role"""
        if participant_id not in self.participants:
            return False

        participant = self.participants[participant_id]
        old_role = participant.role
        participant.role = new_role

        logger.info(f"Participant role updated: {participant_id} - {old_role} -> {new_role}")
        return True

    def get_participant_count(self) -> int:
        """Get the number of active participants"""
        return len(self.participants)

    def get_participants_by_role(self, role: ParticipantRole) -> List[Participant]:
        """Get all participants with a specific role"""
        return [p for p in self.participants.values() if p.role == role]

    def get_speaking_participants(self) -> List[Participant]:
        """Get all currently speaking participants"""
        return [p for p in self.participants.values() if p.is_speaking]

    def get_raised_hands(self) -> List[Participant]:
        """Get all participants with raised hands"""
        return [p for p in self.participants.values() if p.is_hand_raised]

    def on_event(self, event_name: str, callback: Callable) -> None:
        """Register an event handler"""
        if event_name in self.event_handlers:
            self.event_handlers[event_name].append(callback)

    def _trigger_event(self, event_name: str, data: Dict) -> None:
        """Trigger an event"""
        if event_name in self.event_handlers:
            for callback in self.event_handlers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler {event_name}: {e}")

    def get_conference_stats(self) -> Dict:
        """Get conference statistics"""
        return {
            "id": self.id,
            "title": self.title,
            "is_active": self.is_active,
            "is_locked": self.is_locked,
            "is_recording": self.is_recording,
            "participant_count": len(self.participants),
            "waiting_room_count": len(self.waiting_room),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "duration_seconds": (datetime.now() - self.started_at).total_seconds()
                if self.started_at else 0,
            "participants": [p.to_dict() for p in self.participants.values()],
        }

    def export_conference_data(self) -> str:
        """Export conference data as JSON"""
        return json.dumps(self.get_conference_stats(), indent=2)


class ConferenceManager:
    """
    Manages multiple conferences
    """

    def __init__(self):
        self.conferences: Dict[str, Conference] = {}
        self.scheduled_conferences: Dict[str, Dict] = {}
        logger.info("ConferenceManager initialized")

    def create_conference(
        self,
        title: str,
        settings: Optional[ConferenceSettings] = None,
    ) -> Conference:
        """Create a new conference"""
        conference = Conference(title=title, settings=settings)
        self.conferences[conference.id] = conference
        logger.info(f"Conference created: {conference.id}")
        return conference

    def get_conference(self, conference_id: str) -> Optional[Conference]:
        """Get a conference by ID"""
        return self.conferences.get(conference_id)

    def delete_conference(self, conference_id: str) -> bool:
        """Delete a conference"""
        if conference_id not in self.conferences:
            return False

        conference = self.conferences[conference_id]
        if conference.is_active:
            conference.end()

        del self.conferences[conference_id]
        logger.info(f"Conference deleted: {conference_id}")
        return True

    def get_active_conferences(self) -> List[Conference]:
        """Get all active conferences"""
        return [c for c in self.conferences.values() if c.is_active]

    def get_all_conferences(self) -> List[Conference]:
        """Get all conferences"""
        return list(self.conferences.values())

    def schedule_conference(
        self,
        title: str,
        scheduled_time: datetime,
        duration_minutes: int,
        settings: Optional[ConferenceSettings] = None,
    ) -> str:
        """Schedule a future conference"""
        conference_id = str(uuid4())
        self.scheduled_conferences[conference_id] = {
            "id": conference_id,
            "title": title,
            "scheduled_time": scheduled_time,
            "duration_minutes": duration_minutes,
            "settings": settings or ConferenceSettings(),
        }
        logger.info(f"Conference scheduled: {conference_id} at {scheduled_time}")
        return conference_id

    def get_scheduled_conferences(self) -> List[Dict]:
        """Get all scheduled conferences"""
        return list(self.scheduled_conferences.values())
