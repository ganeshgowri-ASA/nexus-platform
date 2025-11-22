"""
NEXUS Recording Module - Cloud and Local Recording with Auto-Transcription
Handles video/audio recording, storage, and transcription
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable
from uuid import uuid4
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class RecordingType(Enum):
    """Types of recordings"""
    VIDEO_AUDIO = "video_audio"
    AUDIO_ONLY = "audio_only"
    SCREEN_SHARE = "screen_share"
    GALLERY_VIEW = "gallery_view"
    SPEAKER_VIEW = "speaker_view"


class RecordingQuality(Enum):
    """Recording quality settings"""
    LOW = "360p"
    MEDIUM = "720p"
    HIGH = "1080p"
    ULTRA = "4k"


class RecordingStatus(Enum):
    """Recording status"""
    IDLE = "idle"
    STARTING = "starting"
    RECORDING = "recording"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StorageType(Enum):
    """Storage location types"""
    LOCAL = "local"
    CLOUD = "cloud"
    BOTH = "both"


@dataclass
class RecordingSettings:
    """Settings for a recording"""
    recording_type: RecordingType = RecordingType.VIDEO_AUDIO
    quality: RecordingQuality = RecordingQuality.HIGH
    storage_type: StorageType = StorageType.CLOUD
    auto_start: bool = False
    auto_transcribe: bool = False
    record_chat: bool = True
    record_reactions: bool = True
    record_polls: bool = True
    separate_audio_tracks: bool = False
    local_path: Optional[Path] = None
    cloud_bucket: Optional[str] = None
    max_duration_minutes: int = 480  # 8 hours
    file_format: str = "mp4"
    audio_format: str = "aac"
    video_codec: str = "h264"


@dataclass
class RecordingMetadata:
    """Metadata for a recording"""
    conference_id: str
    conference_title: str
    host_name: str
    participant_count: int
    recording_duration: timedelta = field(default_factory=lambda: timedelta(seconds=0))
    file_size_bytes: int = 0
    chat_messages: int = 0
    polls_count: int = 0
    transcription_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict = field(default_factory=dict)


@dataclass
class RecordingSegment:
    """A segment of a recording (for pause/resume)"""
    segment_id: str = field(default_factory=lambda: str(uuid4()))
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration: timedelta = field(default_factory=lambda: timedelta(seconds=0))
    file_path: Optional[Path] = None
    file_size: int = 0

    def complete(self) -> None:
        """Mark segment as complete"""
        self.end_time = datetime.now()
        self.duration = self.end_time - self.start_time


class Recording:
    """
    Represents a single recording session
    Handles recording lifecycle and metadata
    """

    def __init__(
        self,
        conference_id: str,
        conference_title: str,
        settings: Optional[RecordingSettings] = None,
    ):
        self.id = str(uuid4())
        self.conference_id = conference_id
        self.conference_title = conference_title
        self.settings = settings or RecordingSettings()

        # Recording state
        self.status = RecordingStatus.IDLE
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        self.paused_at: Optional[datetime] = None

        # Recording segments
        self.segments: List[RecordingSegment] = []
        self.current_segment: Optional[RecordingSegment] = None

        # File information
        self.local_file_path: Optional[Path] = None
        self.cloud_url: Optional[str] = None
        self.file_size_bytes: int = 0

        # Metadata
        self.metadata: Optional[RecordingMetadata] = None

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "recording_started": [],
            "recording_stopped": [],
            "recording_paused": [],
            "recording_resumed": [],
            "processing_started": [],
            "processing_completed": [],
            "upload_started": [],
            "upload_completed": [],
            "error": [],
        }

        logger.info(f"Recording created: {self.id}")

    async def start(self) -> bool:
        """Start the recording"""
        if self.status == RecordingStatus.RECORDING:
            logger.warning(f"Recording {self.id} already started")
            return False

        self.status = RecordingStatus.STARTING
        self.started_at = datetime.now()

        # Create new segment
        self.current_segment = RecordingSegment()
        self.segments.append(self.current_segment)

        # Simulate recording start
        await asyncio.sleep(0.1)

        self.status = RecordingStatus.RECORDING
        self._trigger_event("recording_started", {"recording_id": self.id})

        logger.info(f"Recording started: {self.id}")
        return True

    async def stop(self) -> bool:
        """Stop the recording"""
        if self.status != RecordingStatus.RECORDING:
            logger.warning(f"Recording {self.id} not in recording state")
            return False

        self.status = RecordingStatus.STOPPING
        self.stopped_at = datetime.now()

        # Complete current segment
        if self.current_segment:
            self.current_segment.complete()
            self.current_segment = None

        # Simulate recording stop
        await asyncio.sleep(0.1)

        self.status = RecordingStatus.STOPPED
        self._trigger_event("recording_stopped", {"recording_id": self.id})

        # Start processing
        await self._process_recording()

        logger.info(f"Recording stopped: {self.id}")
        return True

    async def pause(self) -> bool:
        """Pause the recording"""
        if self.status != RecordingStatus.RECORDING:
            logger.warning(f"Recording {self.id} not in recording state")
            return False

        self.status = RecordingStatus.PAUSED
        self.paused_at = datetime.now()

        # Complete current segment
        if self.current_segment:
            self.current_segment.complete()
            self.current_segment = None

        self._trigger_event("recording_paused", {"recording_id": self.id})

        logger.info(f"Recording paused: {self.id}")
        return True

    async def resume(self) -> bool:
        """Resume the recording"""
        if self.status != RecordingStatus.PAUSED:
            logger.warning(f"Recording {self.id} not in paused state")
            return False

        # Create new segment
        self.current_segment = RecordingSegment()
        self.segments.append(self.current_segment)

        self.status = RecordingStatus.RECORDING
        self.paused_at = None
        self._trigger_event("recording_resumed", {"recording_id": self.id})

        logger.info(f"Recording resumed: {self.id}")
        return True

    async def _process_recording(self) -> None:
        """Process the recording (merge segments, encode, etc.)"""
        self.status = RecordingStatus.PROCESSING
        self._trigger_event("processing_started", {"recording_id": self.id})

        logger.info(f"Processing recording: {self.id}")

        # Simulate processing
        await asyncio.sleep(1.0)

        # Calculate total duration and size
        total_duration = sum(
            (seg.duration for seg in self.segments),
            timedelta()
        )

        # Simulate file creation
        if self.settings.storage_type in [StorageType.LOCAL, StorageType.BOTH]:
            self.local_file_path = self._generate_local_path()
            self.file_size_bytes = int(total_duration.total_seconds() * 1024 * 1024)  # ~1MB per second

        # Upload to cloud if needed
        if self.settings.storage_type in [StorageType.CLOUD, StorageType.BOTH]:
            await self._upload_to_cloud()

        self.status = RecordingStatus.COMPLETED
        self._trigger_event("processing_completed", {
            "recording_id": self.id,
            "duration": total_duration.total_seconds(),
            "file_size": self.file_size_bytes,
        })

        logger.info(f"Recording processing completed: {self.id}")

    async def _upload_to_cloud(self) -> None:
        """Upload recording to cloud storage"""
        self._trigger_event("upload_started", {"recording_id": self.id})

        logger.info(f"Uploading recording to cloud: {self.id}")

        # Simulate upload
        await asyncio.sleep(0.5)

        # Generate cloud URL
        bucket = self.settings.cloud_bucket or "nexus-recordings"
        self.cloud_url = f"https://{bucket}.s3.amazonaws.com/recordings/{self.id}.{self.settings.file_format}"

        self._trigger_event("upload_completed", {
            "recording_id": self.id,
            "cloud_url": self.cloud_url,
        })

        logger.info(f"Recording uploaded to cloud: {self.cloud_url}")

    def _generate_local_path(self) -> Path:
        """Generate local file path"""
        base_path = self.settings.local_path or Path.home() / "NEXUS" / "Recordings"
        base_path.mkdir(parents=True, exist_ok=True)

        filename = f"{self.conference_title}_{self.created_at.strftime('%Y%m%d_%H%M%S')}.{self.settings.file_format}"
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")

        return base_path / filename

    def get_duration(self) -> timedelta:
        """Get total recording duration"""
        return sum(
            (seg.duration for seg in self.segments),
            timedelta()
        )

    def get_info(self) -> Dict:
        """Get recording information"""
        return {
            "id": self.id,
            "conference_id": self.conference_id,
            "conference_title": self.conference_title,
            "status": self.status.value,
            "duration_seconds": self.get_duration().total_seconds(),
            "file_size_bytes": self.file_size_bytes,
            "local_path": str(self.local_file_path) if self.local_file_path else None,
            "cloud_url": self.cloud_url,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "segments": len(self.segments),
        }

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


class RecordingManager:
    """
    Manages multiple recordings
    Handles recording lifecycle, storage, and retrieval
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / "NEXUS" / "Recordings"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.recordings: Dict[str, Recording] = {}
        self.active_recordings: Dict[str, Recording] = {}  # conference_id -> recording

        logger.info("RecordingManager initialized")

    def create_recording(
        self,
        conference_id: str,
        conference_title: str,
        settings: Optional[RecordingSettings] = None,
    ) -> Recording:
        """Create a new recording"""
        recording = Recording(
            conference_id=conference_id,
            conference_title=conference_title,
            settings=settings,
        )

        self.recordings[recording.id] = recording

        logger.info(f"Recording created: {recording.id}")
        return recording

    async def start_recording(
        self,
        conference_id: str,
        conference_title: str,
        settings: Optional[RecordingSettings] = None,
    ) -> Optional[Recording]:
        """Start a new recording for a conference"""
        # Check if already recording
        if conference_id in self.active_recordings:
            logger.warning(f"Conference {conference_id} already being recorded")
            return None

        # Create and start recording
        recording = self.create_recording(conference_id, conference_title, settings)
        await recording.start()

        self.active_recordings[conference_id] = recording

        logger.info(f"Recording started for conference: {conference_id}")
        return recording

    async def stop_recording(self, conference_id: str) -> bool:
        """Stop recording for a conference"""
        if conference_id not in self.active_recordings:
            logger.warning(f"No active recording for conference: {conference_id}")
            return False

        recording = self.active_recordings[conference_id]
        await recording.stop()

        del self.active_recordings[conference_id]

        logger.info(f"Recording stopped for conference: {conference_id}")
        return True

    async def pause_recording(self, conference_id: str) -> bool:
        """Pause recording for a conference"""
        if conference_id not in self.active_recordings:
            return False

        recording = self.active_recordings[conference_id]
        return await recording.pause()

    async def resume_recording(self, conference_id: str) -> bool:
        """Resume recording for a conference"""
        if conference_id not in self.active_recordings:
            return False

        recording = self.active_recordings[conference_id]
        return await recording.resume()

    def get_recording(self, recording_id: str) -> Optional[Recording]:
        """Get a recording by ID"""
        return self.recordings.get(recording_id)

    def get_conference_recordings(self, conference_id: str) -> List[Recording]:
        """Get all recordings for a conference"""
        return [
            r for r in self.recordings.values()
            if r.conference_id == conference_id
        ]

    def get_all_recordings(self) -> List[Recording]:
        """Get all recordings"""
        return list(self.recordings.values())

    def get_active_recordings(self) -> List[Recording]:
        """Get all active recordings"""
        return list(self.active_recordings.values())

    def delete_recording(self, recording_id: str) -> bool:
        """Delete a recording"""
        if recording_id not in self.recordings:
            return False

        recording = self.recordings[recording_id]

        # Delete local file if exists
        if recording.local_file_path and recording.local_file_path.exists():
            try:
                recording.local_file_path.unlink()
                logger.info(f"Deleted local file: {recording.local_file_path}")
            except Exception as e:
                logger.error(f"Error deleting local file: {e}")

        del self.recordings[recording_id]

        logger.info(f"Recording deleted: {recording_id}")
        return True

    def get_storage_usage(self) -> Dict:
        """Get storage usage statistics"""
        total_size = sum(r.file_size_bytes for r in self.recordings.values())
        total_duration = sum(
            (r.get_duration() for r in self.recordings.values()),
            timedelta()
        )

        return {
            "total_recordings": len(self.recordings),
            "active_recordings": len(self.active_recordings),
            "total_size_bytes": total_size,
            "total_size_gb": total_size / (1024 ** 3),
            "total_duration_seconds": total_duration.total_seconds(),
            "total_duration_hours": total_duration.total_seconds() / 3600,
            "storage_path": str(self.storage_path),
        }

    async def cleanup_old_recordings(self, days: int = 30) -> int:
        """Delete recordings older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for recording_id, recording in list(self.recordings.items()):
            if recording.created_at < cutoff_date:
                if self.delete_recording(recording_id):
                    deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} recordings older than {days} days")
        return deleted_count

    def export_recordings_list(self) -> str:
        """Export list of all recordings as JSON"""
        recordings_data = [r.get_info() for r in self.recordings.values()]
        return json.dumps(recordings_data, indent=2)
