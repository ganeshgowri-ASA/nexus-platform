"""
Infographics Designer - Designer Module

This module provides the main infographic designer with features including
drag-drop, alignment, grouping, layering, duplication, flip/rotate, and more.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from enum import Enum
import json
from copy import deepcopy

from .elements import BaseElement, Position, GroupElement
from .templates import Template
from .animations import Animation, AnimationSequence


class AlignmentType(Enum):
    """Alignment types."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"
    HORIZONTAL_CENTER = "horizontal_center"
    VERTICAL_CENTER = "vertical_center"


class DistributionType(Enum):
    """Distribution types."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class FlipDirection(Enum):
    """Flip directions."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass
class CanvasConfig:
    """Canvas configuration."""
    width: float = 1920
    height: float = 1080
    background_color: str = "#FFFFFF"
    background_image: Optional[str] = None
    show_grid: bool = True
    grid_size: float = 20
    grid_color: str = "#E0E0E0"
    snap_to_grid: bool = False
    snap_threshold: float = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'width': self.width,
            'height': self.height,
            'background_color': self.background_color,
            'background_image': self.background_image,
            'show_grid': self.show_grid,
            'grid_size': self.grid_size,
            'grid_color': self.grid_color,
            'snap_to_grid': self.snap_to_grid,
            'snap_threshold': self.snap_threshold
        }


@dataclass
class HistoryEntry:
    """History entry for undo/redo."""
    action: str
    timestamp: float
    data: Dict[str, Any]


class InfographicDesigner:
    """Main infographic designer class."""

    def __init__(self, canvas_config: Optional[CanvasConfig] = None):
        """Initialize designer."""
        self.canvas = canvas_config or CanvasConfig()
        self.elements: List[BaseElement] = []
        self.selected_elements: Set[str] = set()
        self.clipboard: List[BaseElement] = []
        self.history: List[HistoryEntry] = []
        self.history_index: int = -1
        self.max_history: int = 50
        self.animations: List[Animation] = []
        self.animation_sequences: List[AnimationSequence] = []

    # Element Management

    def add_element(self, element: BaseElement) -> None:
        """Add element to canvas."""
        self.elements.append(element)
        self._save_history("add_element", {'element_id': element.id})

    def remove_element(self, element_id: str) -> bool:
        """Remove element from canvas."""
        for i, elem in enumerate(self.elements):
            if elem.id == element_id:
                self.elements.pop(i)
                self.selected_elements.discard(element_id)
                self._save_history("remove_element", {'element_id': element_id})
                return True
        return False

    def get_element(self, element_id: str) -> Optional[BaseElement]:
        """Get element by ID."""
        for elem in self.elements:
            if elem.id == element_id:
                return elem
        return None

    def get_elements(self) -> List[BaseElement]:
        """Get all elements."""
        return self.elements.copy()

    def clear_canvas(self) -> None:
        """Remove all elements."""
        self.elements.clear()
        self.selected_elements.clear()
        self._save_history("clear_canvas", {})

    # Selection Management

    def select_element(self, element_id: str) -> None:
        """Select element."""
        if self.get_element(element_id):
            self.selected_elements.add(element_id)

    def deselect_element(self, element_id: str) -> None:
        """Deselect element."""
        self.selected_elements.discard(element_id)

    def select_all(self) -> None:
        """Select all elements."""
        self.selected_elements = {elem.id for elem in self.elements}

    def deselect_all(self) -> None:
        """Deselect all elements."""
        self.selected_elements.clear()

    def get_selected_elements(self) -> List[BaseElement]:
        """Get selected elements."""
        return [elem for elem in self.elements if elem.id in self.selected_elements]

    def select_in_area(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Select elements within rectangular area."""
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        for elem in self.elements:
            if (elem.position.x >= min_x and elem.position.x <= max_x and
                elem.position.y >= min_y and elem.position.y <= max_y):
                self.selected_elements.add(elem.id)

    # Position and Transform

    def move_element(self, element_id: str, dx: float, dy: float) -> bool:
        """Move element by delta."""
        elem = self.get_element(element_id)
        if elem:
            elem.position.x += dx
            elem.position.y += dy
            return True
        return False

    def set_position(self, element_id: str, x: float, y: float) -> bool:
        """Set element position."""
        elem = self.get_element(element_id)
        if elem:
            elem.position.x = x
            elem.position.y = y
            return True
        return False

    def resize_element(self, element_id: str, width: float, height: float) -> bool:
        """Resize element."""
        elem = self.get_element(element_id)
        if elem:
            elem.position.width = width
            elem.position.height = height
            return True
        return False

    def rotate_element(self, element_id: str, degrees: float) -> bool:
        """Rotate element."""
        elem = self.get_element(element_id)
        if elem:
            elem.position.rotation = (elem.position.rotation + degrees) % 360
            return True
        return False

    def flip_element(self, element_id: str, direction: FlipDirection) -> bool:
        """Flip element."""
        elem = self.get_element(element_id)
        if elem:
            if direction == FlipDirection.HORIZONTAL:
                # In production, would modify element rendering
                elem.metadata['flip_h'] = not elem.metadata.get('flip_h', False)
            else:
                elem.metadata['flip_v'] = not elem.metadata.get('flip_v', False)
            return True
        return False

    # Layering (Z-Index)

    def bring_to_front(self, element_id: str) -> bool:
        """Bring element to front."""
        elem = self.get_element(element_id)
        if elem:
            max_z = max([e.position.z_index for e in self.elements], default=0)
            elem.position.z_index = max_z + 1
            self._reorder_elements()
            return True
        return False

    def send_to_back(self, element_id: str) -> bool:
        """Send element to back."""
        elem = self.get_element(element_id)
        if elem:
            min_z = min([e.position.z_index for e in self.elements], default=0)
            elem.position.z_index = min_z - 1
            self._reorder_elements()
            return True
        return False

    def bring_forward(self, element_id: str) -> bool:
        """Bring element forward one layer."""
        elem = self.get_element(element_id)
        if elem:
            elem.position.z_index += 1
            self._reorder_elements()
            return True
        return False

    def send_backward(self, element_id: str) -> bool:
        """Send element backward one layer."""
        elem = self.get_element(element_id)
        if elem:
            elem.position.z_index -= 1
            self._reorder_elements()
            return True
        return False

    def _reorder_elements(self) -> None:
        """Reorder elements by z-index."""
        self.elements.sort(key=lambda e: e.position.z_index)

    # Alignment

    def align_elements(self, element_ids: List[str], alignment: AlignmentType) -> None:
        """Align elements."""
        elements = [self.get_element(eid) for eid in element_ids]
        elements = [e for e in elements if e is not None]

        if not elements:
            return

        if alignment == AlignmentType.LEFT:
            min_x = min(e.position.x for e in elements)
            for elem in elements:
                elem.position.x = min_x

        elif alignment == AlignmentType.CENTER:
            avg_x = sum(e.position.x + e.position.width / 2 for e in elements) / len(elements)
            for elem in elements:
                elem.position.x = avg_x - elem.position.width / 2

        elif alignment == AlignmentType.RIGHT:
            max_x = max(e.position.x + e.position.width for e in elements)
            for elem in elements:
                elem.position.x = max_x - elem.position.width

        elif alignment == AlignmentType.TOP:
            min_y = min(e.position.y for e in elements)
            for elem in elements:
                elem.position.y = min_y

        elif alignment == AlignmentType.MIDDLE:
            avg_y = sum(e.position.y + e.position.height / 2 for e in elements) / len(elements)
            for elem in elements:
                elem.position.y = avg_y - elem.position.height / 2

        elif alignment == AlignmentType.BOTTOM:
            max_y = max(e.position.y + e.position.height for e in elements)
            for elem in elements:
                elem.position.y = max_y - elem.position.height

        elif alignment == AlignmentType.HORIZONTAL_CENTER:
            center_x = self.canvas.width / 2
            for elem in elements:
                elem.position.x = center_x - elem.position.width / 2

        elif alignment == AlignmentType.VERTICAL_CENTER:
            center_y = self.canvas.height / 2
            for elem in elements:
                elem.position.y = center_y - elem.position.height / 2

    def distribute_elements(self, element_ids: List[str],
                          distribution: DistributionType) -> None:
        """Distribute elements evenly."""
        elements = [self.get_element(eid) for eid in element_ids]
        elements = [e for e in elements if e is not None]

        if len(elements) < 3:
            return

        if distribution == DistributionType.HORIZONTAL:
            elements.sort(key=lambda e: e.position.x)
            min_x = elements[0].position.x
            max_x = elements[-1].position.x + elements[-1].position.width
            spacing = (max_x - min_x) / (len(elements) - 1)

            for i, elem in enumerate(elements[1:-1], 1):
                elem.position.x = min_x + spacing * i

        elif distribution == DistributionType.VERTICAL:
            elements.sort(key=lambda e: e.position.y)
            min_y = elements[0].position.y
            max_y = elements[-1].position.y + elements[-1].position.height
            spacing = (max_y - min_y) / (len(elements) - 1)

            for i, elem in enumerate(elements[1:-1], 1):
                elem.position.y = min_y + spacing * i

    # Grouping

    def group_elements(self, element_ids: List[str]) -> Optional[str]:
        """Group elements."""
        elements = [self.get_element(eid) for eid in element_ids]
        elements = [e for e in elements if e is not None]

        if len(elements) < 2:
            return None

        # Create group
        group = GroupElement(children=elements)

        # Calculate group bounds
        min_x = min(e.position.x for e in elements)
        min_y = min(e.position.y for e in elements)
        max_x = max(e.position.x + e.position.width for e in elements)
        max_y = max(e.position.y + e.position.height for e in elements)

        group.position = Position(
            x=min_x,
            y=min_y,
            width=max_x - min_x,
            height=max_y - min_y
        )

        # Remove individual elements
        for elem in elements:
            self.remove_element(elem.id)

        # Add group
        self.add_element(group)

        return group.id

    def ungroup_elements(self, group_id: str) -> List[str]:
        """Ungroup elements."""
        group = self.get_element(group_id)
        if not isinstance(group, GroupElement):
            return []

        # Add children back to canvas
        child_ids = []
        for child in group.children:
            self.add_element(child)
            child_ids.append(child.id)

        # Remove group
        self.remove_element(group_id)

        return child_ids

    # Duplication

    def duplicate_element(self, element_id: str) -> Optional[str]:
        """Duplicate element."""
        elem = self.get_element(element_id)
        if elem:
            duplicate = elem.duplicate()
            self.add_element(duplicate)
            return duplicate.id
        return None

    def duplicate_selected(self) -> List[str]:
        """Duplicate selected elements."""
        duplicated_ids = []
        for elem_id in list(self.selected_elements):
            dup_id = self.duplicate_element(elem_id)
            if dup_id:
                duplicated_ids.append(dup_id)
        return duplicated_ids

    # Clipboard Operations

    def copy_selected(self) -> None:
        """Copy selected elements to clipboard."""
        self.clipboard = [
            deepcopy(self.get_element(eid))
            for eid in self.selected_elements
        ]
        self.clipboard = [e for e in self.clipboard if e is not None]

    def cut_selected(self) -> None:
        """Cut selected elements to clipboard."""
        self.copy_selected()
        for elem_id in list(self.selected_elements):
            self.remove_element(elem_id)

    def paste(self, offset_x: float = 10, offset_y: float = 10) -> List[str]:
        """Paste elements from clipboard."""
        pasted_ids = []

        for elem in self.clipboard:
            # Create deep copy and offset
            new_elem = deepcopy(elem)
            new_elem.position.x += offset_x
            new_elem.position.y += offset_y

            self.add_element(new_elem)
            pasted_ids.append(new_elem.id)

        return pasted_ids

    # Locking and Visibility

    def lock_element(self, element_id: str) -> bool:
        """Lock element."""
        elem = self.get_element(element_id)
        if elem:
            elem.locked = True
            return True
        return False

    def unlock_element(self, element_id: str) -> bool:
        """Unlock element."""
        elem = self.get_element(element_id)
        if elem:
            elem.locked = False
            return True
        return False

    def hide_element(self, element_id: str) -> bool:
        """Hide element."""
        elem = self.get_element(element_id)
        if elem:
            elem.visible = False
            return True
        return False

    def show_element(self, element_id: str) -> bool:
        """Show element."""
        elem = self.get_element(element_id)
        if elem:
            elem.visible = True
            return True
        return False

    # History (Undo/Redo)

    def _save_history(self, action: str, data: Dict[str, Any]) -> None:
        """Save action to history."""
        import time

        # Remove future history if we're not at the end
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        # Add new entry
        entry = HistoryEntry(
            action=action,
            timestamp=time.time(),
            data=data
        )
        self.history.append(entry)
        self.history_index += 1

        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self) -> bool:
        """Undo last action."""
        # TODO: Implement undo logic based on history
        if self.history_index >= 0:
            self.history_index -= 1
            return True
        return False

    def redo(self) -> bool:
        """Redo last undone action."""
        # TODO: Implement redo logic based on history
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            return True
        return False

    # Template Management

    def load_template(self, template: Template) -> None:
        """Load template into designer."""
        self.clear_canvas()
        self.canvas.width = template.canvas_width
        self.canvas.height = template.canvas_height
        self.canvas.background_color = template.background_color
        self.canvas.background_image = template.background_image

        for elem in template.elements:
            self.add_element(deepcopy(elem))

    def save_as_template(self, name: str, category: str) -> Template:
        """Save current design as template."""
        from .templates import Template, TemplateMetadata, TemplateCategory, TemplateStyle

        metadata = TemplateMetadata(
            id=f"custom_{name}",
            name=name,
            category=TemplateCategory.BUSINESS,  # Default
            style=TemplateStyle.MODERN,
            description="Custom template"
        )

        template = Template(
            metadata=metadata,
            canvas_width=self.canvas.width,
            canvas_height=self.canvas.height,
            background_color=self.canvas.background_color,
            background_image=self.canvas.background_image,
            elements=[deepcopy(elem) for elem in self.elements]
        )

        return template

    # Export

    def to_dict(self) -> Dict[str, Any]:
        """Export designer state to dictionary."""
        return {
            'canvas': self.canvas.to_dict(),
            'elements': [elem.to_dict() for elem in self.elements],
            'animations': [anim.to_dict() for anim in self.animations],
            'animation_sequences': [seq.to_dict() for seq in self.animation_sequences]
        }

    def to_json(self) -> str:
        """Export designer state to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    def save_to_file(self, filepath: str) -> None:
        """Save design to file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    def load_from_file(self, filepath: str) -> None:
        """Load design from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        # TODO: Implement full deserialization


__all__ = [
    'AlignmentType', 'DistributionType', 'FlipDirection',
    'CanvasConfig', 'HistoryEntry', 'InfographicDesigner'
]
