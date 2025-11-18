"""Tests for notes models."""

import pytest
from datetime import datetime

from nexus.modules.notes.models import (
    Note,
    Notebook,
    Tag,
    NoteTag,
    Template,
    Attachment,
    Comment,
    NoteStatus,
    TemplateType,
)


def test_create_note(db_session, sample_user_id):
    """Test creating a note."""
    note = Note(
        user_id=sample_user_id,
        title="Test Note",
        content="Test content",
        status=NoteStatus.ACTIVE,
    )

    db_session.add(note)
    db_session.commit()
    db_session.refresh(note)

    assert note.id is not None
    assert note.title == "Test Note"
    assert note.user_id == sample_user_id
    assert note.status == NoteStatus.ACTIVE
    assert note.version == 1
    assert isinstance(note.created_at, datetime)


def test_create_notebook(db_session, sample_user_id):
    """Test creating a notebook."""
    notebook = Notebook(user_id=sample_user_id, name="Test Notebook")

    db_session.add(notebook)
    db_session.commit()
    db_session.refresh(notebook)

    assert notebook.id is not None
    assert notebook.name == "Test Notebook"
    assert notebook.user_id == sample_user_id
    assert notebook.color == "#4A90E2"
    assert notebook.icon == "📓"


def test_create_tag(db_session, sample_user_id):
    """Test creating a tag."""
    tag = Tag(user_id=sample_user_id, name="test-tag")

    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)

    assert tag.id is not None
    assert tag.name == "test-tag"
    assert tag.user_id == sample_user_id


def test_note_tag_relationship(db_session, sample_user_id):
    """Test many-to-many relationship between notes and tags."""
    note = Note(user_id=sample_user_id, title="Test Note")
    tag1 = Tag(user_id=sample_user_id, name="tag1")
    tag2 = Tag(user_id=sample_user_id, name="tag2")

    db_session.add_all([note, tag1, tag2])
    db_session.commit()

    # Add tags to note
    note.tags.append(tag1)
    note.tags.append(tag2)
    db_session.commit()

    # Verify relationship
    assert len(note.tags) == 2
    assert tag1 in note.tags
    assert tag2 in note.tags


def test_create_template(db_session, sample_user_id):
    """Test creating a template."""
    template = Template(
        user_id=sample_user_id,
        name="Meeting Notes",
        content="# Meeting Notes\n\n## Agenda\n\n## Notes\n",
        template_type=TemplateType.MEETING,
    )

    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)

    assert template.id is not None
    assert template.name == "Meeting Notes"
    assert template.template_type == TemplateType.MEETING
    assert template.usage_count == 0


def test_create_attachment(db_session, sample_user_id):
    """Test creating an attachment."""
    note = Note(user_id=sample_user_id, title="Test Note")
    db_session.add(note)
    db_session.commit()

    attachment = Attachment(
        note_id=note.id,
        filename="test.pdf",
        original_filename="test.pdf",
        file_type="document",
        file_size=1024,
    )

    db_session.add(attachment)
    db_session.commit()
    db_session.refresh(attachment)

    assert attachment.id is not None
    assert attachment.note_id == note.id
    assert attachment.filename == "test.pdf"


def test_create_comment(db_session, sample_user_id):
    """Test creating a comment."""
    note = Note(user_id=sample_user_id, title="Test Note")
    db_session.add(note)
    db_session.commit()

    comment = Comment(note_id=note.id, user_id=sample_user_id, content="Great note!")

    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    assert comment.id is not None
    assert comment.note_id == note.id
    assert comment.content == "Great note!"
    assert comment.is_resolved is False


def test_note_to_dict(db_session, sample_user_id):
    """Test note to_dict method."""
    note = Note(
        user_id=sample_user_id,
        title="Test Note",
        content="Test content",
        status=NoteStatus.ACTIVE,
        is_favorite=True,
    )

    db_session.add(note)
    db_session.commit()

    note_dict = note.to_dict()

    assert note_dict["id"] == note.id
    assert note_dict["title"] == "Test Note"
    assert note_dict["user_id"] == sample_user_id
    assert note_dict["status"] == "active"
    assert note_dict["is_favorite"] is True
