"""Integration between Notes and Chat modules."""

from typing import Optional

from sqlalchemy.orm import Session

from ..models import Note
from ..service import NoteService


class NoteChatIntegration:
    """Integration between Notes and Chat modules."""

    def __init__(self, db: Session):
        """Initialize integration.

        Args:
            db: Database session
        """
        self.db = db
        self.note_service = NoteService(db)

    def create_note_from_chat(
        self, chat_id: str, user_id: str, title: str, content: str
    ) -> Note:
        """Create a note from a chat message or conversation.

        Args:
            chat_id: Chat/conversation ID
            user_id: User ID
            title: Note title
            content: Note content

        Returns:
            Created note
        """
        from ..schemas import NoteCreate

        note_data = NoteCreate(
            title=title, content=content, content_markdown=content, tags=["chat"]
        )

        note = self.note_service.create_note(user_id, note_data)

        # Link to chat
        self.note_service.note_repo.update(note.id, chat_id=chat_id)

        return note

    def share_note_in_chat(
        self, note_id: int, chat_id: str, user_id: str
    ) -> dict[str, str]:
        """Share a note in a chat.

        Args:
            note_id: Note ID
            chat_id: Chat/conversation ID
            user_id: User ID

        Returns:
            Share information
        """
        note = self.note_service.get_note(note_id, user_id)

        # Return note data for chat system to display
        return {
            "note_id": str(note.id),
            "title": note.title,
            "content": note.content or "",
            "url": f"/notes/{note.id}",  # URL to note
        }

    def get_notes_from_chat(self, chat_id: str, user_id: str) -> list[Note]:
        """Get all notes created from a chat.

        Args:
            chat_id: Chat/conversation ID
            user_id: User ID

        Returns:
            List of notes
        """
        return (
            self.db.query(Note)
            .filter(Note.chat_id == chat_id, Note.user_id == user_id)
            .order_by(Note.created_at.desc())
            .all()
        )

    def link_note_to_chat(self, note_id: int, chat_id: str, user_id: str) -> Note:
        """Link existing note to a chat.

        Args:
            note_id: Note ID
            chat_id: Chat/conversation ID
            user_id: User ID

        Returns:
            Updated note
        """
        note = self.note_service.get_note(note_id, user_id)
        return self.note_service.note_repo.update(note.id, chat_id=chat_id)
