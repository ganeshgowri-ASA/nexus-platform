<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
"""NEXUS Platform modules."""
=======
"""NEXUS Platform Modules."""
>>>>>>> origin/claude/ab-testing-module-01D3o2ivEGbVpUmsgesHtDjA
=======
"""
NEXUS Platform Modules
Collection of 24 integrated productivity modules
"""

__all__ = [
    # Core productivity modules
    "word",
    "excel",
    "powerpoint",
    "email",
    "chat",
    "projects",
    "flowcharts",
    "analytics",

    # Organization modules
    "calendar",
    "files",
    "notes",
    "database_manager",

    # Creative & Design
    "design",

    # Communication
    "video_calls",

    # AI & Intelligence
    "ai_assistant",
    "search",

    # Security & Management
    "password_manager",
    "settings",

    # Collaboration
    "team_collaboration",
    "knowledge_base",

    # Utilities
    "reports",
    "notifications",
    "web_browser",
    "backup_sync",
]
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
=======
"""
NEXUS Platform Modules
Sessions 36-45: Advanced Features
"""

__all__ = [
    'session36_flowchart',
    'session37_mindmap',
    'session38_infographics',
    'session39_whiteboard',
    'session40_gantt',
    'session41_database',
    'session42_api_tester',
    'session43_code_editor',
    'session44_website_builder',
    'session45_blog'
]
>>>>>>> origin/claude/nexus-batch-features-01Tj2bV7P7zrLp4WgtRXnoS8
=======
"""NEXUS Platform Modules."""
>>>>>>> origin/claude/build-etl-integration-hub-01CuRDV55w16up98jJhFz8Ts
=======
"""Modules registry for NEXUS platform."""

from typing import Dict, Type
from core.base_module import BaseModule


def get_available_modules() -> Dict[str, Type[BaseModule]]:
    """
    Get all available modules.

    Returns:
        Dictionary mapping module names to module classes
    """
    from modules.pipeline.module import PipelineModule

    return {
        "pipeline": PipelineModule,
    }


def load_modules() -> Dict[str, BaseModule]:
    """
    Load and instantiate all modules.

    Returns:
        Dictionary of instantiated modules
    """
    modules = {}
    available_modules = get_available_modules()

    for name, module_class in available_modules.items():
        try:
            modules[name] = module_class()
        except Exception as e:
            print(f"Error loading module {name}: {e}")

    return modules
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
