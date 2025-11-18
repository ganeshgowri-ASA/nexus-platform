"""
NEXUS Presentation Module - Professional Presentation Editor

A comprehensive presentation creation and editing module with features rivaling
Google Slides and PowerPoint Online.

Components:
- editor: Main presentation engine
- slide_manager: Slide creation and editing
- element_handler: Text, images, shapes management
- animation: Transitions and animations
- template_manager: Slide templates
- theme_builder: Color schemes and fonts
- export_renderer: Export to PDF, PPTX, HTML5
- presenter_view: Presentation mode
- collaboration: Multi-user editing
- ai_assistant: AI-powered content generation
- streamlit_ui: Streamlit user interface
"""

from typing import Dict, Any

__version__ = "1.0.0"
__author__ = "NEXUS Platform"

# Module exports
__all__ = [
    "PresentationEditor",
    "SlideManager",
    "ElementHandler",
    "AnimationEngine",
    "TemplateManager",
    "ThemeBuilder",
    "ExportRenderer",
    "PresenterView",
    "CollaborationManager",
    "AIAssistant",
]


def get_module_info() -> Dict[str, Any]:
    """Get module information and metadata."""
    return {
        "name": "Presentation Editor",
        "version": __version__,
        "description": "Professional presentation creation and editing",
        "features": [
            "Slide Management",
            "Rich Content Elements",
            "Animations & Transitions",
            "Professional Templates",
            "Custom Themes",
            "Multi-format Export",
            "Presenter Mode",
            "Real-time Collaboration",
            "AI Assistant",
        ],
        "supported_formats": {
            "import": ["pptx", "pdf", "json"],
            "export": ["pptx", "pdf", "html5", "png", "jpg", "mp4"],
        },
    }
