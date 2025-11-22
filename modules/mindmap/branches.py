"""
Mind Map Branch and Connection Management

This module handles connections and relationships between nodes,
including visual styling and relationship types.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Literal, Tuple
from enum import Enum
import uuid
from datetime import datetime


class ConnectionType(Enum):
    """Types of connections between nodes."""
    PARENT_CHILD = "parent_child"  # Hierarchical connection
    ASSOCIATION = "association"  # Related ideas
    DEPENDENCY = "dependency"  # One depends on the other
    SEQUENCE = "sequence"  # Sequential relationship
    CONFLICT = "conflict"  # Opposing ideas
    REFERENCE = "reference"  # Cross-reference


class LineStyle(Enum):
    """Visual line styles for connections."""
    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"
    DOUBLE = "double"


class ArrowType(Enum):
    """Arrow head types."""
    NONE = "none"
    SINGLE = "single"
    DOUBLE = "double"
    DIAMOND = "diamond"
    CIRCLE = "circle"


class CurveType(Enum):
    """Curve types for connection lines."""
    STRAIGHT = "straight"
    BEZIER = "bezier"
    CURVED = "curved"
    ELBOW = "elbow"
    ORGANIC = "organic"


@dataclass
class ConnectionStyle:
    """Visual styling for a connection/branch."""
    color: str = "#000000"
    width: int = 2
    line_style: LineStyle = LineStyle.SOLID
    curve_type: CurveType = CurveType.BEZIER
    arrow_start: ArrowType = ArrowType.NONE
    arrow_end: ArrowType = ArrowType.NONE
    opacity: float = 1.0
    animated: bool = False
    label: str = ""
    label_color: str = "#000000"
    label_background: str = "#FFFFFF"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "color": self.color,
            "width": self.width,
            "line_style": self.line_style.value,
            "curve_type": self.curve_type.value,
            "arrow_start": self.arrow_start.value,
            "arrow_end": self.arrow_end.value,
            "opacity": self.opacity,
            "animated": self.animated,
            "label": self.label,
            "label_color": self.label_color,
            "label_background": self.label_background,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConnectionStyle:
        """Create ConnectionStyle from dictionary."""
        data_copy = data.copy()
        if "line_style" in data_copy:
            data_copy["line_style"] = LineStyle(data_copy["line_style"])
        if "curve_type" in data_copy:
            data_copy["curve_type"] = CurveType(data_copy["curve_type"])
        if "arrow_start" in data_copy:
            data_copy["arrow_start"] = ArrowType(data_copy["arrow_start"])
        if "arrow_end" in data_copy:
            data_copy["arrow_end"] = ArrowType(data_copy["arrow_end"])
        return cls(**data_copy)


class Branch:
    """
    Represents a connection/branch between two nodes.

    Branches can be:
    - Hierarchical (parent-child relationships)
    - Associative (related ideas)
    - Custom relationships with labels
    """

    def __init__(
        self,
        source_id: str,
        target_id: str,
        connection_type: ConnectionType = ConnectionType.PARENT_CHILD,
        branch_id: Optional[str] = None,
        style: Optional[ConnectionStyle] = None,
    ):
        self.id: str = branch_id or str(uuid.uuid4())
        self.source_id: str = source_id
        self.target_id: str = target_id
        self.connection_type: ConnectionType = connection_type
        self.style: ConnectionStyle = style or self._default_style_for_type(connection_type)

        # Metadata
        self.description: str = ""
        self.weight: float = 1.0  # Importance/strength of connection
        self.created_at: datetime = datetime.now()
        self.modified_at: datetime = datetime.now()
        self.metadata: Dict[str, Any] = {}

    @staticmethod
    def _default_style_for_type(connection_type: ConnectionType) -> ConnectionStyle:
        """Get default style based on connection type."""
        styles = {
            ConnectionType.PARENT_CHILD: ConnectionStyle(
                color="#000000",
                curve_type=CurveType.BEZIER,
                arrow_end=ArrowType.NONE,
            ),
            ConnectionType.ASSOCIATION: ConnectionStyle(
                color="#4285F4",
                line_style=LineStyle.DASHED,
                curve_type=CurveType.CURVED,
                arrow_end=ArrowType.SINGLE,
            ),
            ConnectionType.DEPENDENCY: ConnectionStyle(
                color="#EA4335",
                arrow_end=ArrowType.SINGLE,
                curve_type=CurveType.STRAIGHT,
            ),
            ConnectionType.SEQUENCE: ConnectionStyle(
                color="#34A853",
                arrow_end=ArrowType.SINGLE,
                curve_type=CurveType.ELBOW,
            ),
            ConnectionType.CONFLICT: ConnectionStyle(
                color="#EA4335",
                line_style=LineStyle.DOUBLE,
                arrow_start=ArrowType.CIRCLE,
                arrow_end=ArrowType.CIRCLE,
            ),
            ConnectionType.REFERENCE: ConnectionStyle(
                color="#FBBC04",
                line_style=LineStyle.DOTTED,
                arrow_end=ArrowType.DIAMOND,
            ),
        }
        return styles.get(connection_type, ConnectionStyle())

    def reverse(self) -> Branch:
        """Create a reversed branch (swap source and target)."""
        return Branch(
            source_id=self.target_id,
            target_id=self.source_id,
            connection_type=self.connection_type,
            style=self.style,
        )

    def update_style(self, **kwargs: Any) -> None:
        """Update style properties."""
        for key, value in kwargs.items():
            if hasattr(self.style, key):
                setattr(self.style, key, value)
        self.modified_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert branch to dictionary for serialization."""
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "connection_type": self.connection_type.value,
            "style": self.style.to_dict(),
            "description": self.description,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Branch:
        """Create branch from dictionary."""
        branch = cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            connection_type=ConnectionType(data["connection_type"]),
            branch_id=data["id"],
            style=ConnectionStyle.from_dict(data["style"]),
        )
        branch.description = data.get("description", "")
        branch.weight = data.get("weight", 1.0)
        branch.created_at = datetime.fromisoformat(data["created_at"])
        branch.modified_at = datetime.fromisoformat(data["modified_at"])
        branch.metadata = data.get("metadata", {})
        return branch

    def __repr__(self) -> str:
        """String representation."""
        return f"Branch(id={self.id}, {self.source_id} -> {self.target_id}, type={self.connection_type.value})"


class BranchManager:
    """
    Manages all branches/connections in a mind map.

    Features:
    - Create and delete connections
    - Query connections by node
    - Validate connection integrity
    - Find paths between nodes
    """

    def __init__(self):
        self.branches: Dict[str, Branch] = {}

    def add_branch(self, branch: Branch) -> None:
        """Add a branch to the manager."""
        self.branches[branch.id] = branch

    def remove_branch(self, branch_id: str) -> bool:
        """Remove a branch by ID. Returns True if found and removed."""
        if branch_id in self.branches:
            del self.branches[branch_id]
            return True
        return False

    def get_branch(self, branch_id: str) -> Optional[Branch]:
        """Get a branch by ID."""
        return self.branches.get(branch_id)

    def get_branches_from_node(self, node_id: str) -> List[Branch]:
        """Get all branches originating from a node."""
        return [b for b in self.branches.values() if b.source_id == node_id]

    def get_branches_to_node(self, node_id: str) -> List[Branch]:
        """Get all branches pointing to a node."""
        return [b for b in self.branches.values() if b.target_id == node_id]

    def get_all_branches_for_node(self, node_id: str) -> List[Branch]:
        """Get all branches connected to a node (in or out)."""
        return [
            b
            for b in self.branches.values()
            if b.source_id == node_id or b.target_id == node_id
        ]

    def get_branches_by_type(self, connection_type: ConnectionType) -> List[Branch]:
        """Get all branches of a specific type."""
        return [b for b in self.branches.values() if b.connection_type == connection_type]

    def find_branch_between(
        self, source_id: str, target_id: str
    ) -> Optional[Branch]:
        """Find a branch between two specific nodes."""
        for branch in self.branches.values():
            if branch.source_id == source_id and branch.target_id == target_id:
                return branch
        return None

    def has_connection(self, source_id: str, target_id: str) -> bool:
        """Check if a direct connection exists between two nodes."""
        return self.find_branch_between(source_id, target_id) is not None

    def remove_all_branches_for_node(self, node_id: str) -> int:
        """Remove all branches connected to a node. Returns count removed."""
        to_remove = [
            b.id
            for b in self.branches.values()
            if b.source_id == node_id or b.target_id == node_id
        ]
        for branch_id in to_remove:
            del self.branches[branch_id]
        return len(to_remove)

    def find_path(
        self, start_id: str, end_id: str, max_depth: int = 10
    ) -> Optional[List[str]]:
        """
        Find a path between two nodes using BFS.
        Returns list of node IDs forming the path, or None if no path exists.
        """
        if start_id == end_id:
            return [start_id]

        visited = set()
        queue = [(start_id, [start_id])]

        while queue:
            current_id, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            if current_id in visited:
                continue

            visited.add(current_id)

            # Get all outgoing branches
            for branch in self.get_branches_from_node(current_id):
                next_id = branch.target_id

                if next_id == end_id:
                    return path + [next_id]

                if next_id not in visited:
                    queue.append((next_id, path + [next_id]))

        return None

    def get_connected_component(self, node_id: str) -> Set[str]:
        """Get all nodes connected to the given node (directly or indirectly)."""
        component = set()
        to_visit = [node_id]

        while to_visit:
            current = to_visit.pop()
            if current in component:
                continue

            component.add(current)

            # Add all connected nodes
            for branch in self.get_all_branches_for_node(current):
                if branch.source_id == current:
                    to_visit.append(branch.target_id)
                else:
                    to_visit.append(branch.source_id)

        return component

    def validate_integrity(self, valid_node_ids: Set[str]) -> List[str]:
        """
        Validate branch integrity against a set of valid node IDs.
        Returns list of invalid branch IDs.
        """
        invalid = []
        for branch in self.branches.values():
            if (
                branch.source_id not in valid_node_ids
                or branch.target_id not in valid_node_ids
            ):
                invalid.append(branch.id)
        return invalid

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about branches."""
        type_counts = {}
        for branch in self.branches.values():
            type_name = branch.connection_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "total_branches": len(self.branches),
            "by_type": type_counts,
            "avg_weight": (
                sum(b.weight for b in self.branches.values()) / len(self.branches)
                if self.branches
                else 0
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert manager to dictionary for serialization."""
        return {
            "branches": {
                branch_id: branch.to_dict()
                for branch_id, branch in self.branches.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BranchManager:
        """Create manager from dictionary."""
        manager = cls()
        for branch_data in data.get("branches", {}).values():
            branch = Branch.from_dict(branch_data)
            manager.add_branch(branch)
        return manager

    def __len__(self) -> int:
        """Return number of branches."""
        return len(self.branches)

    def __repr__(self) -> str:
        """String representation."""
        return f"BranchManager(branches={len(self.branches)})"
