"""
Main Word Editor Class

Provides the core editing functionality for the NEXUS word processor.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class DocumentStatus(Enum):
    """Document status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class DocumentMetadata:
    """Document metadata structure"""
    id: str
    title: str
    author: str
    created_at: datetime
    modified_at: datetime
    tags: List[str]
    description: str
    status: DocumentStatus
    word_count: int
    character_count: int
    version: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['modified_at'] = self.modified_at.isoformat()
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentMetadata':
        """Create metadata from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        data['status'] = DocumentStatus(data['status'])
        return cls(**data)


class WordEditor:
    """
    Main Word Editor class providing core document editing functionality.

    Features:
    - Rich text editing with full formatting support
    - Undo/redo with 50 levels
    - Auto-save functionality
    - Version history tracking
    - Document statistics
    - Search and replace
    """

    def __init__(self, user_id: str, document_id: Optional[str] = None):
        """
        Initialize the word editor.

        Args:
            user_id: ID of the current user
            document_id: Optional existing document ID to load
        """
        self.user_id = user_id
        self.document_id = document_id or str(uuid.uuid4())

        # Document content and state
        self.content: Dict[str, Any] = {"ops": []}  # Quill Delta format
        self.metadata: Optional[DocumentMetadata] = None

        # Undo/redo stacks (max 50 levels)
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.max_undo_levels = 50

        # Auto-save settings
        self.auto_save_enabled = True
        self.auto_save_interval = 30  # seconds
        self.last_save_time: Optional[datetime] = None
        self.is_modified = False

        # Statistics cache
        self._stats_cache: Optional[Dict[str, Any]] = None
        self._stats_cache_time: Optional[datetime] = None

        # Initialize metadata if new document
        if not document_id:
            self._initialize_new_document()

    def _initialize_new_document(self) -> None:
        """Initialize a new document with default metadata"""
        self.metadata = DocumentMetadata(
            id=self.document_id,
            title="Untitled Document",
            author=self.user_id,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            tags=[],
            description="",
            status=DocumentStatus.DRAFT,
            word_count=0,
            character_count=0,
            version=1
        )

    def set_content(self, content: Dict[str, Any]) -> None:
        """
        Set the document content (Quill Delta format).

        Args:
            content: Document content in Quill Delta format
        """
        # Save current state to undo stack
        if self.content["ops"]:
            self._save_to_undo_stack()

        self.content = content
        self.is_modified = True
        self._invalidate_stats_cache()

        # Update metadata
        if self.metadata:
            self.metadata.modified_at = datetime.now()

    def get_content(self) -> Dict[str, Any]:
        """
        Get the current document content.

        Returns:
            Document content in Quill Delta format
        """
        return self.content

    def apply_delta(self, delta: Dict[str, Any]) -> None:
        """
        Apply a delta change to the document.

        Args:
            delta: Change delta in Quill Delta format
        """
        self._save_to_undo_stack()

        # Apply delta to content (simplified - in production use quill-delta library)
        if "ops" in delta:
            self.content["ops"].extend(delta["ops"])

        self.is_modified = True
        self._invalidate_stats_cache()

        if self.metadata:
            self.metadata.modified_at = datetime.now()

    def undo(self) -> bool:
        """
        Undo the last change.

        Returns:
            True if undo was successful, False if nothing to undo
        """
        if not self.undo_stack:
            return False

        # Save current state to redo stack
        self.redo_stack.append(self.content.copy())
        if len(self.redo_stack) > self.max_undo_levels:
            self.redo_stack.pop(0)

        # Restore previous state
        self.content = self.undo_stack.pop()
        self.is_modified = True
        self._invalidate_stats_cache()

        return True

    def redo(self) -> bool:
        """
        Redo the last undone change.

        Returns:
            True if redo was successful, False if nothing to redo
        """
        if not self.redo_stack:
            return False

        # Save current state to undo stack (without clearing redo stack)
        self.undo_stack.append(self.content.copy())
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)

        # Restore redo state
        self.content = self.redo_stack.pop()
        self.is_modified = True
        self._invalidate_stats_cache()

        return True

    def _save_to_undo_stack(self) -> None:
        """Save current content to undo stack"""
        self.undo_stack.append(self.content.copy())
        if len(self.undo_stack) > self.max_undo_levels:
            self.undo_stack.pop(0)

        # Clear redo stack when new change is made
        self.redo_stack.clear()

    def _invalidate_stats_cache(self) -> None:
        """Invalidate the statistics cache"""
        self._stats_cache = None
        self._stats_cache_time = None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get document statistics.

        Returns:
            Dictionary containing word count, character count, etc.
        """
        # Use cache if available and recent (< 1 second old)
        if self._stats_cache and self._stats_cache_time:
            age = (datetime.now() - self._stats_cache_time).total_seconds()
            if age < 1.0:
                return self._stats_cache

        # Calculate statistics from content
        text = self._extract_text_from_content()

        words = text.split()
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        paragraphs = text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # Calculate reading time (average 200 words per minute)
        reading_time_minutes = len(words) / 200

        # Calculate speaking time (average 150 words per minute)
        speaking_time_minutes = len(words) / 150

        stats = {
            'word_count': len(words),
            'character_count': len(text),
            'character_count_no_spaces': len(text.replace(' ', '')),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'reading_time_minutes': round(reading_time_minutes, 1),
            'speaking_time_minutes': round(speaking_time_minutes, 1),
            'avg_words_per_sentence': round(len(words) / max(len(sentences), 1), 1),
        }

        # Cache the results
        self._stats_cache = stats
        self._stats_cache_time = datetime.now()

        # Update metadata
        if self.metadata:
            self.metadata.word_count = stats['word_count']
            self.metadata.character_count = stats['character_count']

        return stats

    def _extract_text_from_content(self) -> str:
        """
        Extract plain text from Quill Delta content.

        Returns:
            Plain text string
        """
        text_parts = []

        for op in self.content.get("ops", []):
            if isinstance(op.get("insert"), str):
                text_parts.append(op["insert"])

        return ''.join(text_parts)

    def find_and_replace(
        self,
        find_text: str,
        replace_text: str,
        case_sensitive: bool = False,
        whole_word: bool = False
    ) -> int:
        """
        Find and replace text in the document.

        Args:
            find_text: Text to find
            replace_text: Text to replace with
            case_sensitive: Whether search is case-sensitive
            whole_word: Whether to match whole words only

        Returns:
            Number of replacements made
        """
        self._save_to_undo_stack()

        text = self._extract_text_from_content()

        if not case_sensitive:
            # Case-insensitive search
            import re
            if whole_word:
                pattern = r'\b' + re.escape(find_text) + r'\b'
                new_text, count = re.subn(pattern, replace_text, text, flags=re.IGNORECASE)
            else:
                new_text, count = re.subn(
                    re.escape(find_text),
                    replace_text,
                    text,
                    flags=re.IGNORECASE
                )
        else:
            # Case-sensitive search
            if whole_word:
                import re
                pattern = r'\b' + re.escape(find_text) + r'\b'
                new_text, count = re.subn(pattern, replace_text, text)
            else:
                count = text.count(find_text)
                new_text = text.replace(find_text, replace_text)

        if count > 0:
            # Update content with replaced text
            self.content = {"ops": [{"insert": new_text}]}
            self.is_modified = True
            self._invalidate_stats_cache()

        return count

    def get_metadata(self) -> Optional[DocumentMetadata]:
        """
        Get document metadata.

        Returns:
            DocumentMetadata object or None
        """
        return self.metadata

    def update_metadata(self, **kwargs) -> None:
        """
        Update document metadata.

        Args:
            **kwargs: Metadata fields to update
        """
        if not self.metadata:
            return

        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)

        self.metadata.modified_at = datetime.now()
        self.is_modified = True

    def needs_save(self) -> bool:
        """
        Check if document needs to be saved.

        Returns:
            True if document has unsaved changes
        """
        return self.is_modified

    def mark_as_saved(self) -> None:
        """Mark document as saved"""
        self.is_modified = False
        self.last_save_time = datetime.now()

    def increment_version(self) -> None:
        """Increment document version number"""
        if self.metadata:
            self.metadata.version += 1

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert editor state to dictionary.

        Returns:
            Dictionary representation of editor state
        """
        return {
            'document_id': self.document_id,
            'user_id': self.user_id,
            'content': self.content,
            'metadata': self.metadata.to_dict() if self.metadata else None,
            'is_modified': self.is_modified,
            'last_save_time': self.last_save_time.isoformat() if self.last_save_time else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WordEditor':
        """
        Create editor from dictionary.

        Args:
            data: Dictionary representation of editor state

        Returns:
            WordEditor instance
        """
        editor = cls(
            user_id=data['user_id'],
            document_id=data['document_id']
        )

        editor.content = data['content']

        if data.get('metadata'):
            editor.metadata = DocumentMetadata.from_dict(data['metadata'])

        editor.is_modified = data.get('is_modified', False)

        if data.get('last_save_time'):
            editor.last_save_time = datetime.fromisoformat(data['last_save_time'])

        return editor
