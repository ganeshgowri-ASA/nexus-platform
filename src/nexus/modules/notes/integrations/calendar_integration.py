"""Integration between Notes and Calendar modules."""

from typing import Optional

from sqlalchemy.orm import Session

from ..models import Note
from ..service import NoteService


class NoteCalendarIntegration:
    """Integration between Notes and Calendar modules."""

    def __init__(self, db: Session):
        """Initialize integration.

        Args:
            db: Database session
        """
        self.db = db
        self.note_service = NoteService(db)

    def create_note_for_event(
        self, event_id: str, user_id: str, event_title: str, event_date: str
    ) -> Note:
        """Create a note for a calendar event.

        Args:
            event_id: Calendar event ID
            user_id: User ID
            event_title: Event title
            event_date: Event date/time

        Returns:
            Created note
        """
        from ..schemas import NoteCreate

        note_data = NoteCreate(
            title=f"Notes: {event_title}",
            content=f"# {event_title}\n\n**Date:** {event_date}\n\n## Agenda\n\n## Notes\n\n## Action Items\n",
            content_markdown=f"# {event_title}\n\n**Date:** {event_date}\n\n## Agenda\n\n## Notes\n\n## Action Items\n",
            tags=["meeting", "calendar"],
        )

        note = self.note_service.create_note(user_id, note_data)

        # Link to calendar event
        self.note_service.note_repo.update(note.id, calendar_event_id=event_id)

        return note

    def link_note_to_event(self, note_id: int, event_id: str, user_id: str) -> Note:
        """Link existing note to calendar event.

        Args:
            note_id: Note ID
            event_id: Calendar event ID
            user_id: User ID

        Returns:
            Updated note
        """
        note = self.note_service.get_note(note_id, user_id)
        return self.note_service.note_repo.update(note.id, calendar_event_id=event_id)

    def get_notes_for_event(self, event_id: str, user_id: str) -> list[Note]:
        """Get all notes linked to a calendar event.

        Args:
            event_id: Calendar event ID
            user_id: User ID

        Returns:
            List of notes
        """
        return (
            self.db.query(Note)
            .filter(Note.calendar_event_id == event_id, Note.user_id == user_id)
            .all()
        )

    def unlink_note_from_event(self, note_id: int, user_id: str) -> Note:
        """Unlink note from calendar event.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            Updated note
        """
        note = self.note_service.get_note(note_id, user_id)
        return self.note_service.note_repo.update(note.id, calendar_event_id=None)
