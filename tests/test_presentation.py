"""
Comprehensive Unit Tests for Presentation Module

Tests all components of the presentation editor including:
- Slide management
- Element handling
- Animations
- Templates
- Themes
- Export
- Presenter view
- Collaboration
- AI assistant
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.presentation.slide_manager import (
    SlideManager, Slide, SlideLayout, SlideSize, Section
)
from modules.presentation.element_handler import (
    ElementHandler, ShapeType, TextElement, ImageElement, ShapeElement
)
from modules.presentation.animation import (
    AnimationEngine, AnimationType, TransitionType, AnimationTrigger
)
from modules.presentation.template_manager import (
    TemplateManager, TemplateCategory
)
from modules.presentation.theme_builder import (
    ThemeBuilder, ThemeStyle, ColorScheme
)
from modules.presentation.export_renderer import (
    ExportRenderer, ExportFormat, ExportQuality
)
from modules.presentation.presenter_view import (
    PresenterView, PresentationState, PresentationSettings
)
from modules.presentation.collaboration import (
    CollaborationManager, User, PermissionLevel, CommentStatus
)
from modules.presentation.ai_assistant import (
    AIAssistant, AIFeature
)
from modules.presentation.editor import PresentationEditor


class TestSlideManager(unittest.TestCase):
    """Test slide management functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = SlideManager()

    def test_create_slide(self):
        """Test slide creation."""
        slide = self.manager.create_slide(
            layout=SlideLayout.TITLE_SLIDE,
            title="Test Slide"
        )

        self.assertIsNotNone(slide)
        self.assertEqual(slide.title, "Test Slide")
        self.assertEqual(slide.layout, SlideLayout.TITLE_SLIDE)
        self.assertEqual(self.manager.get_slide_count(), 1)

    def test_delete_slide(self):
        """Test slide deletion."""
        slide = self.manager.create_slide()
        slide_id = slide.id

        self.assertTrue(self.manager.delete_slide(slide_id))
        self.assertEqual(self.manager.get_slide_count(), 0)
        self.assertIsNone(self.manager.get_slide(slide_id))

    def test_duplicate_slide(self):
        """Test slide duplication."""
        original = self.manager.create_slide(title="Original")
        duplicate = self.manager.duplicate_slide(original.id)

        self.assertIsNotNone(duplicate)
        self.assertNotEqual(duplicate.id, original.id)
        self.assertEqual(duplicate.title, "Original (Copy)")
        self.assertEqual(self.manager.get_slide_count(), 2)

    def test_reorder_slides(self):
        """Test slide reordering."""
        slide1 = self.manager.create_slide(title="Slide 1")
        slide2 = self.manager.create_slide(title="Slide 2")
        slide3 = self.manager.create_slide(title="Slide 3")

        self.manager.reorder_slide(slide3.id, 0)

        slides = self.manager.get_all_slides()
        self.assertEqual(slides[0].id, slide3.id)
        self.assertEqual(slides[1].id, slide1.id)
        self.assertEqual(slides[2].id, slide2.id)

    def test_section_management(self):
        """Test section creation and management."""
        section = self.manager.create_section("Introduction", 0)

        self.assertEqual(section.name, "Introduction")
        self.assertEqual(section.start_slide_index, 0)

        self.assertTrue(self.manager.rename_section(section.id, "Overview"))
        self.assertEqual(section.name, "Overview")


class TestElementHandler(unittest.TestCase):
    """Test element handling functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.handler = ElementHandler()

    def test_create_text_element(self):
        """Test text element creation."""
        element = self.handler.create_text_element(
            content="Hello World"
        )

        self.assertIsNotNone(element)
        self.assertEqual(element.content, "Hello World")
        self.assertIn(element.id, self.handler.elements)

    def test_create_image_element(self):
        """Test image element creation."""
        element = self.handler.create_image_element(
            source="https://example.com/image.jpg",
            alt_text="Test Image"
        )

        self.assertIsNotNone(element)
        self.assertEqual(element.source, "https://example.com/image.jpg")
        self.assertEqual(element.alt_text, "Test Image")

    def test_create_shape_element(self):
        """Test shape element creation."""
        element = self.handler.create_shape_element(
            shape_type=ShapeType.CIRCLE
        )

        self.assertIsNotNone(element)
        self.assertEqual(element.shape_type, ShapeType.CIRCLE)

    def test_delete_element(self):
        """Test element deletion."""
        element = self.handler.create_text_element("Test")
        element_id = element.id

        self.assertTrue(self.handler.delete_element(element_id))
        self.assertIsNone(self.handler.get_element(element_id))

    def test_duplicate_element(self):
        """Test element duplication."""
        original = self.handler.create_text_element("Original")
        duplicate = self.handler.duplicate_element(original.id)

        self.assertIsNotNone(duplicate)
        self.assertNotEqual(duplicate.id, original.id)
        # Position should be offset
        self.assertNotEqual(
            duplicate.position.x,
            original.position.x
        )

    def test_align_elements(self):
        """Test element alignment."""
        elem1 = self.handler.create_text_element("One")
        elem2 = self.handler.create_text_element("Two")

        elem1.position.x = 100
        elem2.position.x = 200

        self.handler.align_elements([elem1.id, elem2.id], "left")

        # Both should have same x position
        self.assertEqual(elem1.position.x, elem2.position.x)


class TestAnimationEngine(unittest.TestCase):
    """Test animation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = AnimationEngine()

    def test_add_animation(self):
        """Test adding animation."""
        animation = self.engine.add_animation(
            element_id="elem_1",
            animation_type=AnimationType.FADE_IN,
            duration=0.5
        )

        self.assertIsNotNone(animation)
        self.assertEqual(animation.element_id, "elem_1")
        self.assertEqual(animation.animation_type, AnimationType.FADE_IN)
        self.assertEqual(animation.duration, 0.5)

    def test_slide_transition(self):
        """Test slide transitions."""
        transition = self.engine.set_slide_transition(
            slide_id="slide_1",
            transition_type=TransitionType.FADE,
            duration=0.8
        )

        self.assertIsNotNone(transition)
        self.assertEqual(transition.type, TransitionType.FADE)

        retrieved = self.engine.get_slide_transition("slide_1")
        self.assertEqual(retrieved.type, TransitionType.FADE)

    def test_remove_animation(self):
        """Test animation removal."""
        animation = self.engine.add_animation(
            element_id="elem_1",
            animation_type=AnimationType.FADE_IN
        )

        self.assertTrue(self.engine.remove_animation(animation.id))
        # Timeline should be rebuilt
        self.assertEqual(len(self.engine.animation_timeline), 0)

    def test_animation_timeline(self):
        """Test animation timeline building."""
        self.engine.add_animation(
            "elem_1",
            AnimationType.FADE_IN,
            trigger=AnimationTrigger.ON_CLICK
        )
        self.engine.add_animation(
            "elem_2",
            AnimationType.ZOOM_IN,
            trigger=AnimationTrigger.WITH_PREVIOUS
        )

        timeline = self.engine.get_timeline()
        self.assertEqual(len(timeline), 2)


class TestTemplateManager(unittest.TestCase):
    """Test template management."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = TemplateManager()

    def test_get_templates_by_category(self):
        """Test template filtering by category."""
        business_templates = self.manager.get_templates_by_category(
            TemplateCategory.BUSINESS
        )

        self.assertGreater(len(business_templates), 0)
        for template in business_templates:
            self.assertEqual(template.category, TemplateCategory.BUSINESS)

    def test_search_templates(self):
        """Test template search."""
        results = self.manager.search_templates("business")

        self.assertGreater(len(results), 0)

    def test_apply_template(self):
        """Test template application."""
        template = self.manager.templates["business_title"]
        result = self.manager.apply_template(
            template.id,
            replacements={"TITLE": "My Presentation"}
        )

        self.assertIsNotNone(result)
        self.assertIn("elements", result)
        self.assertIn("background", result)

    def test_create_custom_template(self):
        """Test custom template creation."""
        template = self.manager.create_custom_template(
            name="My Template",
            description="Custom template",
            category=TemplateCategory.BUSINESS,
            elements=[],
            background={"type": "solid", "color": "#FFFFFF"}
        )

        self.assertIsNotNone(template)
        self.assertTrue(template.id.startswith("custom_"))


class TestThemeBuilder(unittest.TestCase):
    """Test theme building functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.builder = ThemeBuilder()

    def test_get_themes_by_style(self):
        """Test theme filtering by style."""
        professional_themes = self.builder.get_themes_by_style(
            ThemeStyle.PROFESSIONAL
        )

        self.assertGreater(len(professional_themes), 0)

    def test_color_scheme_creation(self):
        """Test custom color scheme creation."""
        scheme = self.builder.create_custom_color_scheme(
            name="My Colors",
            primary="#FF0000",
            secondary="#00FF00",
            accent="#0000FF"
        )

        self.assertIsNotNone(scheme)
        self.assertEqual(scheme.primary, "#FF0000")

    def test_color_generation(self):
        """Test color generation tools."""
        complementary = self.builder.generate_complementary_colors("#3498DB")
        self.assertEqual(len(complementary), 2)

        analogous = self.builder.generate_analogous_colors("#3498DB")
        self.assertEqual(len(analogous), 3)

        triadic = self.builder.generate_triadic_colors("#3498DB")
        self.assertEqual(len(triadic), 3)

    def test_lighten_darken(self):
        """Test color lightening and darkening."""
        base_color = "#3498DB"

        lighter = self.builder.lighten_color(base_color, 0.2)
        self.assertNotEqual(lighter, base_color)

        darker = self.builder.darken_color(base_color, 0.2)
        self.assertNotEqual(darker, base_color)


class TestExportRenderer(unittest.TestCase):
    """Test export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.renderer = ExportRenderer()

    def test_export_formats(self):
        """Test supported export formats."""
        formats = self.renderer.get_supported_formats()

        self.assertIn("pptx", formats)
        self.assertIn("pdf", formats)
        self.assertIn("html5", formats)

    def test_export_json(self):
        """Test JSON export."""
        presentation_data = {
            "title": "Test",
            "slides": []
        }

        result = self.renderer.export(
            presentation_data,
            ExportFormat.JSON
        )

        self.assertIsNotNone(result)
        self.assertGreater(len(result.getvalue()), 0)

    def test_export_html5(self):
        """Test HTML5 export."""
        presentation_data = {
            "title": "Test Presentation",
            "slides": [
                {"title": "Slide 1"},
                {"title": "Slide 2"}
            ]
        }

        result = self.renderer.export(
            presentation_data,
            ExportFormat.HTML5
        )

        html_content = result.getvalue().decode('utf-8')
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("Test Presentation", html_content)


class TestPresenterView(unittest.TestCase):
    """Test presenter view functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.presenter = PresenterView()

    def test_load_presentation(self):
        """Test loading presentation."""
        slides = [
            {"id": "1", "title": "Slide 1"},
            {"id": "2", "title": "Slide 2"}
        ]

        self.presenter.load_presentation(slides)
        self.assertEqual(self.presenter.total_slides, 2)

    def test_navigation(self):
        """Test slide navigation."""
        slides = [
            {"id": "1", "title": "Slide 1"},
            {"id": "2", "title": "Slide 2"},
            {"id": "3", "title": "Slide 3"}
        ]

        self.presenter.load_presentation(slides)
        self.presenter.start_presentation()

        self.assertTrue(self.presenter.next_slide())
        self.assertEqual(self.presenter.current_slide_index, 1)

        self.assertTrue(self.presenter.previous_slide())
        self.assertEqual(self.presenter.current_slide_index, 0)

    def test_timer(self):
        """Test presentation timer."""
        slides = [{"id": "1", "title": "Slide 1"}]

        self.presenter.load_presentation(slides)
        self.presenter.start_presentation(target_duration_minutes=30)

        self.assertIsNotNone(self.presenter.timer.start_time)
        self.assertIsNotNone(self.presenter.timer.target_duration)

    def test_progress_tracking(self):
        """Test progress tracking."""
        slides = [
            {"id": "1", "title": "Slide 1"},
            {"id": "2", "title": "Slide 2"}
        ]

        self.presenter.load_presentation(slides)
        self.presenter.start_presentation()

        progress = self.presenter.get_progress()

        self.assertEqual(progress["current_slide"], 1)
        self.assertEqual(progress["total_slides"], 2)
        self.assertEqual(progress["percentage"], 50.0)


class TestCollaborationManager(unittest.TestCase):
    """Test collaboration functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = CollaborationManager()
        self.user = User(
            id="user_1",
            name="Test User",
            email="test@example.com"
        )

    def test_join_session(self):
        """Test user session joining."""
        session = self.manager.join_session(
            self.user,
            PermissionLevel.EDITOR
        )

        self.assertIsNotNone(session)
        self.assertEqual(session.user.id, self.user.id)
        self.assertEqual(session.permission, PermissionLevel.EDITOR)

    def test_permissions(self):
        """Test permission management."""
        self.manager.join_session(self.user, PermissionLevel.VIEWER)

        self.assertFalse(self.manager.can_edit(self.user.id))
        self.assertFalse(self.manager.can_comment(self.user.id))

        self.manager.set_permission(self.user.id, PermissionLevel.EDITOR)
        self.assertTrue(self.manager.can_edit(self.user.id))

    def test_comments(self):
        """Test comment management."""
        self.manager.join_session(self.user, PermissionLevel.COMMENTER)

        comment = self.manager.add_comment(
            user=self.user,
            content="Test comment",
            slide_id="slide_1"
        )

        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, "Test comment")

        # Test reply
        reply = self.manager.reply_to_comment(
            comment.id,
            self.user,
            "Test reply"
        )

        self.assertIsNotNone(reply)

    def test_version_history(self):
        """Test version management."""
        presentation_data = {"title": "Test"}

        version = self.manager.create_version(
            user=self.user,
            presentation_data=presentation_data,
            description="Initial version"
        )

        self.assertIsNotNone(version)
        self.assertEqual(version.version_number, 1)
        self.assertTrue(version.is_current)


class TestAIAssistant(unittest.TestCase):
    """Test AI assistant functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.assistant = AIAssistant()

    def test_generate_outline(self):
        """Test presentation outline generation."""
        response = self.assistant.generate_presentation_outline(
            topic="AI in Healthcare",
            num_slides=5
        )

        self.assertTrue(response.success)
        self.assertIsNotNone(response.result)
        self.assertEqual(len(response.result), 5)

    def test_grammar_check(self):
        """Test grammar checking."""
        response = self.assistant.check_grammar(
            "this is a test sentence"
        )

        self.assertTrue(response.success)
        self.assertIn("issues", response.result)

    def test_summarize_text(self):
        """Test text summarization."""
        long_text = "This is a long text. " * 50

        response = self.assistant.summarize_text(long_text)

        self.assertTrue(response.success)
        self.assertIn("summary", response.result)

    def test_design_suggestions(self):
        """Test design suggestions."""
        slide_data = {
            "elements": [{"type": "text"}] * 10  # Too many elements
        }

        response = self.assistant.suggest_design_improvements(slide_data)

        self.assertTrue(response.success)
        self.assertGreater(len(response.suggestions), 0)


class TestPresentationEditor(unittest.TestCase):
    """Test main presentation editor."""

    def setUp(self):
        """Set up test fixtures."""
        self.editor = PresentationEditor()

    def test_initialization(self):
        """Test editor initialization."""
        self.assertIsNotNone(self.editor.presentation_id)
        self.assertIsNotNone(self.editor.slide_manager)
        self.assertIsNotNone(self.editor.element_handler)

    def test_add_slide(self):
        """Test adding slides through editor."""
        slide = self.editor.add_slide(
            layout=SlideLayout.TITLE_SLIDE,
            title="Test Slide"
        )

        self.assertIsNotNone(slide)
        self.assertEqual(len(self.editor.get_all_slides()), 1)

    def test_add_elements(self):
        """Test adding elements through editor."""
        slide = self.editor.add_slide()

        text_id = self.editor.add_text_element(
            slide.id,
            "Hello World"
        )
        self.assertIsNotNone(text_id)

        image_id = self.editor.add_image_element(
            slide.id,
            "https://example.com/image.jpg"
        )
        self.assertIsNotNone(image_id)

    def test_apply_theme(self):
        """Test theme application."""
        slide = self.editor.add_slide()
        success = self.editor.apply_theme("professional")

        self.assertTrue(success)
        self.assertEqual(self.editor.active_theme_id, "professional")

    def test_serialization(self):
        """Test save and load."""
        self.editor.set_presentation_info(
            title="Test Presentation",
            author="Test Author"
        )

        slide = self.editor.add_slide(title="Test Slide")

        # Convert to dict
        data = self.editor.to_dict()

        self.assertEqual(data["title"], "Test Presentation")
        self.assertEqual(len(data["slides"]), 1)

        # Load into new editor
        new_editor = PresentationEditor()
        new_editor.from_dict(data)

        self.assertEqual(new_editor.title, "Test Presentation")
        self.assertEqual(len(new_editor.get_all_slides()), 1)

    def test_statistics(self):
        """Test statistics gathering."""
        self.editor.add_slide()
        self.editor.add_slide()

        stats = self.editor.get_statistics()

        self.assertEqual(stats["total_slides"], 2)
        self.assertIn("total_elements", stats)

    def test_validation(self):
        """Test presentation validation."""
        issues = self.editor.validate()

        # Should have issues (no title, no slides)
        self.assertGreater(len(issues), 0)

        self.editor.set_presentation_info(title="My Presentation")
        slide = self.editor.add_slide()
        self.editor.add_text_element(slide.id, "Content")

        issues = self.editor.validate()

        # Should have fewer issues now
        self.assertLess(len(issues), 3)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSlideManager))
    suite.addTests(loader.loadTestsFromTestCase(TestElementHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestAnimationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestTemplateManager))
    suite.addTests(loader.loadTestsFromTestCase(TestThemeBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestExportRenderer))
    suite.addTests(loader.loadTestsFromTestCase(TestPresenterView))
    suite.addTests(loader.loadTestsFromTestCase(TestCollaborationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAIAssistant))
    suite.addTests(loader.loadTestsFromTestCase(TestPresentationEditor))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
