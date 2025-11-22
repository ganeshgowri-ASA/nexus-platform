"""
NEXUS Wiki System Module

A comprehensive, production-ready wiki system with advanced features including:
- Rich text editing with markdown support
- Version control and history tracking
- Advanced search (full-text and semantic)
- Real-time collaboration
- Granular permissions
- AI-powered content assistance
- Multi-format import/export
- Analytics and insights

Author: NEXUS Platform Team
Version: 1.0.0
"""

from typing import Optional

# Module metadata
__version__ = "1.0.0"
__author__ = "NEXUS Platform Team"
__all__ = [
    "WikiPage",
    "WikiSection",
    "WikiCategory",
    "WikiTag",
    "WikiLink",
    "WikiAttachment",
    "WikiHistory",
    "WikiComment",
    "WikiPermission",
    "WikiTemplate",
    "PageManager",
    "EditorService",
    "VersioningService",
    "LinkingService",
    "CategoryService",
    "SearchService",
    "NavigationService",
    "TemplateService",
    "CollaborationService",
    "PermissionService",
    "MacroService",
    "ExportService",
    "ImportService",
    "AttachmentService",
    "CommentService",
    "AnalyticsService",
    "AIAssistantService",
    "IntegrationService",
]

# Lazy imports to avoid circular dependencies
def get_page_manager():
    """Get an instance of PageManager."""
    from modules.wiki.pages import PageManager
    return PageManager()


def get_editor_service():
    """Get an instance of EditorService."""
    from modules.wiki.editor import EditorService
    return EditorService()


def get_versioning_service():
    """Get an instance of VersioningService."""
    from modules.wiki.versioning import VersioningService
    return VersioningService()


def get_search_service():
    """Get an instance of SearchService."""
    from modules.wiki.search import SearchService
    return SearchService()


def get_ai_assistant():
    """Get an instance of AIAssistantService."""
    from modules.wiki.ai_assistant import AIAssistantService
    return AIAssistantService()
