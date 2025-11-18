"""
Mind Map Layout Algorithms

This module provides various automatic layout algorithms for positioning
nodes in a mind map, including radial, tree, organic, and force-directed layouts.
"""

from __future__ import annotations
from typing import Dict, List, Set, Tuple, Optional, TYPE_CHECKING
from enum import Enum
import math
from dataclasses import dataclass

if TYPE_CHECKING:
    from .nodes import MindMapNode, Position


class LayoutType(Enum):
    """Available layout algorithms."""
    RADIAL = "radial"  # Central node with children radiating outward
    TREE = "tree"  # Traditional tree layout (vertical or horizontal)
    ORGANIC = "organic"  # Natural, balanced layout
    FORCE_DIRECTED = "force_directed"  # Physics-based layout
    TIMELINE = "timeline"  # Linear timeline layout
    MIND_MAP = "mind_map"  # Classic mind map style (left and right branches)
    CIRCLE = "circle"  # Nodes arranged in a circle
    GRID = "grid"  # Organized grid layout


@dataclass
class LayoutConfig:
    """Configuration for layout algorithms."""
    node_spacing: float = 100.0  # Space between sibling nodes
    level_spacing: float = 150.0  # Space between hierarchy levels
    canvas_width: float = 1920.0
    canvas_height: float = 1080.0
    center_x: float = 960.0
    center_y: float = 540.0
    padding: float = 50.0
    compact_mode: bool = False


class LayoutEngine:
    """
    Main layout engine for positioning nodes automatically.

    Provides multiple layout algorithms and intelligent positioning.
    """

    def __init__(self, config: Optional[LayoutConfig] = None):
        self.config = config or LayoutConfig()

    def apply_layout(
        self,
        nodes: Dict[str, MindMapNode],
        root_id: str,
        layout_type: LayoutType = LayoutType.MIND_MAP,
    ) -> Dict[str, Position]:
        """
        Apply a layout algorithm to all nodes.

        Args:
            nodes: Dictionary of all nodes
            root_id: ID of the root node
            layout_type: Layout algorithm to use

        Returns:
            Dictionary mapping node IDs to new positions
        """
        layout_methods = {
            LayoutType.RADIAL: self._radial_layout,
            LayoutType.TREE: self._tree_layout,
            LayoutType.ORGANIC: self._organic_layout,
            LayoutType.FORCE_DIRECTED: self._force_directed_layout,
            LayoutType.TIMELINE: self._timeline_layout,
            LayoutType.MIND_MAP: self._mindmap_layout,
            LayoutType.CIRCLE: self._circle_layout,
            LayoutType.GRID: self._grid_layout,
        }

        method = layout_methods.get(layout_type, self._mindmap_layout)
        return method(nodes, root_id)

    def _get_tree_hierarchy(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, int]:
        """Get hierarchy level for each node (BFS)."""
        levels = {root_id: 0}
        queue = [root_id]

        while queue:
            current_id = queue.pop(0)
            current_level = levels[current_id]

            if current_id in nodes:
                for child_id in nodes[current_id].children_ids:
                    if child_id not in levels:
                        levels[child_id] = current_level + 1
                        queue.append(child_id)

        return levels

    def _mindmap_layout(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, Position]:
        """
        Classic mind map layout with branches on left and right.
        """
        from .nodes import Position

        positions = {}
        root = nodes.get(root_id)
        if not root:
            return positions

        # Place root at center
        positions[root_id] = Position(self.config.center_x, self.config.center_y)

        children = root.children_ids
        if not children:
            return positions

        # Split children between left and right
        mid = len(children) // 2
        right_children = children[:mid]
        left_children = children[mid:]

        # Layout right side
        self._layout_branch(
            nodes, right_children, positions, self.config.center_x,
            self.config.center_y, 1, direction=1
        )

        # Layout left side
        self._layout_branch(
            nodes, left_children, positions, self.config.center_x,
            self.config.center_y, 1, direction=-1
        )

        return positions

    def _layout_branch(
        self,
        nodes: Dict[str, MindMapNode],
        node_ids: List[str],
        positions: Dict[str, Position],
        parent_x: float,
        parent_y: float,
        level: int,
        direction: int = 1,  # 1 for right, -1 for left
    ) -> float:
        """
        Recursively layout a branch of the mind map.
        Returns the total height used.
        """
        from .nodes import Position

        if not node_ids:
            return 0

        total_height = 0
        current_y = parent_y - (len(node_ids) - 1) * self.config.node_spacing / 2

        for node_id in node_ids:
            if node_id not in nodes:
                continue

            node = nodes[node_id]

            # Calculate position
            x = parent_x + direction * self.config.level_spacing
            y = current_y

            # Get subtree height to center this node with its children
            subtree_height = self._estimate_subtree_height(nodes, node_id)

            positions[node_id] = Position(x, y)

            # Layout children recursively
            if node.children_ids:
                child_height = self._layout_branch(
                    nodes, node.children_ids, positions, x, y, level + 1, direction
                )
                total_height += max(subtree_height, child_height)
            else:
                total_height += self.config.node_spacing

            current_y += max(subtree_height, self.config.node_spacing)

        return total_height

    def _estimate_subtree_height(
        self, nodes: Dict[str, MindMapNode], node_id: str
    ) -> float:
        """Estimate the vertical space needed for a subtree."""
        if node_id not in nodes:
            return self.config.node_spacing

        node = nodes[node_id]
        if not node.children_ids:
            return self.config.node_spacing

        total = 0
        for child_id in node.children_ids:
            total += self._estimate_subtree_height(nodes, child_id)

        return max(total, self.config.node_spacing)

    def _radial_layout(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, Position]:
        """
        Radial layout with root at center and children in concentric circles.
        """
        from .nodes import Position

        positions = {}
        levels = self._get_tree_hierarchy(nodes, root_id)

        # Group nodes by level
        nodes_by_level: Dict[int, List[str]] = {}
        for node_id, level in levels.items():
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node_id)

        # Position root at center
        positions[root_id] = Position(self.config.center_x, self.config.center_y)

        # Position each level in a circle
        for level in sorted(nodes_by_level.keys()):
            if level == 0:  # Skip root
                continue

            level_nodes = nodes_by_level[level]
            radius = level * self.config.level_spacing
            angle_step = 2 * math.pi / len(level_nodes)

            for i, node_id in enumerate(level_nodes):
                angle = i * angle_step
                x = self.config.center_x + radius * math.cos(angle)
                y = self.config.center_y + radius * math.sin(angle)
                positions[node_id] = Position(x, y)

        return positions

    def _tree_layout(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, Position]:
        """
        Traditional vertical tree layout.
        """
        from .nodes import Position

        positions = {}
        levels = self._get_tree_hierarchy(nodes, root_id)

        # Group nodes by level
        nodes_by_level: Dict[int, List[str]] = {}
        for node_id, level in levels.items():
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node_id)

        # Calculate positions level by level
        for level in sorted(nodes_by_level.keys()):
            level_nodes = nodes_by_level[level]
            y = self.config.padding + level * self.config.level_spacing

            # Distribute horizontally
            total_width = self.config.canvas_width - 2 * self.config.padding
            if len(level_nodes) == 1:
                x_positions = [self.config.center_x]
            else:
                spacing = total_width / (len(level_nodes) - 1)
                x_positions = [
                    self.config.padding + i * spacing
                    for i in range(len(level_nodes))
                ]

            for node_id, x in zip(level_nodes, x_positions):
                positions[node_id] = Position(x, y)

        return positions

    def _organic_layout(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, Position]:
        """
        Organic layout using a simple force-directed approach.
        """
        # Start with radial layout as base
        positions = self._radial_layout(nodes, root_id)

        # Apply some relaxation iterations
        for _ in range(50):
            self._apply_forces(nodes, positions)

        return positions

    def _force_directed_layout(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, Position]:
        """
        Force-directed layout using spring and repulsion forces.
        """
        from .nodes import Position

        # Initialize with random positions
        positions = {}
        for i, node_id in enumerate(nodes.keys()):
            angle = (i / len(nodes)) * 2 * math.pi
            radius = 200
            x = self.config.center_x + radius * math.cos(angle)
            y = self.config.center_y + radius * math.sin(angle)
            positions[node_id] = Position(x, y)

        # Run simulation
        for iteration in range(100):
            self._apply_forces(nodes, positions, iteration)

        return positions

    def _apply_forces(
        self, nodes: Dict[str, MindMapNode], positions: Dict[str, Position], iteration: int = 0
    ) -> None:
        """Apply force-directed algorithm forces."""
        from .nodes import Position

        forces = {node_id: Position(0, 0) for node_id in nodes}

        # Repulsion between all nodes
        node_ids = list(nodes.keys())
        for i, id1 in enumerate(node_ids):
            for id2 in node_ids[i + 1 :]:
                if id1 not in positions or id2 not in positions:
                    continue

                pos1, pos2 = positions[id1], positions[id2]
                dx = pos2.x - pos1.x
                dy = pos2.y - pos1.y
                dist = max(math.sqrt(dx * dx + dy * dy), 0.1)

                # Repulsion force
                force = 5000 / (dist * dist)
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                forces[id1].x -= fx
                forces[id1].y -= fy
                forces[id2].x += fx
                forces[id2].y += fy

        # Attraction along edges
        for node_id, node in nodes.items():
            if node_id not in positions:
                continue

            for child_id in node.children_ids:
                if child_id not in positions:
                    continue

                pos1, pos2 = positions[node_id], positions[child_id]
                dx = pos2.x - pos1.x
                dy = pos2.y - pos1.y
                dist = max(math.sqrt(dx * dx + dy * dy), 0.1)

                # Spring force
                force = dist * 0.01
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                forces[node_id].x += fx
                forces[node_id].y += fy
                forces[child_id].x -= fx
                forces[child_id].y -= fy

        # Apply forces with damping
        damping = 0.9 - (iteration * 0.005)  # Decrease over time
        for node_id, force in forces.items():
            if node_id in positions:
                positions[node_id].x += force.x * damping
                positions[node_id].y += force.y * damping

    def _timeline_layout(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, Position]:
        """
        Linear timeline layout.
        """
        from .nodes import Position

        positions = {}
        levels = self._get_tree_hierarchy(nodes, root_id)

        # Sort nodes by level (timeline order)
        sorted_nodes = sorted(levels.items(), key=lambda x: x[1])

        y = self.config.center_y
        for i, (node_id, level) in enumerate(sorted_nodes):
            x = self.config.padding + i * self.config.node_spacing
            positions[node_id] = Position(x, y)

        return positions

    def _circle_layout(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, Position]:
        """
        Arrange all nodes in a circle.
        """
        from .nodes import Position

        positions = {}
        node_ids = list(nodes.keys())
        radius = min(self.config.canvas_width, self.config.canvas_height) / 3

        for i, node_id in enumerate(node_ids):
            angle = (i / len(node_ids)) * 2 * math.pi
            x = self.config.center_x + radius * math.cos(angle)
            y = self.config.center_y + radius * math.sin(angle)
            positions[node_id] = Position(x, y)

        return positions

    def _grid_layout(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, Position]:
        """
        Organize nodes in a grid.
        """
        from .nodes import Position

        positions = {}
        node_ids = list(nodes.keys())

        # Calculate grid dimensions
        cols = math.ceil(math.sqrt(len(node_ids)))
        rows = math.ceil(len(node_ids) / cols)

        cell_width = (self.config.canvas_width - 2 * self.config.padding) / cols
        cell_height = (self.config.canvas_height - 2 * self.config.padding) / rows

        for i, node_id in enumerate(node_ids):
            col = i % cols
            row = i // cols
            x = self.config.padding + col * cell_width + cell_width / 2
            y = self.config.padding + row * cell_height + cell_height / 2
            positions[node_id] = Position(x, y)

        return positions

    def optimize_positions(
        self, nodes: Dict[str, MindMapNode], positions: Dict[str, Position]
    ) -> Dict[str, Position]:
        """
        Optimize positions to avoid overlaps and improve readability.
        """
        # Simple overlap detection and adjustment
        node_ids = list(positions.keys())
        min_distance = 80  # Minimum distance between nodes

        for _ in range(10):  # Multiple passes
            adjusted = False
            for i, id1 in enumerate(node_ids):
                for id2 in node_ids[i + 1 :]:
                    pos1, pos2 = positions[id1], positions[id2]
                    dist = pos1.distance_to(pos2)

                    if dist < min_distance and dist > 0:
                        # Move nodes apart
                        dx = pos2.x - pos1.x
                        dy = pos2.y - pos1.y
                        adjust = (min_distance - dist) / 2

                        positions[id1].x -= (dx / dist) * adjust
                        positions[id1].y -= (dy / dist) * adjust
                        positions[id2].x += (dx / dist) * adjust
                        positions[id2].y += (dy / dist) * adjust
                        adjusted = True

            if not adjusted:
                break

        return positions
