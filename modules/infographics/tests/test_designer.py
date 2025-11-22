"""
Tests for designer module.
"""

import unittest
from modules.infographics.designer import InfographicDesigner, AlignmentType
from modules.infographics.elements import ElementFactory, ShapeType


class TestInfographicDesigner(unittest.TestCase):
    """Tests for InfographicDesigner."""

    def setUp(self):
        """Set up test designer."""
        self.designer = InfographicDesigner()

    def test_add_element(self):
        """Test adding element."""
        elem = ElementFactory.create_text("Test")
        self.designer.add_element(elem)

        self.assertEqual(len(self.designer.elements), 1)
        self.assertEqual(self.designer.get_element(elem.id), elem)

    def test_remove_element(self):
        """Test removing element."""
        elem = ElementFactory.create_text("Test")
        self.designer.add_element(elem)
        self.designer.remove_element(elem.id)

        self.assertEqual(len(self.designer.elements), 0)

    def test_select_element(self):
        """Test selecting element."""
        elem = ElementFactory.create_text("Test")
        self.designer.add_element(elem)
        self.designer.select_element(elem.id)

        self.assertIn(elem.id, self.designer.selected_elements)

    def test_move_element(self):
        """Test moving element."""
        elem = ElementFactory.create_text("Test", 100, 100)
        self.designer.add_element(elem)
        self.designer.move_element(elem.id, 10, 20)

        self.assertEqual(elem.position.x, 110)
        self.assertEqual(elem.position.y, 120)

    def test_rotate_element(self):
        """Test rotating element."""
        elem = ElementFactory.create_shape(ShapeType.RECTANGLE, 0, 0, 100, 100)
        self.designer.add_element(elem)
        self.designer.rotate_element(elem.id, 45)

        self.assertEqual(elem.position.rotation, 45)

    def test_duplicate_element(self):
        """Test duplicating element."""
        elem = ElementFactory.create_text("Original")
        self.designer.add_element(elem)
        dup_id = self.designer.duplicate_element(elem.id)

        self.assertEqual(len(self.designer.elements), 2)
        self.assertIsNotNone(dup_id)

    def test_group_elements(self):
        """Test grouping elements."""
        elem1 = ElementFactory.create_text("Text1")
        elem2 = ElementFactory.create_text("Text2")
        self.designer.add_element(elem1)
        self.designer.add_element(elem2)

        group_id = self.designer.group_elements([elem1.id, elem2.id])

        self.assertIsNotNone(group_id)
        # Original elements should be removed, group added
        self.assertEqual(len(self.designer.elements), 1)

    def test_align_elements(self):
        """Test aligning elements."""
        elem1 = ElementFactory.create_shape(ShapeType.RECTANGLE, 100, 100, 50, 50)
        elem2 = ElementFactory.create_shape(ShapeType.RECTANGLE, 200, 150, 50, 50)
        self.designer.add_element(elem1)
        self.designer.add_element(elem2)

        self.designer.align_elements([elem1.id, elem2.id], AlignmentType.LEFT)

        # Both should have same x position
        self.assertEqual(elem1.position.x, elem2.position.x)

    def test_bring_to_front(self):
        """Test bringing element to front."""
        elem1 = ElementFactory.create_text("Back")
        elem2 = ElementFactory.create_text("Front")
        self.designer.add_element(elem1)
        self.designer.add_element(elem2)

        self.designer.bring_to_front(elem1.id)

        self.assertGreater(elem1.position.z_index, elem2.position.z_index)

    def test_clipboard_operations(self):
        """Test copy/paste."""
        elem = ElementFactory.create_text("Original")
        self.designer.add_element(elem)
        self.designer.select_element(elem.id)

        self.designer.copy_selected()
        pasted_ids = self.designer.paste()

        self.assertEqual(len(pasted_ids), 1)
        self.assertEqual(len(self.designer.elements), 2)


if __name__ == '__main__':
    unittest.main()
