"""Service layer for notes module - contains business logic."""

import logging
import markdown
from datetime import datetime
from typing import Any, Dict, List, Optional

import bleach
from sqlalchemy.orm import Session

from nexus.core.exceptions import NotFoundException, ValidationException

from .models import Note, NoteStatus, NoteVersion, Tag
from .repository import (
    AttachmentRepository,
    CommentRepository,
    NoteRepository,
    NotebookRepository,
    TagRepository,
    TemplateRepository,
)
from .schemas import NoteCreate, NoteUpdate

logger = logging.getLogger(__name__)


class NoteService:
    """Service for note operations."""

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.note_repo = NoteRepository(db)
        self.notebook_repo = NotebookRepository(db)
        self.tag_repo = TagRepository(db)
        self.template_repo = TemplateRepository(db)
        self.attachment_repo = AttachmentRepository(db)
        self.comment_repo = CommentRepository(db)

    def create_note(
        self,
        user_id: str,
        data: NoteCreate,
    ) -> Note:
        """Create a new note.

        Args:
            user_id: ID of the user creating the note
            data: Note creation data

        Returns:
            Created note

        Raises:
            ValidationException: If validation fails
        """
        # If template_id provided, load template content
        if data.template_id:
            template = self.template_repo.get_by_id(data.template_id)
            if template:
                data.content = template.content
                self.template_repo.increment_usage(data.template_id)

        # Convert markdown to HTML if provided
        content_html = None
        if data.content_markdown:
            content_html = self._markdown_to_html(data.content_markdown)

        # Create note
        note = self.note_repo.create(
            user_id=user_id,
            title=data.title,
            content=data.content,
            content_markdown=data.content_markdown,
            content_html=content_html,
            notebook_id=data.notebook_id,
            section_id=data.section_id,
            is_favorite=data.is_favorite,
            color=data.color,
        )

        # Add tags
        if data.tags:
            self._add_tags_to_note(note.id, user_id, data.tags)

        # Refresh to load relationships
        self.db.refresh(note)
        logger.info(f"Created note {note.id} for user {user_id}")
        return note

    def get_note(self, note_id: int, user_id: str) -> Note:
        """Get a note by ID.

        Args:
            note_id: Note ID
            user_id: User ID (for permission check)

        Returns:
            Note

        Raises:
            NotFoundException: If note not found or user doesn't have access
        """
        note = self.note_repo.get_by_id(note_id)
        if not note:
            raise NotFoundException(f"Note {note_id} not found")

        # Check permissions
        if not self._can_access_note(note, user_id):
            raise NotFoundException(f"Note {note_id} not found")

        # Update last viewed timestamp
        note.last_viewed_at = datetime.utcnow()
        self.db.commit()

        return note

    def update_note(
        self,
        note_id: int,
        user_id: str,
        data: NoteUpdate,
        create_version: bool = True,
    ) -> Note:
        """Update a note.

        Args:
            note_id: Note ID
            user_id: User ID
            data: Update data
            create_version: Whether to create a version snapshot

        Returns:
            Updated note

        Raises:
            NotFoundException: If note not found
        """
        note = self.get_note(note_id, user_id)

        # Create version snapshot if requested
        if create_version and (data.title or data.content or data.content_markdown):
            self._create_version_snapshot(note, user_id, "Manual save")

        # Update content
        update_data = {}
        if data.title is not None:
            update_data["title"] = data.title
        if data.content is not None:
            update_data["content"] = data.content
        if data.content_markdown is not None:
            update_data["content_markdown"] = data.content_markdown
            update_data["content_html"] = self._markdown_to_html(data.content_markdown)

        # Update metadata
        if data.notebook_id is not None:
            update_data["notebook_id"] = data.notebook_id
        if data.section_id is not None:
            update_data["section_id"] = data.section_id
        if data.status is not None:
            update_data["status"] = data.status
        if data.is_favorite is not None:
            update_data["is_favorite"] = data.is_favorite
        if data.is_pinned is not None:
            update_data["is_pinned"] = data.is_pinned
        if data.color is not None:
            update_data["color"] = data.color

        # Update tags
        if data.tags is not None:
            self._update_note_tags(note_id, user_id, data.tags)

        # Perform update
        note = self.note_repo.update(note_id, **update_data)

        logger.info(f"Updated note {note_id}")
        return note

    def delete_note(self, note_id: int, user_id: str, permanent: bool = False) -> bool:
        """Delete a note.

        Args:
            note_id: Note ID
            user_id: User ID
            permanent: If True, permanently delete; otherwise soft delete

        Returns:
            True if deleted

        Raises:
            NotFoundException: If note not found
        """
        note = self.get_note(note_id, user_id)

        success = self.note_repo.delete(note_id, soft_delete=not permanent)
        logger.info(f"Deleted note {note_id} (permanent={permanent})")
        return success

    def list_notes(
        self,
        user_id: str,
        notebook_id: Optional[int] = None,
        status: Optional[NoteStatus] = NoteStatus.ACTIVE,
        favorites_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Note]:
        """List notes for a user.

        Args:
            user_id: User ID
            notebook_id: Optional notebook filter
            status: Note status
            favorites_only: Only return favorites
            limit: Maximum results
            offset: Results offset

        Returns:
            List of notes
        """
        if favorites_only:
            return self.note_repo.get_favorites(user_id, limit, offset)
        elif notebook_id:
            return self.note_repo.get_by_notebook(notebook_id, user_id, limit, offset)
        else:
            return self.note_repo.get_by_user(user_id, status, limit, offset)

    def search_notes(
        self,
        user_id: str,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notebooks: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        is_favorite: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Note]:
        """Search notes with filters.

        Args:
            user_id: User ID
            query: Text search query
            tags: Filter by tags
            notebooks: Filter by notebooks
            date_from: Start date
            date_to: End date
            is_favorite: Favorite filter
            limit: Maximum results
            offset: Results offset

        Returns:
            List of matching notes
        """
        return self.note_repo.search(
            user_id=user_id,
            query=query,
            tag_names=tags,
            notebook_ids=notebooks,
            date_from=date_from,
            date_to=date_to,
            is_favorite=is_favorite,
            limit=limit,
            offset=offset,
        )

    def toggle_favorite(self, note_id: int, user_id: str) -> Note:
        """Toggle favorite status of a note.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            Updated note
        """
        note = self.get_note(note_id, user_id)
        return self.note_repo.update(note_id, is_favorite=not note.is_favorite)

    def archive_note(self, note_id: int, user_id: str) -> Note:
        """Archive a note.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            Archived note
        """
        note = self.get_note(note_id, user_id)
        return self.note_repo.update(note_id, status=NoteStatus.ARCHIVED)

    def restore_note(self, note_id: int, user_id: str) -> Note:
        """Restore an archived or deleted note.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            Restored note
        """
        note = self.note_repo.get_by_id(note_id)
        if not note or not self._can_access_note(note, user_id):
            raise NotFoundException(f"Note {note_id} not found")

        return self.note_repo.update(note_id, status=NoteStatus.ACTIVE)

    def get_note_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for user's notes.

        Args:
            user_id: User ID

        Returns:
            Dictionary with statistics
        """
        return {
            "total": self.note_repo.count_by_user(user_id),
            "active": self.note_repo.count_by_user(user_id, NoteStatus.ACTIVE),
            "archived": self.note_repo.count_by_user(user_id, NoteStatus.ARCHIVED),
            "favorites": len(self.note_repo.get_favorites(user_id, limit=10000)),
            "tags": len(self.tag_repo.get_by_user(user_id)),
            "notebooks": len(self.notebook_repo.get_by_user(user_id)),
        }

    def share_note(
        self, note_id: int, user_id: str, share_with_user_ids: List[str], permission: str
    ) -> Note:
        """Share a note with other users.

        Args:
            note_id: Note ID
            user_id: Owner user ID
            share_with_user_ids: List of user IDs to share with
            permission: Permission level (view, comment, edit)

        Returns:
            Updated note
        """
        note = self.get_note(note_id, user_id)

        # Update shared_with field
        shared_with = note.shared_with or []
        for uid in share_with_user_ids:
            shared_with.append({"user_id": uid, "permission": permission})

        return self.note_repo.update(note_id, shared_with=shared_with)

    # Private helper methods

    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to HTML.

        Args:
            markdown_text: Markdown content

        Returns:
            HTML content
        """
        # Convert markdown to HTML
        html = markdown.markdown(
            markdown_text,
            extensions=[
                "extra",
                "codehilite",
                "tables",
                "fenced_code",
                "nl2br",
            ],
        )

        # Sanitize HTML to prevent XSS
        allowed_tags = [
            "p",
            "br",
            "strong",
            "em",
            "u",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "blockquote",
            "code",
            "pre",
            "ul",
            "ol",
            "li",
            "a",
            "img",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
        ]
        allowed_attrs = {
            "a": ["href", "title"],
            "img": ["src", "alt", "title"],
            "code": ["class"],
            "pre": ["class"],
        }

        clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
        return clean_html

    def _add_tags_to_note(self, note_id: int, user_id: str, tag_names: List[str]) -> None:
        """Add tags to a note.

        Args:
            note_id: Note ID
            user_id: User ID
            tag_names: List of tag names
        """
        for tag_name in tag_names:
            tag = self.tag_repo.get_or_create(user_id, tag_name.strip())
            try:
                self.tag_repo.add_tag_to_note(note_id, tag.id)
            except Exception:
                # Tag already exists on note
                pass

    def _update_note_tags(self, note_id: int, user_id: str, tag_names: List[str]) -> None:
        """Update all tags for a note.

        Args:
            note_id: Note ID
            user_id: User ID
            tag_names: New list of tag names
        """
        # Get current note
        note = self.note_repo.get_by_id(note_id)
        if not note:
            return

        # Remove existing tags
        for tag in note.tags:
            self.tag_repo.remove_tag_from_note(note_id, tag.id)

        # Add new tags
        self._add_tags_to_note(note_id, user_id, tag_names)

    def _can_access_note(self, note: Note, user_id: str) -> bool:
        """Check if user can access a note.

        Args:
            note: Note object
            user_id: User ID

        Returns:
            True if user has access
        """
        # Owner always has access
        if note.user_id == user_id:
            return True

        # Check if note is public
        if note.is_public:
            return True

        # Check if shared with user
        if note.shared_with:
            for share in note.shared_with:
                if share.get("user_id") == user_id:
                    return True

        return False

    def _create_version_snapshot(
        self, note: Note, user_id: str, change_summary: Optional[str] = None
    ) -> NoteVersion:
        """Create a version snapshot of a note.

        Args:
            note: Note to snapshot
            user_id: User creating the version
            change_summary: Optional summary of changes

        Returns:
            Created version
        """
        version = NoteVersion(
            note_id=note.id,
            version=note.version,
            title=note.title,
            content=note.content,
            content_html=note.content_html,
            created_by=user_id,
            change_summary=change_summary,
        )
        self.db.add(version)

        # Increment note version
        note.version += 1
        self.db.commit()

        logger.info(f"Created version snapshot for note {note.id}")
        return version
