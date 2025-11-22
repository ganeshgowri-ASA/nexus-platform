"""
Mind Map Collaboration System

This module provides real-time collaboration features including
multi-user editing, change tracking, and conflict resolution.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json


class OperationType(Enum):
    """Types of collaborative operations."""
    NODE_CREATE = "node_create"
    NODE_UPDATE = "node_update"
    NODE_DELETE = "node_delete"
    NODE_MOVE = "node_move"
    BRANCH_CREATE = "branch_create"
    BRANCH_DELETE = "branch_delete"
    COMMENT_ADD = "comment_add"
    COMMENT_REMOVE = "comment_remove"
    TASK_ADD = "task_add"
    TASK_UPDATE = "task_update"
    TASK_DELETE = "task_delete"
    STYLE_UPDATE = "style_update"


class PresenceStatus(Enum):
    """User presence status."""
    ACTIVE = "active"
    IDLE = "idle"
    AWAY = "away"
    OFFLINE = "offline"


@dataclass
class User:
    """Represents a collaborating user."""
    id: str
    name: str
    email: str
    color: str  # Cursor/selection color
    avatar_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "color": self.color,
            "avatar_url": self.avatar_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> User:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class UserPresence:
    """Tracks user presence and activity."""
    user: User
    status: PresenceStatus = PresenceStatus.ACTIVE
    last_seen: datetime = field(default_factory=datetime.now)
    current_node_id: Optional[str] = None  # Node being viewed/edited
    cursor_position: Optional[Dict[str, float]] = None

    def update_activity(self) -> None:
        """Update last seen timestamp."""
        self.last_seen = datetime.now()
        self.status = PresenceStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user": self.user.to_dict(),
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat(),
            "current_node_id": self.current_node_id,
            "cursor_position": self.cursor_position,
        }


@dataclass
class Operation:
    """Represents a collaborative operation/change."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: OperationType = OperationType.NODE_UPDATE
    user_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "applied": self.applied,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Operation:
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy["type"] = OperationType(data_copy["type"])
        data_copy["timestamp"] = datetime.fromisoformat(data_copy["timestamp"])
        return cls(**data_copy)


@dataclass
class ChangeSet:
    """A set of related changes (like a transaction)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    operations: List[Operation] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""

    def add_operation(self, operation: Operation) -> None:
        """Add an operation to this change set."""
        self.operations.append(operation)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "operations": [op.to_dict() for op in self.operations],
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ChangeSet:
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy["operations"] = [
            Operation.from_dict(op) for op in data_copy["operations"]
        ]
        data_copy["timestamp"] = datetime.fromisoformat(data_copy["timestamp"])
        return cls(**data_copy)


class CollaborationSession:
    """
    Manages a collaborative editing session.

    Features:
    - User presence tracking
    - Operation history
    - Real-time change broadcasting
    - Conflict detection and resolution
    - Undo/redo support
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.users: Dict[str, UserPresence] = {}
        self.operation_history: List[Operation] = []
        self.change_sets: List[ChangeSet] = []
        self.callbacks: Dict[str, List[Callable]] = {}
        self.locks: Dict[str, str] = {}  # node_id -> user_id

    def add_user(self, user: User) -> None:
        """Add a user to the session."""
        presence = UserPresence(user=user)
        self.users[user.id] = presence
        self._trigger_callback("user_joined", user)

    def remove_user(self, user_id: str) -> None:
        """Remove a user from the session."""
        if user_id in self.users:
            user = self.users[user_id].user
            del self.users[user_id]

            # Release any locks held by this user
            self._release_user_locks(user_id)

            self._trigger_callback("user_left", user)

    def update_user_presence(
        self,
        user_id: str,
        status: Optional[PresenceStatus] = None,
        current_node_id: Optional[str] = None,
        cursor_position: Optional[Dict[str, float]] = None,
    ) -> None:
        """Update user presence information."""
        if user_id not in self.users:
            return

        presence = self.users[user_id]
        presence.update_activity()

        if status is not None:
            presence.status = status
        if current_node_id is not None:
            presence.current_node_id = current_node_id
        if cursor_position is not None:
            presence.cursor_position = cursor_position

        self._trigger_callback("presence_updated", presence)

    def add_operation(self, operation: Operation) -> bool:
        """
        Add an operation to the history.

        Returns:
            True if operation was accepted, False if rejected (conflict)
        """
        # Check for conflicts
        if self._has_conflict(operation):
            self._trigger_callback("conflict_detected", operation)
            return False

        # Add to history
        self.operation_history.append(operation)
        operation.applied = True

        # Broadcast to other users
        self._trigger_callback("operation_applied", operation)

        return True

    def create_change_set(
        self, user_id: str, description: str = ""
    ) -> ChangeSet:
        """Create a new change set for grouping operations."""
        change_set = ChangeSet(user_id=user_id, description=description)
        self.change_sets.append(change_set)
        return change_set

    def apply_change_set(self, change_set: ChangeSet) -> bool:
        """Apply all operations in a change set."""
        success = True
        for operation in change_set.operations:
            if not self.add_operation(operation):
                success = False
                break

        if success:
            self._trigger_callback("change_set_applied", change_set)

        return success

    def lock_node(self, node_id: str, user_id: str) -> bool:
        """
        Lock a node for editing by a user.

        Returns:
            True if lock acquired, False if already locked
        """
        if node_id in self.locks and self.locks[node_id] != user_id:
            return False

        self.locks[node_id] = user_id
        self._trigger_callback("node_locked", {"node_id": node_id, "user_id": user_id})
        return True

    def unlock_node(self, node_id: str, user_id: str) -> bool:
        """
        Unlock a node.

        Returns:
            True if unlocked, False if not locked by this user
        """
        if node_id not in self.locks or self.locks[node_id] != user_id:
            return False

        del self.locks[node_id]
        self._trigger_callback("node_unlocked", {"node_id": node_id, "user_id": user_id})
        return True

    def is_node_locked(self, node_id: str) -> bool:
        """Check if a node is locked."""
        return node_id in self.locks

    def get_node_lock_owner(self, node_id: str) -> Optional[str]:
        """Get the user ID that owns the lock on a node."""
        return self.locks.get(node_id)

    def _release_user_locks(self, user_id: str) -> None:
        """Release all locks held by a user."""
        to_unlock = [
            node_id for node_id, owner in self.locks.items() if owner == user_id
        ]
        for node_id in to_unlock:
            del self.locks[node_id]
            self._trigger_callback("node_unlocked", {"node_id": node_id, "user_id": user_id})

    def _has_conflict(self, operation: Operation) -> bool:
        """
        Check if an operation conflicts with recent changes.

        Simple conflict detection: check if same node was modified
        in last few seconds by different user.
        """
        if operation.type in [
            OperationType.NODE_UPDATE,
            OperationType.NODE_DELETE,
            OperationType.STYLE_UPDATE,
        ]:
            node_id = operation.data.get("node_id")
            if not node_id:
                return False

            # Check recent operations on same node
            cutoff_time = datetime.now().timestamp() - 5  # 5 second window
            for recent_op in reversed(self.operation_history[-10:]):
                if (
                    recent_op.data.get("node_id") == node_id
                    and recent_op.user_id != operation.user_id
                    and recent_op.timestamp.timestamp() > cutoff_time
                ):
                    return True

        return False

    def get_user_operations(self, user_id: str) -> List[Operation]:
        """Get all operations by a specific user."""
        return [op for op in self.operation_history if op.user_id == user_id]

    def get_recent_operations(self, limit: int = 50) -> List[Operation]:
        """Get recent operations."""
        return self.operation_history[-limit:]

    def undo_last_operation(self, user_id: str) -> Optional[Operation]:
        """
        Undo the last operation by a user.

        Returns:
            The undone operation, or None if nothing to undo
        """
        user_ops = [op for op in self.operation_history if op.user_id == user_id]
        if not user_ops:
            return None

        last_op = user_ops[-1]

        # Create reverse operation
        reverse_op = self._create_reverse_operation(last_op)
        if reverse_op:
            self.add_operation(reverse_op)
            return last_op

        return None

    def _create_reverse_operation(self, operation: Operation) -> Optional[Operation]:
        """Create a reverse operation to undo a change."""
        reverse_types = {
            OperationType.NODE_CREATE: OperationType.NODE_DELETE,
            OperationType.NODE_DELETE: OperationType.NODE_CREATE,
        }

        reverse_type = reverse_types.get(operation.type)
        if not reverse_type:
            return None

        return Operation(
            type=reverse_type,
            user_id=operation.user_id,
            data=operation.data,
        )

    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for an event."""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Unregister a callback."""
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)

    def _trigger_callback(self, event: str, data: Any) -> None:
        """Trigger all callbacks for an event."""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in callback: {e}")

    def get_active_users(self) -> List[User]:
        """Get list of active users."""
        return [
            presence.user
            for presence in self.users.values()
            if presence.status == PresenceStatus.ACTIVE
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            "session_id": self.session_id,
            "total_users": len(self.users),
            "active_users": len(self.get_active_users()),
            "total_operations": len(self.operation_history),
            "total_change_sets": len(self.change_sets),
            "locked_nodes": len(self.locks),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "users": {
                user_id: presence.to_dict()
                for user_id, presence in self.users.items()
            },
            "operation_history": [op.to_dict() for op in self.operation_history],
            "change_sets": [cs.to_dict() for cs in self.change_sets],
            "locks": self.locks,
        }


class ConflictResolver:
    """
    Handles conflict resolution for collaborative editing.

    Strategies:
    - Last Write Wins (LWW)
    - Operational Transformation (OT)
    - Manual resolution
    """

    def __init__(self, strategy: str = "lww"):
        self.strategy = strategy

    def resolve(
        self, operation1: Operation, operation2: Operation
    ) -> Operation:
        """
        Resolve conflict between two operations.

        Returns:
            The operation to apply
        """
        if self.strategy == "lww":
            return self._last_write_wins(operation1, operation2)
        elif self.strategy == "manual":
            return self._manual_resolution(operation1, operation2)
        else:
            return operation1

    def _last_write_wins(
        self, operation1: Operation, operation2: Operation
    ) -> Operation:
        """Last write wins strategy."""
        if operation2.timestamp > operation1.timestamp:
            return operation2
        return operation1

    def _manual_resolution(
        self, operation1: Operation, operation2: Operation
    ) -> Operation:
        """
        Manual resolution - returns both for user to decide.
        In practice, this would present options to the user.
        """
        # For now, default to last write wins
        return self._last_write_wins(operation1, operation2)


class ChangeTracker:
    """
    Tracks changes over time for version history and auditing.
    """

    def __init__(self):
        self.snapshots: List[Dict[str, Any]] = []
        self.version: int = 0

    def create_snapshot(self, data: Dict[str, Any], description: str = "") -> None:
        """Create a snapshot of the current state."""
        self.version += 1
        self.snapshots.append(
            {
                "version": self.version,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "data": data,
            }
        )

    def get_snapshot(self, version: int) -> Optional[Dict[str, Any]]:
        """Get a specific version snapshot."""
        for snapshot in self.snapshots:
            if snapshot["version"] == version:
                return snapshot
        return None

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent snapshot."""
        if self.snapshots:
            return self.snapshots[-1]
        return None

    def get_history(self) -> List[Dict[str, Any]]:
        """Get full version history."""
        return [
            {
                "version": s["version"],
                "timestamp": s["timestamp"],
                "description": s["description"],
            }
            for s in self.snapshots
        ]
