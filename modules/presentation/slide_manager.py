"""
Slide Manager - Slide Creation and Editing

Handles all slide operations including creation, deletion, duplication,
reordering, and master slide management.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json


class SlideLayout(Enum):
    """Standard slide layout types."""
    BLANK = "blank"
    TITLE_SLIDE = "title_slide"
    TITLE_CONTENT = "title_content"
    TWO_CONTENT = "two_content"
    COMPARISON = "comparison"
    TITLE_ONLY = "title_only"
    CONTENT_ONLY = "content_only"
    PICTURE_CAPTION = "picture_caption"
    SECTION_HEADER = "section_header"
    VERTICAL_TITLE_TEXT = "vertical_title_text"


class SlideSize(Enum):
    """Standard presentation dimensions."""
    WIDESCREEN_16_9 = (1920, 1080)  # 16:9
    STANDARD_4_3 = (1024, 768)       # 4:3
    LETTER = (816, 1056)             # 8.5" x 11"
    LEDGER = (1056, 816)             # 11" x 8.5"
    A4 = (793, 1122)                 # A4 Portrait
    CUSTOM = (0, 0)                  # Custom dimensions


@dataclass
class SpeakerNotes:
    """Speaker notes for a slide."""
    content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update(self, content: str) -> None:
        """Update notes content."""
        self.content = content
        self.updated_at = datetime.now()


@dataclass
class Slide:
    """Represents a presentation slide."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Slide"
    layout: SlideLayout = SlideLayout.BLANK
    elements: List[Dict[str, Any]] = field(default_factory=list)
    background: Dict[str, Any] = field(default_factory=dict)
    notes: SpeakerNotes = field(default_factory=SpeakerNotes)
    order: int = 0
    section: Optional[str] = None
    hidden: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert slide to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "layout": self.layout.value,
            "elements": self.elements,
            "background": self.background,
            "notes": {
                "content": self.notes.content,
                "created_at": self.notes.created_at.isoformat(),
                "updated_at": self.notes.updated_at.isoformat(),
            },
            "order": self.order,
            "section": self.section,
            "hidden": self.hidden,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Slide':
        """Create slide from dictionary."""
        notes_data = data.get("notes", {})
        notes = SpeakerNotes(
            content=notes_data.get("content", ""),
            created_at=datetime.fromisoformat(notes_data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(notes_data.get("updated_at", datetime.now().isoformat())),
        )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", "Untitled Slide"),
            layout=SlideLayout(data.get("layout", "blank")),
            elements=data.get("elements", []),
            background=data.get("background", {}),
            notes=notes,
            order=data.get("order", 0),
            section=data.get("section"),
            hidden=data.get("hidden", False),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
        )

    def update(self) -> None:
        """Mark slide as updated."""
        self.updated_at = datetime.now()


@dataclass
class Section:
    """Slide section for organization."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Untitled Section"
    start_slide_index: int = 0
    collapsed: bool = False
    color: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert section to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "start_slide_index": self.start_slide_index,
            "collapsed": self.collapsed,
            "color": self.color,
        }


class SlideManager:
    """
    Manages all slide operations for presentations.

    Features:
    - Create, delete, duplicate slides
    - Reorder slides via drag-and-drop
    - Section management
    - Master slides and layouts
    - Slide thumbnails
    - Bulk operations
    """

    def __init__(self):
        """Initialize slide manager."""
        self.slides: List[Slide] = []
        self.sections: List[Section] = []
        self.master_slides: Dict[str, Slide] = {}
        self.default_size: SlideSize = SlideSize.WIDESCREEN_16_9
        self._init_master_slides()

    def _init_master_slides(self) -> None:
        """Initialize default master slides."""
        # Title Slide Master
        self.master_slides["title_slide"] = Slide(
            title="Title Slide Master",
            layout=SlideLayout.TITLE_SLIDE,
            background={"type": "solid", "color": "#FFFFFF"}
        )

        # Content Slide Master
        self.master_slides["content"] = Slide(
            title="Content Slide Master",
            layout=SlideLayout.TITLE_CONTENT,
            background={"type": "solid", "color": "#FFFFFF"}
        )

    def create_slide(
        self,
        layout: SlideLayout = SlideLayout.BLANK,
        title: str = "Untitled Slide",
        position: Optional[int] = None,
        section: Optional[str] = None
    ) -> Slide:
        """
        Create a new slide.

        Args:
            layout: Slide layout type
            title: Slide title
            position: Insert position (None = end)
            section: Section name

        Returns:
            Created slide
        """
        slide = Slide(
            title=title,
            layout=layout,
            section=section,
            order=len(self.slides) if position is None else position
        )

        if position is None:
            self.slides.append(slide)
        else:
            self.slides.insert(position, slide)
            self._reorder_slides()

        return slide

    def delete_slide(self, slide_id: str) -> bool:
        """
        Delete a slide by ID.

        Args:
            slide_id: Slide identifier

        Returns:
            True if deleted, False if not found
        """
        for i, slide in enumerate(self.slides):
            if slide.id == slide_id:
                self.slides.pop(i)
                self._reorder_slides()
                return True
        return False

    def duplicate_slide(self, slide_id: str) -> Optional[Slide]:
        """
        Duplicate an existing slide.

        Args:
            slide_id: Slide to duplicate

        Returns:
            Duplicated slide or None if not found
        """
        for i, slide in enumerate(self.slides):
            if slide.id == slide_id:
                # Create deep copy with new ID
                new_slide = Slide(
                    title=f"{slide.title} (Copy)",
                    layout=slide.layout,
                    elements=json.loads(json.dumps(slide.elements)),  # Deep copy
                    background=slide.background.copy(),
                    section=slide.section,
                    order=i + 1
                )
                new_slide.notes.content = slide.notes.content

                self.slides.insert(i + 1, new_slide)
                self._reorder_slides()
                return new_slide
        return None

    def reorder_slide(self, slide_id: str, new_position: int) -> bool:
        """
        Reorder a slide to a new position.

        Args:
            slide_id: Slide to move
            new_position: New position index

        Returns:
            True if reordered, False if not found
        """
        for i, slide in enumerate(self.slides):
            if slide.id == slide_id:
                if 0 <= new_position < len(self.slides):
                    slide = self.slides.pop(i)
                    self.slides.insert(new_position, slide)
                    self._reorder_slides()
                    return True
        return False

    def move_slide_up(self, slide_id: str) -> bool:
        """Move slide up one position."""
        for i, slide in enumerate(self.slides):
            if slide.id == slide_id and i > 0:
                self.slides[i], self.slides[i-1] = self.slides[i-1], self.slides[i]
                self._reorder_slides()
                return True
        return False

    def move_slide_down(self, slide_id: str) -> bool:
        """Move slide down one position."""
        for i, slide in enumerate(self.slides):
            if slide.id == slide_id and i < len(self.slides) - 1:
                self.slides[i], self.slides[i+1] = self.slides[i+1], self.slides[i]
                self._reorder_slides()
                return True
        return False

    def get_slide(self, slide_id: str) -> Optional[Slide]:
        """Get slide by ID."""
        for slide in self.slides:
            if slide.id == slide_id:
                return slide
        return None

    def get_slide_at_index(self, index: int) -> Optional[Slide]:
        """Get slide at specific index."""
        if 0 <= index < len(self.slides):
            return self.slides[index]
        return None

    def get_all_slides(self) -> List[Slide]:
        """Get all slides in order."""
        return self.slides

    def get_visible_slides(self) -> List[Slide]:
        """Get all visible (non-hidden) slides."""
        return [slide for slide in self.slides if not slide.hidden]

    def toggle_slide_visibility(self, slide_id: str) -> bool:
        """Toggle slide hidden/visible state."""
        slide = self.get_slide(slide_id)
        if slide:
            slide.hidden = not slide.hidden
            slide.update()
            return True
        return False

    def _reorder_slides(self) -> None:
        """Update order attribute for all slides."""
        for i, slide in enumerate(self.slides):
            slide.order = i
            slide.update()

    # Section Management

    def create_section(
        self,
        name: str,
        start_slide_index: int,
        color: Optional[str] = None
    ) -> Section:
        """Create a new section."""
        section = Section(
            name=name,
            start_slide_index=start_slide_index,
            color=color
        )
        self.sections.append(section)
        return section

    def delete_section(self, section_id: str) -> bool:
        """Delete a section."""
        for i, section in enumerate(self.sections):
            if section.id == section_id:
                self.sections.pop(i)
                return True
        return False

    def get_section_slides(self, section_id: str) -> List[Slide]:
        """Get all slides in a section."""
        section = None
        for s in self.sections:
            if s.id == section_id:
                section = s
                break

        if not section:
            return []

        # Find next section start
        next_start = len(self.slides)
        for s in self.sections:
            if s.start_slide_index > section.start_slide_index:
                next_start = min(next_start, s.start_slide_index)

        return self.slides[section.start_slide_index:next_start]

    def rename_section(self, section_id: str, new_name: str) -> bool:
        """Rename a section."""
        for section in self.sections:
            if section.id == section_id:
                section.name = new_name
                return True
        return False

    # Bulk Operations

    def delete_multiple_slides(self, slide_ids: List[str]) -> int:
        """Delete multiple slides. Returns count of deleted slides."""
        deleted = 0
        for slide_id in slide_ids:
            if self.delete_slide(slide_id):
                deleted += 1
        return deleted

    def duplicate_multiple_slides(self, slide_ids: List[str]) -> List[Slide]:
        """Duplicate multiple slides."""
        duplicated = []
        for slide_id in slide_ids:
            new_slide = self.duplicate_slide(slide_id)
            if new_slide:
                duplicated.append(new_slide)
        return duplicated

    def get_slide_count(self) -> int:
        """Get total number of slides."""
        return len(self.slides)

    def get_visible_slide_count(self) -> int:
        """Get number of visible slides."""
        return len(self.get_visible_slides())

    def clear_all_slides(self) -> None:
        """Remove all slides."""
        self.slides.clear()
        self.sections.clear()

    # Master Slide Operations

    def apply_master_slide(self, slide_id: str, master_name: str) -> bool:
        """Apply master slide styling to a slide."""
        slide = self.get_slide(slide_id)
        if not slide or master_name not in self.master_slides:
            return False

        master = self.master_slides[master_name]
        slide.background = master.background.copy()
        slide.update()
        return True

    def create_master_slide(self, name: str, template_slide: Slide) -> None:
        """Create a custom master slide."""
        self.master_slides[name] = template_slide

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "slides": [slide.to_dict() for slide in self.slides],
            "sections": [section.to_dict() for section in self.sections],
            "default_size": {
                "name": self.default_size.name,
                "dimensions": self.default_size.value
            }
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load manager state from dictionary."""
        self.slides = [Slide.from_dict(s) for s in data.get("slides", [])]
        self.sections = [
            Section(**s) for s in data.get("sections", [])
        ]

        size_data = data.get("default_size", {})
        if size_data:
            try:
                self.default_size = SlideSize[size_data.get("name", "WIDESCREEN_16_9")]
            except KeyError:
                self.default_size = SlideSize.WIDESCREEN_16_9
