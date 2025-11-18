"""Integration between Notes and Projects modules."""

from typing import Optional

from sqlalchemy.orm import Session

from ..models import Note
from ..service import NoteService


class NoteProjectIntegration:
    """Integration between Notes and Projects modules."""

    def __init__(self, db: Session):
        """Initialize integration.

        Args:
            db: Database session
        """
        self.db = db
        self.note_service = NoteService(db)

    def create_project_note(
        self, project_id: int, user_id: str, title: str, content: Optional[str] = None
    ) -> Note:
        """Create a note for a project.

        Args:
            project_id: Project ID
            user_id: User ID
            title: Note title
            content: Note content

        Returns:
            Created note
        """
        from ..schemas import NoteCreate

        note_data = NoteCreate(
            title=title, content=content, content_markdown=content, tags=["project"]
        )

        note = self.note_service.create_note(user_id, note_data)

        # Link to project
        self.note_service.note_repo.update(note.id, project_id=project_id)

        return note

    def get_project_notes(
        self, project_id: int, user_id: str, limit: int = 100
    ) -> list[Note]:
        """Get all notes for a project.

        Args:
            project_id: Project ID
            user_id: User ID
            limit: Maximum number of notes

        Returns:
            List of notes
        """
        return (
            self.db.query(Note)
            .filter(Note.project_id == project_id, Note.user_id == user_id)
            .order_by(Note.updated_at.desc())
            .limit(limit)
            .all()
        )

    def link_note_to_project(self, note_id: int, project_id: int, user_id: str) -> Note:
        """Link existing note to a project.

        Args:
            note_id: Note ID
            project_id: Project ID
            user_id: User ID

        Returns:
            Updated note
        """
        note = self.note_service.get_note(note_id, user_id)
        return self.note_service.note_repo.update(note.id, project_id=project_id)

    def unlink_note_from_project(self, note_id: int, user_id: str) -> Note:
        """Unlink note from project.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            Updated note
        """
        note = self.note_service.get_note(note_id, user_id)
        return self.note_service.note_repo.update(note.id, project_id=None)
