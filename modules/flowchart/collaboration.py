"""
Real-time collaboration features for multi-user diagram editing.
Supports concurrent editing, comments, version history, and conflict resolution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import json
import uuid


class ChangeType(Enum):
    """Types of changes that can occur."""
    ADD_SHAPE = "add_shape"
    REMOVE_SHAPE = "remove_shape"
    UPDATE_SHAPE = "update_shape"
    MOVE_SHAPE = "move_shape"
    ADD_CONNECTOR = "add_connector"
    REMOVE_CONNECTOR = "remove_connector"
    UPDATE_CONNECTOR = "update_connector"
    ADD_LAYER = "add_layer"
    REMOVE_LAYER = "remove_layer"
    UPDATE_SETTINGS = "update_settings"


@dataclass
class User:
    """Represents a collaborating user."""
    id: str
    name: str
    email: str
    color: str = "#4A90E2"  # User cursor/selection color
    avatar_url: Optional[str] = None
    is_online: bool = False
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "color": self.color,
            "avatar_url": self.avatar_url,
            "is_online": self.is_online,
            "last_seen": self.last_seen
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        return cls(**data)


@dataclass
class Change:
    """Represents a single change to the diagram."""
    id: str
    change_type: ChangeType
    user_id: str
    timestamp: str
    data: Dict[str, Any]
    parent_change_id: Optional[str] = None  # For change history tree

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "change_type": self.change_type.value,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "data": self.data,
            "parent_change_id": self.parent_change_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Change":
        data["change_type"] = ChangeType(data["change_type"])
        return cls(**data)


@dataclass
class Comment:
    """Comment on a diagram element."""
    id: str
    user_id: str
    text: str
    timestamp: str
    target_id: Optional[str] = None  # Shape or connector ID
    position: Optional[Dict[str, float]] = None  # Freeform comment position
    resolved: bool = False
    replies: List["Comment"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "timestamp": self.timestamp,
            "target_id": self.target_id,
            "position": self.position,
            "resolved": self.resolved,
            "replies": [r.to_dict() for r in self.replies]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Comment":
        replies_data = data.pop("replies", [])
        comment = cls(**data)
        comment.replies = [Comment.from_dict(r) for r in replies_data]
        return comment


@dataclass
class Version:
    """Represents a saved version of the diagram."""
    id: str
    name: str
    description: str
    user_id: str
    timestamp: str
    diagram_data: Dict[str, Any]
    parent_version_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "diagram_data": self.diagram_data,
            "parent_version_id": self.parent_version_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Version":
        return cls(**data)


@dataclass
class UserPresence:
    """Tracks a user's current activity in the diagram."""
    user_id: str
    selected_items: Set[str] = field(default_factory=set)
    cursor_position: Optional[Dict[str, float]] = None
    current_tool: Optional[str] = None
    viewport: Optional[Dict[str, float]] = None  # What area they're viewing
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "selected_items": list(self.selected_items),
            "cursor_position": self.cursor_position,
            "current_tool": self.current_tool,
            "viewport": self.viewport,
            "last_activity": self.last_activity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPresence":
        data["selected_items"] = set(data.get("selected_items", []))
        return cls(**data)


class CollaborationEngine:
    """Manages real-time collaboration features."""

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.changes: List[Change] = []
        self.comments: Dict[str, Comment] = {}
        self.versions: Dict[str, Version] = {}
        self.presence: Dict[str, UserPresence] = {}
        self.locks: Dict[str, str] = {}  # item_id -> user_id mapping

    # User Management

    def add_user(self, user: User):
        """Add a collaborating user."""
        self.users[user.id] = user

    def remove_user(self, user_id: str):
        """Remove a user."""
        if user_id in self.users:
            del self.users[user_id]

        # Remove user's presence
        if user_id in self.presence:
            del self.presence[user_id]

        # Release user's locks
        self.release_all_locks(user_id)

    def update_user_status(self, user_id: str, is_online: bool):
        """Update user online status."""
        if user_id in self.users:
            self.users[user_id].is_online = is_online
            self.users[user_id].last_seen = datetime.now().isoformat()

    def get_online_users(self) -> List[User]:
        """Get list of currently online users."""
        return [u for u in self.users.values() if u.is_online]

    # Change Tracking

    def record_change(
        self,
        change_type: ChangeType,
        user_id: str,
        data: Dict[str, Any],
        parent_change_id: Optional[str] = None
    ) -> Change:
        """Record a change to the diagram."""
        change = Change(
            id=str(uuid.uuid4()),
            change_type=change_type,
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            data=data,
            parent_change_id=parent_change_id
        )

        self.changes.append(change)
        return change

    def get_changes_since(self, timestamp: str) -> List[Change]:
        """Get all changes since a given timestamp."""
        return [c for c in self.changes if c.timestamp > timestamp]

    def get_changes_by_user(self, user_id: str) -> List[Change]:
        """Get all changes by a specific user."""
        return [c for c in self.changes if c.user_id == user_id]

    def get_recent_changes(self, limit: int = 50) -> List[Change]:
        """Get most recent changes."""
        return sorted(self.changes, key=lambda c: c.timestamp, reverse=True)[:limit]

    # Comments

    def add_comment(
        self,
        user_id: str,
        text: str,
        target_id: Optional[str] = None,
        position: Optional[Dict[str, float]] = None,
        parent_comment_id: Optional[str] = None
    ) -> Comment:
        """Add a comment to the diagram."""
        comment = Comment(
            id=str(uuid.uuid4()),
            user_id=user_id,
            text=text,
            timestamp=datetime.now().isoformat(),
            target_id=target_id,
            position=position
        )

        if parent_comment_id and parent_comment_id in self.comments:
            # This is a reply
            self.comments[parent_comment_id].replies.append(comment)
        else:
            # This is a top-level comment
            self.comments[comment.id] = comment

        return comment

    def resolve_comment(self, comment_id: str) -> bool:
        """Mark a comment as resolved."""
        if comment_id in self.comments:
            self.comments[comment_id].resolved = True
            return True
        return False

    def get_comments_for_item(self, item_id: str) -> List[Comment]:
        """Get all comments for a specific diagram item."""
        return [c for c in self.comments.values() if c.target_id == item_id]

    def get_all_comments(self, include_resolved: bool = False) -> List[Comment]:
        """Get all comments."""
        comments = list(self.comments.values())
        if not include_resolved:
            comments = [c for c in comments if not c.resolved]
        return comments

    # Version Control

    def create_version(
        self,
        name: str,
        description: str,
        user_id: str,
        diagram_data: Dict[str, Any],
        parent_version_id: Optional[str] = None
    ) -> Version:
        """Create a new version of the diagram."""
        version = Version(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            diagram_data=diagram_data,
            parent_version_id=parent_version_id
        )

        self.versions[version.id] = version
        return version

    def get_version(self, version_id: str) -> Optional[Version]:
        """Get a specific version."""
        return self.versions.get(version_id)

    def get_all_versions(self) -> List[Version]:
        """Get all versions, sorted by timestamp."""
        return sorted(self.versions.values(), key=lambda v: v.timestamp, reverse=True)

    def get_version_history(self, version_id: str) -> List[Version]:
        """Get the full history chain for a version."""
        history = []
        current_version = self.versions.get(version_id)

        while current_version:
            history.append(current_version)
            if current_version.parent_version_id:
                current_version = self.versions.get(current_version.parent_version_id)
            else:
                break

        return history

    def compare_versions(
        self,
        version_id_1: str,
        version_id_2: str
    ) -> Dict[str, Any]:
        """Compare two versions and return differences."""
        v1 = self.versions.get(version_id_1)
        v2 = self.versions.get(version_id_2)

        if not v1 or not v2:
            return {}

        # Simple diff - in production, use proper diff algorithm
        return {
            "version_1": {"id": v1.id, "name": v1.name, "timestamp": v1.timestamp},
            "version_2": {"id": v2.id, "name": v2.name, "timestamp": v2.timestamp},
            "shapes_added": [],
            "shapes_removed": [],
            "shapes_modified": [],
            "connectors_added": [],
            "connectors_removed": [],
            "connectors_modified": []
        }

    # User Presence

    def update_presence(
        self,
        user_id: str,
        selected_items: Optional[Set[str]] = None,
        cursor_position: Optional[Dict[str, float]] = None,
        current_tool: Optional[str] = None,
        viewport: Optional[Dict[str, float]] = None
    ):
        """Update user's presence information."""
        if user_id not in self.presence:
            self.presence[user_id] = UserPresence(user_id=user_id)

        presence = self.presence[user_id]

        if selected_items is not None:
            presence.selected_items = selected_items
        if cursor_position is not None:
            presence.cursor_position = cursor_position
        if current_tool is not None:
            presence.current_tool = current_tool
        if viewport is not None:
            presence.viewport = viewport

        presence.last_activity = datetime.now().isoformat()

    def get_presence(self, user_id: str) -> Optional[UserPresence]:
        """Get user's presence information."""
        return self.presence.get(user_id)

    def get_all_presence(self) -> Dict[str, UserPresence]:
        """Get presence for all users."""
        return self.presence.copy()

    # Locking (for preventing concurrent edits)

    def acquire_lock(self, item_id: str, user_id: str) -> bool:
        """Attempt to acquire a lock on a diagram item."""
        if item_id in self.locks:
            # Already locked
            return self.locks[item_id] == user_id
        else:
            # Acquire lock
            self.locks[item_id] = user_id
            return True

    def release_lock(self, item_id: str, user_id: str) -> bool:
        """Release a lock on a diagram item."""
        if item_id in self.locks and self.locks[item_id] == user_id:
            del self.locks[item_id]
            return True
        return False

    def release_all_locks(self, user_id: str):
        """Release all locks held by a user."""
        items_to_release = [
            item_id for item_id, locked_user_id in self.locks.items()
            if locked_user_id == user_id
        ]

        for item_id in items_to_release:
            del self.locks[item_id]

    def is_locked(self, item_id: str) -> bool:
        """Check if an item is locked."""
        return item_id in self.locks

    def get_lock_owner(self, item_id: str) -> Optional[str]:
        """Get the user ID who owns the lock on an item."""
        return self.locks.get(item_id)

    # Conflict Resolution

    def detect_conflicts(
        self,
        change1: Change,
        change2: Change
    ) -> bool:
        """Detect if two changes conflict."""
        # Simplified conflict detection
        # Conflicts occur when:
        # 1. Both changes affect the same item
        # 2. Changes are from different users
        # 3. Changes overlap in time

        if change1.user_id == change2.user_id:
            return False

        # Check if changes affect the same item
        item_id_1 = change1.data.get("shape_id") or change1.data.get("connector_id")
        item_id_2 = change2.data.get("shape_id") or change2.data.get("connector_id")

        return item_id_1 == item_id_2 and item_id_1 is not None

    def resolve_conflict(
        self,
        change1: Change,
        change2: Change,
        resolution: str = "last_write_wins"
    ) -> Change:
        """
        Resolve a conflict between two changes.

        Args:
            change1: First change
            change2: Second change
            resolution: Resolution strategy ('last_write_wins', 'first_write_wins', 'merge')

        Returns:
            The winning change
        """
        if resolution == "last_write_wins":
            return change2 if change2.timestamp > change1.timestamp else change1
        elif resolution == "first_write_wins":
            return change1 if change1.timestamp < change2.timestamp else change2
        elif resolution == "merge":
            # Merge strategy - combine both changes
            # This is simplified; in production, implement proper merge logic
            merged_data = {**change1.data, **change2.data}
            return Change(
                id=str(uuid.uuid4()),
                change_type=change1.change_type,
                user_id="system",
                timestamp=datetime.now().isoformat(),
                data=merged_data
            )
        else:
            return change1

    # Serialization

    def to_dict(self) -> Dict[str, Any]:
        """Serialize collaboration state to dictionary."""
        return {
            "users": {uid: user.to_dict() for uid, user in self.users.items()},
            "changes": [change.to_dict() for change in self.changes],
            "comments": {cid: comment.to_dict() for cid, comment in self.comments.items()},
            "versions": {vid: version.to_dict() for vid, version in self.versions.items()},
            "presence": {uid: presence.to_dict() for uid, presence in self.presence.items()},
            "locks": self.locks
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollaborationEngine":
        """Deserialize from dictionary."""
        engine = cls()

        engine.users = {
            uid: User.from_dict(udata)
            for uid, udata in data.get("users", {}).items()
        }

        engine.changes = [
            Change.from_dict(cdata)
            for cdata in data.get("changes", [])
        ]

        engine.comments = {
            cid: Comment.from_dict(cdata)
            for cid, cdata in data.get("comments", {}).items()
        }

        engine.versions = {
            vid: Version.from_dict(vdata)
            for vid, vdata in data.get("versions", {}).items()
        }

        engine.presence = {
            uid: UserPresence.from_dict(pdata)
            for uid, pdata in data.get("presence", {}).items()
        }

        engine.locks = data.get("locks", {})

        return engine

    @classmethod
    def from_json(cls, json_str: str) -> "CollaborationEngine":
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
