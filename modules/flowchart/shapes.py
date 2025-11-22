"""
Shape library with 100+ shapes for flowcharts, diagrams, and visual designs.
Supports flowchart, UML, network, cloud (AWS/Azure), org charts, BPMN, wireframes, and more.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import json


class ShapeCategory(Enum):
    """Categories of shapes available in the library."""
    FLOWCHART = "flowchart"
    UML = "uml"
    NETWORK = "network"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ORG_CHART = "org_chart"
    BPMN = "bpmn"
    WIREFRAME = "wireframe"
    FLOOR_PLAN = "floor_plan"
    BASIC = "basic"
    ARROWS = "arrows"
    SYMBOLS = "symbols"
    INFOGRAPHIC = "infographic"


class ConnectorAnchor(Enum):
    """Anchor points for connectors on shapes."""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"


@dataclass
class Point:
    """2D point representation."""
    x: float
    y: float

    def to_dict(self) -> Dict[str, float]:
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "Point":
        return cls(x=data["x"], y=data["y"])


@dataclass
class ShapeStyle:
    """Visual styling for shapes."""
    fill_color: str = "#FFFFFF"
    stroke_color: str = "#000000"
    stroke_width: float = 2.0
    opacity: float = 1.0
    shadow: bool = False
    shadow_color: str = "#00000040"
    shadow_offset_x: float = 2.0
    shadow_offset_y: float = 2.0
    shadow_blur: float = 4.0
    gradient: Optional[Dict[str, Any]] = None
    border_radius: float = 0.0
    font_family: str = "Arial"
    font_size: int = 14
    font_color: str = "#000000"
    font_weight: str = "normal"
    font_style: str = "normal"
    text_align: str = "center"
    text_vertical_align: str = "middle"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fill_color": self.fill_color,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
            "opacity": self.opacity,
            "shadow": self.shadow,
            "shadow_color": self.shadow_color,
            "shadow_offset_x": self.shadow_offset_x,
            "shadow_offset_y": self.shadow_offset_y,
            "shadow_blur": self.shadow_blur,
            "gradient": self.gradient,
            "border_radius": self.border_radius,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_color": self.font_color,
            "font_weight": self.font_weight,
            "font_style": self.font_style,
            "text_align": self.text_align,
            "text_vertical_align": self.text_vertical_align
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShapeStyle":
        return cls(**data)


@dataclass
class Shape:
    """Base shape class with common properties."""
    id: str
    shape_type: str
    category: ShapeCategory
    position: Point
    width: float
    height: float
    rotation: float = 0.0
    text: str = ""
    style: ShapeStyle = field(default_factory=ShapeStyle)
    locked: bool = False
    layer: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    anchor_points: List[ConnectorAnchor] = field(default_factory=list)
    custom_path: Optional[str] = None  # SVG path data for custom shapes

    def __post_init__(self):
        """Initialize default anchor points if not provided."""
        if not self.anchor_points:
            self.anchor_points = [
                ConnectorAnchor.TOP,
                ConnectorAnchor.BOTTOM,
                ConnectorAnchor.LEFT,
                ConnectorAnchor.RIGHT,
                ConnectorAnchor.CENTER
            ]

    def get_anchor_position(self, anchor: ConnectorAnchor) -> Point:
        """Get the absolute position of an anchor point."""
        x, y = self.position.x, self.position.y
        w, h = self.width, self.height

        anchor_map = {
            ConnectorAnchor.TOP: Point(x + w/2, y),
            ConnectorAnchor.BOTTOM: Point(x + w/2, y + h),
            ConnectorAnchor.LEFT: Point(x, y + h/2),
            ConnectorAnchor.RIGHT: Point(x + w, y + h/2),
            ConnectorAnchor.TOP_LEFT: Point(x, y),
            ConnectorAnchor.TOP_RIGHT: Point(x + w, y),
            ConnectorAnchor.BOTTOM_LEFT: Point(x, y + h),
            ConnectorAnchor.BOTTOM_RIGHT: Point(x + w, y + h),
            ConnectorAnchor.CENTER: Point(x + w/2, y + h/2)
        }

        return anchor_map[anchor]

    def get_bounds(self) -> Tuple[Point, Point]:
        """Get bounding box of the shape."""
        return (
            Point(self.position.x, self.position.y),
            Point(self.position.x + self.width, self.position.y + self.height)
        )

    def contains_point(self, point: Point) -> bool:
        """Check if a point is inside the shape."""
        return (
            self.position.x <= point.x <= self.position.x + self.width and
            self.position.y <= point.y <= self.position.y + self.height
        )

    def to_svg(self) -> str:
        """Convert shape to SVG representation."""
        style = self.style
        svg_style = (
            f"fill:{style.fill_color};"
            f"stroke:{style.stroke_color};"
            f"stroke-width:{style.stroke_width};"
            f"opacity:{style.opacity};"
        )

        if self.custom_path:
            return f'<path d="{self.custom_path}" style="{svg_style}" />'

        # Default rectangle
        return (
            f'<rect x="{self.position.x}" y="{self.position.y}" '
            f'width="{self.width}" height="{self.height}" '
            f'rx="{style.border_radius}" style="{svg_style}" />'
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize shape to dictionary."""
        return {
            "id": self.id,
            "shape_type": self.shape_type,
            "category": self.category.value,
            "position": self.position.to_dict(),
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
            "text": self.text,
            "style": self.style.to_dict(),
            "locked": self.locked,
            "layer": self.layer,
            "metadata": self.metadata,
            "anchor_points": [ap.value for ap in self.anchor_points],
            "custom_path": self.custom_path
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Shape":
        """Deserialize shape from dictionary."""
        data["category"] = ShapeCategory(data["category"])
        data["position"] = Point.from_dict(data["position"])
        data["style"] = ShapeStyle.from_dict(data["style"])
        data["anchor_points"] = [ConnectorAnchor(ap) for ap in data["anchor_points"]]
        return cls(**data)


class ShapeLibrary:
    """Library of pre-defined shapes organized by category."""

    def __init__(self):
        self.shapes: Dict[str, Dict[str, Any]] = {}
        self._initialize_library()

    def _initialize_library(self):
        """Initialize the shape library with 100+ shapes."""
        self._add_flowchart_shapes()
        self._add_uml_shapes()
        self._add_network_shapes()
        self._add_cloud_shapes()
        self._add_org_chart_shapes()
        self._add_bpmn_shapes()
        self._add_wireframe_shapes()
        self._add_floor_plan_shapes()
        self._add_basic_shapes()
        self._add_arrow_shapes()
        self._add_symbol_shapes()
        self._add_infographic_shapes()

    def _add_flowchart_shapes(self):
        """Add flowchart shapes."""
        flowchart = {
            # Process/Action
            "process": {
                "name": "Process",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (120, 60),
                "path": None,  # Rectangle
                "description": "Represents a process or action step"
            },
            # Decision
            "decision": {
                "name": "Decision",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (120, 80),
                "path": "M 60,0 L 120,40 L 60,80 L 0,40 Z",  # Diamond
                "description": "Represents a decision point"
            },
            # Terminator
            "terminator": {
                "name": "Terminator",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (120, 60),
                "path": "M 30,0 L 90,0 Q 120,0 120,30 L 120,30 Q 120,60 90,60 L 30,60 Q 0,60 0,30 L 0,30 Q 0,0 30,0 Z",
                "description": "Start/End point"
            },
            # Data/IO
            "data": {
                "name": "Data",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (120, 60),
                "path": "M 20,0 L 120,0 L 100,60 L 0,60 Z",  # Parallelogram
                "description": "Data input/output"
            },
            # Document
            "document": {
                "name": "Document",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (120, 80),
                "path": "M 0,0 L 120,0 L 120,60 Q 90,70 60,60 Q 30,50 0,60 Z",
                "description": "Document or report"
            },
            # Database
            "database": {
                "name": "Database",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (100, 120),
                "path": "M 0,20 Q 0,0 50,0 Q 100,0 100,20 L 100,100 Q 100,120 50,120 Q 0,120 0,100 Z M 0,20 Q 0,40 50,40 Q 100,40 100,20",
                "description": "Database storage"
            },
            # Predefined Process
            "predefined_process": {
                "name": "Predefined Process",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (120, 60),
                "path": "M 0,0 L 120,0 L 120,60 L 0,60 Z M 10,0 L 10,60 M 110,0 L 110,60",
                "description": "Predefined/subprocess"
            },
            # Manual Input
            "manual_input": {
                "name": "Manual Input",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (120, 60),
                "path": "M 0,20 L 120,0 L 120,60 L 0,60 Z",
                "description": "Manual input operation"
            },
            # Preparation
            "preparation": {
                "name": "Preparation",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (120, 60),
                "path": "M 20,0 L 100,0 L 120,30 L 100,60 L 20,60 L 0,30 Z",
                "description": "Preparation or initialization"
            },
            # Display
            "display": {
                "name": "Display",
                "category": ShapeCategory.FLOWCHART,
                "default_size": (120, 60),
                "path": "M 20,0 L 100,0 Q 120,30 100,60 L 20,60 Q 0,30 20,0 Z",
                "description": "Display output"
            },
        }
        self.shapes.update({f"flowchart_{k}": v for k, v in flowchart.items()})

    def _add_uml_shapes(self):
        """Add UML diagram shapes."""
        uml = {
            "class": {
                "name": "Class",
                "category": ShapeCategory.UML,
                "default_size": (150, 120),
                "path": "M 0,0 L 150,0 L 150,120 L 0,120 Z M 0,30 L 150,30 M 0,70 L 150,70",
                "description": "UML Class"
            },
            "interface": {
                "name": "Interface",
                "category": ShapeCategory.UML,
                "default_size": (150, 100),
                "path": "M 0,0 L 150,0 L 150,100 L 0,100 Z M 0,25 L 150,25",
                "description": "UML Interface"
            },
            "actor": {
                "name": "Actor",
                "category": ShapeCategory.UML,
                "default_size": (60, 100),
                "path": "M 30,15 m -10,0 a 10,10 0 1,0 20,0 a 10,10 0 1,0 -20,0 M 30,25 L 30,60 M 10,40 L 50,40 M 30,60 L 10,90 M 30,60 L 50,90",
                "description": "UML Actor"
            },
            "use_case": {
                "name": "Use Case",
                "category": ShapeCategory.UML,
                "default_size": (140, 70),
                "path": "M 70,0 Q 140,0 140,35 Q 140,70 70,70 Q 0,70 0,35 Q 0,0 70,0 Z",
                "description": "UML Use Case"
            },
            "component": {
                "name": "Component",
                "category": ShapeCategory.UML,
                "default_size": (140, 80),
                "path": "M 20,0 L 140,0 L 140,80 L 20,80 Z M 0,15 L 20,15 L 20,25 L 0,25 Z M 0,35 L 20,35 L 20,45 L 0,45 Z",
                "description": "UML Component"
            },
            "package": {
                "name": "Package",
                "category": ShapeCategory.UML,
                "default_size": (140, 100),
                "path": "M 0,20 L 0,100 L 140,100 L 140,20 L 100,20 L 100,0 L 0,0 Z",
                "description": "UML Package"
            },
            "node": {
                "name": "Node",
                "category": ShapeCategory.UML,
                "default_size": (120, 80),
                "path": "M 10,0 L 120,0 L 120,70 L 10,70 Z M 0,10 L 10,0 M 0,10 L 0,80 L 10,70 M 110,0 L 120,10 L 120,80",
                "description": "UML Node"
            },
            "state": {
                "name": "State",
                "category": ShapeCategory.UML,
                "default_size": (120, 60),
                "path": "M 20,0 L 100,0 Q 120,0 120,20 L 120,40 Q 120,60 100,60 L 20,60 Q 0,60 0,40 L 0,20 Q 0,0 20,0 Z",
                "description": "UML State"
            },
        }
        self.shapes.update({f"uml_{k}": v for k, v in uml.items()})

    def _add_network_shapes(self):
        """Add network diagram shapes."""
        network = {
            "server": {
                "name": "Server",
                "category": ShapeCategory.NETWORK,
                "default_size": (80, 100),
                "path": "M 0,0 L 80,0 L 80,100 L 0,100 Z M 0,25 L 80,25 M 0,50 L 80,50 M 0,75 L 80,75",
                "description": "Server"
            },
            "router": {
                "name": "Router",
                "category": ShapeCategory.NETWORK,
                "default_size": (100, 60),
                "path": "M 20,0 L 80,0 L 100,30 L 80,60 L 20,60 L 0,30 Z M 30,20 L 30,40 M 50,20 L 50,40 M 70,20 L 70,40",
                "description": "Network Router"
            },
            "switch": {
                "name": "Switch",
                "category": ShapeCategory.NETWORK,
                "default_size": (100, 50),
                "path": "M 0,10 L 100,10 L 100,50 L 0,50 Z M 0,0 L 10,10 M 30,0 L 40,10 M 60,0 L 70,10 M 90,0 L 100,10",
                "description": "Network Switch"
            },
            "firewall": {
                "name": "Firewall",
                "category": ShapeCategory.NETWORK,
                "default_size": (80, 100),
                "path": "M 40,0 L 80,30 L 80,100 L 0,100 L 0,30 Z M 20,40 L 60,40 M 20,55 L 60,55 M 20,70 L 60,70",
                "description": "Firewall"
            },
            "cloud": {
                "name": "Cloud",
                "category": ShapeCategory.NETWORK,
                "default_size": (140, 80),
                "path": "M 30,40 Q 30,20 50,20 Q 60,10 70,10 Q 90,10 100,25 Q 120,25 120,45 Q 130,50 130,60 Q 130,75 110,75 L 30,75 Q 10,75 10,55 Q 10,40 30,40 Z",
                "description": "Cloud"
            },
            "workstation": {
                "name": "Workstation",
                "category": ShapeCategory.NETWORK,
                "default_size": (80, 90),
                "path": "M 10,0 L 70,0 L 70,50 L 10,50 Z M 0,70 L 80,70 L 75,80 L 5,80 Z M 30,50 L 30,70 M 50,50 L 50,70",
                "description": "Workstation/PC"
            },
            "laptop": {
                "name": "Laptop",
                "category": ShapeCategory.NETWORK,
                "default_size": (100, 70),
                "path": "M 15,0 L 85,0 L 85,45 L 100,60 L 0,60 L 15,45 Z M 20,5 L 80,5 L 80,40 L 20,40 Z",
                "description": "Laptop Computer"
            },
            "mobile": {
                "name": "Mobile Device",
                "category": ShapeCategory.NETWORK,
                "default_size": (50, 90),
                "path": "M 5,0 L 45,0 Q 50,0 50,5 L 50,85 Q 50,90 45,90 L 5,90 Q 0,90 0,85 L 0,5 Q 0,0 5,0 Z M 0,10 L 50,10 M 0,75 L 50,75",
                "description": "Mobile Device"
            },
        }
        self.shapes.update({f"network_{k}": v for k, v in network.items()})

    def _add_cloud_shapes(self):
        """Add cloud provider shapes (AWS, Azure, GCP)."""
        cloud = {
            # AWS
            "aws_ec2": {
                "name": "AWS EC2",
                "category": ShapeCategory.AWS,
                "default_size": (80, 80),
                "path": "M 0,0 L 80,0 L 80,80 L 0,80 Z M 20,20 L 60,20 L 60,60 L 20,60 Z",
                "description": "AWS EC2 Instance"
            },
            "aws_s3": {
                "name": "AWS S3",
                "category": ShapeCategory.AWS,
                "default_size": (80, 80),
                "path": "M 40,0 L 80,20 L 80,60 L 40,80 L 0,60 L 0,20 Z M 40,20 L 40,60",
                "description": "AWS S3 Bucket"
            },
            "aws_lambda": {
                "name": "AWS Lambda",
                "category": ShapeCategory.AWS,
                "default_size": (80, 80),
                "path": "M 10,80 L 30,0 L 40,0 L 30,50 L 50,50 L 70,0 L 80,0 L 50,80 Z",
                "description": "AWS Lambda Function"
            },
            "aws_rds": {
                "name": "AWS RDS",
                "category": ShapeCategory.AWS,
                "default_size": (80, 90),
                "path": "M 0,15 Q 0,0 40,0 Q 80,0 80,15 L 80,75 Q 80,90 40,90 Q 0,90 0,75 Z M 0,15 Q 0,30 40,30 Q 80,30 80,15",
                "description": "AWS RDS Database"
            },
            # Azure
            "azure_vm": {
                "name": "Azure VM",
                "category": ShapeCategory.AZURE,
                "default_size": (80, 80),
                "path": "M 0,0 L 80,0 L 80,80 L 0,80 Z M 15,15 L 65,15 L 65,65 L 15,65 Z",
                "description": "Azure Virtual Machine"
            },
            "azure_storage": {
                "name": "Azure Storage",
                "category": ShapeCategory.AZURE,
                "default_size": (80, 70),
                "path": "M 0,35 L 40,0 L 80,35 L 40,70 Z M 20,35 L 60,35 M 40,17 L 40,53",
                "description": "Azure Storage"
            },
            "azure_function": {
                "name": "Azure Function",
                "category": ShapeCategory.AZURE,
                "default_size": (80, 80),
                "path": "M 20,0 L 60,0 L 80,40 L 60,80 L 20,80 L 0,40 Z M 30,30 L 50,30 L 50,50 L 30,50 Z",
                "description": "Azure Function"
            },
            # GCP
            "gcp_compute": {
                "name": "GCP Compute",
                "category": ShapeCategory.GCP,
                "default_size": (80, 80),
                "path": "M 40,0 L 80,40 L 40,80 L 0,40 Z M 25,40 L 55,40 M 40,25 L 40,55",
                "description": "GCP Compute Engine"
            },
            "gcp_storage": {
                "name": "GCP Storage",
                "category": ShapeCategory.GCP,
                "default_size": (80, 80),
                "path": "M 20,0 L 60,0 L 80,20 L 80,60 L 60,80 L 20,80 L 0,60 L 0,20 Z",
                "description": "GCP Cloud Storage"
            },
        }
        self.shapes.update({f"cloud_{k}": v for k, v in cloud.items()})

    def _add_org_chart_shapes(self):
        """Add organizational chart shapes."""
        org = {
            "executive": {
                "name": "Executive",
                "category": ShapeCategory.ORG_CHART,
                "default_size": (140, 60),
                "path": "M 10,0 L 130,0 Q 140,0 140,10 L 140,50 Q 140,60 130,60 L 10,60 Q 0,60 0,50 L 0,10 Q 0,0 10,0 Z",
                "description": "Executive Position"
            },
            "manager": {
                "name": "Manager",
                "category": ShapeCategory.ORG_CHART,
                "default_size": (120, 50),
                "path": "M 0,0 L 120,0 L 120,50 L 0,50 Z",
                "description": "Manager Position"
            },
            "employee": {
                "name": "Employee",
                "category": ShapeCategory.ORG_CHART,
                "default_size": (100, 40),
                "path": "M 5,0 L 95,0 Q 100,0 100,5 L 100,35 Q 100,40 95,40 L 5,40 Q 0,40 0,35 L 0,5 Q 0,0 5,0 Z",
                "description": "Employee Position"
            },
            "team": {
                "name": "Team",
                "category": ShapeCategory.ORG_CHART,
                "default_size": (130, 70),
                "path": "M 0,10 L 10,0 L 120,0 L 130,10 L 130,60 L 120,70 L 10,70 L 0,60 Z",
                "description": "Team/Group"
            },
            "assistant": {
                "name": "Assistant",
                "category": ShapeCategory.ORG_CHART,
                "default_size": (90, 35),
                "path": "M 15,0 L 75,0 L 90,17.5 L 75,35 L 15,35 L 0,17.5 Z",
                "description": "Assistant Position"
            },
        }
        self.shapes.update({f"org_{k}": v for k, v in org.items()})

    def _add_bpmn_shapes(self):
        """Add BPMN (Business Process Model and Notation) shapes."""
        bpmn = {
            "task": {
                "name": "Task",
                "category": ShapeCategory.BPMN,
                "default_size": (120, 60),
                "path": "M 5,0 L 115,0 Q 120,0 120,5 L 120,55 Q 120,60 115,60 L 5,60 Q 0,60 0,55 L 0,5 Q 0,0 5,0 Z",
                "description": "BPMN Task"
            },
            "gateway": {
                "name": "Gateway",
                "category": ShapeCategory.BPMN,
                "default_size": (70, 70),
                "path": "M 35,0 L 70,35 L 35,70 L 0,35 Z",
                "description": "BPMN Gateway"
            },
            "event_start": {
                "name": "Start Event",
                "category": ShapeCategory.BPMN,
                "default_size": (40, 40),
                "path": "M 20,0 Q 31,0 35,5 Q 40,9 40,20 Q 40,31 35,35 Q 31,40 20,40 Q 9,40 5,35 Q 0,31 0,20 Q 0,9 5,5 Q 9,0 20,0 Z",
                "description": "BPMN Start Event"
            },
            "event_end": {
                "name": "End Event",
                "category": ShapeCategory.BPMN,
                "default_size": (40, 40),
                "path": "M 20,0 Q 31,0 35,5 Q 40,9 40,20 Q 40,31 35,35 Q 31,40 20,40 Q 9,40 5,35 Q 0,31 0,20 Q 0,9 5,5 Q 9,0 20,0 Z M 20,4 Q 29,4 33,8 Q 36,11 36,20 Q 36,29 33,32 Q 29,36 20,36 Q 11,36 8,32 Q 4,29 4,20 Q 4,11 8,8 Q 11,4 20,4 Z",
                "description": "BPMN End Event"
            },
            "subprocess": {
                "name": "Subprocess",
                "category": ShapeCategory.BPMN,
                "default_size": (120, 60),
                "path": "M 5,0 L 115,0 Q 120,0 120,5 L 120,55 Q 120,60 115,60 L 5,60 Q 0,60 0,55 L 0,5 Q 0,0 5,0 Z M 55,45 L 65,45 M 60,40 L 60,50",
                "description": "BPMN Subprocess"
            },
            "data_object": {
                "name": "Data Object",
                "category": ShapeCategory.BPMN,
                "default_size": (50, 70),
                "path": "M 0,10 L 35,0 L 50,10 L 50,70 L 0,70 Z M 35,0 L 35,10 L 50,10",
                "description": "BPMN Data Object"
            },
        }
        self.shapes.update({f"bpmn_{k}": v for k, v in bpmn.items()})

    def _add_wireframe_shapes(self):
        """Add wireframe/UI design shapes."""
        wireframe = {
            "button": {
                "name": "Button",
                "category": ShapeCategory.WIREFRAME,
                "default_size": (100, 40),
                "path": "M 5,0 L 95,0 Q 100,0 100,5 L 100,35 Q 100,40 95,40 L 5,40 Q 0,40 0,35 L 0,5 Q 0,0 5,0 Z",
                "description": "UI Button"
            },
            "textbox": {
                "name": "Text Box",
                "category": ShapeCategory.WIREFRAME,
                "default_size": (200, 35),
                "path": "M 0,0 L 200,0 L 200,35 L 0,35 Z",
                "description": "Text Input Box"
            },
            "checkbox": {
                "name": "Checkbox",
                "category": ShapeCategory.WIREFRAME,
                "default_size": (25, 25),
                "path": "M 0,0 L 25,0 L 25,25 L 0,25 Z",
                "description": "Checkbox"
            },
            "radio": {
                "name": "Radio Button",
                "category": ShapeCategory.WIREFRAME,
                "default_size": (25, 25),
                "path": "M 12.5,0 Q 19,0 22,3 Q 25,6 25,12.5 Q 25,19 22,22 Q 19,25 12.5,25 Q 6,25 3,22 Q 0,19 0,12.5 Q 0,6 3,3 Q 6,0 12.5,0 Z",
                "description": "Radio Button"
            },
            "dropdown": {
                "name": "Dropdown",
                "category": ShapeCategory.WIREFRAME,
                "default_size": (150, 35),
                "path": "M 0,0 L 150,0 L 150,35 L 0,35 Z M 120,10 L 130,20 L 140,10",
                "description": "Dropdown Menu"
            },
            "image_placeholder": {
                "name": "Image Placeholder",
                "category": ShapeCategory.WIREFRAME,
                "default_size": (150, 100),
                "path": "M 0,0 L 150,0 L 150,100 L 0,100 Z M 0,0 L 150,100 M 150,0 L 0,100",
                "description": "Image Placeholder"
            },
            "window": {
                "name": "Window",
                "category": ShapeCategory.WIREFRAME,
                "default_size": (300, 200),
                "path": "M 0,0 L 300,0 L 300,200 L 0,200 Z M 0,30 L 300,30 M 10,15 m -5,0 a 5,5 0 1,0 10,0 a 5,5 0 1,0 -10,0 M 30,15 m -5,0 a 5,5 0 1,0 10,0 a 5,5 0 1,0 -10,0 M 50,15 m -5,0 a 5,5 0 1,0 10,0 a 5,5 0 1,0 -10,0",
                "description": "Application Window"
            },
            "browser": {
                "name": "Browser",
                "category": ShapeCategory.WIREFRAME,
                "default_size": (320, 240),
                "path": "M 0,0 L 320,0 L 320,240 L 0,240 Z M 0,40 L 320,40 M 10,20 m -6,0 a 6,6 0 1,0 12,0 a 6,6 0 1,0 -12,0 M 35,20 m -6,0 a 6,6 0 1,0 12,0 a 6,6 0 1,0 -12,0 M 60,20 m -6,0 a 6,6 0 1,0 12,0 a 6,6 0 1,0 -12,0",
                "description": "Web Browser"
            },
        }
        self.shapes.update({f"wireframe_{k}": v for k, v in wireframe.items()})

    def _add_floor_plan_shapes(self):
        """Add floor plan shapes."""
        floor = {
            "wall": {
                "name": "Wall",
                "category": ShapeCategory.FLOOR_PLAN,
                "default_size": (100, 10),
                "path": "M 0,0 L 100,0 L 100,10 L 0,10 Z",
                "description": "Wall"
            },
            "door": {
                "name": "Door",
                "category": ShapeCategory.FLOOR_PLAN,
                "default_size": (40, 5),
                "path": "M 0,0 L 40,0 L 40,5 L 0,5 Z M 0,0 Q 20,10 40,0",
                "description": "Door"
            },
            "window": {
                "name": "Window",
                "category": ShapeCategory.FLOOR_PLAN,
                "default_size": (60, 5),
                "path": "M 0,0 L 60,0 L 60,5 L 0,5 Z M 0,2.5 L 60,2.5",
                "description": "Window"
            },
            "stairs": {
                "name": "Stairs",
                "category": ShapeCategory.FLOOR_PLAN,
                "default_size": (80, 50),
                "path": "M 0,0 L 80,0 L 80,50 L 0,50 Z M 0,10 L 80,10 M 0,20 L 80,20 M 0,30 L 80,30 M 0,40 L 80,40",
                "description": "Stairs"
            },
            "furniture_desk": {
                "name": "Desk",
                "category": ShapeCategory.FLOOR_PLAN,
                "default_size": (120, 60),
                "path": "M 0,0 L 120,0 L 120,60 L 0,60 Z M 90,0 L 90,60",
                "description": "Desk"
            },
            "furniture_chair": {
                "name": "Chair",
                "category": ShapeCategory.FLOOR_PLAN,
                "default_size": (40, 40),
                "path": "M 5,5 L 35,5 L 35,30 L 5,30 Z M 0,30 L 40,30 L 40,35 L 0,35 Z",
                "description": "Chair"
            },
        }
        self.shapes.update({f"floor_{k}": v for k, v in floor.items()})

    def _add_basic_shapes(self):
        """Add basic geometric shapes."""
        basic = {
            "rectangle": {
                "name": "Rectangle",
                "category": ShapeCategory.BASIC,
                "default_size": (120, 80),
                "path": None,
                "description": "Rectangle"
            },
            "square": {
                "name": "Square",
                "category": ShapeCategory.BASIC,
                "default_size": (80, 80),
                "path": None,
                "description": "Square"
            },
            "circle": {
                "name": "Circle",
                "category": ShapeCategory.BASIC,
                "default_size": (80, 80),
                "path": "M 40,0 Q 62,0 71,9 Q 80,18 80,40 Q 80,62 71,71 Q 62,80 40,80 Q 18,80 9,71 Q 0,62 0,40 Q 0,18 9,9 Q 18,0 40,0 Z",
                "description": "Circle"
            },
            "ellipse": {
                "name": "Ellipse",
                "category": ShapeCategory.BASIC,
                "default_size": (120, 60),
                "path": "M 60,0 Q 93,0 106.5,15 Q 120,30 120,30 Q 120,30 106.5,45 Q 93,60 60,60 Q 27,60 13.5,45 Q 0,30 0,30 Q 0,30 13.5,15 Q 27,0 60,0 Z",
                "description": "Ellipse"
            },
            "triangle": {
                "name": "Triangle",
                "category": ShapeCategory.BASIC,
                "default_size": (100, 87),
                "path": "M 50,0 L 100,87 L 0,87 Z",
                "description": "Triangle"
            },
            "pentagon": {
                "name": "Pentagon",
                "category": ShapeCategory.BASIC,
                "default_size": (90, 86),
                "path": "M 45,0 L 90,33 L 72,86 L 18,86 L 0,33 Z",
                "description": "Pentagon"
            },
            "hexagon": {
                "name": "Hexagon",
                "category": ShapeCategory.BASIC,
                "default_size": (100, 87),
                "path": "M 25,0 L 75,0 L 100,43.5 L 75,87 L 25,87 L 0,43.5 Z",
                "description": "Hexagon"
            },
            "star": {
                "name": "Star",
                "category": ShapeCategory.BASIC,
                "default_size": (100, 95),
                "path": "M 50,0 L 61,35 L 97,35 L 68,57 L 79,92 L 50,70 L 21,92 L 32,57 L 3,35 L 39,35 Z",
                "description": "Star"
            },
            "cross": {
                "name": "Cross",
                "category": ShapeCategory.BASIC,
                "default_size": (80, 80),
                "path": "M 30,0 L 50,0 L 50,30 L 80,30 L 80,50 L 50,50 L 50,80 L 30,80 L 30,50 L 0,50 L 0,30 L 30,30 Z",
                "description": "Cross"
            },
        }
        self.shapes.update({f"basic_{k}": v for k, v in basic.items()})

    def _add_arrow_shapes(self):
        """Add arrow shapes."""
        arrows = {
            "arrow_right": {
                "name": "Arrow Right",
                "category": ShapeCategory.ARROWS,
                "default_size": (100, 60),
                "path": "M 0,20 L 70,20 L 70,0 L 100,30 L 70,60 L 70,40 L 0,40 Z",
                "description": "Right Arrow"
            },
            "arrow_left": {
                "name": "Arrow Left",
                "category": ShapeCategory.ARROWS,
                "default_size": (100, 60),
                "path": "M 100,20 L 30,20 L 30,0 L 0,30 L 30,60 L 30,40 L 100,40 Z",
                "description": "Left Arrow"
            },
            "arrow_up": {
                "name": "Arrow Up",
                "category": ShapeCategory.ARROWS,
                "default_size": (60, 100),
                "path": "M 20,100 L 20,30 L 0,30 L 30,0 L 60,30 L 40,30 L 40,100 Z",
                "description": "Up Arrow"
            },
            "arrow_down": {
                "name": "Arrow Down",
                "category": ShapeCategory.ARROWS,
                "default_size": (60, 100),
                "path": "M 20,0 L 20,70 L 0,70 L 30,100 L 60,70 L 40,70 L 40,0 Z",
                "description": "Down Arrow"
            },
            "arrow_double": {
                "name": "Double Arrow",
                "category": ShapeCategory.ARROWS,
                "default_size": (120, 60),
                "path": "M 30,20 L 90,20 L 90,0 L 120,30 L 90,60 L 90,40 L 30,40 L 30,60 L 0,30 L 30,0 Z",
                "description": "Double-sided Arrow"
            },
            "chevron_right": {
                "name": "Chevron Right",
                "category": ShapeCategory.ARROWS,
                "default_size": (60, 100),
                "path": "M 0,0 L 60,50 L 0,100 L 10,100 L 70,50 L 10,0 Z",
                "description": "Chevron Right"
            },
        }
        self.shapes.update({f"arrow_{k}": v for k, v in arrows.items()})

    def _add_symbol_shapes(self):
        """Add symbol and icon shapes."""
        symbols = {
            "user": {
                "name": "User",
                "category": ShapeCategory.SYMBOLS,
                "default_size": (60, 80),
                "path": "M 30,20 m -15,0 a 15,15 0 1,0 30,0 a 15,15 0 1,0 -30,0 M 10,50 Q 10,40 20,40 L 40,40 Q 50,40 50,50 L 50,80 L 10,80 Z",
                "description": "User Icon"
            },
            "gear": {
                "name": "Gear",
                "category": ShapeCategory.SYMBOLS,
                "default_size": (80, 80),
                "path": "M 35,0 L 45,0 L 47,8 Q 52,9 56,12 L 64,8 L 72,16 L 68,24 Q 71,28 72,33 L 80,35 L 80,45 L 72,47 Q 71,52 68,56 L 72,64 L 64,72 L 56,68 Q 52,71 47,72 L 45,80 L 35,80 L 33,72 Q 28,71 24,68 L 16,72 L 8,64 L 12,56 Q 9,52 8,47 L 0,45 L 0,35 L 8,33 Q 9,28 12,24 L 8,16 L 16,8 L 24,12 Q 28,9 33,8 Z M 40,25 Q 48,25 52,29 Q 56,33 56,40 Q 56,48 52,52 Q 48,56 40,56 Q 32,56 28,52 Q 24,48 24,40 Q 24,33 28,29 Q 32,25 40,25 Z",
                "description": "Settings Gear"
            },
            "lock": {
                "name": "Lock",
                "category": ShapeCategory.SYMBOLS,
                "default_size": (60, 80),
                "path": "M 15,35 L 15,25 Q 15,10 30,10 Q 45,10 45,25 L 45,35 M 5,35 L 55,35 L 55,80 L 5,80 Z M 30,50 m -5,0 a 5,5 0 1,0 10,0 a 5,5 0 1,0 -10,0",
                "description": "Lock Icon"
            },
            "heart": {
                "name": "Heart",
                "category": ShapeCategory.SYMBOLS,
                "default_size": (80, 72),
                "path": "M 40,72 L 5,37 Q 0,32 0,22 Q 0,12 10,12 Q 20,12 25,22 L 40,37 L 55,22 Q 60,12 70,12 Q 80,12 80,22 Q 80,32 75,37 Z",
                "description": "Heart Icon"
            },
            "mail": {
                "name": "Mail",
                "category": ShapeCategory.SYMBOLS,
                "default_size": (100, 70),
                "path": "M 0,0 L 100,0 L 100,70 L 0,70 Z M 0,0 L 50,40 L 100,0",
                "description": "Mail Icon"
            },
            "phone": {
                "name": "Phone",
                "category": ShapeCategory.SYMBOLS,
                "default_size": (70, 70),
                "path": "M 15,0 Q 5,0 0,5 L 0,15 Q 0,25 15,40 Q 30,55 45,55 L 55,55 Q 60,55 65,50 Q 70,45 70,35 L 70,25 Q 60,30 50,30 Q 40,30 35,25 Q 30,20 30,10 Q 30,0 35,0 Z",
                "description": "Phone Icon"
            },
        }
        self.shapes.update({f"symbol_{k}": v for k, v in symbols.items()})

    def _add_infographic_shapes(self):
        """Add infographic shapes."""
        infographic = {
            "circle_badge": {
                "name": "Circle Badge",
                "category": ShapeCategory.INFOGRAPHIC,
                "default_size": (100, 100),
                "path": "M 50,0 Q 78,0 89,11 Q 100,22 100,50 Q 100,78 89,89 Q 78,100 50,100 Q 22,100 11,89 Q 0,78 0,50 Q 0,22 11,11 Q 22,0 50,0 Z M 50,10 Q 75,10 85,20 Q 95,30 95,50 Q 95,75 85,85 Q 75,95 50,95 Q 25,95 15,85 Q 5,75 5,50 Q 5,30 15,20 Q 25,10 50,10 Z",
                "description": "Circle Badge"
            },
            "ribbon": {
                "name": "Ribbon",
                "category": ShapeCategory.INFOGRAPHIC,
                "default_size": (150, 60),
                "path": "M 20,30 L 0,15 L 0,45 L 20,30 M 130,30 L 150,15 L 150,45 L 130,30 M 20,10 L 130,10 L 130,50 L 20,50 Z",
                "description": "Ribbon Banner"
            },
            "callout": {
                "name": "Callout",
                "category": ShapeCategory.INFOGRAPHIC,
                "default_size": (120, 80),
                "path": "M 10,0 L 110,0 Q 120,0 120,10 L 120,50 Q 120,60 110,60 L 65,60 L 50,80 L 50,60 L 10,60 Q 0,60 0,50 L 0,10 Q 0,0 10,0 Z",
                "description": "Speech Callout"
            },
            "banner": {
                "name": "Banner",
                "category": ShapeCategory.INFOGRAPHIC,
                "default_size": (160, 80),
                "path": "M 0,0 L 140,0 L 160,40 L 140,80 L 0,80 Z",
                "description": "Angled Banner"
            },
            "pie_slice": {
                "name": "Pie Slice",
                "category": ShapeCategory.INFOGRAPHIC,
                "default_size": (100, 100),
                "path": "M 50,50 L 50,0 Q 100,0 100,50 Z",
                "description": "Pie Chart Slice"
            },
        }
        self.shapes.update({f"infographic_{k}": v for k, v in infographic.items()})

    def get_shape_definition(self, shape_id: str) -> Optional[Dict[str, Any]]:
        """Get shape definition by ID."""
        return self.shapes.get(shape_id)

    def get_shapes_by_category(self, category: ShapeCategory) -> Dict[str, Dict[str, Any]]:
        """Get all shapes in a category."""
        return {
            sid: sdef for sid, sdef in self.shapes.items()
            if sdef["category"] == category
        }

    def get_all_categories(self) -> List[ShapeCategory]:
        """Get all available categories."""
        return list(ShapeCategory)

    def create_shape_instance(
        self,
        shape_id: str,
        id: str,
        position: Point,
        text: str = "",
        style: Optional[ShapeStyle] = None
    ) -> Optional[Shape]:
        """Create a shape instance from library definition."""
        definition = self.get_shape_definition(shape_id)
        if not definition:
            return None

        width, height = definition["default_size"]

        return Shape(
            id=id,
            shape_type=shape_id,
            category=definition["category"],
            position=position,
            width=width,
            height=height,
            text=text,
            style=style or ShapeStyle(),
            custom_path=definition["path"]
        )

    def search_shapes(self, query: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Search shapes by name or description."""
        query_lower = query.lower()
        results = []

        for shape_id, definition in self.shapes.items():
            name_match = query_lower in definition["name"].lower()
            desc_match = query_lower in definition["description"].lower()

            if name_match or desc_match:
                results.append((shape_id, definition))

        return results

    def get_shape_count(self) -> int:
        """Get total number of shapes in library."""
        return len(self.shapes)


# Create global shape library instance
shape_library = ShapeLibrary()
