"""Notes module for Nexus Platform.

This module provides comprehensive note-taking functionality including:
- Rich text editing with markdown support
- Organization via notebooks, sections, and tags
- Full-text search and filtering
- Collaboration and sharing
- Templates and attachments
- AI-powered features
- Export to multiple formats
"""

from .models import Attachment, Comment, Note, Notebook, SavedSearch, Section, Tag, Template
from .schemas import (
    AttachmentCreate,
    CommentCreate,
    NoteCreate,
    NoteUpdate,
    NotebookCreate,
    SectionCreate,
    TagCreate,
    TemplateCreate,
)
from .service import NoteService

__all__ = [
    # Models
    "Note",
    "Notebook",
    "Section",
    "Tag",
    "Template",
    "Attachment",
    "Comment",
    "SavedSearch",
    # Schemas
    "NoteCreate",
    "NoteUpdate",
    "NotebookCreate",
    "SectionCreate",
    "TagCreate",
    "TemplateCreate",
    "AttachmentCreate",
    "CommentCreate",
    # Service
    "NoteService",
]
