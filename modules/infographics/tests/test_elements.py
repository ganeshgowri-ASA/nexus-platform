"""
Tests for elements module.
"""

import unittest
from modules.infographics.elements import (
    ElementFactory, ElementPresets, ShapeType, TextAlign,
    TextElement, ShapeElement, IconElement, GroupElement
)


class TestElementFactory(unittest.TestCase):
    """Tests for ElementFactory."""

    def test_create_text(self):
        """Test creating text element."""
        elem = ElementFactory.create_text("Hello", 10, 20, font_size=24)
        self.assertIsInstance(elem, TextElement)
        self.assertEqual(elem.text, "Hello")
        self.assertEqual(elem.position.x, 10)
        self.assertEqual(elem.position.y, 20)
        self.assertEqual(elem.text_style.font_size, 24)

    def test_create_shape(self):
        """Test creating shape element."""
        elem = ElementFactory.create_shape(ShapeType.RECTANGLE, 0, 0, 100, 100)
        self.assertIsInstance(elem, ShapeElement)
        self.assertEqual(elem.shape_type, ShapeType.RECTANGLE)
        self.assertEqual(elem.position.width, 100)
        self.assertEqual(elem.position.height, 100)

    def test_create_icon(self):
        """Test creating icon element."""
        elem = ElementFactory.create_icon("star", 50, 50, size=64)
        self.assertIsInstance(elem, IconElement)
        self.assertEqual(elem.icon_name, "star")
        self.assertEqual(elem.position.width, 64)
        self.assertEqual(elem.position.height, 64)

    def test_create_group(self):
        """Test creating group element."""
        elem1 = ElementFactory.create_text("Text1")
        elem2 = ElementFactory.create_shape(ShapeType.CIRCLE, 0, 0, 50, 50)
        group = ElementFactory.create_group([elem1, elem2])

        self.assertIsInstance(group, GroupElement)
        self.assertEqual(len(group.children), 2)


class TestElementPresets(unittest.TestCase):
    """Tests for ElementPresets."""

    def test_heading(self):
        """Test heading preset."""
        elem = ElementPresets.heading("Title", 100, 100)
        self.assertEqual(elem.text, "Title")
        self.assertEqual(elem.text_style.font_size, 32)
        self.assertEqual(elem.text_style.font_weight, "bold")

    def test_circle(self):
        """Test circle preset."""
        elem = ElementPresets.circle(100, 100, radius=25)
        self.assertEqual(elem.shape_type, ShapeType.CIRCLE)
        self.assertEqual(elem.position.width, 50)  # diameter = 2*radius


class TestElementOperations(unittest.TestCase):
    """Tests for element operations."""

    def test_duplicate(self):
        """Test element duplication."""
        original = ElementFactory.create_text("Original", 100, 100)
        duplicate = original.duplicate()

        self.assertNotEqual(original.id, duplicate.id)
        self.assertEqual(original.text, duplicate.text)
        self.assertNotEqual(original.position.x, duplicate.position.x)  # Offset applied

    def test_to_dict(self):
        """Test element serialization."""
        elem = ElementFactory.create_text("Test", 50, 50)
        data = elem.to_dict()

        self.assertIn('id', data)
        self.assertIn('text', data)
        self.assertEqual(data['text'], "Test")
        self.assertEqual(data['position']['x'], 50)


if __name__ == '__main__':
    unittest.main()
