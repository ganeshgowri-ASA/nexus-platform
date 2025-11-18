"""
Connector system for linking shapes with smart routing and styling.
Supports straight, curved, elbow lines with arrows and labels.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
import math

from .shapes import Point, Shape, ConnectorAnchor


class ConnectorType(Enum):
    """Types of connector lines."""
    STRAIGHT = "straight"
    CURVED = "curved"
    ELBOW = "elbow"
    BEZIER = "bezier"


class ArrowType(Enum):
    """Types of arrow heads."""
    NONE = "none"
    SIMPLE = "simple"
    FILLED = "filled"
    HOLLOW = "hollow"
    DIAMOND = "diamond"
    CIRCLE = "circle"


class LineStyle(Enum):
    """Line drawing styles."""
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"


@dataclass
class ConnectorStyle:
    """Visual styling for connectors."""
    color: str = "#000000"
    width: float = 2.0
    line_style: LineStyle = LineStyle.SOLID
    opacity: float = 1.0
    start_arrow: ArrowType = ArrowType.NONE
    end_arrow: ArrowType = ArrowType.FILLED
    arrow_size: float = 10.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "color": self.color,
            "width": self.width,
            "line_style": self.line_style.value,
            "opacity": self.opacity,
            "start_arrow": self.start_arrow.value,
            "end_arrow": self.end_arrow.value,
            "arrow_size": self.arrow_size
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectorStyle":
        data["line_style"] = LineStyle(data["line_style"])
        data["start_arrow"] = ArrowType(data["start_arrow"])
        data["end_arrow"] = ArrowType(data["end_arrow"])
        return cls(**data)


@dataclass
class ConnectorLabel:
    """Label that can be placed on a connector."""
    text: str
    position: float = 0.5  # 0.0 to 1.0 along the line
    offset_x: float = 0.0
    offset_y: float = -10.0
    font_size: int = 12
    font_family: str = "Arial"
    color: str = "#000000"
    background: Optional[str] = "#FFFFFF"
    padding: float = 4.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "position": self.position,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "font_size": self.font_size,
            "font_family": self.font_family,
            "color": self.color,
            "background": self.background,
            "padding": self.padding
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectorLabel":
        return cls(**data)


@dataclass
class Connector:
    """Connection between two shapes or points."""
    id: str
    connector_type: ConnectorType
    source_shape_id: Optional[str] = None
    target_shape_id: Optional[str] = None
    source_anchor: Optional[ConnectorAnchor] = None
    target_anchor: Optional[ConnectorAnchor] = None
    source_point: Optional[Point] = None  # For floating connections
    target_point: Optional[Point] = None
    style: ConnectorStyle = field(default_factory=ConnectorStyle)
    labels: List[ConnectorLabel] = field(default_factory=list)
    waypoints: List[Point] = field(default_factory=list)  # Custom routing points
    locked: bool = False
    layer: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_start_point(self, shapes: Dict[str, Shape]) -> Point:
        """Get the starting point of the connector."""
        if self.source_point:
            return self.source_point

        if self.source_shape_id and self.source_shape_id in shapes:
            shape = shapes[self.source_shape_id]
            anchor = self.source_anchor or ConnectorAnchor.CENTER
            return shape.get_anchor_position(anchor)

        return Point(0, 0)

    def get_end_point(self, shapes: Dict[str, Shape]) -> Point:
        """Get the ending point of the connector."""
        if self.target_point:
            return self.target_point

        if self.target_shape_id and self.target_shape_id in shapes:
            shape = shapes[self.target_shape_id]
            anchor = self.target_anchor or ConnectorAnchor.CENTER
            return shape.get_anchor_position(anchor)

        return Point(100, 100)

    def to_svg_path(self, shapes: Dict[str, Shape]) -> str:
        """Convert connector to SVG path."""
        start = self.get_start_point(shapes)
        end = self.get_end_point(shapes)

        if self.connector_type == ConnectorType.STRAIGHT:
            return self._straight_path(start, end)
        elif self.connector_type == ConnectorType.CURVED:
            return self._curved_path(start, end)
        elif self.connector_type == ConnectorType.ELBOW:
            return self._elbow_path(start, end)
        elif self.connector_type == ConnectorType.BEZIER:
            return self._bezier_path(start, end)

        return self._straight_path(start, end)

    def _straight_path(self, start: Point, end: Point) -> str:
        """Create straight line path."""
        if self.waypoints:
            path = f"M {start.x},{start.y}"
            for wp in self.waypoints:
                path += f" L {wp.x},{wp.y}"
            path += f" L {end.x},{end.y}"
            return path
        return f"M {start.x},{start.y} L {end.x},{end.y}"

    def _curved_path(self, start: Point, end: Point) -> str:
        """Create smooth curved path."""
        if self.waypoints:
            # Catmull-Rom spline through waypoints
            points = [start] + self.waypoints + [end]
            path = f"M {start.x},{start.y}"

            for i in range(len(points) - 1):
                p0 = points[i - 1] if i > 0 else points[i]
                p1 = points[i]
                p2 = points[i + 1]
                p3 = points[i + 2] if i + 2 < len(points) else points[i + 1]

                # Calculate control points
                cp1_x = p1.x + (p2.x - p0.x) / 6
                cp1_y = p1.y + (p2.y - p0.y) / 6
                cp2_x = p2.x - (p3.x - p1.x) / 6
                cp2_y = p2.y - (p3.y - p1.y) / 6

                path += f" C {cp1_x},{cp1_y} {cp2_x},{cp2_y} {p2.x},{p2.y}"

            return path
        else:
            # Simple quadratic curve
            mid_x = (start.x + end.x) / 2
            mid_y = (start.y + end.y) / 2
            return f"M {start.x},{start.y} Q {mid_x},{mid_y} {end.x},{end.y}"

    def _elbow_path(self, start: Point, end: Point) -> str:
        """Create elbow (orthogonal) path with right angles."""
        if self.waypoints:
            path = f"M {start.x},{start.y}"
            current = start

            for wp in self.waypoints:
                # Create right angles
                path += f" L {current.x},{wp.y} L {wp.x},{wp.y}"
                current = wp

            path += f" L {current.x},{end.y} L {end.x},{end.y}"
            return path
        else:
            # Auto-route with single elbow
            mid_x = (start.x + end.x) / 2

            return (
                f"M {start.x},{start.y} "
                f"L {mid_x},{start.y} "
                f"L {mid_x},{end.y} "
                f"L {end.x},{end.y}"
            )

    def _bezier_path(self, start: Point, end: Point) -> str:
        """Create cubic Bezier curve."""
        if self.waypoints and len(self.waypoints) >= 2:
            cp1 = self.waypoints[0]
            cp2 = self.waypoints[1]
            return (
                f"M {start.x},{start.y} "
                f"C {cp1.x},{cp1.y} {cp2.x},{cp2.y} {end.x},{end.y}"
            )
        else:
            # Auto-generate control points
            dx = end.x - start.x
            dy = end.y - start.y

            cp1_x = start.x + dx * 0.33
            cp1_y = start.y
            cp2_x = start.x + dx * 0.67
            cp2_y = end.y

            return (
                f"M {start.x},{start.y} "
                f"C {cp1_x},{cp1_y} {cp2_x},{cp2_y} {end.x},{end.y}"
            )

    def get_arrow_transform(
        self,
        point: Point,
        angle: float,
        arrow_type: ArrowType
    ) -> str:
        """Get SVG transform for arrow at given point and angle."""
        return f"translate({point.x},{point.y}) rotate({math.degrees(angle)})"

    def get_arrow_path(self, arrow_type: ArrowType, size: float) -> str:
        """Get SVG path for arrow head."""
        if arrow_type == ArrowType.NONE:
            return ""
        elif arrow_type == ArrowType.SIMPLE:
            return f"M 0,0 L {-size},{-size/2} M 0,0 L {-size},{size/2}"
        elif arrow_type == ArrowType.FILLED:
            return f"M 0,0 L {-size},{-size/2} L {-size},{size/2} Z"
        elif arrow_type == ArrowType.HOLLOW:
            return f"M 0,0 L {-size},{-size/2} L {-size},{size/2} Z"
        elif arrow_type == ArrowType.DIAMOND:
            return f"M 0,0 L {-size/2},{-size/2} L {-size},0 L {-size/2},{size/2} Z"
        elif arrow_type == ArrowType.CIRCLE:
            r = size / 2
            return f"M {-r},0 m {-r},0 a {r},{r} 0 1,0 {2*r},0 a {r},{r} 0 1,0 {-2*r},0"
        return ""

    def to_svg(self, shapes: Dict[str, Shape]) -> str:
        """Convert connector to complete SVG representation."""
        path = self.to_svg_path(shapes)
        style = self.style

        # Line style
        stroke_dasharray = ""
        if style.line_style == LineStyle.DASHED:
            stroke_dasharray = 'stroke-dasharray="10,5"'
        elif style.line_style == LineStyle.DOTTED:
            stroke_dasharray = 'stroke-dasharray="2,3"'

        svg_parts = []

        # Main path
        svg_parts.append(
            f'<path d="{path}" '
            f'stroke="{style.color}" '
            f'stroke-width="{style.width}" '
            f'fill="none" '
            f'opacity="{style.opacity}" '
            f'{stroke_dasharray} />'
        )

        # Arrows
        start = self.get_start_point(shapes)
        end = self.get_end_point(shapes)

        if style.start_arrow != ArrowType.NONE:
            angle = self._get_angle_at_start(shapes)
            arrow_path = self.get_arrow_path(style.start_arrow, style.arrow_size)
            transform = self.get_arrow_transform(start, angle, style.start_arrow)

            fill = "none" if style.start_arrow == ArrowType.HOLLOW else style.color
            svg_parts.append(
                f'<path d="{arrow_path}" '
                f'fill="{fill}" '
                f'stroke="{style.color}" '
                f'stroke-width="{style.width}" '
                f'transform="{transform}" />'
            )

        if style.end_arrow != ArrowType.NONE:
            angle = self._get_angle_at_end(shapes)
            arrow_path = self.get_arrow_path(style.end_arrow, style.arrow_size)
            transform = self.get_arrow_transform(end, angle, style.end_arrow)

            fill = "none" if style.end_arrow == ArrowType.HOLLOW else style.color
            svg_parts.append(
                f'<path d="{arrow_path}" '
                f'fill="{fill}" '
                f'stroke="{style.color}" '
                f'stroke-width="{style.width}" '
                f'transform="{transform}" />'
            )

        # Labels
        for label in self.labels:
            label_pos = self._get_point_along_path(label.position, shapes)
            svg_parts.append(self._label_to_svg(label, label_pos))

        return '\n'.join(svg_parts)

    def _get_angle_at_start(self, shapes: Dict[str, Shape]) -> float:
        """Get angle of line at start point."""
        start = self.get_start_point(shapes)

        if self.waypoints:
            next_point = self.waypoints[0]
        else:
            next_point = self.get_end_point(shapes)

        dx = next_point.x - start.x
        dy = next_point.y - start.y
        return math.atan2(dy, dx)

    def _get_angle_at_end(self, shapes: Dict[str, Shape]) -> float:
        """Get angle of line at end point."""
        end = self.get_end_point(shapes)

        if self.waypoints:
            prev_point = self.waypoints[-1]
        else:
            prev_point = self.get_start_point(shapes)

        dx = end.x - prev_point.x
        dy = end.y - prev_point.y
        return math.atan2(dy, dx)

    def _get_point_along_path(self, t: float, shapes: Dict[str, Shape]) -> Point:
        """Get point at position t (0.0 to 1.0) along the path."""
        start = self.get_start_point(shapes)
        end = self.get_end_point(shapes)

        # Simple linear interpolation for now
        x = start.x + (end.x - start.x) * t
        y = start.y + (end.y - start.y) * t

        return Point(x, y)

    def _label_to_svg(self, label: ConnectorLabel, position: Point) -> str:
        """Convert label to SVG."""
        x = position.x + label.offset_x
        y = position.y + label.offset_y

        svg_parts = []

        # Background rectangle (if specified)
        if label.background:
            # Estimate text width (rough approximation)
            text_width = len(label.text) * label.font_size * 0.6
            text_height = label.font_size * 1.2

            rect_x = x - text_width / 2 - label.padding
            rect_y = y - text_height / 2 - label.padding
            rect_width = text_width + label.padding * 2
            rect_height = text_height + label.padding * 2

            svg_parts.append(
                f'<rect x="{rect_x}" y="{rect_y}" '
                f'width="{rect_width}" height="{rect_height}" '
                f'fill="{label.background}" '
                f'stroke="{label.color}" stroke-width="0.5" />'
            )

        # Text
        svg_parts.append(
            f'<text x="{x}" y="{y}" '
            f'font-family="{label.font_family}" '
            f'font-size="{label.font_size}" '
            f'fill="{label.color}" '
            f'text-anchor="middle" '
            f'dominant-baseline="middle">'
            f'{label.text}'
            f'</text>'
        )

        return '\n'.join(svg_parts)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize connector to dictionary."""
        return {
            "id": self.id,
            "connector_type": self.connector_type.value,
            "source_shape_id": self.source_shape_id,
            "target_shape_id": self.target_shape_id,
            "source_anchor": self.source_anchor.value if self.source_anchor else None,
            "target_anchor": self.target_anchor.value if self.target_anchor else None,
            "source_point": self.source_point.to_dict() if self.source_point else None,
            "target_point": self.target_point.to_dict() if self.target_point else None,
            "style": self.style.to_dict(),
            "labels": [label.to_dict() for label in self.labels],
            "waypoints": [wp.to_dict() for wp in self.waypoints],
            "locked": self.locked,
            "layer": self.layer,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Connector":
        """Deserialize connector from dictionary."""
        data["connector_type"] = ConnectorType(data["connector_type"])
        data["source_anchor"] = ConnectorAnchor(data["source_anchor"]) if data.get("source_anchor") else None
        data["target_anchor"] = ConnectorAnchor(data["target_anchor"]) if data.get("target_anchor") else None
        data["source_point"] = Point.from_dict(data["source_point"]) if data.get("source_point") else None
        data["target_point"] = Point.from_dict(data["target_point"]) if data.get("target_point") else None
        data["style"] = ConnectorStyle.from_dict(data["style"])
        data["labels"] = [ConnectorLabel.from_dict(l) for l in data.get("labels", [])]
        data["waypoints"] = [Point.from_dict(wp) for wp in data.get("waypoints", [])]
        return cls(**data)


class ConnectorRouter:
    """Auto-routing algorithms for connectors."""

    @staticmethod
    def find_best_anchors(
        source_shape: Shape,
        target_shape: Shape
    ) -> Tuple[ConnectorAnchor, ConnectorAnchor]:
        """Find the best anchor points to connect two shapes."""
        source_center = source_shape.get_anchor_position(ConnectorAnchor.CENTER)
        target_center = target_shape.get_anchor_position(ConnectorAnchor.CENTER)

        dx = target_center.x - source_center.x
        dy = target_center.y - source_center.y

        # Determine primary direction
        if abs(dx) > abs(dy):
            # Horizontal connection
            if dx > 0:
                source_anchor = ConnectorAnchor.RIGHT
                target_anchor = ConnectorAnchor.LEFT
            else:
                source_anchor = ConnectorAnchor.LEFT
                target_anchor = ConnectorAnchor.RIGHT
        else:
            # Vertical connection
            if dy > 0:
                source_anchor = ConnectorAnchor.BOTTOM
                target_anchor = ConnectorAnchor.TOP
            else:
                source_anchor = ConnectorAnchor.TOP
                target_anchor = ConnectorAnchor.BOTTOM

        return source_anchor, target_anchor

    @staticmethod
    def calculate_elbow_waypoints(
        start: Point,
        end: Point,
        start_dir: str = "right",
        end_dir: str = "left"
    ) -> List[Point]:
        """Calculate waypoints for elbow connector routing."""
        waypoints = []

        # Simple Manhattan routing
        if start_dir in ["right", "left"] and end_dir in ["right", "left"]:
            # Horizontal to horizontal
            mid_x = (start.x + end.x) / 2
            waypoints.append(Point(mid_x, start.y))
            waypoints.append(Point(mid_x, end.y))
        elif start_dir in ["top", "bottom"] and end_dir in ["top", "bottom"]:
            # Vertical to vertical
            mid_y = (start.y + end.y) / 2
            waypoints.append(Point(start.x, mid_y))
            waypoints.append(Point(end.x, mid_y))
        else:
            # Mixed direction - one corner
            if start_dir in ["right", "left"]:
                waypoints.append(Point(end.x, start.y))
            else:
                waypoints.append(Point(start.x, end.y))

        return waypoints

    @staticmethod
    def avoid_shapes(
        start: Point,
        end: Point,
        obstacles: List[Shape]
    ) -> List[Point]:
        """Calculate waypoints that avoid obstacles (simplified A* algorithm)."""
        # Simplified obstacle avoidance
        # In a full implementation, this would use A* or similar pathfinding
        waypoints = []

        # Check if direct path intersects any obstacles
        direct_path_clear = True
        for obstacle in obstacles:
            if ConnectorRouter._line_intersects_shape(start, end, obstacle):
                direct_path_clear = False
                break

        if not direct_path_clear:
            # Route around obstacles (simplified)
            mid_x = (start.x + end.x) / 2
            mid_y = (start.y + end.y) / 2
            waypoints.append(Point(mid_x, start.y))
            waypoints.append(Point(mid_x, end.y))

        return waypoints

    @staticmethod
    def _line_intersects_shape(p1: Point, p2: Point, shape: Shape) -> bool:
        """Check if line segment intersects with shape bounds."""
        # Simplified bounding box intersection check
        min_x = min(p1.x, p2.x)
        max_x = max(p1.x, p2.x)
        min_y = min(p1.y, p2.y)
        max_y = max(p1.y, p2.y)

        shape_min_x = shape.position.x
        shape_max_x = shape.position.x + shape.width
        shape_min_y = shape.position.y
        shape_max_y = shape.position.y + shape.height

        # Check if bounding boxes overlap
        return not (
            max_x < shape_min_x or
            min_x > shape_max_x or
            max_y < shape_min_y or
            min_y > shape_max_y
        )
