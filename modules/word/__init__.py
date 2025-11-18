"""
NEXUS Word Processing Editor Module

A world-class word processor with rich text editing, AI assistance,
real-time collaboration, and comprehensive document management.
"""

from .editor import WordEditor
from .formatting import TextFormatter
from .document_manager import DocumentManager
from .ai_assistant import AIWritingAssistant
from .collaboration import CollaborationManager
from .templates import TemplateManager

__version__ = "1.0.0"
__all__ = [
    "WordEditor",
    "TextFormatter",
    "DocumentManager",
    "AIWritingAssistant",
    "CollaborationManager",
    "TemplateManager",
]
