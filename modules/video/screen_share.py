"""
NEXUS Screen Share Module - Screen Sharing with Annotation Tools
Supports full screen, application window, and annotation capabilities
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Tuple
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ScreenShareType(Enum):
    """Types of screen sharing"""
    FULL_SCREEN = "full_screen"
    WINDOW = "window"
    TAB = "tab"
    REGION = "region"


class AnnotationType(Enum):
    """Types of annotations"""
    ARROW = "arrow"
    LINE = "line"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    TEXT = "text"
    HIGHLIGHT = "highlight"
    PEN = "pen"
    ERASER = "eraser"
    POINTER = "pointer"


class ScreenShareQuality(Enum):
    """Screen share quality settings"""
    LOW = "low"  # 720p, 5fps
    MEDIUM = "medium"  # 1080p, 15fps
    HIGH = "high"  # 1080p, 30fps
    ULTRA = "ultra"  # 4K, 30fps


@dataclass
class ScreenShareSettings:
    """Settings for screen sharing"""
    share_type: ScreenShareType = ScreenShareType.FULL_SCREEN
    quality: ScreenShareQuality = ScreenShareQuality.HIGH
    share_audio: bool = True
    share_system_audio: bool = False
    optimize_for_video: bool = False
    optimize_for_text: bool = True
    frame_rate: int = 30
    resolution_width: int = 1920
    resolution_height: int = 1080
    enable_annotations: bool = True
    enable_cursor: bool = True


@dataclass
class Annotation:
    """Represents an annotation on screen share"""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: AnnotationType = AnnotationType.PEN
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    color: str = "#FF0000"
    thickness: int = 3
    points: List[Tuple[int, int]] = field(default_factory=list)
    text: str = ""
    position: Tuple[int, int] = (0, 0)
    size: Tuple[int, int] = (100, 100)
    opacity: float = 1.0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "color": self.color,
            "thickness": self.thickness,
            "points": self.points,
            "text": self.text,
            "position": self.position,
            "size": self.size,
            "opacity": self.opacity,
        }


class AnnotationTool:
    """
    Annotation tool for screen sharing
    Allows drawing and annotating on shared screens
    """

    def __init__(self):
        self.annotations: Dict[str, Annotation] = {}
        self.active_tool: AnnotationType = AnnotationType.PEN
        self.color: str = "#FF0000"
        self.thickness: int = 3
        self.undo_stack: List[str] = []
        self.redo_stack: List[str] = []

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "annotation_added": [],
            "annotation_removed": [],
            "annotation_updated": [],
            "annotations_cleared": [],
        }

        logger.info("AnnotationTool initialized")

    def set_active_tool(self, tool: AnnotationType) -> None:
        """Set the active annotation tool"""
        self.active_tool = tool
        logger.debug(f"Active tool set to: {tool.value}")

    def set_color(self, color: str) -> None:
        """Set annotation color"""
        self.color = color

    def set_thickness(self, thickness: int) -> None:
        """Set annotation thickness"""
        self.thickness = thickness

    def add_annotation(
        self,
        user_id: str,
        annotation_type: Optional[AnnotationType] = None,
        **kwargs
    ) -> Annotation:
        """Add a new annotation"""
        tool = annotation_type or self.active_tool

        annotation = Annotation(
            type=tool,
            created_by=user_id,
            color=kwargs.get("color", self.color),
            thickness=kwargs.get("thickness", self.thickness),
            points=kwargs.get("points", []),
            text=kwargs.get("text", ""),
            position=kwargs.get("position", (0, 0)),
            size=kwargs.get("size", (100, 100)),
        )

        self.annotations[annotation.id] = annotation
        self.undo_stack.append(annotation.id)
        self.redo_stack.clear()

        self._trigger_event("annotation_added", annotation.to_dict())

        logger.debug(f"Annotation added: {annotation.id}")
        return annotation

    def update_annotation(
        self,
        annotation_id: str,
        **kwargs
    ) -> bool:
        """Update an existing annotation"""
        if annotation_id not in self.annotations:
            return False

        annotation = self.annotations[annotation_id]

        if "points" in kwargs:
            annotation.points = kwargs["points"]
        if "text" in kwargs:
            annotation.text = kwargs["text"]
        if "position" in kwargs:
            annotation.position = kwargs["position"]
        if "size" in kwargs:
            annotation.size = kwargs["size"]
        if "color" in kwargs:
            annotation.color = kwargs["color"]
        if "thickness" in kwargs:
            annotation.thickness = kwargs["thickness"]

        self._trigger_event("annotation_updated", annotation.to_dict())

        logger.debug(f"Annotation updated: {annotation_id}")
        return True

    def remove_annotation(self, annotation_id: str) -> bool:
        """Remove an annotation"""
        if annotation_id not in self.annotations:
            return False

        annotation = self.annotations.pop(annotation_id)
        self._trigger_event("annotation_removed", {"id": annotation_id})

        logger.debug(f"Annotation removed: {annotation_id}")
        return True

    def clear_annotations(self) -> int:
        """Clear all annotations"""
        count = len(self.annotations)
        self.annotations.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

        self._trigger_event("annotations_cleared", {"count": count})

        logger.info(f"Cleared {count} annotations")
        return count

    def undo(self) -> bool:
        """Undo last annotation"""
        if not self.undo_stack:
            return False

        annotation_id = self.undo_stack.pop()
        if annotation_id in self.annotations:
            self.redo_stack.append(annotation_id)
            return self.remove_annotation(annotation_id)

        return False

    def redo(self) -> bool:
        """Redo last undone annotation"""
        if not self.redo_stack:
            return False

        # In a full implementation, would restore the annotation
        annotation_id = self.redo_stack.pop()
        self.undo_stack.append(annotation_id)

        return True

    def get_annotations(self) -> List[Annotation]:
        """Get all annotations"""
        return list(self.annotations.values())

    def get_user_annotations(self, user_id: str) -> List[Annotation]:
        """Get annotations by a specific user"""
        return [a for a in self.annotations.values() if a.created_by == user_id]

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


class ScreenShare:
    """
    Represents an active screen share session
    """

    def __init__(
        self,
        participant_id: str,
        participant_name: str,
        settings: Optional[ScreenShareSettings] = None,
    ):
        self.id = str(uuid4())
        self.participant_id = participant_id
        self.participant_name = participant_name
        self.settings = settings or ScreenShareSettings()

        self.started_at = datetime.now()
        self.stopped_at: Optional[datetime] = None
        self.is_active = False
        self.is_paused = False

        # Annotation tool
        self.annotation_tool = AnnotationTool() if settings and settings.enable_annotations else None

        # Viewers
        self.viewers: Set[str] = set()

        # Statistics
        self.frame_count = 0
        self.bytes_sent = 0

        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            "started": [],
            "stopped": [],
            "paused": [],
            "resumed": [],
            "viewer_joined": [],
            "viewer_left": [],
        }

        logger.info(f"ScreenShare created: {self.id} by {participant_name}")

    def start(self) -> bool:
        """Start screen sharing"""
        if self.is_active:
            logger.warning(f"ScreenShare {self.id} already active")
            return False

        self.is_active = True
        self.started_at = datetime.now()

        self._trigger_event("started", {
            "screen_share_id": self.id,
            "participant_id": self.participant_id,
        })

        logger.info(f"ScreenShare started: {self.id}")
        return True

    def stop(self) -> bool:
        """Stop screen sharing"""
        if not self.is_active:
            logger.warning(f"ScreenShare {self.id} not active")
            return False

        self.is_active = False
        self.stopped_at = datetime.now()

        # Clear viewers
        self.viewers.clear()

        self._trigger_event("stopped", {
            "screen_share_id": self.id,
            "participant_id": self.participant_id,
        })

        logger.info(f"ScreenShare stopped: {self.id}")
        return True

    def pause(self) -> bool:
        """Pause screen sharing"""
        if not self.is_active or self.is_paused:
            return False

        self.is_paused = True
        self._trigger_event("paused", {"screen_share_id": self.id})

        logger.info(f"ScreenShare paused: {self.id}")
        return True

    def resume(self) -> bool:
        """Resume screen sharing"""
        if not self.is_active or not self.is_paused:
            return False

        self.is_paused = False
        self._trigger_event("resumed", {"screen_share_id": self.id}")

        logger.info(f"ScreenShare resumed: {self.id}")
        return True

    def add_viewer(self, viewer_id: str) -> bool:
        """Add a viewer to the screen share"""
        if viewer_id in self.viewers:
            return False

        self.viewers.add(viewer_id)
        self._trigger_event("viewer_joined", {
            "screen_share_id": self.id,
            "viewer_id": viewer_id,
        })

        logger.debug(f"Viewer added to ScreenShare {self.id}: {viewer_id}")
        return True

    def remove_viewer(self, viewer_id: str) -> bool:
        """Remove a viewer from the screen share"""
        if viewer_id not in self.viewers:
            return False

        self.viewers.remove(viewer_id)
        self._trigger_event("viewer_left", {
            "screen_share_id": self.id,
            "viewer_id": viewer_id,
        })

        logger.debug(f"Viewer removed from ScreenShare {self.id}: {viewer_id}")
        return True

    def get_info(self) -> Dict:
        """Get screen share information"""
        duration = (
            (self.stopped_at or datetime.now()) - self.started_at
        ).total_seconds()

        return {
            "id": self.id,
            "participant_id": self.participant_id,
            "participant_name": self.participant_name,
            "is_active": self.is_active,
            "is_paused": self.is_paused,
            "viewer_count": len(self.viewers),
            "duration_seconds": duration,
            "frame_count": self.frame_count,
            "bytes_sent": self.bytes_sent,
            "started_at": self.started_at.isoformat(),
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
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


class ScreenShareManager:
    """
    Manages screen sharing in a conference
    """

    def __init__(self, conference_id: str):
        self.conference_id = conference_id
        self.active_shares: Dict[str, ScreenShare] = {}  # participant_id -> ScreenShare
        self.share_history: List[ScreenShare] = []
        self.max_simultaneous_shares = 1  # Only one person can share at a time by default

        logger.info(f"ScreenShareManager initialized for conference: {conference_id}")

    def start_screen_share(
        self,
        participant_id: str,
        participant_name: str,
        settings: Optional[ScreenShareSettings] = None,
    ) -> Optional[ScreenShare]:
        """Start screen sharing for a participant"""

        # Check if participant is already sharing
        if participant_id in self.active_shares:
            logger.warning(f"Participant {participant_id} already sharing screen")
            return None

        # Check simultaneous shares limit
        if len(self.active_shares) >= self.max_simultaneous_shares:
            logger.warning(f"Max simultaneous shares ({self.max_simultaneous_shares}) reached")
            return None

        # Create and start screen share
        screen_share = ScreenShare(participant_id, participant_name, settings)
        screen_share.start()

        self.active_shares[participant_id] = screen_share
        self.share_history.append(screen_share)

        logger.info(f"Screen share started for participant: {participant_id}")
        return screen_share

    def stop_screen_share(self, participant_id: str) -> bool:
        """Stop screen sharing for a participant"""
        if participant_id not in self.active_shares:
            logger.warning(f"No active screen share for participant: {participant_id}")
            return False

        screen_share = self.active_shares[participant_id]
        screen_share.stop()

        del self.active_shares[participant_id]

        logger.info(f"Screen share stopped for participant: {participant_id}")
        return True

    def get_active_share(self, participant_id: str) -> Optional[ScreenShare]:
        """Get active screen share for a participant"""
        return self.active_shares.get(participant_id)

    def get_all_active_shares(self) -> List[ScreenShare]:
        """Get all active screen shares"""
        return list(self.active_shares.values())

    def is_sharing(self, participant_id: str) -> bool:
        """Check if a participant is sharing"""
        return participant_id in self.active_shares

    def set_max_simultaneous_shares(self, max_shares: int) -> None:
        """Set maximum simultaneous screen shares"""
        self.max_simultaneous_shares = max_shares
        logger.info(f"Max simultaneous shares set to: {max_shares}")

    def get_stats(self) -> Dict:
        """Get screen sharing statistics"""
        return {
            "conference_id": self.conference_id,
            "active_shares": len(self.active_shares),
            "total_shares": len(self.share_history),
            "max_simultaneous_shares": self.max_simultaneous_shares,
            "shares": [share.get_info() for share in self.active_shares.values()],
        }
