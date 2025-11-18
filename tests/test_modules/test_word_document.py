"""
Tests for Word Editor document module.
"""
import pytest
from modules.word.document import Document, DocumentMetadata, Comment, Version


class TestDocument:
    """Test Document class."""

    def test_document_creation(self):
        """Test creating a new document."""
        doc = Document(title="Test Document", content="Test content", author="Test User")

        assert doc.metadata.title == "Test Document"
        assert doc.content == "Test content"
        assert doc.metadata.author == "Test User"
        assert doc.metadata.word_count == 2
        assert doc.metadata.version == 1

    def test_update_content(self):
        """Test updating document content."""
        doc = Document()
        doc.update_content("New content here")

        assert doc.content == "New content here"
        assert doc.metadata.word_count == 3

    def test_add_comment(self):
        """Test adding a comment."""
        doc = Document()
        comment = doc.add_comment("Test comment", "User1", position=10)

        assert len(doc.comments) == 1
        assert comment.text == "Test comment"
        assert comment.author == "User1"
        assert comment.position == 10
        assert not comment.resolved

    def test_resolve_comment(self):
        """Test resolving a comment."""
        doc = Document()
        comment = doc.add_comment("Test comment", "User1")

        result = doc.resolve_comment(comment.id)
        assert result is True
        assert comment.resolved is True

    def test_save_version(self):
        """Test saving a document version."""
        doc = Document(content="Version 1")
        initial_version_count = len(doc.versions)

        doc.update_content("Version 2")
        doc.save_version("Updated content")

        assert len(doc.versions) == initial_version_count + 1
        assert doc.versions[-1].comment == "Updated content"

    def test_restore_version(self):
        """Test restoring a previous version."""
        doc = Document(content="Original content")
        original_version = doc.versions[0]

        doc.update_content("Modified content")
        doc.save_version("Modification")

        result = doc.restore_version(original_version.id)
        assert result is True
        assert doc.content == "Original content"

    def test_word_count(self):
        """Test word counting."""
        doc = Document(content="This is a test document with eight words")
        assert doc.metadata.word_count == 8

    def test_character_count(self):
        """Test character counting."""
        doc = Document(content="Hello World")
        assert doc.metadata.character_count == 11

    def test_export_to_markdown(self):
        """Test exporting to Markdown."""
        doc = Document(title="Test", content="Content", author="Author")
        markdown = doc.export_to_markdown()

        assert "# Test" in markdown
        assert "Author" in markdown
        assert "Content" in markdown

    def test_export_to_html(self):
        """Test exporting to HTML."""
        doc = Document(title="Test", content="# Heading\n\nParagraph")
        html = doc.export_to_html()

        assert "<!DOCTYPE html>" in html
        assert "<title>Test</title>" in html
        assert doc.metadata.title in html

    def test_to_dict(self):
        """Test converting document to dictionary."""
        doc = Document(title="Test", content="Content")
        doc_dict = doc.to_dict()

        assert "metadata" in doc_dict
        assert "content" in doc_dict
        assert "comments" in doc_dict
        assert "versions" in doc_dict
        assert doc_dict["metadata"]["title"] == "Test"
        assert doc_dict["content"] == "Content"

    def test_from_dict(self):
        """Test creating document from dictionary."""
        doc1 = Document(title="Original", content="Content")
        doc_dict = doc1.to_dict()

        doc2 = Document.from_dict(doc_dict)

        assert doc2.metadata.title == "Original"
        assert doc2.content == "Content"

    def test_formatting(self):
        """Test document formatting options."""
        doc = Document()

        assert "font" in doc.formatting
        assert "font_size" in doc.formatting
        assert "color" in doc.formatting

        doc.formatting["font"] = "Times New Roman"
        assert doc.formatting["font"] == "Times New Roman"


class TestDocumentMetadata:
    """Test DocumentMetadata class."""

    def test_metadata_creation(self):
        """Test creating metadata."""
        metadata = DocumentMetadata(
            id="test123",
            title="Test Doc",
            created_at="2024-01-01T00:00:00",
            modified_at="2024-01-01T00:00:00",
            author="Test User",
        )

        assert metadata.id == "test123"
        assert metadata.title == "Test Doc"
        assert metadata.author == "Test User"
        assert metadata.word_count == 0
        assert metadata.version == 1


class TestComment:
    """Test Comment class."""

    def test_comment_creation(self):
        """Test creating a comment."""
        comment = Comment(
            id="comment1",
            text="Test comment",
            author="User1",
            timestamp="2024-01-01T00:00:00",
            position=100,
        )

        assert comment.id == "comment1"
        assert comment.text == "Test comment"
        assert comment.author == "User1"
        assert comment.position == 100
        assert not comment.resolved


class TestVersion:
    """Test Version class."""

    def test_version_creation(self):
        """Test creating a version."""
        version = Version(
            id="version1",
            content="Version content",
            timestamp="2024-01-01T00:00:00",
            author="User1",
            comment="Initial version",
        )

        assert version.id == "version1"
        assert version.content == "Version content"
        assert version.author == "User1"
        assert version.comment == "Initial version"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
