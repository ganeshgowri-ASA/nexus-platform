"""
Presenter View - Presentation Mode

Handles presentation mode with presenter view features including notes,
timer, next slide preview, and presentation controls.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time


class PresentationState(Enum):
    """Presentation states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ENDED = "ended"


class PointerTool(Enum):
    """Presenter pointer tools."""
    NONE = "none"
    LASER = "laser"
    PEN = "pen"
    HIGHLIGHTER = "highlighter"
    ERASER = "eraser"


@dataclass
class PresentationSettings:
    """Presentation mode settings."""
    show_timer: bool = True
    show_notes: bool = True
    show_next_slide: bool = True
    auto_advance: bool = False
    auto_advance_delay: float = 5.0  # seconds
    loop_presentation: bool = False
    show_slide_numbers: bool = True
    pointer_tool: PointerTool = PointerTool.NONE
    pointer_color: str = "#FF0000"
    fullscreen: bool = True
    show_controls: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "show_timer": self.show_timer,
            "show_notes": self.show_notes,
            "show_next_slide": self.show_next_slide,
            "auto_advance": self.auto_advance,
            "auto_advance_delay": self.auto_advance_delay,
            "loop_presentation": self.loop_presentation,
            "show_slide_numbers": self.show_slide_numbers,
            "pointer_tool": self.pointer_tool.value,
            "pointer_color": self.pointer_color,
            "fullscreen": self.fullscreen,
            "show_controls": self.show_controls,
        }


@dataclass
class PresentationTimer:
    """Presentation timer."""
    start_time: Optional[datetime] = None
    pause_time: Optional[datetime] = None
    total_paused: timedelta = field(default_factory=lambda: timedelta())
    target_duration: Optional[timedelta] = None

    def start(self) -> None:
        """Start the timer."""
        if not self.start_time:
            self.start_time = datetime.now()
        elif self.pause_time:
            # Resume from pause
            pause_duration = datetime.now() - self.pause_time
            self.total_paused += pause_duration
            self.pause_time = None

    def pause(self) -> None:
        """Pause the timer."""
        if self.start_time and not self.pause_time:
            self.pause_time = datetime.now()

    def reset(self) -> None:
        """Reset the timer."""
        self.start_time = None
        self.pause_time = None
        self.total_paused = timedelta()

    def get_elapsed_time(self) -> timedelta:
        """Get elapsed time."""
        if not self.start_time:
            return timedelta()

        if self.pause_time:
            # Paused
            return (self.pause_time - self.start_time) - self.total_paused
        else:
            # Running
            return (datetime.now() - self.start_time) - self.total_paused

    def get_remaining_time(self) -> Optional[timedelta]:
        """Get remaining time if target duration is set."""
        if not self.target_duration:
            return None

        elapsed = self.get_elapsed_time()
        remaining = self.target_duration - elapsed
        return remaining if remaining > timedelta() else timedelta()

    def is_overtime(self) -> bool:
        """Check if presentation is over time."""
        if not self.target_duration:
            return False

        return self.get_elapsed_time() > self.target_duration

    def format_time(self, td: timedelta) -> str:
        """Format timedelta as HH:MM:SS."""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


@dataclass
class SlideProgress:
    """Track slide viewing progress."""
    slide_id: str
    view_count: int = 0
    total_time: timedelta = field(default_factory=lambda: timedelta())
    first_viewed: Optional[datetime] = None
    last_viewed: Optional[datetime] = None

    def record_view(self) -> None:
        """Record a slide view."""
        now = datetime.now()
        if not self.first_viewed:
            self.first_viewed = now
        self.last_viewed = now
        self.view_count += 1


class PresenterView:
    """
    Manages presentation mode and presenter view.

    Features:
    - Full-screen presentation
    - Presenter view (notes, timer, next slide)
    - Pointer tools (laser, pen, highlighter)
    - Presentation timer
    - Slide navigation
    - Auto-advance slides
    - Remote control support
    - Slide progress tracking
    """

    def __init__(self):
        """Initialize presenter view."""
        self.state: PresentationState = PresentationState.IDLE
        self.settings: PresentationSettings = PresentationSettings()
        self.timer: PresentationTimer = PresentationTimer()

        self.current_slide_index: int = 0
        self.total_slides: int = 0
        self.slides: List[Dict[str, Any]] = []

        self.slide_progress: Dict[str, SlideProgress] = {}
        self.annotations: List[Dict[str, Any]] = []

        self.on_slide_change: Optional[Callable] = None
        self.on_presentation_end: Optional[Callable] = None

    def load_presentation(
        self,
        slides: List[Dict[str, Any]],
        settings: Optional[PresentationSettings] = None
    ) -> None:
        """
        Load presentation for presenting.

        Args:
            slides: List of slide data
            settings: Presentation settings
        """
        self.slides = slides
        self.total_slides = len(slides)
        self.current_slide_index = 0

        if settings:
            self.settings = settings

        # Initialize slide progress tracking
        for slide in slides:
            slide_id = slide.get("id", "")
            if slide_id:
                self.slide_progress[slide_id] = SlideProgress(slide_id=slide_id)

    def start_presentation(
        self,
        target_duration_minutes: Optional[float] = None
    ) -> None:
        """
        Start the presentation.

        Args:
            target_duration_minutes: Target presentation duration in minutes
        """
        self.state = PresentationState.RUNNING
        self.timer.reset()

        if target_duration_minutes:
            self.timer.target_duration = timedelta(minutes=target_duration_minutes)

        self.timer.start()
        self._record_slide_view()

    def pause_presentation(self) -> None:
        """Pause the presentation."""
        if self.state == PresentationState.RUNNING:
            self.state = PresentationState.PAUSED
            self.timer.pause()

    def resume_presentation(self) -> None:
        """Resume the presentation."""
        if self.state == PresentationState.PAUSED:
            self.state = PresentationState.RUNNING
            self.timer.start()

    def end_presentation(self) -> None:
        """End the presentation."""
        self.state = PresentationState.ENDED
        self.timer.pause()

        if self.on_presentation_end:
            self.on_presentation_end()

    def next_slide(self) -> bool:
        """
        Go to next slide.

        Returns:
            True if moved to next slide, False if at end
        """
        if self.current_slide_index < self.total_slides - 1:
            self.current_slide_index += 1
            self._record_slide_view()
            self._trigger_slide_change()
            return True
        elif self.settings.loop_presentation:
            self.current_slide_index = 0
            self._record_slide_view()
            self._trigger_slide_change()
            return True
        else:
            self.end_presentation()
            return False

    def previous_slide(self) -> bool:
        """
        Go to previous slide.

        Returns:
            True if moved to previous slide, False if at beginning
        """
        if self.current_slide_index > 0:
            self.current_slide_index -= 1
            self._record_slide_view()
            self._trigger_slide_change()
            return True
        return False

    def go_to_slide(self, index: int) -> bool:
        """
        Jump to specific slide.

        Args:
            index: Slide index (0-based)

        Returns:
            True if successful, False if index out of range
        """
        if 0 <= index < self.total_slides:
            self.current_slide_index = index
            self._record_slide_view()
            self._trigger_slide_change()
            return True
        return False

    def first_slide(self) -> None:
        """Jump to first slide."""
        self.go_to_slide(0)

    def last_slide(self) -> None:
        """Jump to last slide."""
        self.go_to_slide(self.total_slides - 1)

    def _record_slide_view(self) -> None:
        """Record viewing of current slide."""
        current_slide = self.get_current_slide()
        if current_slide:
            slide_id = current_slide.get("id", "")
            if slide_id in self.slide_progress:
                self.slide_progress[slide_id].record_view()

    def _trigger_slide_change(self) -> None:
        """Trigger slide change callback."""
        if self.on_slide_change:
            self.on_slide_change(self.current_slide_index)

    def get_current_slide(self) -> Optional[Dict[str, Any]]:
        """Get current slide data."""
        if 0 <= self.current_slide_index < self.total_slides:
            return self.slides[self.current_slide_index]
        return None

    def get_next_slide(self) -> Optional[Dict[str, Any]]:
        """Get next slide data for preview."""
        next_index = self.current_slide_index + 1
        if next_index < self.total_slides:
            return self.slides[next_index]
        elif self.settings.loop_presentation:
            return self.slides[0]
        return None

    def get_previous_slide(self) -> Optional[Dict[str, Any]]:
        """Get previous slide data."""
        prev_index = self.current_slide_index - 1
        if prev_index >= 0:
            return self.slides[prev_index]
        return None

    def get_current_notes(self) -> str:
        """Get speaker notes for current slide."""
        current_slide = self.get_current_slide()
        if current_slide:
            notes = current_slide.get("notes", {})
            if isinstance(notes, dict):
                return notes.get("content", "")
            return str(notes)
        return ""

    def get_progress(self) -> Dict[str, Any]:
        """Get presentation progress information."""
        return {
            "current_slide": self.current_slide_index + 1,
            "total_slides": self.total_slides,
            "percentage": ((self.current_slide_index + 1) / self.total_slides * 100)
                         if self.total_slides > 0 else 0,
            "elapsed_time": self.timer.format_time(self.timer.get_elapsed_time()),
            "remaining_time": (
                self.timer.format_time(self.timer.get_remaining_time())
                if self.timer.get_remaining_time() else None
            ),
            "is_overtime": self.timer.is_overtime(),
        }

    # Pointer Tools

    def set_pointer_tool(self, tool: PointerTool, color: Optional[str] = None) -> None:
        """Set active pointer tool."""
        self.settings.pointer_tool = tool
        if color:
            self.settings.pointer_color = color

    def add_annotation(
        self,
        slide_index: int,
        annotation_type: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Add annotation to slide.

        Args:
            slide_index: Slide index
            annotation_type: Type (pen, highlighter, shape)
            data: Annotation data (coordinates, color, etc.)
        """
        annotation = {
            "slide_index": slide_index,
            "type": annotation_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }
        self.annotations.append(annotation)

    def clear_annotations(self, slide_index: Optional[int] = None) -> None:
        """Clear annotations for specific slide or all slides."""
        if slide_index is not None:
            self.annotations = [
                a for a in self.annotations
                if a["slide_index"] != slide_index
            ]
        else:
            self.annotations.clear()

    def get_slide_annotations(self, slide_index: int) -> List[Dict[str, Any]]:
        """Get all annotations for a slide."""
        return [
            a for a in self.annotations
            if a["slide_index"] == slide_index
        ]

    # Zoom Feature

    def zoom_to_area(
        self,
        x: float,
        y: float,
        zoom_level: float = 2.0
    ) -> Dict[str, Any]:
        """
        Zoom to specific area of slide.

        Args:
            x: X coordinate (0-1)
            y: Y coordinate (0-1)
            zoom_level: Zoom multiplier

        Returns:
            Zoom configuration
        """
        return {
            "x": x,
            "y": y,
            "zoom": zoom_level,
        }

    # Statistics

    def get_presentation_statistics(self) -> Dict[str, Any]:
        """Get presentation statistics."""
        total_time = self.timer.get_elapsed_time()
        slides_viewed = sum(
            1 for progress in self.slide_progress.values()
            if progress.view_count > 0
        )

        most_viewed = None
        max_views = 0
        for slide_id, progress in self.slide_progress.items():
            if progress.view_count > max_views:
                max_views = progress.view_count
                most_viewed = slide_id

        return {
            "total_time": self.timer.format_time(total_time),
            "total_seconds": int(total_time.total_seconds()),
            "slides_viewed": slides_viewed,
            "total_slides": self.total_slides,
            "completion_rate": (slides_viewed / self.total_slides * 100)
                              if self.total_slides > 0 else 0,
            "most_viewed_slide": most_viewed,
            "max_view_count": max_views,
            "average_time_per_slide": (
                self.timer.format_time(total_time / slides_viewed)
                if slides_viewed > 0 else "00:00"
            ),
        }

    def get_slide_statistics(self, slide_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for specific slide."""
        if slide_id in self.slide_progress:
            progress = self.slide_progress[slide_id]
            return {
                "slide_id": slide_id,
                "view_count": progress.view_count,
                "total_time": self.timer.format_time(progress.total_time),
                "first_viewed": (
                    progress.first_viewed.isoformat()
                    if progress.first_viewed else None
                ),
                "last_viewed": (
                    progress.last_viewed.isoformat()
                    if progress.last_viewed else None
                ),
            }
        return None

    # Remote Control Support

    def handle_remote_command(self, command: str) -> bool:
        """
        Handle remote control commands.

        Args:
            command: Command name (next, previous, first, last, pause, resume, end)

        Returns:
            True if command handled successfully
        """
        commands = {
            "next": self.next_slide,
            "previous": self.previous_slide,
            "first": self.first_slide,
            "last": self.last_slide,
            "pause": self.pause_presentation,
            "resume": self.resume_presentation,
            "end": self.end_presentation,
        }

        if command in commands:
            commands[command]()
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state": self.state.value,
            "settings": self.settings.to_dict(),
            "current_slide": self.current_slide_index,
            "total_slides": self.total_slides,
            "progress": self.get_progress(),
            "statistics": self.get_presentation_statistics(),
        }
