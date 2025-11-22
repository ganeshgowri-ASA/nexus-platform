"""
Infographics Designer - Elements Module

This module provides all design elements for the infographics designer,
including text boxes, shapes, icons, images, lines, and arrows.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import uuid


class ElementType(Enum):
    """Types of design elements."""
    TEXT = "text"
    SHAPE = "shape"
    ICON = "icon"
    IMAGE = "image"
    LINE = "line"
    ARROW = "arrow"
    GROUP = "group"


class ShapeType(Enum):
    """Types of shapes."""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    TRIANGLE = "triangle"
    POLYGON = "polygon"
    STAR = "star"
    HEART = "heart"
    SPEECH_BUBBLE = "speech_bubble"
    BANNER = "banner"
    RIBBON = "ribbon"


class LineStyle(Enum):
    """Line styles."""
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    DOUBLE = "double"


class ArrowType(Enum):
    """Arrow head types."""
    NONE = "none"
    SIMPLE = "simple"
    FILLED = "filled"
    TRIANGLE = "triangle"
    CIRCLE = "circle"
    DIAMOND = "diamond"


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


@dataclass
class Position:
    """Position and dimensions of an element."""
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 100.0
    rotation: float = 0.0
    z_index: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'rotation': self.rotation,
            'z_index': self.z_index
        }


@dataclass
class Style:
    """Styling properties for elements."""
    fill_color: str = "#FFFFFF"
    stroke_color: str = "#000000"
    stroke_width: float = 1.0
    opacity: float = 1.0
    gradient: Optional[Dict[str, Any]] = None
    shadow: Optional[Dict[str, Any]] = None
    border_radius: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'fill_color': self.fill_color,
            'stroke_color': self.stroke_color,
            'stroke_width': self.stroke_width,
            'opacity': self.opacity,
            'gradient': self.gradient,
            'shadow': self.shadow,
            'border_radius': self.border_radius
        }


@dataclass
class TextStyle:
    """Text-specific styling properties."""
    font_family: str = "Arial"
    font_size: float = 16.0
    font_weight: str = "normal"
    font_style: str = "normal"
    text_align: TextAlign = TextAlign.LEFT
    vertical_align: VerticalAlign = VerticalAlign.TOP
    line_height: float = 1.2
    letter_spacing: float = 0.0
    text_transform: str = "none"
    text_decoration: str = "none"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'font_family': self.font_family,
            'font_size': self.font_size,
            'font_weight': self.font_weight,
            'font_style': self.font_style,
            'text_align': self.text_align.value,
            'vertical_align': self.vertical_align.value,
            'line_height': self.line_height,
            'letter_spacing': self.letter_spacing,
            'text_transform': self.text_transform,
            'text_decoration': self.text_decoration
        }


@dataclass
class BaseElement:
    """Base class for all design elements."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    element_type: ElementType = ElementType.SHAPE
    name: str = "Element"
    position: Position = field(default_factory=Position)
    style: Style = field(default_factory=Style)
    locked: bool = False
    visible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert element to dictionary."""
        return {
            'id': self.id,
            'element_type': self.element_type.value,
            'name': self.name,
            'position': self.position.to_dict(),
            'style': self.style.to_dict(),
            'locked': self.locked,
            'visible': self.visible,
            'metadata': self.metadata
        }

    def duplicate(self) -> 'BaseElement':
        """Create a duplicate of this element."""
        raise NotImplementedError("Subclasses must implement duplicate()")


@dataclass
class TextElement(BaseElement):
    """Text element for infographics."""
    text: str = "Text"
    text_style: TextStyle = field(default_factory=TextStyle)
    auto_resize: bool = True
    max_width: Optional[float] = None

    def __post_init__(self):
        """Set element type."""
        self.element_type = ElementType.TEXT

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'text': self.text,
            'text_style': self.text_style.to_dict(),
            'auto_resize': self.auto_resize,
            'max_width': self.max_width
        })
        return data

    def duplicate(self) -> 'TextElement':
        """Create a duplicate."""
        from copy import deepcopy
        new_elem = deepcopy(self)
        new_elem.id = str(uuid.uuid4())
        new_elem.position.x += 10
        new_elem.position.y += 10
        return new_elem


@dataclass
class ShapeElement(BaseElement):
    """Shape element for infographics."""
    shape_type: ShapeType = ShapeType.RECTANGLE
    points: Optional[List[Tuple[float, float]]] = None
    sides: int = 5  # For polygons and stars

    def __post_init__(self):
        """Set element type."""
        self.element_type = ElementType.SHAPE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'shape_type': self.shape_type.value,
            'points': self.points,
            'sides': self.sides
        })
        return data

    def duplicate(self) -> 'ShapeElement':
        """Create a duplicate."""
        from copy import deepcopy
        new_elem = deepcopy(self)
        new_elem.id = str(uuid.uuid4())
        new_elem.position.x += 10
        new_elem.position.y += 10
        return new_elem


@dataclass
class IconElement(BaseElement):
    """Icon element for infographics."""
    icon_name: str = "star"
    icon_category: str = "general"
    icon_data: Optional[str] = None  # SVG data or icon code

    def __post_init__(self):
        """Set element type."""
        self.element_type = ElementType.ICON

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'icon_name': self.icon_name,
            'icon_category': self.icon_category,
            'icon_data': self.icon_data
        })
        return data

    def duplicate(self) -> 'IconElement':
        """Create a duplicate."""
        from copy import deepcopy
        new_elem = deepcopy(self)
        new_elem.id = str(uuid.uuid4())
        new_elem.position.x += 10
        new_elem.position.y += 10
        return new_elem


@dataclass
class ImageElement(BaseElement):
    """Image element for infographics."""
    image_url: str = ""
    image_data: Optional[str] = None  # Base64 encoded image
    crop: Optional[Dict[str, float]] = None
    filters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set element type."""
        self.element_type = ElementType.IMAGE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'image_url': self.image_url,
            'image_data': self.image_data,
            'crop': self.crop,
            'filters': self.filters
        })
        return data

    def duplicate(self) -> 'ImageElement':
        """Create a duplicate."""
        from copy import deepcopy
        new_elem = deepcopy(self)
        new_elem.id = str(uuid.uuid4())
        new_elem.position.x += 10
        new_elem.position.y += 10
        return new_elem


@dataclass
class LineElement(BaseElement):
    """Line element for infographics."""
    start_point: Tuple[float, float] = (0, 0)
    end_point: Tuple[float, float] = (100, 100)
    line_style: LineStyle = LineStyle.SOLID
    start_arrow: ArrowType = ArrowType.NONE
    end_arrow: ArrowType = ArrowType.NONE

    def __post_init__(self):
        """Set element type."""
        self.element_type = ElementType.LINE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'start_point': self.start_point,
            'end_point': self.end_point,
            'line_style': self.line_style.value,
            'start_arrow': self.start_arrow.value,
            'end_arrow': self.end_arrow.value
        })
        return data

    def duplicate(self) -> 'LineElement':
        """Create a duplicate."""
        from copy import deepcopy
        new_elem = deepcopy(self)
        new_elem.id = str(uuid.uuid4())
        new_elem.position.x += 10
        new_elem.position.y += 10
        return new_elem


@dataclass
class GroupElement(BaseElement):
    """Group of elements."""
    children: List[BaseElement] = field(default_factory=list)

    def __post_init__(self):
        """Set element type."""
        self.element_type = ElementType.GROUP

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = super().to_dict()
        data.update({
            'children': [child.to_dict() for child in self.children]
        })
        return data

    def add_child(self, element: BaseElement) -> None:
        """Add element to group."""
        self.children.append(element)

    def remove_child(self, element_id: str) -> None:
        """Remove element from group."""
        self.children = [c for c in self.children if c.id != element_id]

    def duplicate(self) -> 'GroupElement':
        """Create a duplicate."""
        from copy import deepcopy
        new_elem = deepcopy(self)
        new_elem.id = str(uuid.uuid4())
        new_elem.position.x += 10
        new_elem.position.y += 10
        # Duplicate all children with new IDs
        new_elem.children = [child.duplicate() for child in self.children]
        return new_elem


class ElementFactory:
    """Factory for creating design elements."""

    @staticmethod
    def create_text(text: str = "Text", x: float = 0, y: float = 0,
                   font_size: float = 16, **kwargs) -> TextElement:
        """Create a text element."""
        position = Position(x=x, y=y, width=200, height=50)
        text_style = TextStyle(font_size=font_size)
        return TextElement(
            text=text,
            position=position,
            text_style=text_style,
            **kwargs
        )

    @staticmethod
    def create_shape(shape_type: ShapeType, x: float = 0, y: float = 0,
                    width: float = 100, height: float = 100, **kwargs) -> ShapeElement:
        """Create a shape element."""
        position = Position(x=x, y=y, width=width, height=height)
        return ShapeElement(
            shape_type=shape_type,
            position=position,
            **kwargs
        )

    @staticmethod
    def create_icon(icon_name: str, x: float = 0, y: float = 0,
                   size: float = 50, **kwargs) -> IconElement:
        """Create an icon element."""
        position = Position(x=x, y=y, width=size, height=size)
        return IconElement(
            icon_name=icon_name,
            position=position,
            **kwargs
        )

    @staticmethod
    def create_image(image_url: str, x: float = 0, y: float = 0,
                    width: float = 200, height: float = 200, **kwargs) -> ImageElement:
        """Create an image element."""
        position = Position(x=x, y=y, width=width, height=height)
        return ImageElement(
            image_url=image_url,
            position=position,
            **kwargs
        )

    @staticmethod
    def create_line(start: Tuple[float, float], end: Tuple[float, float],
                   **kwargs) -> LineElement:
        """Create a line element."""
        return LineElement(
            start_point=start,
            end_point=end,
            **kwargs
        )

    @staticmethod
    def create_arrow(start: Tuple[float, float], end: Tuple[float, float],
                    arrow_type: ArrowType = ArrowType.FILLED, **kwargs) -> LineElement:
        """Create an arrow element."""
        return LineElement(
            start_point=start,
            end_point=end,
            end_arrow=arrow_type,
            **kwargs
        )

    @staticmethod
    def create_group(elements: List[BaseElement], **kwargs) -> GroupElement:
        """Create a group element."""
        return GroupElement(
            children=elements,
            **kwargs
        )


# Predefined element presets
class ElementPresets:
    """Common element presets for quick creation."""

    @staticmethod
    def heading(text: str = "Heading", x: float = 0, y: float = 0) -> TextElement:
        """Create a heading text element."""
        return ElementFactory.create_text(
            text=text, x=x, y=y, font_size=32,
            text_style=TextStyle(
                font_size=32,
                font_weight="bold",
                text_align=TextAlign.CENTER
            )
        )

    @staticmethod
    def subheading(text: str = "Subheading", x: float = 0, y: float = 0) -> TextElement:
        """Create a subheading text element."""
        return ElementFactory.create_text(
            text=text, x=x, y=y, font_size=24,
            text_style=TextStyle(
                font_size=24,
                font_weight="600"
            )
        )

    @staticmethod
    def body_text(text: str = "Body text", x: float = 0, y: float = 0) -> TextElement:
        """Create body text element."""
        return ElementFactory.create_text(
            text=text, x=x, y=y, font_size=14,
            text_style=TextStyle(font_size=14)
        )

    @staticmethod
    def rounded_rectangle(x: float = 0, y: float = 0,
                         width: float = 100, height: float = 100) -> ShapeElement:
        """Create a rounded rectangle."""
        elem = ElementFactory.create_shape(
            ShapeType.RECTANGLE, x, y, width, height
        )
        elem.style.border_radius = 10
        return elem

    @staticmethod
    def circle(x: float = 0, y: float = 0, radius: float = 50) -> ShapeElement:
        """Create a circle."""
        return ElementFactory.create_shape(
            ShapeType.CIRCLE, x, y, radius * 2, radius * 2
        )

    @staticmethod
    def star(x: float = 0, y: float = 0, size: float = 100, points: int = 5) -> ShapeElement:
        """Create a star."""
        elem = ElementFactory.create_shape(
            ShapeType.STAR, x, y, size, size
        )
        elem.sides = points
        return elem


__all__ = [
    'ElementType', 'ShapeType', 'LineStyle', 'ArrowType', 'TextAlign', 'VerticalAlign',
    'Position', 'Style', 'TextStyle',
    'BaseElement', 'TextElement', 'ShapeElement', 'IconElement', 'ImageElement',
    'LineElement', 'GroupElement',
    'ElementFactory', 'ElementPresets'
]
