"""
NEXUS Mind Map Module

A comprehensive mind mapping and brainstorming module with AI-powered features.

Main Components:
- MindMapEngine: Main orchestrator for mind mapping
- MindMapNode: Node representation with rich content
- Branch: Connection between nodes
- LayoutEngine: Automatic layout algorithms
- ThemeManager: Pre-designed themes and styling
- ExportEngine: Export to multiple formats
- CollaborationSession: Real-time collaboration
- AIBrainstormEngine: AI-powered features
- MindMapUI: Streamlit user interface

Example Usage:
    >>> from modules.mindmap import MindMapEngine
    >>> engine = MindMapEngine()
    >>> root_id = engine.create_root_node("My Project")
    >>> child_id = engine.create_node("Task 1", parent_id=root_id)
    >>> engine.apply_layout(LayoutType.MIND_MAP)
    >>> data = engine.export(ExportFormat.JSON)
"""

__version__ = "1.0.0"
__author__ = "NEXUS Platform"

# Core components
from .mind_engine import MindMapEngine
from .nodes import (
    MindMapNode,
    Position,
    NodeStyle,
    NodeShape,
    Priority,
    Attachment,
    Task,
    Comment,
)
from .branches import (
    Branch,
    BranchManager,
    ConnectionType,
    ConnectionStyle,
    LineStyle,
    ArrowType,
    CurveType,
)
from .layout import (
    LayoutEngine,
    LayoutType,
    LayoutConfig,
)
from .themes import (
    ThemeManager,
    Theme,
    ThemeName,
    ColorPalette,
)
from .export import (
    ExportEngine,
    ExportFormat,
)
from .collaboration import (
    CollaborationSession,
    User,
    UserPresence,
    Operation,
    OperationType,
    ChangeSet,
    ConflictResolver,
    ChangeTracker,
)
from .ai_brainstorm import (
    AIBrainstormEngine,
    AIFeature,
)
from .streamlit_ui import (
    MindMapUI,
    main as run_ui,
)

__all__ = [
    # Version
    "__version__",
    "__author__",

    # Main engine
    "MindMapEngine",

    # Nodes
    "MindMapNode",
    "Position",
    "NodeStyle",
    "NodeShape",
    "Priority",
    "Attachment",
    "Task",
    "Comment",

    # Branches
    "Branch",
    "BranchManager",
    "ConnectionType",
    "ConnectionStyle",
    "LineStyle",
    "ArrowType",
    "CurveType",

    # Layout
    "LayoutEngine",
    "LayoutType",
    "LayoutConfig",

    # Themes
    "ThemeManager",
    "Theme",
    "ThemeName",
    "ColorPalette",

    # Export
    "ExportEngine",
    "ExportFormat",

    # Collaboration
    "CollaborationSession",
    "User",
    "UserPresence",
    "Operation",
    "OperationType",
    "ChangeSet",
    "ConflictResolver",
    "ChangeTracker",

    # AI
    "AIBrainstormEngine",
    "AIFeature",

    # UI
    "MindMapUI",
    "run_ui",
]
