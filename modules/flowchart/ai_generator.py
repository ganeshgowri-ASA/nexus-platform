"""
AI-powered diagram generation and optimization.
Uses AI to generate diagrams from text, optimize layouts, and suggest improvements.
"""

from typing import Dict, List, Optional, Any, Tuple
import re
from dataclasses import dataclass

from .diagram_engine import DiagramEngine
from .shapes import Point, ShapeStyle, shape_library
from .connectors import ConnectorType, ConnectorStyle
from .layout import LayoutEngine, LayoutConfig


@dataclass
class DiagramIntent:
    """Parsed intent from natural language description."""
    diagram_type: str  # flowchart, org_chart, network, etc.
    entities: List[Dict[str, Any]]  # Shapes to create
    relationships: List[Dict[str, Any]]  # Connections between shapes
    layout_preference: Optional[str] = None
    style_preferences: Optional[Dict[str, Any]] = None


class NaturalLanguageParser:
    """Parse natural language descriptions into diagram structure."""

    # Keywords for different diagram types
    DIAGRAM_TYPE_KEYWORDS = {
        "flowchart": ["flowchart", "flow", "process", "workflow", "steps"],
        "org_chart": ["org chart", "organization", "hierarchy", "reporting"],
        "network": ["network", "infrastructure", "server", "topology"],
        "uml": ["uml", "class diagram", "sequence", "object"],
        "bpmn": ["bpmn", "business process"],
        "wireframe": ["wireframe", "mockup", "ui", "interface"]
    }

    # Shape keywords
    SHAPE_KEYWORDS = {
        "process": ["process", "task", "action", "step"],
        "decision": ["decision", "choice", "if", "branch"],
        "data": ["data", "input", "output"],
        "database": ["database", "db", "storage", "store"],
        "server": ["server", "host", "machine"],
        "cloud": ["cloud", "internet"],
        "person": ["person", "user", "actor", "employee"]
    }

    # Connection keywords
    CONNECTION_KEYWORDS = {
        "leads_to": ["leads to", "goes to", "then", "next", "->", "→"],
        "connects_to": ["connects to", "linked to", "connected to"],
        "reports_to": ["reports to", "managed by", "under"],
        "contains": ["contains", "has", "includes"]
    }

    @staticmethod
    def parse(description: str) -> DiagramIntent:
        """Parse natural language description into diagram intent."""
        description_lower = description.lower()

        # Detect diagram type
        diagram_type = NaturalLanguageParser._detect_diagram_type(description_lower)

        # Extract entities (shapes)
        entities = NaturalLanguageParser._extract_entities(description)

        # Extract relationships (connections)
        relationships = NaturalLanguageParser._extract_relationships(description, entities)

        # Detect layout preference
        layout_preference = NaturalLanguageParser._detect_layout(description_lower)

        return DiagramIntent(
            diagram_type=diagram_type,
            entities=entities,
            relationships=relationships,
            layout_preference=layout_preference
        )

    @staticmethod
    def _detect_diagram_type(description: str) -> str:
        """Detect the type of diagram from description."""
        for diagram_type, keywords in NaturalLanguageParser.DIAGRAM_TYPE_KEYWORDS.items():
            if any(keyword in description for keyword in keywords):
                return diagram_type
        return "flowchart"  # Default

    @staticmethod
    def _extract_entities(description: str) -> List[Dict[str, Any]]:
        """Extract entities (shapes) from description."""
        entities = []

        # Look for quoted entities
        quoted_pattern = r'"([^"]+)"'
        quoted_entities = re.findall(quoted_pattern, description)

        for entity in quoted_entities:
            # Determine shape type based on context
            shape_type = NaturalLanguageParser._infer_shape_type(entity, description)

            entities.append({
                "name": entity,
                "shape_type": shape_type,
                "metadata": {}
            })

        # Look for numbered lists
        numbered_pattern = r'(\d+)\.\s+([^\n\.]+)'
        numbered_entities = re.findall(numbered_pattern, description)

        for number, entity in numbered_entities:
            if entity.strip() and not any(e["name"] == entity.strip() for e in entities):
                shape_type = NaturalLanguageParser._infer_shape_type(entity, description)

                entities.append({
                    "name": entity.strip(),
                    "shape_type": shape_type,
                    "metadata": {"order": int(number)}
                })

        # Look for bulleted lists
        bullet_pattern = r'[-*•]\s+([^\n]+)'
        bullet_entities = re.findall(bullet_pattern, description)

        for entity in bullet_entities:
            if entity.strip() and not any(e["name"] == entity.strip() for e in entities):
                shape_type = NaturalLanguageParser._infer_shape_type(entity, description)

                entities.append({
                    "name": entity.strip(),
                    "shape_type": shape_type,
                    "metadata": {}
                })

        return entities

    @staticmethod
    def _infer_shape_type(entity: str, context: str) -> str:
        """Infer the shape type for an entity based on context."""
        entity_lower = entity.lower()
        context_lower = context.lower()

        # Check for specific shape keywords
        for shape_type, keywords in NaturalLanguageParser.SHAPE_KEYWORDS.items():
            if any(keyword in entity_lower or keyword in context_lower for keyword in keywords):
                if shape_type == "process":
                    return "flowchart_process"
                elif shape_type == "decision":
                    return "flowchart_decision"
                elif shape_type == "data":
                    return "flowchart_data"
                elif shape_type == "database":
                    return "flowchart_database"
                elif shape_type == "server":
                    return "network_server"
                elif shape_type == "cloud":
                    return "network_cloud"
                elif shape_type == "person":
                    return "symbol_user"

        # Default based on diagram type in context
        if any(kw in context_lower for kw in ["org", "organization", "hierarchy"]):
            return "org_manager"
        elif any(kw in context_lower for kw in ["network", "infrastructure"]):
            return "network_server"
        else:
            return "flowchart_process"

    @staticmethod
    def _extract_relationships(
        description: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract relationships (connections) between entities."""
        relationships = []

        # Create entity name to index mapping
        entity_names = [e["name"].lower() for e in entities]

        # Look for explicit connections
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i == j:
                    continue

                # Check if there's a connection keyword between entities
                pattern = f"{re.escape(entity1['name'])}(.{{0,100}}){re.escape(entity2['name'])}"
                matches = re.finditer(pattern, description, re.IGNORECASE)

                for match in matches:
                    connector_text = match.group(1).lower()

                    # Determine connection type
                    connection_type = "leads_to"  # Default

                    for conn_type, keywords in NaturalLanguageParser.CONNECTION_KEYWORDS.items():
                        if any(keyword in connector_text for keyword in keywords):
                            connection_type = conn_type
                            break

                    relationships.append({
                        "source": entity1["name"],
                        "target": entity2["name"],
                        "type": connection_type,
                        "label": ""
                    })

        # If no explicit relationships found, infer from order
        if not relationships and len(entities) > 1:
            # Connect entities in sequence based on order or appearance
            sorted_entities = sorted(
                entities,
                key=lambda e: e.get("metadata", {}).get("order", 999)
            )

            for i in range(len(sorted_entities) - 1):
                relationships.append({
                    "source": sorted_entities[i]["name"],
                    "target": sorted_entities[i + 1]["name"],
                    "type": "leads_to",
                    "label": ""
                })

        return relationships

    @staticmethod
    def _detect_layout(description: str) -> Optional[str]:
        """Detect preferred layout from description."""
        layout_keywords = {
            "hierarchical": ["top to bottom", "hierarchical", "tree", "hierarchy"],
            "circular": ["circular", "circle", "radial"],
            "grid": ["grid", "matrix"],
            "organic": ["organic", "natural", "force-directed"]
        }

        for layout, keywords in layout_keywords.items():
            if any(keyword in description for keyword in keywords):
                return layout

        return None


class AIGenerator:
    """AI-powered diagram generator."""

    @staticmethod
    def generate_from_text(description: str) -> DiagramEngine:
        """
        Generate a diagram from natural language description.

        Args:
            description: Natural language description of the diagram

        Returns:
            DiagramEngine with generated diagram
        """
        # Parse the description
        intent = NaturalLanguageParser.parse(description)

        # Create diagram engine
        engine = DiagramEngine()
        engine.metadata.title = f"AI Generated {intent.diagram_type.replace('_', ' ').title()}"
        engine.metadata.description = description

        # Create shapes
        shape_map = {}  # Map entity names to shape IDs

        for i, entity in enumerate(intent.entities):
            # Calculate initial position (will be adjusted by layout)
            position = Point(100 + i * 150, 100)

            # Determine style based on diagram type
            style = AIGenerator._get_default_style(intent.diagram_type, i)

            # Create shape
            shape = engine.add_shape(
                entity["shape_type"],
                position,
                entity["name"],
                style
            )

            if shape:
                shape_map[entity["name"]] = shape.id

        # Create connections
        for relationship in intent.relationships:
            source_name = relationship["source"]
            target_name = relationship["target"]

            if source_name in shape_map and target_name in shape_map:
                source_id = shape_map[source_name]
                target_id = shape_map[target_name]

                # Determine connector type
                connector_type = AIGenerator._get_connector_type(
                    relationship["type"],
                    intent.diagram_type
                )

                engine.add_connector(
                    connector_type,
                    source_id,
                    target_id
                )

        # Apply auto-layout
        layout_type = intent.layout_preference or AIGenerator._get_default_layout(intent.diagram_type)

        if layout_type:
            positions = LayoutEngine.apply_layout(
                layout_type,
                engine.shapes,
                engine.connectors
            )

            # Update shape positions
            for shape_id, position in positions.items():
                engine.update_shape(shape_id, position=position)

        return engine

    @staticmethod
    def _get_default_style(diagram_type: str, index: int) -> ShapeStyle:
        """Get default style based on diagram type."""
        color_palettes = {
            "flowchart": ["#87CEEB", "#90EE90", "#FFD700", "#FFB6C1", "#DDA0DD"],
            "org_chart": ["#4A90E2", "#7ED321", "#F8E71C", "#BD10E0", "#50E3C2"],
            "network": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
            "uml": ["#E3F2FD", "#C8E6C9", "#FFF9C4", "#FFCCBC"],
        }

        colors = color_palettes.get(diagram_type, color_palettes["flowchart"])
        fill_color = colors[index % len(colors)]

        return ShapeStyle(fill_color=fill_color)

    @staticmethod
    def _get_connector_type(relationship_type: str, diagram_type: str) -> ConnectorType:
        """Get connector type based on relationship and diagram type."""
        if diagram_type == "flowchart":
            return ConnectorType.ELBOW
        elif diagram_type == "org_chart":
            return ConnectorType.STRAIGHT
        elif diagram_type == "network":
            return ConnectorType.STRAIGHT
        else:
            return ConnectorType.CURVED

    @staticmethod
    def _get_default_layout(diagram_type: str) -> str:
        """Get default layout for diagram type."""
        layout_map = {
            "flowchart": "hierarchical",
            "org_chart": "tree",
            "network": "hierarchical",
            "uml": "hierarchical",
            "bpmn": "hierarchical"
        }

        return layout_map.get(diagram_type, "organic")

    @staticmethod
    def optimize_layout(engine: DiagramEngine, layout_type: Optional[str] = None) -> DiagramEngine:
        """
        Optimize diagram layout automatically.

        Args:
            engine: DiagramEngine to optimize
            layout_type: Optional specific layout type to use

        Returns:
            Optimized DiagramEngine
        """
        if not layout_type:
            # Auto-detect best layout based on diagram structure
            layout_type = AIGenerator._detect_best_layout(engine)

        # Apply layout
        positions = LayoutEngine.apply_layout(
            layout_type,
            engine.shapes,
            engine.connectors
        )

        # Update positions
        for shape_id, position in positions.items():
            engine.update_shape(shape_id, position=position)

        return engine

    @staticmethod
    def _detect_best_layout(engine: DiagramEngine) -> str:
        """Detect the best layout algorithm for a diagram."""
        # Analyze diagram structure
        num_shapes = len(engine.shapes)
        num_connectors = len(engine.connectors)

        if num_connectors == 0:
            return "grid"

        # Calculate average connections per shape
        avg_connections = num_connectors / num_shapes if num_shapes > 0 else 0

        # Check if it's a tree structure
        is_tree = AIGenerator._is_tree_structure(engine)

        if is_tree:
            return "tree"
        elif avg_connections < 1.5:
            return "hierarchical"
        elif avg_connections > 3:
            return "circular"
        else:
            return "organic"

    @staticmethod
    def _is_tree_structure(engine: DiagramEngine) -> bool:
        """Check if diagram has a tree structure."""
        # A tree has n-1 edges for n nodes and no cycles
        n = len(engine.shapes)
        m = len(engine.connectors)

        if m != n - 1:
            return False

        # Simple cycle detection (BFS)
        # In production, implement proper cycle detection
        return True  # Simplified

    @staticmethod
    def suggest_improvements(engine: DiagramEngine) -> List[Dict[str, Any]]:
        """
        Suggest improvements to a diagram.

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Check for overlapping shapes
        overlaps = AIGenerator._detect_overlaps(engine)
        if overlaps:
            suggestions.append({
                "type": "overlap",
                "severity": "warning",
                "message": f"Found {len(overlaps)} overlapping shapes",
                "action": "Apply auto-layout to fix overlaps",
                "overlapping_shapes": overlaps
            })

        # Check for disconnected shapes
        disconnected = AIGenerator._find_disconnected_shapes(engine)
        if disconnected:
            suggestions.append({
                "type": "disconnected",
                "severity": "info",
                "message": f"Found {len(disconnected)} disconnected shapes",
                "shapes": disconnected
            })

        # Check for inconsistent styling
        style_issues = AIGenerator._check_style_consistency(engine)
        if style_issues:
            suggestions.append({
                "type": "styling",
                "severity": "info",
                "message": "Inconsistent shape styling detected",
                "action": "Apply consistent color scheme",
                "details": style_issues
            })

        # Check diagram complexity
        if len(engine.shapes) > 50:
            suggestions.append({
                "type": "complexity",
                "severity": "warning",
                "message": "Diagram is very complex with many shapes",
                "action": "Consider using layers or breaking into multiple diagrams"
            })

        # Check for very long connections
        long_connections = AIGenerator._find_long_connections(engine)
        if long_connections:
            suggestions.append({
                "type": "layout",
                "severity": "info",
                "message": f"Found {len(long_connections)} very long connections",
                "action": "Optimize layout to shorten connections"
            })

        return suggestions

    @staticmethod
    def _detect_overlaps(engine: DiagramEngine) -> List[Tuple[str, str]]:
        """Detect overlapping shapes."""
        overlaps = []
        shape_list = list(engine.shapes.values())

        for i, shape1 in enumerate(shape_list):
            for shape2 in shape_list[i + 1:]:
                if AIGenerator._shapes_overlap(shape1, shape2):
                    overlaps.append((shape1.id, shape2.id))

        return overlaps

    @staticmethod
    def _shapes_overlap(shape1, shape2) -> bool:
        """Check if two shapes overlap."""
        return not (
            shape1.position.x + shape1.width < shape2.position.x or
            shape2.position.x + shape2.width < shape1.position.x or
            shape1.position.y + shape1.height < shape2.position.y or
            shape2.position.y + shape2.height < shape1.position.y
        )

    @staticmethod
    def _find_disconnected_shapes(engine: DiagramEngine) -> List[str]:
        """Find shapes with no connections."""
        connected_shapes = set()

        for connector in engine.connectors.values():
            if connector.source_shape_id:
                connected_shapes.add(connector.source_shape_id)
            if connector.target_shape_id:
                connected_shapes.add(connector.target_shape_id)

        disconnected = [
            shape_id for shape_id in engine.shapes
            if shape_id not in connected_shapes
        ]

        return disconnected

    @staticmethod
    def _check_style_consistency(engine: DiagramEngine) -> Dict[str, Any]:
        """Check for style consistency issues."""
        colors_used = set()
        font_sizes_used = set()

        for shape in engine.shapes.values():
            colors_used.add(shape.style.fill_color)
            font_sizes_used.add(shape.style.font_size)

        return {
            "unique_colors": len(colors_used),
            "unique_font_sizes": len(font_sizes_used),
            "needs_standardization": len(colors_used) > 10 or len(font_sizes_used) > 3
        }

    @staticmethod
    def _find_long_connections(engine: DiagramEngine) -> List[str]:
        """Find very long connector lines."""
        long_connections = []
        threshold = 500  # pixels

        for conn_id, connector in engine.connectors.items():
            start = connector.get_start_point(engine.shapes)
            end = connector.get_end_point(engine.shapes)

            dx = end.x - start.x
            dy = end.y - start.y
            distance = (dx ** 2 + dy ** 2) ** 0.5

            if distance > threshold:
                long_connections.append(conn_id)

        return long_connections

    @staticmethod
    def apply_color_scheme(
        engine: DiagramEngine,
        scheme: str = "professional"
    ) -> DiagramEngine:
        """
        Apply a color scheme to all shapes.

        Args:
            engine: DiagramEngine to style
            scheme: Color scheme name ('professional', 'pastel', 'vibrant', 'monochrome')

        Returns:
            Styled DiagramEngine
        """
        schemes = {
            "professional": ["#2E4057", "#048A81", "#54C6EB", "#8CBEB2", "#F2B134"],
            "pastel": ["#FFB6C1", "#FFD700", "#98D8C8", "#A8E6CF", "#DDA0DD"],
            "vibrant": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"],
            "monochrome": ["#2C3E50", "#34495E", "#7F8C8D", "#95A5A6", "#BDC3C7"]
        }

        colors = schemes.get(scheme, schemes["professional"])

        # Apply colors to shapes
        for i, shape in enumerate(engine.shapes.values()):
            color = colors[i % len(colors)]
            shape.style.fill_color = color

        return engine
