"""
NEXUS Flowchart & Diagram Editor Module

A comprehensive diagramming tool with 100+ shapes, auto-layout algorithms,
AI-powered generation, real-time collaboration, and multi-format export.

Features:
- 100+ professional shapes across multiple categories
- Smart connectors with auto-routing
- Auto-layout algorithms (hierarchical, organic, circular, tree, grid)
- Pre-built templates for common diagrams
- Export to SVG, PNG, PDF, Visio, and more
- Real-time collaboration with version control
- AI-powered diagram generation from text
- Full Streamlit UI for interactive editing

Rival to: Lucidchart, Draw.io, Visio
"""

__version__ = "1.0.0"
__author__ = "NEXUS Platform"

# Core exports
from .shapes import (
    Shape,
    Point,
    ShapeStyle,
    ShapeCategory,
    ConnectorAnchor,
    shape_library
)

from .connectors import (
    Connector,
    ConnectorType,
    ConnectorStyle,
    ArrowType,
    LineStyle,
    ConnectorLabel,
    ConnectorRouter
)

from .diagram_engine import (
    DiagramEngine,
    DiagramMetadata,
    DiagramSettings,
    Layer
)

from .layout import (
    LayoutEngine,
    LayoutConfig,
    LayoutAlgorithm,
    HierarchicalLayout,
    OrganicLayout,
    CircularLayout,
    TreeLayout,
    GridLayout
)

from .templates import (
    DiagramTemplate,
    template_library,
    BasicFlowchartTemplate,
    OrgChartTemplate,
    NetworkDiagramTemplate,
    CloudArchitectureTemplate,
    UMLClassDiagramTemplate,
    WireframeTemplate,
    BPMNProcessTemplate
)

from .export import (
    DiagramExporter,
    SVGExporter,
    PNGExporter,
    PDFExporter,
    VisioExporter,
    EmbedCodeGenerator
)

from .collaboration import (
    CollaborationEngine,
    User,
    Change,
    Comment,
    Version,
    ChangeType
)

from .ai_generator import (
    AIGenerator,
    NaturalLanguageParser,
    DiagramIntent
)

# UI exports
from .streamlit_ui import main as run_ui


__all__ = [
    # Core classes
    "DiagramEngine",
    "DiagramMetadata",
    "DiagramSettings",
    "Layer",

    # Shapes
    "Shape",
    "Point",
    "ShapeStyle",
    "ShapeCategory",
    "ConnectorAnchor",
    "shape_library",

    # Connectors
    "Connector",
    "ConnectorType",
    "ConnectorStyle",
    "ArrowType",
    "LineStyle",
    "ConnectorLabel",
    "ConnectorRouter",

    # Layout
    "LayoutEngine",
    "LayoutConfig",
    "LayoutAlgorithm",
    "HierarchicalLayout",
    "OrganicLayout",
    "CircularLayout",
    "TreeLayout",
    "GridLayout",

    # Templates
    "DiagramTemplate",
    "template_library",
    "BasicFlowchartTemplate",
    "OrgChartTemplate",
    "NetworkDiagramTemplate",
    "CloudArchitectureTemplate",
    "UMLClassDiagramTemplate",
    "WireframeTemplate",
    "BPMNProcessTemplate",

    # Export
    "DiagramExporter",
    "SVGExporter",
    "PNGExporter",
    "PDFExporter",
    "VisioExporter",
    "EmbedCodeGenerator",

    # Collaboration
    "CollaborationEngine",
    "User",
    "Change",
    "Comment",
    "Version",
    "ChangeType",

    # AI
    "AIGenerator",
    "NaturalLanguageParser",
    "DiagramIntent",

    # UI
    "run_ui"
]


def create_diagram(template: str = None) -> DiagramEngine:
    """
    Quick helper to create a new diagram, optionally from a template.

    Args:
        template: Optional template name to use

    Returns:
        DiagramEngine instance
    """
    if template:
        return template_library.create_from_template(template)
    else:
        return DiagramEngine()


def generate_diagram_from_text(description: str) -> DiagramEngine:
    """
    Generate a diagram from natural language description.

    Args:
        description: Natural language description of the diagram

    Returns:
        DiagramEngine with generated diagram
    """
    return AIGenerator.generate_from_text(description)


# Module metadata
MODULE_INFO = {
    "name": "flowchart",
    "version": __version__,
    "description": "Professional flowchart and diagram editor",
    "features": [
        "100+ professional shapes",
        "Smart connectors with auto-routing",
        "Auto-layout algorithms",
        "Pre-built templates",
        "Multi-format export (SVG, PNG, PDF, Visio)",
        "Real-time collaboration",
        "AI-powered generation",
        "Full Streamlit UI"
    ],
    "shape_count": shape_library.get_shape_count(),
    "template_count": len(template_library.get_all_templates()),
    "supported_exports": ["SVG", "PNG", "PDF", "Visio", "JSON"],
    "layout_algorithms": ["hierarchical", "organic", "circular", "tree", "grid"]
}


def get_module_info() -> dict:
    """Get information about this module."""
    return MODULE_INFO.copy()
