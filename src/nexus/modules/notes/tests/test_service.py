"""Tests for notes service layer."""

import pytest

from nexus.core.exceptions import NotFoundException
from nexus.modules.notes.models import NoteStatus
from nexus.modules.notes.schemas import NoteCreate, NoteUpdate
from nexus.modules.notes.service import NoteService


def test_create_note(db_session, sample_user_id):
    """Test creating a note via service."""
    service = NoteService(db_session)

    note_data = NoteCreate(
        title="Test Note",
        content="Test content",
        content_markdown="# Test Note",
        tags=["test", "example"],
    )

    note = service.create_note(sample_user_id, note_data)

    assert note.id is not None
    assert note.title == "Test Note"
    assert note.user_id == sample_user_id
    assert len(note.tags) == 2
    assert note.content_html is not None  # Should be generated from markdown


def test_get_note(db_session, sample_user_id):
    """Test getting a note."""
    service = NoteService(db_session)

    # Create note
    note_data = NoteCreate(title="Test Note", content="Test content")
    note = service.create_note(sample_user_id, note_data)

    # Get note
    retrieved_note = service.get_note(note.id, sample_user_id)

    assert retrieved_note.id == note.id
    assert retrieved_note.title == note.title
    assert retrieved_note.last_viewed_at is not None


def test_get_nonexistent_note(db_session, sample_user_id):
    """Test getting a nonexistent note raises exception."""
    service = NoteService(db_session)

    with pytest.raises(NotFoundException):
        service.get_note(9999, sample_user_id)


def test_update_note(db_session, sample_user_id):
    """Test updating a note."""
    service = NoteService(db_session)

    # Create note
    note_data = NoteCreate(title="Original Title", content="Original content")
    note = service.create_note(sample_user_id, note_data)

    # Update note
    update_data = NoteUpdate(title="Updated Title", content="Updated content")
    updated_note = service.update_note(note.id, sample_user_id, update_data)

    assert updated_note.title == "Updated Title"
    assert updated_note.content == "Updated content"


def test_delete_note_soft(db_session, sample_user_id):
    """Test soft deleting a note."""
    service = NoteService(db_session)

    # Create note
    note_data = NoteCreate(title="Test Note", content="Test content")
    note = service.create_note(sample_user_id, note_data)

    # Soft delete
    success = service.delete_note(note.id, sample_user_id, permanent=False)

    assert success is True

    # Verify note is marked as deleted
    deleted_note = service.note_repo.get_by_id(note.id)
    assert deleted_note.status == NoteStatus.DELETED


def test_list_notes(db_session, sample_user_id):
    """Test listing notes."""
    service = NoteService(db_session)

    # Create multiple notes
    for i in range(5):
        note_data = NoteCreate(title=f"Note {i}", content=f"Content {i}")
        service.create_note(sample_user_id, note_data)

    # List notes
    notes = service.list_notes(sample_user_id)

    assert len(notes) == 5


def test_search_notes(db_session, sample_user_id):
    """Test searching notes."""
    service = NoteService(db_session)

    # Create notes with different content
    note_data1 = NoteCreate(
        title="Python Tutorial", content="Learn Python programming", tags=["python", "coding"]
    )
    note_data2 = NoteCreate(
        title="JavaScript Guide", content="Learn JavaScript", tags=["javascript", "coding"]
    )

    service.create_note(sample_user_id, note_data1)
    service.create_note(sample_user_id, note_data2)

    # Search for Python
    results = service.search_notes(sample_user_id, query="Python")
    assert len(results) == 1
    assert results[0].title == "Python Tutorial"

    # Search by tag
    results = service.search_notes(sample_user_id, tags=["python"])
    assert len(results) == 1


def test_toggle_favorite(db_session, sample_user_id):
    """Test toggling favorite status."""
    service = NoteService(db_session)

    # Create note
    note_data = NoteCreate(title="Test Note", content="Test content")
    note = service.create_note(sample_user_id, note_data)

    assert note.is_favorite is False

    # Toggle to favorite
    note = service.toggle_favorite(note.id, sample_user_id)
    assert note.is_favorite is True

    # Toggle back
    note = service.toggle_favorite(note.id, sample_user_id)
    assert note.is_favorite is False


def test_archive_note(db_session, sample_user_id):
    """Test archiving a note."""
    service = NoteService(db_session)

    # Create note
    note_data = NoteCreate(title="Test Note", content="Test content")
    note = service.create_note(sample_user_id, note_data)

    # Archive
    archived_note = service.archive_note(note.id, sample_user_id)

    assert archived_note.status == NoteStatus.ARCHIVED


def test_restore_note(db_session, sample_user_id):
    """Test restoring an archived note."""
    service = NoteService(db_session)

    # Create and archive note
    note_data = NoteCreate(title="Test Note", content="Test content")
    note = service.create_note(sample_user_id, note_data)
    service.archive_note(note.id, sample_user_id)

    # Restore
    restored_note = service.restore_note(note.id, sample_user_id)

    assert restored_note.status == NoteStatus.ACTIVE


def test_get_note_stats(db_session, sample_user_id):
    """Test getting note statistics."""
    service = NoteService(db_session)

    # Create some notes
    for i in range(3):
        note_data = NoteCreate(
            title=f"Note {i}", content=f"Content {i}", is_favorite=(i == 0)
        )
        service.create_note(sample_user_id, note_data)

    # Archive one note
    note_data = NoteCreate(title="Archived Note", content="Content")
    note = service.create_note(sample_user_id, note_data)
    service.archive_note(note.id, sample_user_id)

    # Get stats
    stats = service.get_note_stats(sample_user_id)

    assert stats["total"] == 4
    assert stats["active"] == 3
    assert stats["archived"] == 1
    assert stats["favorites"] == 1
