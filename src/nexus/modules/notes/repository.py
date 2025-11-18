"""Repository layer for notes module - handles database operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from nexus.core.exceptions import NotFoundException

from .models import (
    Attachment,
    Comment,
    Note,
    NoteStatus,
    NoteTag,
    NoteVersion,
    Notebook,
    SavedSearch,
    Section,
    Tag,
    Template,
)


class NoteRepository:
    """Repository for Note CRUD operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(
        self,
        user_id: str,
        title: str,
        content: Optional[str] = None,
        **kwargs: Any,
    ) -> Note:
        """Create a new note.

        Args:
            user_id: ID of the user creating the note
            title: Note title
            content: Note content
            **kwargs: Additional note attributes

        Returns:
            Created note
        """
        note = Note(user_id=user_id, title=title, content=content, **kwargs)
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_by_id(self, note_id: int) -> Optional[Note]:
        """Get note by ID.

        Args:
            note_id: Note ID

        Returns:
            Note if found, None otherwise
        """
        return (
            self.db.query(Note)
            .options(joinedload(Note.tags), joinedload(Note.attachments))
            .filter(Note.id == note_id)
            .first()
        )

    def get_by_user(
        self,
        user_id: str,
        status: Optional[NoteStatus] = NoteStatus.ACTIVE,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Note]:
        """Get notes by user ID.

        Args:
            user_id: User ID
            status: Note status filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of notes
        """
        query = self.db.query(Note).filter(Note.user_id == user_id)

        if status:
            query = query.filter(Note.status == status)

        return (
            query.options(joinedload(Note.tags))
            .order_by(desc(Note.updated_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_notebook(
        self, notebook_id: int, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Note]:
        """Get notes by notebook.

        Args:
            notebook_id: Notebook ID
            user_id: User ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of notes
        """
        return (
            self.db.query(Note)
            .filter(
                and_(
                    Note.notebook_id == notebook_id,
                    Note.user_id == user_id,
                    Note.status == NoteStatus.ACTIVE,
                )
            )
            .options(joinedload(Note.tags))
            .order_by(desc(Note.updated_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_favorites(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Note]:
        """Get favorite notes.

        Args:
            user_id: User ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of favorite notes
        """
        return (
            self.db.query(Note)
            .filter(
                and_(
                    Note.user_id == user_id,
                    Note.is_favorite == True,
                    Note.status == NoteStatus.ACTIVE,
                )
            )
            .options(joinedload(Note.tags))
            .order_by(desc(Note.updated_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def search(
        self,
        user_id: str,
        query: Optional[str] = None,
        tag_names: Optional[List[str]] = None,
        notebook_ids: Optional[List[int]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        is_favorite: Optional[bool] = None,
        status: Optional[NoteStatus] = NoteStatus.ACTIVE,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Note]:
        """Search notes with filters.

        Args:
            user_id: User ID
            query: Text search query
            tag_names: Filter by tag names
            notebook_ids: Filter by notebook IDs
            date_from: Filter by created date (from)
            date_to: Filter by created date (to)
            is_favorite: Filter by favorite status
            status: Note status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching notes
        """
        q = self.db.query(Note).filter(Note.user_id == user_id)

        if status:
            q = q.filter(Note.status == status)

        if query:
            # Search in title and content
            search_filter = or_(
                Note.title.ilike(f"%{query}%"), Note.content.ilike(f"%{query}%")
            )
            q = q.filter(search_filter)

        if tag_names:
            q = q.join(Note.tags).filter(Tag.name.in_(tag_names))

        if notebook_ids:
            q = q.filter(Note.notebook_id.in_(notebook_ids))

        if date_from:
            q = q.filter(Note.created_at >= date_from)

        if date_to:
            q = q.filter(Note.created_at <= date_to)

        if is_favorite is not None:
            q = q.filter(Note.is_favorite == is_favorite)

        return (
            q.options(joinedload(Note.tags))
            .order_by(desc(Note.updated_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def update(self, note_id: int, **kwargs: Any) -> Optional[Note]:
        """Update a note.

        Args:
            note_id: Note ID
            **kwargs: Attributes to update

        Returns:
            Updated note if found, None otherwise
        """
        note = self.get_by_id(note_id)
        if not note:
            return None

        for key, value in kwargs.items():
            if hasattr(note, key) and value is not None:
                setattr(note, key, value)

        note.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(note)
        return note

    def delete(self, note_id: int, soft_delete: bool = True) -> bool:
        """Delete a note.

        Args:
            note_id: Note ID
            soft_delete: If True, marks as deleted; if False, permanently deletes

        Returns:
            True if deleted, False if not found
        """
        note = self.get_by_id(note_id)
        if not note:
            return False

        if soft_delete:
            note.status = NoteStatus.DELETED
            note.updated_at = datetime.utcnow()
            self.db.commit()
        else:
            self.db.delete(note)
            self.db.commit()

        return True

    def count_by_user(self, user_id: str, status: Optional[NoteStatus] = None) -> int:
        """Count notes by user.

        Args:
            user_id: User ID
            status: Optional status filter

        Returns:
            Number of notes
        """
        query = self.db.query(func.count(Note.id)).filter(Note.user_id == user_id)
        if status:
            query = query.filter(Note.status == status)
        return query.scalar()


class NotebookRepository:
    """Repository for Notebook CRUD operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def create(self, user_id: str, name: str, **kwargs: Any) -> Notebook:
        """Create a new notebook."""
        notebook = Notebook(user_id=user_id, name=name, **kwargs)
        self.db.add(notebook)
        self.db.commit()
        self.db.refresh(notebook)
        return notebook

    def get_by_id(self, notebook_id: int) -> Optional[Notebook]:
        """Get notebook by ID."""
        return self.db.query(Notebook).filter(Notebook.id == notebook_id).first()

    def get_by_user(self, user_id: str) -> List[Notebook]:
        """Get all notebooks for a user."""
        return (
            self.db.query(Notebook)
            .filter(Notebook.user_id == user_id)
            .order_by(Notebook.created_at)
            .all()
        )

    def update(self, notebook_id: int, **kwargs: Any) -> Optional[Notebook]:
        """Update a notebook."""
        notebook = self.get_by_id(notebook_id)
        if not notebook:
            return None

        for key, value in kwargs.items():
            if hasattr(notebook, key) and value is not None:
                setattr(notebook, key, value)

        notebook.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(notebook)
        return notebook

    def delete(self, notebook_id: int) -> bool:
        """Delete a notebook."""
        notebook = self.get_by_id(notebook_id)
        if not notebook:
            return False

        self.db.delete(notebook)
        self.db.commit()
        return True


class TagRepository:
    """Repository for Tag CRUD operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def create(self, user_id: str, name: str, **kwargs: Any) -> Tag:
        """Create a new tag."""
        tag = Tag(user_id=user_id, name=name, **kwargs)
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def get_by_id(self, tag_id: int) -> Optional[Tag]:
        """Get tag by ID."""
        return self.db.query(Tag).filter(Tag.id == tag_id).first()

    def get_by_name(self, user_id: str, name: str) -> Optional[Tag]:
        """Get tag by name."""
        return (
            self.db.query(Tag).filter(and_(Tag.user_id == user_id, Tag.name == name)).first()
        )

    def get_or_create(self, user_id: str, name: str, **kwargs: Any) -> Tag:
        """Get existing tag or create new one."""
        tag = self.get_by_name(user_id, name)
        if tag:
            return tag
        return self.create(user_id, name, **kwargs)

    def get_by_user(self, user_id: str) -> List[Tag]:
        """Get all tags for a user."""
        return (
            self.db.query(Tag)
            .filter(Tag.user_id == user_id)
            .order_by(Tag.name)
            .all()
        )

    def get_popular_tags(self, user_id: str, limit: int = 20) -> List[tuple]:
        """Get most used tags.

        Returns:
            List of (tag, count) tuples
        """
        return (
            self.db.query(Tag, func.count(NoteTag.note_id).label("count"))
            .join(NoteTag)
            .filter(Tag.user_id == user_id)
            .group_by(Tag.id)
            .order_by(desc("count"))
            .limit(limit)
            .all()
        )

    def add_tag_to_note(self, note_id: int, tag_id: int) -> None:
        """Add tag to note."""
        note_tag = NoteTag(note_id=note_id, tag_id=tag_id)
        self.db.add(note_tag)
        self.db.commit()

    def remove_tag_from_note(self, note_id: int, tag_id: int) -> None:
        """Remove tag from note."""
        self.db.query(NoteTag).filter(
            and_(NoteTag.note_id == note_id, NoteTag.tag_id == tag_id)
        ).delete()
        self.db.commit()


class TemplateRepository:
    """Repository for Template CRUD operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def create(self, name: str, content: str, user_id: Optional[str] = None, **kwargs: Any) -> Template:
        """Create a new template."""
        template = Template(name=name, content=content, user_id=user_id, **kwargs)
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_by_id(self, template_id: int) -> Optional[Template]:
        """Get template by ID."""
        return self.db.query(Template).filter(Template.id == template_id).first()

    def get_by_user(self, user_id: str) -> List[Template]:
        """Get user's custom templates."""
        return (
            self.db.query(Template)
            .filter(Template.user_id == user_id)
            .order_by(desc(Template.usage_count))
            .all()
        )

    def get_system_templates(self) -> List[Template]:
        """Get system templates."""
        return (
            self.db.query(Template)
            .filter(Template.is_system == True)
            .order_by(Template.name)
            .all()
        )

    def increment_usage(self, template_id: int) -> None:
        """Increment template usage count."""
        template = self.get_by_id(template_id)
        if template:
            template.usage_count += 1
            self.db.commit()


class AttachmentRepository:
    """Repository for Attachment CRUD operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def create(self, note_id: int, **kwargs: Any) -> Attachment:
        """Create a new attachment."""
        attachment = Attachment(note_id=note_id, **kwargs)
        self.db.add(attachment)
        self.db.commit()
        self.db.refresh(attachment)
        return attachment

    def get_by_id(self, attachment_id: int) -> Optional[Attachment]:
        """Get attachment by ID."""
        return self.db.query(Attachment).filter(Attachment.id == attachment_id).first()

    def get_by_note(self, note_id: int) -> List[Attachment]:
        """Get all attachments for a note."""
        return (
            self.db.query(Attachment)
            .filter(Attachment.note_id == note_id)
            .order_by(Attachment.created_at)
            .all()
        )

    def delete(self, attachment_id: int) -> bool:
        """Delete an attachment."""
        attachment = self.get_by_id(attachment_id)
        if not attachment:
            return False

        self.db.delete(attachment)
        self.db.commit()
        return True


class CommentRepository:
    """Repository for Comment CRUD operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def create(self, note_id: int, user_id: str, content: str, **kwargs: Any) -> Comment:
        """Create a new comment."""
        comment = Comment(note_id=note_id, user_id=user_id, content=content, **kwargs)
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def get_by_note(self, note_id: int) -> List[Comment]:
        """Get all comments for a note."""
        return (
            self.db.query(Comment)
            .filter(Comment.note_id == note_id)
            .order_by(Comment.created_at)
            .all()
        )

    def update(self, comment_id: int, **kwargs: Any) -> Optional[Comment]:
        """Update a comment."""
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return None

        for key, value in kwargs.items():
            if hasattr(comment, key) and value is not None:
                setattr(comment, key, value)

        comment.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def delete(self, comment_id: int) -> bool:
        """Delete a comment."""
        comment = self.db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return False

        self.db.delete(comment)
        self.db.commit()
        return True
