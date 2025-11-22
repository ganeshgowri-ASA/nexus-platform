"""
Unit Tests for NEXUS Word Processing Module

Tests for editor, formatting, document management, AI assistant,
collaboration, and templates functionality.
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import sys

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.word.editor import WordEditor, DocumentMetadata, DocumentStatus
from modules.word.formatting import (
    TextFormatter,
    TextAlign,
    ListType,
    HeadingLevel,
    FontStyle,
    ParagraphStyle
)
from modules.word.document_manager import DocumentManager, PageSetup, DocumentVersion
from modules.word.ai_assistant import AIWritingAssistant, ToneStyle, GrammarIssue
from modules.word.collaboration import (
    CollaborationManager,
    PermissionLevel,
    ChangeType,
    CommentStatus,
    User
)
from modules.word.templates import TemplateManager, TemplateCategory


class TestWordEditor(unittest.TestCase):
    """Test cases for WordEditor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.user_id = "test_user"
        self.editor = WordEditor(user_id=self.user_id)

    def test_editor_initialization(self):
        """Test editor initializes correctly"""
        self.assertIsNotNone(self.editor.document_id)
        self.assertEqual(self.editor.user_id, self.user_id)
        self.assertIsNotNone(self.editor.metadata)
        self.assertEqual(self.editor.metadata.word_count, 0)

    def test_set_and_get_content(self):
        """Test setting and getting content"""
        content = {"ops": [{"insert": "Hello World"}]}
        self.editor.set_content(content)

        retrieved = self.editor.get_content()
        self.assertEqual(retrieved, content)
        self.assertTrue(self.editor.needs_save())

    def test_undo_redo(self):
        """Test undo and redo functionality"""
        # Set initial content
        content1 = {"ops": [{"insert": "First"}]}
        self.editor.set_content(content1)

        # Change content
        content2 = {"ops": [{"insert": "Second"}]}
        self.editor.set_content(content2)

        # Undo
        self.assertTrue(self.editor.undo())
        current = self.editor.get_content()
        self.assertEqual(current, content1)

        # Redo
        self.assertTrue(self.editor.redo())
        current = self.editor.get_content()
        self.assertEqual(current, content2)

    def test_statistics(self):
        """Test document statistics calculation"""
        content = {
            "ops": [
                {"insert": "This is a test document. "},
                {"insert": "It has multiple sentences.\n\n"},
                {"insert": "And multiple paragraphs."}
            ]
        }
        self.editor.set_content(content)

        stats = self.editor.get_statistics()

        self.assertGreater(stats['word_count'], 0)
        self.assertGreater(stats['character_count'], 0)
        self.assertGreater(stats['sentence_count'], 0)
        self.assertGreater(stats['paragraph_count'], 0)

    def test_find_and_replace(self):
        """Test find and replace functionality"""
        content = {"ops": [{"insert": "Hello World. Hello Universe."}]}
        self.editor.set_content(content)

        count = self.editor.find_and_replace("Hello", "Hi", case_sensitive=True)

        self.assertEqual(count, 2)

    def test_metadata_update(self):
        """Test metadata updating"""
        self.editor.update_metadata(title="Test Document", tags=["test", "sample"])

        self.assertEqual(self.editor.metadata.title, "Test Document")
        self.assertIn("test", self.editor.metadata.tags)

    def test_version_increment(self):
        """Test version incrementing"""
        initial_version = self.editor.metadata.version
        self.editor.increment_version()

        self.assertEqual(self.editor.metadata.version, initial_version + 1)

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization"""
        self.editor.set_content({"ops": [{"insert": "Test"}]})
        self.editor.update_metadata(title="Test Doc")

        # Convert to dict
        data = self.editor.to_dict()

        # Create new editor from dict
        new_editor = WordEditor.from_dict(data)

        self.assertEqual(new_editor.document_id, self.editor.document_id)
        self.assertEqual(new_editor.user_id, self.editor.user_id)
        self.assertEqual(new_editor.metadata.title, "Test Doc")


class TestTextFormatter(unittest.TestCase):
    """Test cases for TextFormatter class"""

    def setUp(self):
        """Set up test fixtures"""
        self.formatter = TextFormatter()

    def test_apply_bold(self):
        """Test applying bold formatting"""
        ops = [{"insert": "Hello"}]
        result = TextFormatter.apply_bold(ops)

        self.assertTrue(result[0]['attributes']['bold'])

    def test_apply_italic(self):
        """Test applying italic formatting"""
        ops = [{"insert": "Hello"}]
        result = TextFormatter.apply_italic(ops)

        self.assertTrue(result[0]['attributes']['italic'])

    def test_apply_font_family(self):
        """Test applying font family"""
        ops = [{"insert": "Hello"}]
        result = TextFormatter.apply_font_family(ops, "Arial")

        self.assertEqual(result[0]['attributes']['font'], "Arial")

    def test_apply_heading(self):
        """Test applying heading"""
        ops = [{"insert": "Heading"}]
        result = TextFormatter.apply_heading(ops, HeadingLevel.H1)

        self.assertEqual(result[0]['attributes']['header'], 1)

    def test_apply_alignment(self):
        """Test applying text alignment"""
        ops = [{"insert": "Text"}]
        result = TextFormatter.apply_alignment(ops, TextAlign.CENTER)

        self.assertEqual(result[0]['attributes']['align'], "center")

    def test_create_link(self):
        """Test creating a link"""
        link = TextFormatter.create_link("Click here", "https://example.com")

        self.assertEqual(link['insert'], "Click here")
        self.assertEqual(link['attributes']['link'], "https://example.com")

    def test_delta_to_plain_text(self):
        """Test converting Delta to plain text"""
        delta = {"ops": [
            {"insert": "Hello "},
            {"insert": "World", "attributes": {"bold": True}},
            {"insert": "!"}
        ]}

        text = TextFormatter.delta_to_plain_text(delta)
        self.assertEqual(text, "Hello World!")


class TestDocumentManager(unittest.TestCase):
    """Test cases for DocumentManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.doc_manager = DocumentManager(storage_path=self.temp_dir)
        self.editor = WordEditor(user_id="test_user")
        self.editor.set_content({"ops": [{"insert": "Test content"}]})

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_document(self):
        """Test saving a document"""
        success = self.doc_manager.save_document(self.editor)

        self.assertTrue(success)
        self.assertFalse(self.editor.needs_save())

    def test_load_document(self):
        """Test loading a document"""
        # Save first
        self.doc_manager.save_document(self.editor)

        # Load
        loaded_editor = self.doc_manager.load_document(
            self.editor.document_id,
            "test_user"
        )

        self.assertIsNotNone(loaded_editor)
        self.assertEqual(loaded_editor.document_id, self.editor.document_id)

    def test_version_history(self):
        """Test version history tracking"""
        # Save multiple versions
        self.doc_manager.save_document(self.editor, "Initial version")

        self.editor.set_content({"ops": [{"insert": "Updated content"}]})
        self.editor.increment_version()
        self.doc_manager.save_document(self.editor, "Second version")

        # Get version history
        versions = self.doc_manager.get_version_history(self.editor.document_id)

        self.assertGreater(len(versions), 0)

    def test_list_documents(self):
        """Test listing documents"""
        # Save a document
        self.doc_manager.save_document(self.editor)

        # List documents
        docs = self.doc_manager.list_documents()

        self.assertGreater(len(docs), 0)

    def test_export_to_txt(self):
        """Test exporting to plain text"""
        output_path = f"{self.temp_dir}/test.txt"
        success = self.doc_manager.export_to_txt(self.editor, output_path)

        self.assertTrue(success)
        self.assertTrue(Path(output_path).exists())

    def test_export_to_html(self):
        """Test exporting to HTML"""
        output_path = f"{self.temp_dir}/test.html"
        success = self.doc_manager.export_to_html(self.editor, output_path)

        self.assertTrue(success)
        self.assertTrue(Path(output_path).exists())

    def test_export_to_markdown(self):
        """Test exporting to Markdown"""
        output_path = f"{self.temp_dir}/test.md"
        success = self.doc_manager.export_to_markdown(self.editor, output_path)

        self.assertTrue(success)
        self.assertTrue(Path(output_path).exists())


class TestAIWritingAssistant(unittest.TestCase):
    """Test cases for AIWritingAssistant class"""

    def setUp(self):
        """Set up test fixtures"""
        self.ai = AIWritingAssistant()

    def test_grammar_check(self):
        """Test grammar checking"""
        text = "this is a test.This needs a space"
        issues = self.ai.check_grammar(text)

        self.assertIsInstance(issues, list)

    def test_spell_check(self):
        """Test spell checking"""
        text = "This is a test"
        issues = self.ai.check_spelling(text)

        self.assertIsInstance(issues, list)

    def test_style_suggestions(self):
        """Test style suggestions"""
        text = "In order to complete the task, we need to work."
        suggestions = self.ai.suggest_style_improvements(text)

        self.assertIsInstance(suggestions, list)

    def test_summarize(self):
        """Test text summarization"""
        text = "This is a long document. " * 50
        summary = self.ai.summarize(text, max_length=20)

        self.assertIsInstance(summary, str)
        self.assertLess(len(summary.split()), len(text.split()))

    def test_writing_statistics(self):
        """Test writing statistics"""
        text = "This is a test document. It has multiple sentences."
        stats = self.ai.get_writing_statistics(text)

        self.assertIn('flesch_reading_ease', stats)
        self.assertIn('grade_level', stats)
        self.assertGreater(stats['flesch_reading_ease'], 0)


class TestCollaborationManager(unittest.TestCase):
    """Test cases for CollaborationManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.collab = CollaborationManager(document_id="test_doc")
        self.user = User(
            user_id="user1",
            username="Test User",
            email="test@example.com",
            avatar_color="#FF0000"
        )

    def test_add_user(self):
        """Test adding a user"""
        self.collab.add_user(self.user, PermissionLevel.EDIT)

        active_users = self.collab.get_active_users()
        self.assertEqual(len(active_users), 1)
        self.assertTrue(self.user.is_online)

    def test_permissions(self):
        """Test permission checking"""
        self.collab.add_user(self.user, PermissionLevel.VIEW)

        self.assertTrue(self.collab.check_permission(self.user.user_id, PermissionLevel.VIEW))
        self.assertFalse(self.collab.check_permission(self.user.user_id, PermissionLevel.EDIT))

    def test_add_comment(self):
        """Test adding a comment"""
        comment = self.collab.add_comment(
            author_id=self.user.user_id,
            author_name=self.user.username,
            content="This is a test comment",
            position=0,
            length=10
        )

        self.assertIsNotNone(comment.comment_id)
        self.assertEqual(comment.status, CommentStatus.OPEN)

    def test_resolve_comment(self):
        """Test resolving a comment"""
        comment = self.collab.add_comment(
            author_id=self.user.user_id,
            author_name=self.user.username,
            content="Test comment",
            position=0,
            length=10
        )

        success = self.collab.resolve_comment(comment.comment_id)
        self.assertTrue(success)

        resolved_comment = self.collab.comments[comment.comment_id]
        self.assertEqual(resolved_comment.status, CommentStatus.RESOLVED)

    def test_track_changes(self):
        """Test change tracking"""
        self.collab.enable_track_changes(True)

        change = self.collab.track_change(
            author_id=self.user.user_id,
            author_name=self.user.username,
            change_type=ChangeType.INSERT,
            position=0,
            length=5,
            new_content="Hello"
        )

        self.assertIsNotNone(change.change_id)
        self.assertIsNone(change.accepted)

    def test_share_link(self):
        """Test creating a share link"""
        link = self.collab.create_share_link(
            created_by=self.user.user_id,
            permission=PermissionLevel.VIEW,
            is_public=True
        )

        self.assertIsNotNone(link.link_id)
        self.assertEqual(link.permission, PermissionLevel.VIEW)

        # Test getting link
        retrieved_link = self.collab.get_share_link(link.link_id)
        self.assertIsNotNone(retrieved_link)
        self.assertEqual(retrieved_link.access_count, 1)


class TestTemplateManager(unittest.TestCase):
    """Test cases for TemplateManager class"""

    def setUp(self):
        """Set up test fixtures"""
        self.template_manager = TemplateManager()

    def test_get_template(self):
        """Test getting a template"""
        template = self.template_manager.get_template("business_letter")

        self.assertIsNotNone(template)
        self.assertEqual(template.template_id, "business_letter")
        self.assertIn("ops", template.content)

    def test_get_all_templates(self):
        """Test getting all templates"""
        templates = self.template_manager.get_all_templates()

        self.assertGreater(len(templates), 0)

    def test_get_templates_by_category(self):
        """Test getting templates by category"""
        templates = self.template_manager.get_templates_by_category(
            TemplateCategory.BUSINESS
        )

        self.assertGreater(len(templates), 0)
        for template in templates:
            self.assertEqual(template.category, TemplateCategory.BUSINESS)

    def test_search_templates(self):
        """Test searching templates"""
        results = self.template_manager.search_templates("letter")

        self.assertGreater(len(results), 0)

    def test_save_custom_template(self):
        """Test saving a custom template"""
        template = self.template_manager.save_custom_template(
            name="My Custom Template",
            description="A custom template for testing",
            category=TemplateCategory.PERSONAL,
            content={"ops": [{"insert": "Custom content"}]},
            tags=["custom", "test"]
        )

        self.assertIsNotNone(template.template_id)
        self.assertTrue(template.template_id.startswith("custom_"))

        # Verify it can be retrieved
        retrieved = self.template_manager.get_template(template.template_id)
        self.assertIsNotNone(retrieved)

    def test_delete_custom_template(self):
        """Test deleting a custom template"""
        # Create custom template
        template = self.template_manager.save_custom_template(
            name="Test Template",
            description="For deletion",
            category=TemplateCategory.PERSONAL,
            content={"ops": [{"insert": "Test"}]}
        )

        # Delete it
        success = self.template_manager.delete_template(template.template_id)
        self.assertTrue(success)

        # Verify it's deleted
        retrieved = self.template_manager.get_template(template.template_id)
        self.assertIsNone(retrieved)

    def test_cannot_delete_builtin_template(self):
        """Test that built-in templates cannot be deleted"""
        success = self.template_manager.delete_template("business_letter")
        self.assertFalse(success)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestWordEditor))
    suite.addTests(loader.loadTestsFromTestCase(TestTextFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestDocumentManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAIWritingAssistant))
    suite.addTests(loader.loadTestsFromTestCase(TestCollaborationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateManager))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
