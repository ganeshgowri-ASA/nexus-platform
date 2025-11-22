"""
Comprehensive test suite for the Mind Map module.

Tests cover:
- Node creation and management
- Branch connections
- Layout algorithms
- Theme application
- Export functionality
- AI features
- Collaboration
"""

import unittest
from datetime import datetime
import json

from ..mind_engine import MindMapEngine
from ..nodes import MindMapNode, Position, NodeShape, Priority, Task
from ..branches import Branch, ConnectionType
from ..layout import LayoutType, LayoutConfig
from ..themes import ThemeName
from ..export import ExportFormat
from ..collaboration import User, CollaborationSession
from ..ai_brainstorm import AIBrainstormEngine


class TestMindMapNode(unittest.TestCase):
    """Test node functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.node = MindMapNode(
            text="Test Node",
            position=Position(100, 100)
        )

    def test_node_creation(self):
        """Test basic node creation."""
        self.assertEqual(self.node.text, "Test Node")
        self.assertEqual(self.node.position.x, 100)
        self.assertEqual(self.node.position.y, 100)
        self.assertIsNotNone(self.node.id)

    def test_add_child(self):
        """Test adding children to a node."""
        child_id = "child-1"
        self.node.add_child(child_id)
        self.assertIn(child_id, self.node.children_ids)

    def test_add_tag(self):
        """Test adding tags."""
        self.node.add_tag("important")
        self.assertIn("important", self.node.tags)

    def test_add_task(self):
        """Test adding tasks."""
        task = Task(description="Complete this task")
        self.node.add_task(task)
        self.assertEqual(len(self.node.tasks), 1)
        self.assertFalse(self.node.tasks[0].completed)

    def test_toggle_task(self):
        """Test toggling task completion."""
        task = Task(description="Test task")
        self.node.add_task(task)
        status = self.node.toggle_task(task.id)
        self.assertTrue(status)

    def test_node_serialization(self):
        """Test node to/from dict conversion."""
        node_dict = self.node.to_dict()
        restored_node = MindMapNode.from_dict(node_dict)

        self.assertEqual(restored_node.text, self.node.text)
        self.assertEqual(restored_node.position.x, self.node.position.x)
        self.assertEqual(restored_node.id, self.node.id)


class TestMindMapEngine(unittest.TestCase):
    """Test main engine functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = MindMapEngine()

    def test_create_root_node(self):
        """Test creating a root node."""
        root_id = self.engine.create_root_node("Root")
        self.assertEqual(self.engine.root_id, root_id)
        self.assertIn(root_id, self.engine.nodes)

    def test_create_child_node(self):
        """Test creating child nodes."""
        root_id = self.engine.create_root_node("Root")
        child_id = self.engine.create_node("Child", parent_id=root_id)

        self.assertIn(child_id, self.engine.nodes)
        self.assertEqual(self.engine.nodes[child_id].parent_id, root_id)
        self.assertIn(child_id, self.engine.nodes[root_id].children_ids)

    def test_delete_node(self):
        """Test deleting nodes."""
        root_id = self.engine.create_root_node("Root")
        child_id = self.engine.create_node("Child", parent_id=root_id)

        self.engine.delete_node(child_id)
        self.assertNotIn(child_id, self.engine.nodes)

    def test_reparent_node(self):
        """Test changing node parent."""
        root_id = self.engine.create_root_node("Root")
        child1_id = self.engine.create_node("Child 1", parent_id=root_id)
        child2_id = self.engine.create_node("Child 2", parent_id=root_id)

        # Reparent child2 to child1
        self.engine.reparent_node(child2_id, child1_id)

        self.assertEqual(self.engine.nodes[child2_id].parent_id, child1_id)
        self.assertIn(child2_id, self.engine.nodes[child1_id].children_ids)

    def test_search_nodes(self):
        """Test node search functionality."""
        root_id = self.engine.create_root_node("Project Plan")
        child1_id = self.engine.create_node("Design Phase", parent_id=root_id)
        child2_id = self.engine.create_node("Development Phase", parent_id=root_id)

        results = self.engine.search_nodes("phase")
        self.assertEqual(len(results), 2)

    def test_apply_layout(self):
        """Test layout application."""
        root_id = self.engine.create_root_node("Root")
        for i in range(3):
            self.engine.create_node(f"Child {i}", parent_id=root_id)

        self.engine.apply_layout(LayoutType.RADIAL)

        # Check that nodes have been positioned
        for node in self.engine.nodes.values():
            self.assertIsNotNone(node.position)

    def test_apply_theme(self):
        """Test theme application."""
        root_id = self.engine.create_root_node("Root")
        child_id = self.engine.create_node("Child", parent_id=root_id)

        success = self.engine.apply_theme(ThemeName.PROFESSIONAL.value)
        self.assertTrue(success)

        # Check that theme was applied
        root = self.engine.nodes[root_id]
        self.assertIsNotNone(root.style.background_color)

    def test_export_json(self):
        """Test JSON export."""
        root_id = self.engine.create_root_node("Test Map")
        child_id = self.engine.create_node("Child", parent_id=root_id)

        data = self.engine.export(ExportFormat.JSON)
        self.assertIsInstance(data, bytes)

        # Verify it's valid JSON
        json_data = json.loads(data.decode('utf-8'))
        self.assertIn("nodes", json_data)
        self.assertIn("branches", json_data)

    def test_export_markdown(self):
        """Test Markdown export."""
        root_id = self.engine.create_root_node("Test Map")
        child_id = self.engine.create_node("Child", parent_id=root_id)

        data = self.engine.export(ExportFormat.MARKDOWN)
        self.assertIsInstance(data, bytes)

        content = data.decode('utf-8')
        self.assertIn("# Test Map", content)
        self.assertIn("## Child", content)

    def test_import_export_roundtrip(self):
        """Test export and import maintain data integrity."""
        # Create a mind map
        root_id = self.engine.create_root_node("Test Map")
        child_id = self.engine.create_node("Child", parent_id=root_id)
        self.engine.nodes[child_id].notes = "Test notes"

        # Export to JSON
        data = self.engine.export(ExportFormat.JSON)

        # Import into new engine
        new_engine = MindMapEngine()
        new_engine.import_from_json(data)

        # Verify data
        self.assertEqual(len(new_engine.nodes), len(self.engine.nodes))
        self.assertIn(root_id, new_engine.nodes)
        self.assertIn(child_id, new_engine.nodes)
        self.assertEqual(new_engine.nodes[child_id].notes, "Test notes")

    def test_undo_redo(self):
        """Test undo/redo functionality."""
        root_id = self.engine.create_root_node("Root")
        child_id = self.engine.create_node("Child", parent_id=root_id)

        initial_count = len(self.engine.nodes)

        # Delete node and undo
        self.engine.delete_node(child_id)
        self.assertEqual(len(self.engine.nodes), initial_count - 1)

        self.engine.undo()
        self.assertEqual(len(self.engine.nodes), initial_count)

    def test_validate_integrity(self):
        """Test integrity validation."""
        root_id = self.engine.create_root_node("Root")
        child_id = self.engine.create_node("Child", parent_id=root_id)

        errors = self.engine.validate_integrity()
        self.assertEqual(len(errors), 0)


class TestBranches(unittest.TestCase):
    """Test branch functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = MindMapEngine()
        self.root_id = self.engine.create_root_node("Root")
        self.child1_id = self.engine.create_node("Child 1", parent_id=self.root_id)
        self.child2_id = self.engine.create_node("Child 2", parent_id=self.root_id)

    def test_create_association_branch(self):
        """Test creating association branches."""
        branch_id = self.engine.create_branch(
            self.child1_id,
            self.child2_id,
            ConnectionType.ASSOCIATION
        )

        self.assertIsNotNone(branch_id)
        branch = self.engine.branch_manager.get_branch(branch_id)
        self.assertEqual(branch.connection_type, ConnectionType.ASSOCIATION)

    def test_find_branch_between(self):
        """Test finding branches between nodes."""
        branch = self.engine.branch_manager.find_branch_between(
            self.root_id,
            self.child1_id
        )
        self.assertIsNotNone(branch)


class TestAIFeatures(unittest.TestCase):
    """Test AI-powered features."""

    def setUp(self):
        """Set up test fixtures."""
        self.ai_engine = AIBrainstormEngine()

    def test_generate_from_text(self):
        """Test mind map generation from text."""
        text = """
        Project Planning
        - Phase 1: Research
        - Phase 2: Design
        - Phase 3: Development
        """

        nodes, root_id = self.ai_engine.generate_mindmap_from_text(text)

        self.assertIsNotNone(root_id)
        self.assertIn(root_id, nodes)
        self.assertGreater(len(nodes), 1)

    def test_suggest_ideas(self):
        """Test idea suggestions."""
        suggestions = self.ai_engine.suggest_related_ideas("Marketing", count=5)

        self.assertEqual(len(suggestions), 5)
        self.assertIsInstance(suggestions[0], str)

    def test_extract_structure(self):
        """Test structure extraction from text."""
        text = """
        Main Topic
        - Subtopic 1
        - Subtopic 2
          - Detail A
          - Detail B
        """

        structure = self.ai_engine._extract_structure_from_text(text)

        self.assertIn("title", structure)
        self.assertIn("topics", structure)
        self.assertGreater(len(structure["topics"]), 0)

    def test_organize_by_category(self):
        """Test automatic categorization."""
        engine = MindMapEngine()
        root_id = engine.create_root_node("Root")
        engine.create_node("TODO: Complete this task", parent_id=root_id)
        engine.create_node("What is the deadline?", parent_id=root_id)
        engine.create_node("New idea for feature", parent_id=root_id)

        categories = self.ai_engine.organize_nodes_by_category(engine.nodes)

        self.assertIn("Action Items", categories)
        self.assertIn("Questions", categories)
        self.assertIn("Ideas", categories)


class TestCollaboration(unittest.TestCase):
    """Test collaboration features."""

    def setUp(self):
        """Set up test fixtures."""
        self.session = CollaborationSession()
        self.user1 = User(
            id="user1",
            name="Alice",
            email="alice@example.com",
            color="#FF0000"
        )
        self.user2 = User(
            id="user2",
            name="Bob",
            email="bob@example.com",
            color="#0000FF"
        )

    def test_add_users(self):
        """Test adding users to session."""
        self.session.add_user(self.user1)
        self.session.add_user(self.user2)

        self.assertEqual(len(self.session.users), 2)
        self.assertIn(self.user1.id, self.session.users)

    def test_lock_node(self):
        """Test node locking."""
        self.session.add_user(self.user1)

        success = self.session.lock_node("node1", self.user1.id)
        self.assertTrue(success)

        # Try to lock same node with different user
        success = self.session.lock_node("node1", self.user2.id)
        self.assertFalse(success)

    def test_unlock_node(self):
        """Test node unlocking."""
        self.session.add_user(self.user1)
        self.session.lock_node("node1", self.user1.id)

        success = self.session.unlock_node("node1", self.user1.id)
        self.assertTrue(success)

        self.assertFalse(self.session.is_node_locked("node1"))


class TestLayouts(unittest.TestCase):
    """Test layout algorithms."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = MindMapEngine()
        root_id = self.engine.create_root_node("Root")

        # Create a tree structure
        for i in range(3):
            child_id = self.engine.create_node(f"Child {i}", parent_id=root_id)
            for j in range(2):
                self.engine.create_node(f"Grandchild {i}-{j}", parent_id=child_id)

    def test_radial_layout(self):
        """Test radial layout algorithm."""
        self.engine.apply_layout(LayoutType.RADIAL)

        # Verify all nodes are positioned
        for node in self.engine.nodes.values():
            self.assertIsNotNone(node.position)
            self.assertIsInstance(node.position.x, (int, float))
            self.assertIsInstance(node.position.y, (int, float))

    def test_tree_layout(self):
        """Test tree layout algorithm."""
        self.engine.apply_layout(LayoutType.TREE)

        for node in self.engine.nodes.values():
            self.assertIsNotNone(node.position)

    def test_mindmap_layout(self):
        """Test mind map layout algorithm."""
        self.engine.apply_layout(LayoutType.MIND_MAP)

        for node in self.engine.nodes.values():
            self.assertIsNotNone(node.position)


class TestThemes(unittest.TestCase):
    """Test theme system."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = MindMapEngine()

    def test_list_themes(self):
        """Test listing available themes."""
        themes = self.engine.theme_manager.list_themes()

        self.assertGreater(len(themes), 0)
        self.assertIn(ThemeName.CLASSIC.value, themes)
        self.assertIn(ThemeName.PROFESSIONAL.value, themes)

    def test_get_theme(self):
        """Test getting a theme."""
        theme = self.engine.theme_manager.get_theme(ThemeName.DARK.value)

        self.assertIsNotNone(theme)
        self.assertEqual(theme.name, "Dark")

    def test_create_custom_theme(self):
        """Test creating custom themes."""
        theme = self.engine.theme_manager.create_custom_theme(
            name="MyTheme",
            base_color="#FF5733",
            description="My custom theme"
        )

        self.assertEqual(theme.name, "MyTheme")
        self.assertIn("MyTheme", self.engine.theme_manager.list_themes())


def run_tests():
    """Run all tests."""
    unittest.main()


if __name__ == "__main__":
    run_tests()
