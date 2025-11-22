"""
Element Handler - Content Element Management

Handles all content elements: text boxes, images, shapes, tables, charts,
videos, audio, icons, and SmartArt diagrams.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import base64


class ElementType(Enum):
    """Types of slide elements."""
    TEXT = "text"
    IMAGE = "image"
    SHAPE = "shape"
    ICON = "icon"
    TABLE = "table"
    CHART = "chart"
    VIDEO = "video"
    AUDIO = "audio"
    SMARTART = "smartart"
    LINE = "line"
    CONNECTOR = "connector"


class ShapeType(Enum):
    """Standard shape types."""
    RECTANGLE = "rectangle"
    ROUNDED_RECTANGLE = "rounded_rectangle"
    ELLIPSE = "ellipse"
    CIRCLE = "circle"
    TRIANGLE = "triangle"
    DIAMOND = "diamond"
    PENTAGON = "pentagon"
    HEXAGON = "hexagon"
    STAR = "star"
    ARROW_RIGHT = "arrow_right"
    ARROW_LEFT = "arrow_left"
    ARROW_UP = "arrow_up"
    ARROW_DOWN = "arrow_down"
    CALLOUT_RECTANGLE = "callout_rectangle"
    CALLOUT_ROUNDED = "callout_rounded"
    CALLOUT_CLOUD = "callout_cloud"
    HEART = "heart"
    LIGHTNING = "lightning"


class TextAlign(Enum):
    """Text alignment options."""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class VerticalAlign(Enum):
    """Vertical alignment options."""
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class LineStyle(Enum):
    """Line styles."""
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    DASH_DOT = "dash_dot"


@dataclass
class Position:
    """Element position on slide."""
    x: float  # Pixels from left
    y: float  # Pixels from top
    z_index: int = 0  # Layer order

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y, "z_index": self.z_index}


@dataclass
class Size:
    """Element dimensions."""
    width: float  # Pixels
    height: float  # Pixels
    maintain_aspect_ratio: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "maintain_aspect_ratio": self.maintain_aspect_ratio
        }


@dataclass
class TextStyle:
    """Text formatting properties."""
    font_family: str = "Arial"
    font_size: int = 18
    color: str = "#000000"
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    highlight_color: Optional[str] = None
    shadow: bool = False
    glow: bool = False
    glow_color: Optional[str] = None
    reflection: bool = False
    rotation: float = 0.0
    line_spacing: float = 1.0
    letter_spacing: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.color,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "strikethrough": self.strikethrough,
            "highlight_color": self.highlight_color,
            "shadow": self.shadow,
            "glow": self.glow,
            "glow_color": self.glow_color,
            "reflection": self.reflection,
            "rotation": self.rotation,
            "line_spacing": self.line_spacing,
            "letter_spacing": self.letter_spacing,
        }


@dataclass
class Border:
    """Element border properties."""
    color: str = "#000000"
    width: float = 1.0
    style: LineStyle = LineStyle.SOLID
    rounded_corners: float = 0.0  # Radius in pixels

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "color": self.color,
            "width": self.width,
            "style": self.style.value,
            "rounded_corners": self.rounded_corners,
        }


@dataclass
class Fill:
    """Element fill properties."""
    type: str = "solid"  # solid, gradient, pattern, image
    color: Optional[str] = "#FFFFFF"
    gradient_colors: Optional[List[str]] = None
    gradient_angle: float = 0.0
    pattern: Optional[str] = None
    image_url: Optional[str] = None
    opacity: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "color": self.color,
            "gradient_colors": self.gradient_colors,
            "gradient_angle": self.gradient_angle,
            "pattern": self.pattern,
            "image_url": self.image_url,
            "opacity": self.opacity,
        }


@dataclass
class Element:
    """Base class for slide elements."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: ElementType = ElementType.TEXT
    position: Position = field(default_factory=lambda: Position(0, 0))
    size: Size = field(default_factory=lambda: Size(200, 100))
    rotation: float = 0.0
    locked: bool = False
    visible: bool = True
    name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "position": self.position.to_dict(),
            "size": self.size.to_dict(),
            "rotation": self.rotation,
            "locked": self.locked,
            "visible": self.visible,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def update(self) -> None:
        """Mark element as updated."""
        self.updated_at = datetime.now()


@dataclass
class TextElement(Element):
    """Text box element."""
    content: str = ""
    style: TextStyle = field(default_factory=TextStyle)
    align: TextAlign = TextAlign.LEFT
    vertical_align: VerticalAlign = VerticalAlign.TOP
    bullet_list: bool = False
    numbered_list: bool = False
    border: Optional[Border] = None
    fill: Fill = field(default_factory=Fill)
    padding: float = 10.0

    def __post_init__(self):
        """Set element type."""
        self.type = ElementType.TEXT

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "content": self.content,
            "style": self.style.to_dict(),
            "align": self.align.value,
            "vertical_align": self.vertical_align.value,
            "bullet_list": self.bullet_list,
            "numbered_list": self.numbered_list,
            "border": self.border.to_dict() if self.border else None,
            "fill": self.fill.to_dict(),
            "padding": self.padding,
        })
        return base


@dataclass
class ImageElement(Element):
    """Image element."""
    source: str = ""  # URL or base64
    alt_text: str = ""
    border: Optional[Border] = None
    opacity: float = 1.0
    filters: Dict[str, Any] = field(default_factory=dict)
    crop: Optional[Dict[str, float]] = None  # {top, right, bottom, left}

    def __post_init__(self):
        """Set element type."""
        self.type = ElementType.IMAGE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "source": self.source,
            "alt_text": self.alt_text,
            "border": self.border.to_dict() if self.border else None,
            "opacity": self.opacity,
            "filters": self.filters,
            "crop": self.crop,
        })
        return base


@dataclass
class ShapeElement(Element):
    """Shape element."""
    shape_type: ShapeType = ShapeType.RECTANGLE
    fill: Fill = field(default_factory=Fill)
    border: Border = field(default_factory=Border)
    shadow: bool = False
    shadow_color: str = "#000000"
    shadow_blur: float = 5.0
    shadow_offset_x: float = 2.0
    shadow_offset_y: float = 2.0

    def __post_init__(self):
        """Set element type."""
        self.type = ElementType.SHAPE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "shape_type": self.shape_type.value,
            "fill": self.fill.to_dict(),
            "border": self.border.to_dict(),
            "shadow": self.shadow,
            "shadow_color": self.shadow_color,
            "shadow_blur": self.shadow_blur,
            "shadow_offset_x": self.shadow_offset_x,
            "shadow_offset_y": self.shadow_offset_y,
        })
        return base


@dataclass
class TableElement(Element):
    """Table element."""
    rows: int = 2
    columns: int = 2
    data: List[List[str]] = field(default_factory=list)
    header_row: bool = True
    header_style: Optional[TextStyle] = None
    cell_style: TextStyle = field(default_factory=TextStyle)
    border: Border = field(default_factory=Border)
    cell_padding: float = 5.0
    row_heights: Optional[List[float]] = None
    column_widths: Optional[List[float]] = None

    def __post_init__(self):
        """Set element type and initialize data."""
        self.type = ElementType.TABLE
        if not self.data:
            self.data = [["" for _ in range(self.columns)] for _ in range(self.rows)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "rows": self.rows,
            "columns": self.columns,
            "data": self.data,
            "header_row": self.header_row,
            "header_style": self.header_style.to_dict() if self.header_style else None,
            "cell_style": self.cell_style.to_dict(),
            "border": self.border.to_dict(),
            "cell_padding": self.cell_padding,
            "row_heights": self.row_heights,
            "column_widths": self.column_widths,
        })
        return base


@dataclass
class ChartElement(Element):
    """Chart element."""
    chart_type: str = "bar"  # bar, line, pie, scatter, area
    data: Dict[str, Any] = field(default_factory=dict)
    title: str = ""
    legend: bool = True
    colors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Set element type."""
        self.type = ElementType.CHART

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "chart_type": self.chart_type,
            "data": self.data,
            "title": self.title,
            "legend": self.legend,
            "colors": self.colors,
        })
        return base


@dataclass
class VideoElement(Element):
    """Video element."""
    source: str = ""
    poster: Optional[str] = None  # Thumbnail image
    autoplay: bool = False
    loop: bool = False
    controls: bool = True
    start_time: float = 0.0
    end_time: Optional[float] = None

    def __post_init__(self):
        """Set element type."""
        self.type = ElementType.VIDEO

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        base = super().to_dict()
        base.update({
            "source": self.source,
            "poster": self.poster,
            "autoplay": self.autoplay,
            "loop": self.loop,
            "controls": self.controls,
            "start_time": self.start_time,
            "end_time": self.end_time,
        })
        return base


class ElementHandler:
    """
    Manages all slide elements.

    Features:
    - Create, update, delete elements
    - Element layering (z-index)
    - Alignment and distribution
    - Grouping and ungrouping
    - Copy, cut, paste
    - Format painter
    """

    def __init__(self):
        """Initialize element handler."""
        self.elements: Dict[str, Element] = {}
        self.clipboard: Optional[Element] = None
        self.format_clipboard: Optional[Dict[str, Any]] = None

    def create_text_element(
        self,
        content: str = "",
        position: Optional[Position] = None,
        size: Optional[Size] = None,
        style: Optional[TextStyle] = None
    ) -> TextElement:
        """Create a text element."""
        element = TextElement(
            content=content,
            position=position or Position(100, 100),
            size=size or Size(300, 100),
            style=style or TextStyle()
        )
        self.elements[element.id] = element
        return element

    def create_image_element(
        self,
        source: str,
        position: Optional[Position] = None,
        size: Optional[Size] = None,
        alt_text: str = ""
    ) -> ImageElement:
        """Create an image element."""
        element = ImageElement(
            source=source,
            alt_text=alt_text,
            position=position or Position(100, 100),
            size=size or Size(400, 300)
        )
        self.elements[element.id] = element
        return element

    def create_shape_element(
        self,
        shape_type: ShapeType,
        position: Optional[Position] = None,
        size: Optional[Size] = None,
        fill: Optional[Fill] = None
    ) -> ShapeElement:
        """Create a shape element."""
        element = ShapeElement(
            shape_type=shape_type,
            position=position or Position(100, 100),
            size=size or Size(200, 200),
            fill=fill or Fill()
        )
        self.elements[element.id] = element
        return element

    def create_table_element(
        self,
        rows: int = 2,
        columns: int = 2,
        position: Optional[Position] = None,
        size: Optional[Size] = None
    ) -> TableElement:
        """Create a table element."""
        element = TableElement(
            rows=rows,
            columns=columns,
            position=position or Position(100, 100),
            size=size or Size(400, 200)
        )
        self.elements[element.id] = element
        return element

    def create_chart_element(
        self,
        chart_type: str = "bar",
        data: Optional[Dict[str, Any]] = None,
        position: Optional[Position] = None,
        size: Optional[Size] = None
    ) -> ChartElement:
        """Create a chart element."""
        element = ChartElement(
            chart_type=chart_type,
            data=data or {},
            position=position or Position(100, 100),
            size=size or Size(500, 300)
        )
        self.elements[element.id] = element
        return element

    def create_video_element(
        self,
        source: str,
        position: Optional[Position] = None,
        size: Optional[Size] = None
    ) -> VideoElement:
        """Create a video element."""
        element = VideoElement(
            source=source,
            position=position or Position(100, 100),
            size=size or Size(640, 360)
        )
        self.elements[element.id] = element
        return element

    def get_element(self, element_id: str) -> Optional[Element]:
        """Get element by ID."""
        return self.elements.get(element_id)

    def update_element(self, element_id: str, properties: Dict[str, Any]) -> bool:
        """Update element properties."""
        element = self.get_element(element_id)
        if not element:
            return False

        for key, value in properties.items():
            if hasattr(element, key):
                setattr(element, key, value)

        element.update()
        return True

    def delete_element(self, element_id: str) -> bool:
        """Delete an element."""
        if element_id in self.elements:
            del self.elements[element_id]
            return True
        return False

    def duplicate_element(self, element_id: str) -> Optional[Element]:
        """Duplicate an element."""
        element = self.get_element(element_id)
        if not element:
            return None

        # Create new element with offset position
        element_dict = element.to_dict()
        element_dict["id"] = str(uuid.uuid4())
        element_dict["position"]["x"] += 20
        element_dict["position"]["y"] += 20

        # Create appropriate element type
        new_element = self._create_from_dict(element_dict)
        if new_element:
            self.elements[new_element.id] = new_element
        return new_element

    def _create_from_dict(self, data: Dict[str, Any]) -> Optional[Element]:
        """Create element from dictionary."""
        element_type = ElementType(data.get("type", "text"))

        if element_type == ElementType.TEXT:
            return TextElement(**self._parse_element_data(data))
        elif element_type == ElementType.IMAGE:
            return ImageElement(**self._parse_element_data(data))
        elif element_type == ElementType.SHAPE:
            return ShapeElement(**self._parse_element_data(data))
        elif element_type == ElementType.TABLE:
            return TableElement(**self._parse_element_data(data))
        elif element_type == ElementType.CHART:
            return ChartElement(**self._parse_element_data(data))
        elif element_type == ElementType.VIDEO:
            return VideoElement(**self._parse_element_data(data))

        return None

    def _parse_element_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse element data for creation."""
        # Basic parsing - in production, would need more sophisticated conversion
        return {k: v for k, v in data.items() if k not in ["created_at", "updated_at"]}

    # Alignment and Distribution

    def align_elements(self, element_ids: List[str], alignment: str) -> bool:
        """
        Align multiple elements.

        alignment: left, center, right, top, middle, bottom
        """
        if len(element_ids) < 2:
            return False

        elements = [self.get_element(eid) for eid in element_ids]
        elements = [e for e in elements if e is not None]

        if not elements:
            return False

        if alignment == "left":
            min_x = min(e.position.x for e in elements)
            for e in elements:
                e.position.x = min_x
                e.update()
        elif alignment == "right":
            max_x = max(e.position.x + e.size.width for e in elements)
            for e in elements:
                e.position.x = max_x - e.size.width
                e.update()
        elif alignment == "center":
            avg_x = sum(e.position.x + e.size.width / 2 for e in elements) / len(elements)
            for e in elements:
                e.position.x = avg_x - e.size.width / 2
                e.update()
        elif alignment == "top":
            min_y = min(e.position.y for e in elements)
            for e in elements:
                e.position.y = min_y
                e.update()
        elif alignment == "bottom":
            max_y = max(e.position.y + e.size.height for e in elements)
            for e in elements:
                e.position.y = max_y - e.size.height
                e.update()
        elif alignment == "middle":
            avg_y = sum(e.position.y + e.size.height / 2 for e in elements) / len(elements)
            for e in elements:
                e.position.y = avg_y - e.size.height / 2
                e.update()

        return True

    def distribute_elements(self, element_ids: List[str], direction: str) -> bool:
        """
        Distribute elements evenly.

        direction: horizontal, vertical
        """
        if len(element_ids) < 3:
            return False

        elements = [self.get_element(eid) for eid in element_ids]
        elements = [e for e in elements if e is not None]

        if not elements:
            return False

        if direction == "horizontal":
            elements.sort(key=lambda e: e.position.x)
            start_x = elements[0].position.x
            end_x = elements[-1].position.x + elements[-1].size.width
            total_width = sum(e.size.width for e in elements)
            gap = (end_x - start_x - total_width) / (len(elements) - 1)

            current_x = start_x
            for e in elements:
                e.position.x = current_x
                current_x += e.size.width + gap
                e.update()
        else:  # vertical
            elements.sort(key=lambda e: e.position.y)
            start_y = elements[0].position.y
            end_y = elements[-1].position.y + elements[-1].size.height
            total_height = sum(e.size.height for e in elements)
            gap = (end_y - start_y - total_height) / (len(elements) - 1)

            current_y = start_y
            for e in elements:
                e.position.y = current_y
                current_y += e.size.height + gap
                e.update()

        return True

    # Layering

    def bring_to_front(self, element_id: str) -> bool:
        """Bring element to front."""
        element = self.get_element(element_id)
        if not element:
            return False

        max_z = max((e.position.z_index for e in self.elements.values()), default=0)
        element.position.z_index = max_z + 1
        element.update()
        return True

    def send_to_back(self, element_id: str) -> bool:
        """Send element to back."""
        element = self.get_element(element_id)
        if not element:
            return False

        min_z = min((e.position.z_index for e in self.elements.values()), default=0)
        element.position.z_index = min_z - 1
        element.update()
        return True

    def bring_forward(self, element_id: str) -> bool:
        """Bring element forward one layer."""
        element = self.get_element(element_id)
        if not element:
            return False

        element.position.z_index += 1
        element.update()
        return True

    def send_backward(self, element_id: str) -> bool:
        """Send element backward one layer."""
        element = self.get_element(element_id)
        if not element:
            return False

        element.position.z_index -= 1
        element.update()
        return True

    # Clipboard Operations

    def copy_element(self, element_id: str) -> bool:
        """Copy element to clipboard."""
        element = self.get_element(element_id)
        if not element:
            return False

        self.clipboard = element
        return True

    def cut_element(self, element_id: str) -> bool:
        """Cut element to clipboard."""
        if self.copy_element(element_id):
            return self.delete_element(element_id)
        return False

    def paste_element(self) -> Optional[Element]:
        """Paste element from clipboard."""
        if not self.clipboard:
            return None

        return self.duplicate_element(self.clipboard.id)

    def copy_format(self, element_id: str) -> bool:
        """Copy element formatting."""
        element = self.get_element(element_id)
        if not element:
            return False

        self.format_clipboard = element.to_dict()
        return True

    def paste_format(self, element_id: str) -> bool:
        """Paste formatting to element."""
        if not self.format_clipboard:
            return False

        element = self.get_element(element_id)
        if not element:
            return False

        # Apply formatting properties (excluding position, size, content)
        exclude = {"id", "position", "size", "content", "source", "data", "created_at", "updated_at"}
        for key, value in self.format_clipboard.items():
            if key not in exclude and hasattr(element, key):
                setattr(element, key, value)

        element.update()
        return True

    def get_all_elements(self) -> List[Element]:
        """Get all elements sorted by z-index."""
        return sorted(self.elements.values(), key=lambda e: e.position.z_index)

    def clear_all_elements(self) -> None:
        """Remove all elements."""
        self.elements.clear()
