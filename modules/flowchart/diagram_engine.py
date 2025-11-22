"""
Core diagram engine for managing shapes, connectors, and diagram operations.
Provides the main API for creating and manipulating diagrams.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
import json
import uuid
from datetime import datetime
from collections import defaultdict

from .shapes import Shape, Point, ShapeStyle, ConnectorAnchor, shape_library
from .connectors import Connector, ConnectorStyle, ConnectorType, ConnectorRouter


@dataclass
class Layer:
    """Diagram layer for organizing shapes and connectors."""
    id: int
    name: str
    visible: bool = True
    locked: bool = False
    opacity: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "visible": self.visible,
            "locked": self.locked,
            "opacity": self.opacity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Layer":
        return cls(**data)


@dataclass
class DiagramMetadata:
    """Metadata for a diagram."""
    title: str = "Untitled Diagram"
    description: str = ""
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    tags: List[str] = field(default_factory=list)
    custom_properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "version": self.version,
            "tags": self.tags,
            "custom_properties": self.custom_properties
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagramMetadata":
        return cls(**data)


@dataclass
class DiagramSettings:
    """Settings for diagram canvas and behavior."""
    canvas_width: float = 2000.0
    canvas_height: float = 2000.0
    grid_size: int = 20
    grid_visible: bool = True
    snap_to_grid: bool = True
    snap_to_shapes: bool = True
    snap_threshold: float = 10.0
    background_color: str = "#FFFFFF"
    show_rulers: bool = True
    show_guides: bool = True
    zoom_level: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "grid_size": self.grid_size,
            "grid_visible": self.grid_visible,
            "snap_to_grid": self.snap_to_grid,
            "snap_to_shapes": self.snap_to_shapes,
            "snap_threshold": self.snap_threshold,
            "background_color": self.background_color,
            "show_rulers": self.show_rulers,
            "show_guides": self.show_guides,
            "zoom_level": self.zoom_level,
            "pan_x": self.pan_x,
            "pan_y": self.pan_y
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagramSettings":
        return cls(**data)


class DiagramEngine:
    """Main engine for managing diagrams."""

    def __init__(self):
        self.shapes: Dict[str, Shape] = {}
        self.connectors: Dict[str, Connector] = {}
        self.layers: Dict[int, Layer] = {0: Layer(id=0, name="Default")}
        self.metadata = DiagramMetadata()
        self.settings = DiagramSettings()
        self.selection: Set[str] = set()  # Selected shape/connector IDs
        self.history: List[Dict[str, Any]] = []  # Undo/redo history
        self.history_index: int = -1
        self.max_history: int = 50

    # Shape Management

    def add_shape(
        self,
        shape_type: str,
        position: Point,
        text: str = "",
        style: Optional[ShapeStyle] = None,
        layer: int = 0
    ) -> Optional[Shape]:
        """Add a new shape to the diagram."""
        shape_id = str(uuid.uuid4())
        shape = shape_library.create_shape_instance(
            shape_type, shape_id, position, text, style
        )

        if shape:
            shape.layer = layer
            self.shapes[shape_id] = shape
            self._record_history("add_shape", {"shape_id": shape_id})
            self._update_modified_time()
            return shape

        return None

    def remove_shape(self, shape_id: str) -> bool:
        """Remove a shape from the diagram."""
        if shape_id not in self.shapes:
            return False

        # Remove shape
        shape = self.shapes.pop(shape_id)

        # Remove connected connectors
        connectors_to_remove = [
            cid for cid, conn in self.connectors.items()
            if conn.source_shape_id == shape_id or conn.target_shape_id == shape_id
        ]

        for cid in connectors_to_remove:
            self.connectors.pop(cid)

        # Remove from selection
        self.selection.discard(shape_id)

        self._record_history("remove_shape", {
            "shape_id": shape_id,
            "shape_data": shape.to_dict(),
            "removed_connectors": [
                self.connectors.get(cid, Connector(id=cid, connector_type=ConnectorType.STRAIGHT)).to_dict()
                for cid in connectors_to_remove
            ]
        })
        self._update_modified_time()
        return True

    def get_shape(self, shape_id: str) -> Optional[Shape]:
        """Get a shape by ID."""
        return self.shapes.get(shape_id)

    def update_shape(
        self,
        shape_id: str,
        position: Optional[Point] = None,
        width: Optional[float] = None,
        height: Optional[float] = None,
        rotation: Optional[float] = None,
        text: Optional[str] = None,
        style: Optional[ShapeStyle] = None
    ) -> bool:
        """Update shape properties."""
        if shape_id not in self.shapes:
            return False

        shape = self.shapes[shape_id]
        old_data = shape.to_dict()

        if position is not None:
            shape.position = position
        if width is not None:
            shape.width = width
        if height is not None:
            shape.height = height
        if rotation is not None:
            shape.rotation = rotation
        if text is not None:
            shape.text = text
        if style is not None:
            shape.style = style

        self._record_history("update_shape", {
            "shape_id": shape_id,
            "old_data": old_data,
            "new_data": shape.to_dict()
        })
        self._update_modified_time()
        return True

    def move_shape(self, shape_id: str, dx: float, dy: float) -> bool:
        """Move a shape by delta x and y."""
        if shape_id not in self.shapes:
            return False

        shape = self.shapes[shape_id]
        new_position = Point(shape.position.x + dx, shape.position.y + dy)

        # Snap to grid if enabled
        if self.settings.snap_to_grid:
            new_position = self._snap_to_grid(new_position)

        return self.update_shape(shape_id, position=new_position)

    def resize_shape(
        self,
        shape_id: str,
        width: float,
        height: float
    ) -> bool:
        """Resize a shape."""
        return self.update_shape(shape_id, width=width, height=height)

    def rotate_shape(self, shape_id: str, angle: float) -> bool:
        """Rotate a shape by angle in degrees."""
        if shape_id not in self.shapes:
            return False

        shape = self.shapes[shape_id]
        new_rotation = (shape.rotation + angle) % 360
        return self.update_shape(shape_id, rotation=new_rotation)

    # Connector Management

    def add_connector(
        self,
        connector_type: ConnectorType,
        source_shape_id: Optional[str] = None,
        target_shape_id: Optional[str] = None,
        source_anchor: Optional[ConnectorAnchor] = None,
        target_anchor: Optional[ConnectorAnchor] = None,
        source_point: Optional[Point] = None,
        target_point: Optional[Point] = None,
        style: Optional[ConnectorStyle] = None,
        layer: int = 0,
        auto_route: bool = True
    ) -> Optional[Connector]:
        """Add a new connector to the diagram."""
        connector_id = str(uuid.uuid4())

        # Auto-determine anchors if connecting shapes
        if auto_route and source_shape_id and target_shape_id:
            source_shape = self.shapes.get(source_shape_id)
            target_shape = self.shapes.get(target_shape_id)

            if source_shape and target_shape and not source_anchor and not target_anchor:
                source_anchor, target_anchor = ConnectorRouter.find_best_anchors(
                    source_shape, target_shape
                )

        connector = Connector(
            id=connector_id,
            connector_type=connector_type,
            source_shape_id=source_shape_id,
            target_shape_id=target_shape_id,
            source_anchor=source_anchor,
            target_anchor=target_anchor,
            source_point=source_point,
            target_point=target_point,
            style=style or ConnectorStyle(),
            layer=layer
        )

        self.connectors[connector_id] = connector
        self._record_history("add_connector", {"connector_id": connector_id})
        self._update_modified_time()
        return connector

    def remove_connector(self, connector_id: str) -> bool:
        """Remove a connector from the diagram."""
        if connector_id not in self.connectors:
            return False

        connector = self.connectors.pop(connector_id)
        self.selection.discard(connector_id)

        self._record_history("remove_connector", {
            "connector_id": connector_id,
            "connector_data": connector.to_dict()
        })
        self._update_modified_time()
        return True

    def get_connector(self, connector_id: str) -> Optional[Connector]:
        """Get a connector by ID."""
        return self.connectors.get(connector_id)

    def update_connector(
        self,
        connector_id: str,
        connector_type: Optional[ConnectorType] = None,
        style: Optional[ConnectorStyle] = None,
        waypoints: Optional[List[Point]] = None
    ) -> bool:
        """Update connector properties."""
        if connector_id not in self.connectors:
            return False

        connector = self.connectors[connector_id]
        old_data = connector.to_dict()

        if connector_type is not None:
            connector.connector_type = connector_type
        if style is not None:
            connector.style = style
        if waypoints is not None:
            connector.waypoints = waypoints

        self._record_history("update_connector", {
            "connector_id": connector_id,
            "old_data": old_data,
            "new_data": connector.to_dict()
        })
        self._update_modified_time()
        return True

    def get_connected_shapes(self, shape_id: str) -> List[Tuple[str, Connector]]:
        """Get all shapes connected to a given shape."""
        connected = []

        for conn_id, connector in self.connectors.items():
            if connector.source_shape_id == shape_id:
                if connector.target_shape_id:
                    connected.append((connector.target_shape_id, connector))
            elif connector.target_shape_id == shape_id:
                if connector.source_shape_id:
                    connected.append((connector.source_shape_id, connector))

        return connected

    # Layer Management

    def add_layer(self, name: str) -> Layer:
        """Add a new layer."""
        layer_id = max(self.layers.keys()) + 1 if self.layers else 0
        layer = Layer(id=layer_id, name=name)
        self.layers[layer_id] = layer
        self._update_modified_time()
        return layer

    def remove_layer(self, layer_id: int) -> bool:
        """Remove a layer (moves items to default layer)."""
        if layer_id not in self.layers or layer_id == 0:
            return False

        # Move all shapes and connectors to default layer
        for shape in self.shapes.values():
            if shape.layer == layer_id:
                shape.layer = 0

        for connector in self.connectors.values():
            if connector.layer == layer_id:
                connector.layer = 0

        del self.layers[layer_id]
        self._update_modified_time()
        return True

    def get_layer_items(self, layer_id: int) -> Tuple[List[Shape], List[Connector]]:
        """Get all shapes and connectors in a layer."""
        shapes = [s for s in self.shapes.values() if s.layer == layer_id]
        connectors = [c for c in self.connectors.values() if c.layer == layer_id]
        return shapes, connectors

    def set_layer_visibility(self, layer_id: int, visible: bool) -> bool:
        """Set layer visibility."""
        if layer_id not in self.layers:
            return False

        self.layers[layer_id].visible = visible
        return True

    def set_layer_locked(self, layer_id: int, locked: bool) -> bool:
        """Set layer locked status."""
        if layer_id not in self.layers:
            return False

        self.layers[layer_id].locked = locked
        return True

    # Selection Management

    def select(self, item_id: str) -> bool:
        """Select a shape or connector."""
        if item_id in self.shapes or item_id in self.connectors:
            self.selection.add(item_id)
            return True
        return False

    def deselect(self, item_id: str) -> bool:
        """Deselect a shape or connector."""
        if item_id in self.selection:
            self.selection.remove(item_id)
            return True
        return False

    def select_all(self):
        """Select all shapes and connectors."""
        self.selection = set(self.shapes.keys()) | set(self.connectors.keys())

    def clear_selection(self):
        """Clear all selections."""
        self.selection.clear()

    def get_selected_items(self) -> Tuple[List[Shape], List[Connector]]:
        """Get all selected shapes and connectors."""
        shapes = [self.shapes[sid] for sid in self.selection if sid in self.shapes]
        connectors = [self.connectors[cid] for cid in self.selection if cid in self.connectors]
        return shapes, connectors

    # Utility Methods

    def _snap_to_grid(self, point: Point) -> Point:
        """Snap a point to grid."""
        grid_size = self.settings.grid_size
        return Point(
            round(point.x / grid_size) * grid_size,
            round(point.y / grid_size) * grid_size
        )

    def get_bounds(self) -> Tuple[Point, Point]:
        """Get bounding box of all diagram content."""
        if not self.shapes:
            return Point(0, 0), Point(0, 0)

        min_x = min(s.position.x for s in self.shapes.values())
        min_y = min(s.position.y for s in self.shapes.values())
        max_x = max(s.position.x + s.width for s in self.shapes.values())
        max_y = max(s.position.y + s.height for s in self.shapes.values())

        return Point(min_x, min_y), Point(max_x, max_y)

    def find_shapes_at_point(self, point: Point) -> List[Shape]:
        """Find all shapes containing a point."""
        return [s for s in self.shapes.values() if s.contains_point(point)]

    def find_shapes_in_area(
        self,
        top_left: Point,
        bottom_right: Point
    ) -> List[Shape]:
        """Find all shapes within a rectangular area."""
        shapes = []
        for shape in self.shapes.values():
            shape_bounds = shape.get_bounds()
            if (top_left.x <= shape_bounds[0].x and
                top_left.y <= shape_bounds[0].y and
                bottom_right.x >= shape_bounds[1].x and
                bottom_right.y >= shape_bounds[1].y):
                shapes.append(shape)
        return shapes

    # History Management

    def _record_history(self, action: str, data: Dict[str, Any]):
        """Record an action in history for undo/redo."""
        # Remove any history after current index
        self.history = self.history[:self.history_index + 1]

        # Add new history entry
        self.history.append({
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

        # Limit history size
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        else:
            self.history_index += 1

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self.history_index >= 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self.history_index < len(self.history) - 1

    def undo(self) -> bool:
        """Undo the last action."""
        if not self.can_undo():
            return False

        entry = self.history[self.history_index]
        action = entry["action"]
        data = entry["data"]

        # Reverse the action
        if action == "add_shape":
            self.shapes.pop(data["shape_id"], None)
        elif action == "remove_shape":
            shape = Shape.from_dict(data["shape_data"])
            self.shapes[data["shape_id"]] = shape
        elif action == "update_shape":
            shape = Shape.from_dict(data["old_data"])
            self.shapes[data["shape_id"]] = shape
        # Add more action reversals as needed

        self.history_index -= 1
        return True

    def redo(self) -> bool:
        """Redo the last undone action."""
        if not self.can_redo():
            return False

        self.history_index += 1
        entry = self.history[self.history_index]
        action = entry["action"]
        data = entry["data"]

        # Reapply the action
        if action == "add_shape":
            # Shape should still exist, just re-add to shapes dict
            pass
        elif action == "remove_shape":
            self.shapes.pop(data["shape_id"], None)
        elif action == "update_shape":
            shape = Shape.from_dict(data["new_data"])
            self.shapes[data["shape_id"]] = shape

        return True

    def _update_modified_time(self):
        """Update the diagram's modified timestamp."""
        self.metadata.modified_at = datetime.now().isoformat()

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """Serialize entire diagram to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "settings": self.settings.to_dict(),
            "layers": {lid: layer.to_dict() for lid, layer in self.layers.items()},
            "shapes": {sid: shape.to_dict() for sid, shape in self.shapes.items()},
            "connectors": {cid: conn.to_dict() for cid, conn in self.connectors.items()}
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize diagram to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_file(self, filepath: str):
        """Save diagram to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagramEngine":
        """Deserialize diagram from dictionary."""
        engine = cls()

        engine.metadata = DiagramMetadata.from_dict(data.get("metadata", {}))
        engine.settings = DiagramSettings.from_dict(data.get("settings", {}))

        # Load layers
        engine.layers = {
            int(lid): Layer.from_dict(ldata)
            for lid, ldata in data.get("layers", {}).items()
        }

        # Load shapes
        engine.shapes = {
            sid: Shape.from_dict(sdata)
            for sid, sdata in data.get("shapes", {}).items()
        }

        # Load connectors
        engine.connectors = {
            cid: Connector.from_dict(cdata)
            for cid, cdata in data.get("connectors", {}).items()
        }

        return engine

    @classmethod
    def from_json(cls, json_str: str) -> "DiagramEngine":
        """Deserialize diagram from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def load_from_file(cls, filepath: str) -> "DiagramEngine":
        """Load diagram from JSON file."""
        with open(filepath, 'r') as f:
            return cls.from_json(f.read())

    # Statistics

    def get_statistics(self) -> Dict[str, Any]:
        """Get diagram statistics."""
        return {
            "total_shapes": len(self.shapes),
            "total_connectors": len(self.connectors),
            "total_layers": len(self.layers),
            "shapes_by_category": self._count_shapes_by_category(),
            "connector_types": self._count_connector_types(),
            "bounds": {
                "min": self.get_bounds()[0].to_dict(),
                "max": self.get_bounds()[1].to_dict()
            }
        }

    def _count_shapes_by_category(self) -> Dict[str, int]:
        """Count shapes by category."""
        counts = defaultdict(int)
        for shape in self.shapes.values():
            counts[shape.category.value] += 1
        return dict(counts)

    def _count_connector_types(self) -> Dict[str, int]:
        """Count connectors by type."""
        counts = defaultdict(int)
        for connector in self.connectors.values():
            counts[connector.connector_type.value] += 1
        return dict(counts)
