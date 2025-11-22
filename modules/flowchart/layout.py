"""
Auto-layout algorithms for automatic diagram arrangement.
Supports hierarchical, organic, circular, tree, and grid layouts.
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import math
from collections import defaultdict, deque

from .shapes import Shape, Point
from .connectors import Connector


@dataclass
class LayoutConfig:
    """Configuration for layout algorithms."""
    horizontal_spacing: float = 100.0
    vertical_spacing: float = 80.0
    margin: float = 50.0
    node_size_x: float = 120.0
    node_size_y: float = 60.0


class LayoutAlgorithm:
    """Base class for layout algorithms."""

    def __init__(self, config: Optional[LayoutConfig] = None):
        self.config = config or LayoutConfig()

    def apply(
        self,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector]
    ) -> Dict[str, Point]:
        """
        Apply layout algorithm to shapes.
        Returns dictionary mapping shape IDs to new positions.
        """
        raise NotImplementedError


class HierarchicalLayout(LayoutAlgorithm):
    """
    Hierarchical (Sugiyama) layout for directed graphs.
    Arranges nodes in layers from top to bottom based on hierarchy.
    """

    def apply(
        self,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector]
    ) -> Dict[str, Point]:
        """Apply hierarchical layout."""
        if not shapes:
            return {}

        # Build graph adjacency
        graph = self._build_graph(shapes, connectors)

        # Assign layers (topological sort)
        layers = self._assign_layers(graph, shapes)

        # Reduce crossings
        self._reduce_crossings(layers, graph)

        # Calculate positions
        positions = self._calculate_positions(layers, shapes)

        return positions

    def _build_graph(
        self,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector]
    ) -> Dict[str, List[str]]:
        """Build adjacency list from shapes and connectors."""
        graph = defaultdict(list)

        for connector in connectors.values():
            if connector.source_shape_id and connector.target_shape_id:
                if (connector.source_shape_id in shapes and
                    connector.target_shape_id in shapes):
                    graph[connector.source_shape_id].append(connector.target_shape_id)

        # Ensure all shapes are in graph
        for shape_id in shapes:
            if shape_id not in graph:
                graph[shape_id] = []

        return dict(graph)

    def _assign_layers(
        self,
        graph: Dict[str, List[str]],
        shapes: Dict[str, Shape]
    ) -> List[List[str]]:
        """Assign nodes to layers using topological sort."""
        # Calculate in-degree
        in_degree = defaultdict(int)
        for node in graph:
            in_degree[node] = 0

        for node, neighbors in graph.items():
            for neighbor in neighbors:
                in_degree[neighbor] += 1

        # Find roots (nodes with no incoming edges)
        roots = [node for node in graph if in_degree[node] == 0]

        if not roots:
            # Handle cycles - use all nodes as roots
            roots = list(graph.keys())

        # BFS to assign layers
        layers = []
        visited = set()
        queue = deque([(node, 0) for node in roots])

        while queue:
            node, layer_idx = queue.popleft()

            if node in visited:
                continue

            visited.add(node)

            # Ensure layer exists
            while len(layers) <= layer_idx:
                layers.append([])

            layers[layer_idx].append(node)

            # Add children to next layer
            for neighbor in graph[node]:
                if neighbor not in visited:
                    queue.append((neighbor, layer_idx + 1))

        # Add any disconnected nodes
        for node in shapes:
            if node not in visited:
                layers[0].append(node)

        return layers

    def _reduce_crossings(
        self,
        layers: List[List[str]],
        graph: Dict[str, List[str]]
    ):
        """Reduce edge crossings using barycenter method."""
        # Simplified crossing reduction
        for iteration in range(5):  # Multiple passes
            for i in range(len(layers) - 1):
                self._order_layer(layers[i], layers[i + 1], graph)

    def _order_layer(
        self,
        current_layer: List[str],
        next_layer: List[str],
        graph: Dict[str, List[str]]
    ):
        """Order nodes in layer to reduce crossings."""
        # Calculate barycenter for each node in next layer
        barycenters = {}

        for j, node in enumerate(next_layer):
            # Find all connections from current layer
            positions = []
            for i, parent in enumerate(current_layer):
                if node in graph.get(parent, []):
                    positions.append(i)

            if positions:
                barycenters[node] = sum(positions) / len(positions)
            else:
                barycenters[node] = j

        # Sort next layer by barycenter
        next_layer.sort(key=lambda n: barycenters.get(n, 0))

    def _calculate_positions(
        self,
        layers: List[List[str]],
        shapes: Dict[str, Shape]
    ) -> Dict[str, Point]:
        """Calculate final positions for all nodes."""
        positions = {}

        h_spacing = self.config.horizontal_spacing
        v_spacing = self.config.vertical_spacing
        margin = self.config.margin

        for layer_idx, layer in enumerate(layers):
            y = margin + layer_idx * (self.config.node_size_y + v_spacing)

            # Calculate total width of layer
            layer_width = len(layer) * (self.config.node_size_x + h_spacing) - h_spacing

            for node_idx, node_id in enumerate(layer):
                x = margin + node_idx * (self.config.node_size_x + h_spacing)

                # Center the layer
                x += (layer_width / 2) if len(layers) > 1 else 0

                positions[node_id] = Point(x, y)

        return positions


class OrganicLayout(LayoutAlgorithm):
    """
    Organic (force-directed) layout.
    Uses physics simulation to create natural-looking layouts.
    """

    def __init__(
        self,
        config: Optional[LayoutConfig] = None,
        iterations: int = 100,
        temperature: float = 100.0
    ):
        super().__init__(config)
        self.iterations = iterations
        self.temperature = temperature

    def apply(
        self,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector]
    ) -> Dict[str, Point]:
        """Apply force-directed layout."""
        if not shapes:
            return {}

        # Initialize random positions
        positions = self._initialize_positions(shapes)

        # Build adjacency
        adjacency = self._build_adjacency(shapes, connectors)

        # Run simulation
        for i in range(self.iterations):
            t = self.temperature * (1 - i / self.iterations)
            positions = self._iterate(positions, adjacency, t)

        return positions

    def _initialize_positions(
        self,
        shapes: Dict[str, Shape]
    ) -> Dict[str, Point]:
        """Initialize positions in a circle."""
        positions = {}
        n = len(shapes)
        radius = max(100.0, n * 20.0)

        for idx, shape_id in enumerate(shapes):
            angle = 2 * math.pi * idx / n
            x = self.config.margin + radius + radius * math.cos(angle)
            y = self.config.margin + radius + radius * math.sin(angle)
            positions[shape_id] = Point(x, y)

        return positions

    def _build_adjacency(
        self,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector]
    ) -> Dict[str, Set[str]]:
        """Build adjacency set."""
        adjacency = defaultdict(set)

        for connector in connectors.values():
            if connector.source_shape_id and connector.target_shape_id:
                if (connector.source_shape_id in shapes and
                    connector.target_shape_id in shapes):
                    adjacency[connector.source_shape_id].add(connector.target_shape_id)
                    adjacency[connector.target_shape_id].add(connector.source_shape_id)

        return adjacency

    def _iterate(
        self,
        positions: Dict[str, Point],
        adjacency: Dict[str, Set[str]],
        temperature: float
    ) -> Dict[str, Point]:
        """Run one iteration of force-directed algorithm."""
        forces = {shape_id: Point(0, 0) for shape_id in positions}

        # Repulsive forces (all pairs)
        shape_ids = list(positions.keys())
        for i, id1 in enumerate(shape_ids):
            for id2 in shape_ids[i + 1:]:
                self._apply_repulsion(positions, forces, id1, id2)

        # Attractive forces (connected nodes)
        for id1, neighbors in adjacency.items():
            for id2 in neighbors:
                if id1 in positions and id2 in positions:
                    self._apply_attraction(positions, forces, id1, id2)

        # Update positions
        new_positions = {}
        for shape_id, pos in positions.items():
            force = forces[shape_id]

            # Limit displacement by temperature
            displacement = math.sqrt(force.x ** 2 + force.y ** 2)
            if displacement > 0:
                limited = min(displacement, temperature)
                dx = force.x / displacement * limited
                dy = force.y / displacement * limited

                new_positions[shape_id] = Point(
                    pos.x + dx,
                    pos.y + dy
                )
            else:
                new_positions[shape_id] = pos

        return new_positions

    def _apply_repulsion(
        self,
        positions: Dict[str, Point],
        forces: Dict[str, Point],
        id1: str,
        id2: str
    ):
        """Apply repulsive force between two nodes."""
        pos1 = positions[id1]
        pos2 = positions[id2]

        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance < 0.01:
            distance = 0.01
            dx = 0.01
            dy = 0.01

        # Repulsive force inversely proportional to distance
        k = 5000.0  # Repulsion constant
        force = k / (distance ** 2)

        fx = (dx / distance) * force
        fy = (dy / distance) * force

        forces[id1].x += fx
        forces[id1].y += fy
        forces[id2].x -= fx
        forces[id2].y -= fy

    def _apply_attraction(
        self,
        positions: Dict[str, Point],
        forces: Dict[str, Point],
        id1: str,
        id2: str
    ):
        """Apply attractive force between connected nodes."""
        pos1 = positions[id1]
        pos2 = positions[id2]

        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance < 0.01:
            return

        # Attractive force proportional to distance
        k = 0.1  # Attraction constant
        force = distance * k

        fx = (dx / distance) * force
        fy = (dy / distance) * force

        forces[id1].x += fx
        forces[id1].y += fy
        forces[id2].x -= fx
        forces[id2].y -= fy


class CircularLayout(LayoutAlgorithm):
    """Arrange nodes in a circle."""

    def apply(
        self,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector]
    ) -> Dict[str, Point]:
        """Apply circular layout."""
        if not shapes:
            return {}

        positions = {}
        n = len(shapes)
        radius = max(200.0, n * 30.0)

        center_x = self.config.margin + radius
        center_y = self.config.margin + radius

        for idx, shape_id in enumerate(shapes):
            angle = 2 * math.pi * idx / n
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            positions[shape_id] = Point(x, y)

        return positions


class TreeLayout(LayoutAlgorithm):
    """Tree layout for hierarchical structures."""

    def apply(
        self,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector]
    ) -> Dict[str, Point]:
        """Apply tree layout."""
        if not shapes:
            return {}

        # Build tree structure
        graph = self._build_graph(shapes, connectors)
        root = self._find_root(graph, shapes)

        # Calculate tree structure
        tree = self._build_tree(root, graph)

        # Calculate positions using Walker's algorithm
        positions = self._calculate_tree_positions(tree, shapes)

        return positions

    def _build_graph(
        self,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector]
    ) -> Dict[str, List[str]]:
        """Build directed graph."""
        graph = defaultdict(list)

        for connector in connectors.values():
            if connector.source_shape_id and connector.target_shape_id:
                if (connector.source_shape_id in shapes and
                    connector.target_shape_id in shapes):
                    graph[connector.source_shape_id].append(connector.target_shape_id)

        return dict(graph)

    def _find_root(
        self,
        graph: Dict[str, List[str]],
        shapes: Dict[str, Shape]
    ) -> str:
        """Find root node (node with no incoming edges)."""
        # Calculate in-degree
        in_degree = {shape_id: 0 for shape_id in shapes}

        for children in graph.values():
            for child in children:
                in_degree[child] += 1

        # Find nodes with in-degree 0
        roots = [node for node, degree in in_degree.items() if degree == 0]

        return roots[0] if roots else list(shapes.keys())[0]

    def _build_tree(
        self,
        root: str,
        graph: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """Build tree from graph (BFS)."""
        tree = defaultdict(list)
        visited = set()
        queue = deque([root])

        while queue:
            node = queue.popleft()
            if node in visited:
                continue

            visited.add(node)

            for child in graph.get(node, []):
                if child not in visited:
                    tree[node].append(child)
                    queue.append(child)

        return dict(tree)

    def _calculate_tree_positions(
        self,
        tree: Dict[str, List[str]],
        shapes: Dict[str, Shape]
    ) -> Dict[str, Point]:
        """Calculate positions for tree layout."""
        positions = {}

        # Find root
        all_children = set()
        for children in tree.values():
            all_children.update(children)

        roots = [node for node in tree if node not in all_children]
        root = roots[0] if roots else list(shapes.keys())[0]

        # Calculate positions recursively
        self._position_subtree(
            root, tree, positions,
            x=self.config.margin,
            y=self.config.margin,
            level=0
        )

        return positions

    def _position_subtree(
        self,
        node: str,
        tree: Dict[str, List[str]],
        positions: Dict[str, Point],
        x: float,
        y: float,
        level: int
    ) -> float:
        """Position node and its subtree, return width used."""
        children = tree.get(node, [])

        if not children:
            # Leaf node
            positions[node] = Point(x, y)
            return self.config.node_size_x

        # Position children
        child_x = x
        child_y = y + self.config.node_size_y + self.config.vertical_spacing
        total_width = 0

        for child in children:
            width = self._position_subtree(
                child, tree, positions, child_x, child_y, level + 1
            )
            child_x += width + self.config.horizontal_spacing
            total_width += width + self.config.horizontal_spacing

        total_width -= self.config.horizontal_spacing  # Remove last spacing

        # Position current node centered over children
        node_x = x + total_width / 2 - self.config.node_size_x / 2
        positions[node] = Point(node_x, y)

        return total_width


class GridLayout(LayoutAlgorithm):
    """Arrange nodes in a grid pattern."""

    def __init__(
        self,
        config: Optional[LayoutConfig] = None,
        columns: Optional[int] = None
    ):
        super().__init__(config)
        self.columns = columns

    def apply(
        self,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector]
    ) -> Dict[str, Point]:
        """Apply grid layout."""
        if not shapes:
            return {}

        n = len(shapes)

        # Calculate grid dimensions
        if self.columns:
            cols = self.columns
        else:
            cols = math.ceil(math.sqrt(n))

        rows = math.ceil(n / cols)

        positions = {}
        h_spacing = self.config.horizontal_spacing
        v_spacing = self.config.vertical_spacing
        margin = self.config.margin

        for idx, shape_id in enumerate(shapes):
            row = idx // cols
            col = idx % cols

            x = margin + col * (self.config.node_size_x + h_spacing)
            y = margin + row * (self.config.node_size_y + v_spacing)

            positions[shape_id] = Point(x, y)

        return positions


class LayoutEngine:
    """Main engine for applying layouts."""

    @staticmethod
    def apply_layout(
        layout_type: str,
        shapes: Dict[str, Shape],
        connectors: Dict[str, Connector],
        config: Optional[LayoutConfig] = None
    ) -> Dict[str, Point]:
        """
        Apply a layout algorithm to shapes.

        Args:
            layout_type: One of 'hierarchical', 'organic', 'circular', 'tree', 'grid'
            shapes: Dictionary of shapes to layout
            connectors: Dictionary of connectors between shapes
            config: Optional layout configuration

        Returns:
            Dictionary mapping shape IDs to new positions
        """
        layouts = {
            "hierarchical": HierarchicalLayout,
            "organic": OrganicLayout,
            "circular": CircularLayout,
            "tree": TreeLayout,
            "grid": GridLayout
        }

        layout_class = layouts.get(layout_type)
        if not layout_class:
            raise ValueError(f"Unknown layout type: {layout_type}")

        layout = layout_class(config)
        return layout.apply(shapes, connectors)
