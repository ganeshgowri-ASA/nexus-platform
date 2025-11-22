"""
Mind Map Node Management System

This module provides comprehensive node management for mind mapping,
including creation, modification, and rich content support.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Literal
from datetime import datetime
from enum import Enum
import uuid


class NodeShape(Enum):
    """Available node shapes for visual representation."""
    RECTANGLE = "rectangle"
    ROUNDED_RECTANGLE = "rounded_rectangle"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    DIAMOND = "diamond"
    HEXAGON = "hexagon"
    CLOUD = "cloud"
    STAR = "star"
    TRIANGLE = "triangle"


class Priority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Position:
    """2D position on the canvas."""
    x: float
    y: float

    def distance_to(self, other: Position) -> float:
        """Calculate Euclidean distance to another position."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for serialization."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> Position:
        """Create Position from dictionary."""
        return cls(x=data["x"], y=data["y"])


@dataclass
class NodeStyle:
    """Visual styling for a node."""
    background_color: str = "#FFFFFF"
    text_color: str = "#000000"
    border_color: str = "#000000"
    border_width: int = 2
    font_family: str = "Arial"
    font_size: int = 14
    font_weight: Literal["normal", "bold"] = "normal"
    font_style: Literal["normal", "italic"] = "normal"
    shape: NodeShape = NodeShape.ROUNDED_RECTANGLE
    opacity: float = 1.0
    shadow: bool = True
    icon: Optional[str] = None
    emoji: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "background_color": self.background_color,
            "text_color": self.text_color,
            "border_color": self.border_color,
            "border_width": self.border_width,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "font_style": self.font_style,
            "shape": self.shape.value,
            "opacity": self.opacity,
            "shadow": self.shadow,
            "icon": self.icon,
            "emoji": self.emoji,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NodeStyle:
        """Create NodeStyle from dictionary."""
        data_copy = data.copy()
        if "shape" in data_copy:
            data_copy["shape"] = NodeShape(data_copy["shape"])
        return cls(**data_copy)


@dataclass
class Attachment:
    """File or link attachment to a node."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: Literal["file", "link", "image"] = "link"
    url: str = ""
    size: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "url": self.url,
            "size": self.size,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Attachment:
        """Create Attachment from dictionary."""
        data_copy = data.copy()
        if "created_at" in data_copy:
            data_copy["created_at"] = datetime.fromisoformat(data_copy["created_at"])
        return cls(**data_copy)


@dataclass
class Task:
    """Task associated with a node."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    completed: bool = False
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    assignee: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "completed": self.completed,
            "priority": self.priority.value,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "assignee": self.assignee,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Task:
        """Create Task from dictionary."""
        data_copy = data.copy()
        if "priority" in data_copy:
            data_copy["priority"] = Priority(data_copy["priority"])
        if "due_date" in data_copy and data_copy["due_date"]:
            data_copy["due_date"] = datetime.fromisoformat(data_copy["due_date"])
        return cls(**data_copy)


@dataclass
class Comment:
    """Comment on a node for collaboration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: str = ""
    text: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    edited_at: Optional[datetime] = None
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "author": self.author,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "resolved": self.resolved,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Comment:
        """Create Comment from dictionary."""
        data_copy = data.copy()
        if "created_at" in data_copy:
            data_copy["created_at"] = datetime.fromisoformat(data_copy["created_at"])
        if "edited_at" in data_copy and data_copy["edited_at"]:
            data_copy["edited_at"] = datetime.fromisoformat(data_copy["edited_at"])
        return cls(**data_copy)


class MindMapNode:
    """
    Core node class for mind mapping with rich content support.

    Features:
    - Hierarchical structure (parent/children)
    - Rich text content with notes
    - Visual styling and formatting
    - Attachments and links
    - Tasks and priorities
    - Tags and metadata
    - Collaboration comments
    - Positioning and layout
    """

    def __init__(
        self,
        text: str,
        node_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        position: Optional[Position] = None,
        style: Optional[NodeStyle] = None,
    ):
        self.id: str = node_id or str(uuid.uuid4())
        self.text: str = text
        self.parent_id: Optional[str] = parent_id
        self.children_ids: List[str] = []

        # Position and layout
        self.position: Position = position or Position(0.0, 0.0)
        self.is_floating: bool = False  # True if manually positioned

        # Visual styling
        self.style: NodeStyle = style or NodeStyle()

        # Rich content
        self.notes: str = ""
        self.links: List[str] = []
        self.attachments: List[Attachment] = []
        self.image_url: Optional[str] = None

        # Tasks and organization
        self.tasks: List[Task] = []
        self.tags: Set[str] = set()
        self.priority: Optional[Priority] = None

        # Collaboration
        self.comments: List[Comment] = []
        self.assigned_to: List[str] = []

        # Metadata
        self.created_at: datetime = datetime.now()
        self.modified_at: datetime = datetime.now()
        self.collapsed: bool = False
        self.hidden: bool = False

        # Custom data
        self.metadata: Dict[str, Any] = {}

    def add_child(self, child_id: str) -> None:
        """Add a child node ID."""
        if child_id not in self.children_ids:
            self.children_ids.append(child_id)
            self.modified_at = datetime.now()

    def remove_child(self, child_id: str) -> None:
        """Remove a child node ID."""
        if child_id in self.children_ids:
            self.children_ids.remove(child_id)
            self.modified_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Add a tag to this node."""
        self.tags.add(tag.lower())
        self.modified_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this node."""
        self.tags.discard(tag.lower())
        self.modified_at = datetime.now()

    def add_attachment(self, attachment: Attachment) -> None:
        """Add an attachment to this node."""
        self.attachments.append(attachment)
        self.modified_at = datetime.now()

    def remove_attachment(self, attachment_id: str) -> bool:
        """Remove an attachment by ID. Returns True if found and removed."""
        initial_len = len(self.attachments)
        self.attachments = [a for a in self.attachments if a.id != attachment_id]
        if len(self.attachments) < initial_len:
            self.modified_at = datetime.now()
            return True
        return False

    def add_task(self, task: Task) -> None:
        """Add a task to this node."""
        self.tasks.append(task)
        self.modified_at = datetime.now()

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID. Returns True if found and removed."""
        initial_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        if len(self.tasks) < initial_len:
            self.modified_at = datetime.now()
            return True
        return False

    def toggle_task(self, task_id: str) -> bool:
        """Toggle task completion status. Returns new status."""
        for task in self.tasks:
            if task.id == task_id:
                task.completed = not task.completed
                self.modified_at = datetime.now()
                return task.completed
        raise ValueError(f"Task {task_id} not found")

    def add_comment(self, comment: Comment) -> None:
        """Add a comment to this node."""
        self.comments.append(comment)
        self.modified_at = datetime.now()

    def remove_comment(self, comment_id: str) -> bool:
        """Remove a comment by ID. Returns True if found and removed."""
        initial_len = len(self.comments)
        self.comments = [c for c in self.comments if c.id != comment_id]
        if len(self.comments) < initial_len:
            self.modified_at = datetime.now()
            return True
        return False

    def update_position(self, position: Position, is_floating: bool = True) -> None:
        """Update node position."""
        self.position = position
        self.is_floating = is_floating
        self.modified_at = datetime.now()

    def update_style(self, **kwargs: Any) -> None:
        """Update style properties."""
        for key, value in kwargs.items():
            if hasattr(self.style, key):
                setattr(self.style, key, value)
        self.modified_at = datetime.now()

    def toggle_collapse(self) -> bool:
        """Toggle collapse state. Returns new state."""
        self.collapsed = not self.collapsed
        self.modified_at = datetime.now()
        return self.collapsed

    def is_leaf(self) -> bool:
        """Check if node is a leaf (has no children)."""
        return len(self.children_ids) == 0

    def is_root(self) -> bool:
        """Check if node is a root (has no parent)."""
        return self.parent_id is None

    def has_pending_tasks(self) -> bool:
        """Check if node has any incomplete tasks."""
        return any(not task.completed for task in self.tasks)

    def get_completion_rate(self) -> float:
        """Get task completion rate (0.0 to 1.0)."""
        if not self.tasks:
            return 1.0
        completed = sum(1 for task in self.tasks if task.completed)
        return completed / len(self.tasks)

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "position": self.position.to_dict(),
            "is_floating": self.is_floating,
            "style": self.style.to_dict(),
            "notes": self.notes,
            "links": self.links,
            "attachments": [a.to_dict() for a in self.attachments],
            "image_url": self.image_url,
            "tasks": [t.to_dict() for t in self.tasks],
            "tags": list(self.tags),
            "priority": self.priority.value if self.priority else None,
            "comments": [c.to_dict() for c in self.comments],
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "collapsed": self.collapsed,
            "hidden": self.hidden,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MindMapNode:
        """Create node from dictionary."""
        # Create basic node
        node = cls(
            text=data["text"],
            node_id=data["id"],
            parent_id=data.get("parent_id"),
            position=Position.from_dict(data["position"]),
            style=NodeStyle.from_dict(data["style"]),
        )

        # Restore all properties
        node.children_ids = data.get("children_ids", [])
        node.is_floating = data.get("is_floating", False)
        node.notes = data.get("notes", "")
        node.links = data.get("links", [])
        node.attachments = [Attachment.from_dict(a) for a in data.get("attachments", [])]
        node.image_url = data.get("image_url")
        node.tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        node.tags = set(data.get("tags", []))
        node.priority = Priority(data["priority"]) if data.get("priority") else None
        node.comments = [Comment.from_dict(c) for c in data.get("comments", [])]
        node.assigned_to = data.get("assigned_to", [])
        node.created_at = datetime.fromisoformat(data["created_at"])
        node.modified_at = datetime.fromisoformat(data["modified_at"])
        node.collapsed = data.get("collapsed", False)
        node.hidden = data.get("hidden", False)
        node.metadata = data.get("metadata", {})

        return node

    def __repr__(self) -> str:
        """String representation."""
        return f"MindMapNode(id={self.id}, text='{self.text[:30]}...', children={len(self.children_ids)})"
