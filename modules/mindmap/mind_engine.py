"""
Mind Map Engine - Main Orchestrator

This module is the main engine that coordinates all mind mapping features
including nodes, branches, layouts, themes, export, collaboration, and AI.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid
import json

from .nodes import MindMapNode, Position
from .branches import Branch, BranchManager, ConnectionType
from .layout import LayoutEngine, LayoutType, LayoutConfig
from .themes import ThemeManager, Theme
from .export import ExportEngine, ExportFormat
from .collaboration import CollaborationSession, User
from .ai_brainstorm import AIBrainstormEngine


class MindMapEngine:
    """
    Main mind mapping engine that coordinates all features.

    Features:
    - Complete node and branch management
    - Automatic layout algorithms
    - Theme application
    - Export to multiple formats
    - Real-time collaboration
    - AI-powered brainstorming
    - Undo/redo support
    - Template system
    """

    def __init__(self, mindmap_id: Optional[str] = None):
        self.id = mindmap_id or str(uuid.uuid4())
        self.title = "New Mind Map"
        self.description = ""
        self.created_at = datetime.now()
        self.modified_at = datetime.now()

        # Core components
        self.nodes: Dict[str, MindMapNode] = {}
        self.branch_manager = BranchManager()
        self.root_id: Optional[str] = None

        # Feature engines
        self.layout_engine = LayoutEngine()
        self.theme_manager = ThemeManager()
        self.export_engine = ExportEngine()
        self.ai_engine = AIBrainstormEngine()

        # Collaboration
        self.collaboration_session: Optional[CollaborationSession] = None

        # Undo/redo stacks
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []

        # Metadata
        self.metadata: Dict[str, Any] = {}
        self.tags: Set[str] = set()

    # ==================== Node Management ====================

    def create_root_node(self, text: str) -> str:
        """Create the root node of the mind map."""
        node_id = str(uuid.uuid4())
        node = MindMapNode(
            text=text,
            node_id=node_id,
            position=Position(960, 540),
        )
        self.nodes[node_id] = node
        self.root_id = node_id
        self._mark_modified()
        return node_id

    def create_node(
        self,
        text: str,
        parent_id: Optional[str] = None,
        position: Optional[Position] = None,
    ) -> str:
        """
        Create a new node.

        Args:
            text: Node text
            parent_id: Parent node ID (None for floating node)
            position: Node position

        Returns:
            ID of the created node
        """
        node_id = str(uuid.uuid4())
        node = MindMapNode(
            text=text,
            node_id=node_id,
            parent_id=parent_id,
            position=position or Position(0, 0),
        )
        self.nodes[node_id] = node

        # Create branch if has parent
        if parent_id and parent_id in self.nodes:
            self.nodes[parent_id].add_child(node_id)
            branch = Branch(parent_id, node_id, ConnectionType.PARENT_CHILD)
            self.branch_manager.add_branch(branch)

        self._mark_modified()
        self._save_state_for_undo()
        return node_id

    def delete_node(self, node_id: str, delete_children: bool = True) -> bool:
        """
        Delete a node.

        Args:
            node_id: ID of node to delete
            delete_children: If True, delete all children recursively

        Returns:
            True if deleted, False if not found
        """
        if node_id not in self.nodes:
            return False

        if node_id == self.root_id:
            raise ValueError("Cannot delete root node")

        node = self.nodes[node_id]

        # Handle children
        if delete_children:
            for child_id in list(node.children_ids):
                self.delete_node(child_id, delete_children=True)
        else:
            # Re-parent children to this node's parent
            for child_id in node.children_ids:
                if child_id in self.nodes:
                    self.nodes[child_id].parent_id = node.parent_id
                    if node.parent_id and node.parent_id in self.nodes:
                        self.nodes[node.parent_id].add_child(child_id)

        # Remove from parent's children
        if node.parent_id and node.parent_id in self.nodes:
            self.nodes[node.parent_id].remove_child(node_id)

        # Remove all branches connected to this node
        self.branch_manager.remove_all_branches_for_node(node_id)

        # Delete the node
        del self.nodes[node_id]

        self._mark_modified()
        self._save_state_for_undo()
        return True

    def update_node_text(self, node_id: str, text: str) -> bool:
        """Update node text."""
        if node_id not in self.nodes:
            return False

        self.nodes[node_id].text = text
        self._mark_modified()
        return True

    def move_node(self, node_id: str, new_position: Position) -> bool:
        """Move a node to a new position."""
        if node_id not in self.nodes:
            return False

        self.nodes[node_id].update_position(new_position)
        self._mark_modified()
        return True

    def reparent_node(self, node_id: str, new_parent_id: str) -> bool:
        """Change the parent of a node."""
        if node_id not in self.nodes or new_parent_id not in self.nodes:
            return False

        if node_id == self.root_id:
            raise ValueError("Cannot reparent root node")

        # Prevent circular references
        if self._would_create_cycle(node_id, new_parent_id):
            raise ValueError("Would create circular reference")

        node = self.nodes[node_id]
        old_parent_id = node.parent_id

        # Remove from old parent
        if old_parent_id and old_parent_id in self.nodes:
            self.nodes[old_parent_id].remove_child(node_id)

        # Add to new parent
        node.parent_id = new_parent_id
        self.nodes[new_parent_id].add_child(node_id)

        # Update branches
        if old_parent_id:
            old_branch = self.branch_manager.find_branch_between(old_parent_id, node_id)
            if old_branch:
                self.branch_manager.remove_branch(old_branch.id)

        new_branch = Branch(new_parent_id, node_id, ConnectionType.PARENT_CHILD)
        self.branch_manager.add_branch(new_branch)

        self._mark_modified()
        self._save_state_for_undo()
        return True

    def _would_create_cycle(self, node_id: str, potential_parent_id: str) -> bool:
        """Check if reparenting would create a cycle."""
        current = potential_parent_id
        while current:
            if current == node_id:
                return True
            if current not in self.nodes:
                break
            current = self.nodes[current].parent_id
        return False

    def get_node(self, node_id: str) -> Optional[MindMapNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_children(self, node_id: str) -> List[MindMapNode]:
        """Get all children of a node."""
        if node_id not in self.nodes:
            return []
        return [
            self.nodes[child_id]
            for child_id in self.nodes[node_id].children_ids
            if child_id in self.nodes
        ]

    def search_nodes(self, query: str) -> List[MindMapNode]:
        """Search for nodes by text."""
        query_lower = query.lower()
        return [
            node
            for node in self.nodes.values()
            if query_lower in node.text.lower() or query_lower in node.notes.lower()
        ]

    # ==================== Branch Management ====================

    def create_branch(
        self,
        source_id: str,
        target_id: str,
        connection_type: ConnectionType = ConnectionType.ASSOCIATION,
    ) -> Optional[str]:
        """Create a custom branch between nodes."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        branch = Branch(source_id, target_id, connection_type)
        self.branch_manager.add_branch(branch)
        self._mark_modified()
        return branch.id

    def delete_branch(self, branch_id: str) -> bool:
        """Delete a branch."""
        success = self.branch_manager.remove_branch(branch_id)
        if success:
            self._mark_modified()
        return success

    # ==================== Layout Management ====================

    def apply_layout(
        self, layout_type: LayoutType = LayoutType.MIND_MAP, config: Optional[LayoutConfig] = None
    ) -> None:
        """Apply an automatic layout to all nodes."""
        if not self.root_id or not self.nodes:
            return

        if config:
            self.layout_engine.config = config

        positions = self.layout_engine.apply_layout(self.nodes, self.root_id, layout_type)

        # Apply positions to nodes
        for node_id, position in positions.items():
            if node_id in self.nodes:
                self.nodes[node_id].update_position(position, is_floating=False)

        self._mark_modified()

    def optimize_layout(self) -> None:
        """Optimize current layout to avoid overlaps."""
        positions = {node_id: node.position for node_id, node in self.nodes.items()}
        optimized = self.layout_engine.optimize_positions(self.nodes, positions)

        for node_id, position in optimized.items():
            if node_id in self.nodes:
                self.nodes[node_id].update_position(position)

        self._mark_modified()

    # ==================== Theme Management ====================

    def apply_theme(self, theme_name: str) -> bool:
        """Apply a theme to the entire mind map."""
        theme = self.theme_manager.get_theme(theme_name)
        if not theme:
            return False

        # Apply theme to all nodes based on their hierarchy level
        if self.root_id:
            self._apply_theme_recursively(self.root_id, theme, 0)

        self._mark_modified()
        return True

    def _apply_theme_recursively(self, node_id: str, theme: Theme, level: int) -> None:
        """Apply theme to node and its children recursively."""
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]
        self.theme_manager.apply_theme_to_node(node, theme, level)

        for child_id in node.children_ids:
            self._apply_theme_recursively(child_id, theme, level + 1)

    # ==================== Export Management ====================

    def export(
        self, format: ExportFormat, options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export mind map to specified format."""
        return self.export_engine.export(
            self.nodes,
            self.branch_manager.branches,
            self.root_id or "",
            format,
            options,
        )

    def import_from_json(self, data: bytes) -> None:
        """Import mind map from JSON."""
        nodes, branches, root_id = self.export_engine.import_json(data)
        self.nodes = nodes
        self.branch_manager.branches = branches
        self.root_id = root_id
        self._mark_modified()

    # ==================== AI Features ====================

    def generate_from_text(self, text: str, root_text: Optional[str] = None) -> None:
        """Generate mind map from text using AI."""
        nodes, root_id = self.ai_engine.generate_mindmap_from_text(text, root_text)
        self.nodes = nodes
        self.root_id = root_id

        # Create branches
        for node in nodes.values():
            if node.parent_id:
                branch = Branch(node.parent_id, node.id, ConnectionType.PARENT_CHILD)
                self.branch_manager.add_branch(branch)

        # Apply layout
        self.apply_layout(LayoutType.MIND_MAP)

        self._mark_modified()

    def suggest_ideas_for_node(self, node_id: str, count: int = 5) -> List[str]:
        """Get AI suggestions for expanding a node."""
        if node_id not in self.nodes:
            return []

        node = self.nodes[node_id]

        # Get context from siblings and parent
        context = []
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            context.append(parent.text)
            for sibling_id in parent.children_ids:
                if sibling_id != node_id and sibling_id in self.nodes:
                    context.append(self.nodes[sibling_id].text)

        return self.ai_engine.suggest_related_ideas(node.text, context, count)

    def auto_organize(self) -> Dict[str, Any]:
        """Get AI suggestions for organizing the mind map."""
        if not self.root_id:
            return {}

        return self.ai_engine.suggest_reorganization(self.nodes, self.root_id)

    # ==================== Collaboration ====================

    def start_collaboration(self) -> str:
        """Start a collaboration session."""
        self.collaboration_session = CollaborationSession()
        return self.collaboration_session.session_id

    def add_collaborator(self, user: User) -> None:
        """Add a user to the collaboration session."""
        if self.collaboration_session:
            self.collaboration_session.add_user(user)

    # ==================== Undo/Redo ====================

    def _save_state_for_undo(self) -> None:
        """Save current state for undo."""
        state = self.to_dict()
        self.undo_stack.append(state)

        # Limit undo stack size
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

        # Clear redo stack on new action
        self.redo_stack.clear()

    def undo(self) -> bool:
        """Undo the last action."""
        if not self.undo_stack:
            return False

        # Save current state to redo
        current_state = self.to_dict()
        self.redo_stack.append(current_state)

        # Restore previous state
        previous_state = self.undo_stack.pop()
        self._restore_from_dict(previous_state)

        return True

    def redo(self) -> bool:
        """Redo the last undone action."""
        if not self.redo_stack:
            return False

        # Save current state to undo
        current_state = self.to_dict()
        self.undo_stack.append(current_state)

        # Restore next state
        next_state = self.redo_stack.pop()
        self._restore_from_dict(next_state)

        return True

    # ==================== Persistence ====================

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire mind map to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "root_id": self.root_id,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "branches": self.branch_manager.to_dict(),
            "metadata": self.metadata,
            "tags": list(self.tags),
        }

    def _restore_from_dict(self, data: Dict[str, Any]) -> None:
        """Restore mind map from dictionary."""
        self.id = data["id"]
        self.title = data["title"]
        self.description = data.get("description", "")
        self.created_at = datetime.fromisoformat(data["created_at"])
        self.modified_at = datetime.fromisoformat(data["modified_at"])
        self.root_id = data.get("root_id")

        # Restore nodes
        self.nodes = {}
        for node_id, node_data in data["nodes"].items():
            self.nodes[node_id] = MindMapNode.from_dict(node_data)

        # Restore branches
        self.branch_manager = BranchManager.from_dict(data["branches"])

        self.metadata = data.get("metadata", {})
        self.tags = set(data.get("tags", []))

    def save_to_file(self, filepath: str) -> None:
        """Save mind map to JSON file."""
        data = self.to_dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> MindMapEngine:
        """Load mind map from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        engine = cls()
        engine._restore_from_dict(data)
        return engine

    # ==================== Statistics ====================

    def get_statistics(self) -> Dict[str, Any]:
        """Get mind map statistics."""
        if not self.root_id or not self.nodes:
            return {}

        # Calculate depth
        max_depth = 0

        def calc_depth(node_id: str, depth: int = 0):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            if node_id in self.nodes:
                for child_id in self.nodes[node_id].children_ids:
                    calc_depth(child_id, depth + 1)

        calc_depth(self.root_id)

        # Count nodes with tasks, notes, etc.
        nodes_with_tasks = sum(1 for n in self.nodes.values() if n.tasks)
        nodes_with_notes = sum(1 for n in self.nodes.values() if n.notes)
        nodes_with_tags = sum(1 for n in self.nodes.values() if n.tags)

        return {
            "total_nodes": len(self.nodes),
            "total_branches": len(self.branch_manager.branches),
            "max_depth": max_depth,
            "nodes_with_tasks": nodes_with_tasks,
            "nodes_with_notes": nodes_with_notes,
            "nodes_with_tags": nodes_with_tags,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
        }

    # ==================== Utility Methods ====================

    def _mark_modified(self) -> None:
        """Mark mind map as modified."""
        self.modified_at = datetime.now()

    def validate_integrity(self) -> List[str]:
        """
        Validate mind map integrity.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check root exists
        if not self.root_id:
            errors.append("No root node defined")
        elif self.root_id not in self.nodes:
            errors.append(f"Root node {self.root_id} not found in nodes")

        # Check all parent references are valid
        for node_id, node in self.nodes.items():
            if node.parent_id and node.parent_id not in self.nodes:
                errors.append(
                    f"Node {node_id} has invalid parent {node.parent_id}"
                )

            # Check all children exist
            for child_id in node.children_ids:
                if child_id not in self.nodes:
                    errors.append(
                        f"Node {node_id} has invalid child {child_id}"
                    )

        # Validate branches
        invalid_branches = self.branch_manager.validate_integrity(set(self.nodes.keys()))
        if invalid_branches:
            errors.append(f"Found {len(invalid_branches)} invalid branches")

        return errors

    def __repr__(self) -> str:
        """String representation."""
        return f"MindMapEngine(id={self.id}, title='{self.title}', nodes={len(self.nodes)})"
