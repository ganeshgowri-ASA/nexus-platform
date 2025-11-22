"""
Collaboration Manager

Handles real-time collaborative editing, user presence, comments, and change tracking.
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json
import uuid


class PermissionLevel(Enum):
    """Document permission levels"""
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"
    ADMIN = "admin"


class ChangeType(Enum):
    """Types of changes for tracking"""
    INSERT = "insert"
    DELETE = "delete"
    FORMAT = "format"
    REPLACE = "replace"


class CommentStatus(Enum):
    """Comment status"""
    OPEN = "open"
    RESOLVED = "resolved"
    DELETED = "deleted"


@dataclass
class User:
    """User information"""
    user_id: str
    username: str
    email: str
    avatar_color: str  # Hex color for cursor/highlight
    is_online: bool = False
    last_seen: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if self.last_seen:
            data['last_seen'] = self.last_seen.isoformat()
        return data


@dataclass
class CursorPosition:
    """User cursor position"""
    user_id: str
    position: int
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class Comment:
    """Document comment"""
    comment_id: str
    document_id: str
    author_id: str
    author_name: str
    content: str
    created_at: datetime
    modified_at: Optional[datetime]
    position: int  # Character position in document
    length: int  # Length of commented text
    status: CommentStatus
    replies: List['CommentReply']
    thread_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.modified_at:
            data['modified_at'] = self.modified_at.isoformat()
        data['status'] = self.status.value
        data['replies'] = [reply.to_dict() for reply in self.replies]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Comment':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('modified_at'):
            data['modified_at'] = datetime.fromisoformat(data['modified_at'])
        data['status'] = CommentStatus(data['status'])
        data['replies'] = [CommentReply.from_dict(r) for r in data.get('replies', [])]
        return cls(**data)


@dataclass
class CommentReply:
    """Reply to a comment"""
    reply_id: str
    author_id: str
    author_name: str
    content: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommentReply':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class TrackedChange:
    """Tracked change for review"""
    change_id: str
    document_id: str
    author_id: str
    author_name: str
    change_type: ChangeType
    position: int
    length: int
    old_content: Optional[str]
    new_content: Optional[str]
    timestamp: datetime
    accepted: Optional[bool] = None  # None=pending, True=accepted, False=rejected

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['change_type'] = self.change_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrackedChange':
        """Create from dictionary"""
        data['change_type'] = ChangeType(data['change_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ShareLink:
    """Shared document link"""
    link_id: str
    document_id: str
    created_by: str
    permission: PermissionLevel
    expires_at: Optional[datetime]
    is_public: bool
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['permission'] = self.permission.value
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data


class CollaborationManager:
    """
    Collaboration Manager for real-time multi-user editing.

    Features:
    - Real-time user presence tracking
    - Cursor position synchronization
    - Operational Transformation (OT) / CRDT for conflict resolution
    - Comments and suggestions
    - Change tracking (track changes mode)
    - Share links with permissions
    - Access control
    """

    def __init__(self, document_id: str):
        """
        Initialize collaboration manager.

        Args:
            document_id: Document ID to manage collaboration for
        """
        self.document_id = document_id

        # Active users and their cursors
        self.active_users: Dict[str, User] = {}
        self.cursor_positions: Dict[str, CursorPosition] = {}

        # Document permissions
        self.permissions: Dict[str, PermissionLevel] = {}

        # Comments and discussions
        self.comments: Dict[str, Comment] = {}

        # Tracked changes
        self.tracked_changes: Dict[str, TrackedChange] = {}
        self.track_changes_enabled = False

        # Share links
        self.share_links: Dict[str, ShareLink] = {}

        # Operation history for CRDT/OT
        self.operation_history: List[Dict[str, Any]] = []

    def add_user(self, user: User, permission: PermissionLevel) -> None:
        """
        Add a user to the collaboration session.

        Args:
            user: User to add
            permission: Permission level for the user
        """
        self.active_users[user.user_id] = user
        self.permissions[user.user_id] = permission
        user.is_online = True
        user.last_seen = datetime.now()

    def remove_user(self, user_id: str) -> None:
        """
        Remove a user from the collaboration session.

        Args:
            user_id: User ID to remove
        """
        if user_id in self.active_users:
            self.active_users[user_id].is_online = False
            self.active_users[user_id].last_seen = datetime.now()

        if user_id in self.cursor_positions:
            del self.cursor_positions[user_id]

    def update_cursor_position(
        self,
        user_id: str,
        position: int,
        selection_start: Optional[int] = None,
        selection_end: Optional[int] = None
    ) -> None:
        """
        Update a user's cursor position.

        Args:
            user_id: User ID
            position: Cursor position
            selection_start: Optional selection start position
            selection_end: Optional selection end position
        """
        self.cursor_positions[user_id] = CursorPosition(
            user_id=user_id,
            position=position,
            selection_start=selection_start,
            selection_end=selection_end
        )

    def get_active_users(self) -> List[User]:
        """
        Get list of active users.

        Returns:
            List of active users
        """
        return [user for user in self.active_users.values() if user.is_online]

    def get_user_cursors(self) -> Dict[str, CursorPosition]:
        """
        Get all user cursor positions.

        Returns:
            Dictionary of user cursors
        """
        return self.cursor_positions.copy()

    def check_permission(self, user_id: str, required: PermissionLevel) -> bool:
        """
        Check if user has required permission level.

        Args:
            user_id: User ID to check
            required: Required permission level

        Returns:
            True if user has permission
        """
        user_permission = self.permissions.get(user_id)

        if not user_permission:
            return False

        # Permission hierarchy: VIEW < COMMENT < EDIT < ADMIN
        permission_levels = [
            PermissionLevel.VIEW,
            PermissionLevel.COMMENT,
            PermissionLevel.EDIT,
            PermissionLevel.ADMIN
        ]

        user_level = permission_levels.index(user_permission)
        required_level = permission_levels.index(required)

        return user_level >= required_level

    def add_comment(
        self,
        author_id: str,
        author_name: str,
        content: str,
        position: int,
        length: int,
        thread_id: Optional[str] = None
    ) -> Comment:
        """
        Add a comment to the document.

        Args:
            author_id: Author user ID
            author_name: Author display name
            content: Comment content
            position: Character position in document
            length: Length of commented text
            thread_id: Optional thread ID for replies

        Returns:
            Created comment
        """
        comment = Comment(
            comment_id=str(uuid.uuid4()),
            document_id=self.document_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
            created_at=datetime.now(),
            modified_at=None,
            position=position,
            length=length,
            status=CommentStatus.OPEN,
            replies=[],
            thread_id=thread_id
        )

        self.comments[comment.comment_id] = comment
        return comment

    def add_comment_reply(
        self,
        comment_id: str,
        author_id: str,
        author_name: str,
        content: str
    ) -> Optional[CommentReply]:
        """
        Add a reply to a comment.

        Args:
            comment_id: Comment ID to reply to
            author_id: Author user ID
            author_name: Author display name
            content: Reply content

        Returns:
            Created reply or None if comment not found
        """
        comment = self.comments.get(comment_id)

        if not comment:
            return None

        reply = CommentReply(
            reply_id=str(uuid.uuid4()),
            author_id=author_id,
            author_name=author_name,
            content=content,
            created_at=datetime.now()
        )

        comment.replies.append(reply)
        return reply

    def resolve_comment(self, comment_id: str) -> bool:
        """
        Mark a comment as resolved.

        Args:
            comment_id: Comment ID to resolve

        Returns:
            True if successful
        """
        comment = self.comments.get(comment_id)

        if not comment:
            return False

        comment.status = CommentStatus.RESOLVED
        return True

    def delete_comment(self, comment_id: str) -> bool:
        """
        Delete a comment.

        Args:
            comment_id: Comment ID to delete

        Returns:
            True if successful
        """
        comment = self.comments.get(comment_id)

        if not comment:
            return False

        comment.status = CommentStatus.DELETED
        return True

    def get_comments(
        self,
        include_resolved: bool = False,
        include_deleted: bool = False
    ) -> List[Comment]:
        """
        Get document comments.

        Args:
            include_resolved: Include resolved comments
            include_deleted: Include deleted comments

        Returns:
            List of comments
        """
        comments = []

        for comment in self.comments.values():
            if comment.status == CommentStatus.OPEN:
                comments.append(comment)
            elif comment.status == CommentStatus.RESOLVED and include_resolved:
                comments.append(comment)
            elif comment.status == CommentStatus.DELETED and include_deleted:
                comments.append(comment)

        # Sort by position
        comments.sort(key=lambda c: c.position)
        return comments

    def enable_track_changes(self, enabled: bool = True) -> None:
        """
        Enable or disable track changes mode.

        Args:
            enabled: Whether to enable tracking
        """
        self.track_changes_enabled = enabled

    def track_change(
        self,
        author_id: str,
        author_name: str,
        change_type: ChangeType,
        position: int,
        length: int,
        old_content: Optional[str] = None,
        new_content: Optional[str] = None
    ) -> TrackedChange:
        """
        Track a change to the document.

        Args:
            author_id: Author user ID
            author_name: Author display name
            change_type: Type of change
            position: Character position
            length: Length of change
            old_content: Old content (for replacements/deletions)
            new_content: New content (for insertions/replacements)

        Returns:
            Tracked change object
        """
        change = TrackedChange(
            change_id=str(uuid.uuid4()),
            document_id=self.document_id,
            author_id=author_id,
            author_name=author_name,
            change_type=change_type,
            position=position,
            length=length,
            old_content=old_content,
            new_content=new_content,
            timestamp=datetime.now()
        )

        self.tracked_changes[change.change_id] = change
        return change

    def accept_change(self, change_id: str) -> bool:
        """
        Accept a tracked change.

        Args:
            change_id: Change ID to accept

        Returns:
            True if successful
        """
        change = self.tracked_changes.get(change_id)

        if not change:
            return False

        change.accepted = True
        return True

    def reject_change(self, change_id: str) -> bool:
        """
        Reject a tracked change.

        Args:
            change_id: Change ID to reject

        Returns:
            True if successful
        """
        change = self.tracked_changes.get(change_id)

        if not change:
            return False

        change.accepted = False
        return True

    def get_tracked_changes(
        self,
        pending_only: bool = True
    ) -> List[TrackedChange]:
        """
        Get tracked changes.

        Args:
            pending_only: Only return pending changes

        Returns:
            List of tracked changes
        """
        changes = []

        for change in self.tracked_changes.values():
            if pending_only and change.accepted is not None:
                continue
            changes.append(change)

        # Sort by timestamp
        changes.sort(key=lambda c: c.timestamp)
        return changes

    def create_share_link(
        self,
        created_by: str,
        permission: PermissionLevel,
        is_public: bool = False,
        expires_at: Optional[datetime] = None
    ) -> ShareLink:
        """
        Create a share link for the document.

        Args:
            created_by: User ID creating the link
            permission: Permission level for link users
            is_public: Whether link is publicly accessible
            expires_at: Optional expiration datetime

        Returns:
            Created share link
        """
        link = ShareLink(
            link_id=str(uuid.uuid4()),
            document_id=self.document_id,
            created_by=created_by,
            permission=permission,
            expires_at=expires_at,
            is_public=is_public
        )

        self.share_links[link.link_id] = link
        return link

    def get_share_link(self, link_id: str) -> Optional[ShareLink]:
        """
        Get a share link.

        Args:
            link_id: Link ID

        Returns:
            Share link or None if not found/expired
        """
        link = self.share_links.get(link_id)

        if not link:
            return None

        # Check expiration
        if link.expires_at and link.expires_at < datetime.now():
            return None

        link.access_count += 1
        return link

    def revoke_share_link(self, link_id: str) -> bool:
        """
        Revoke a share link.

        Args:
            link_id: Link ID to revoke

        Returns:
            True if successful
        """
        if link_id in self.share_links:
            del self.share_links[link_id]
            return True

        return False

    def apply_operation(
        self,
        user_id: str,
        operation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply an operation using Operational Transformation.

        This is a simplified OT implementation. In production, use a proper
        CRDT library like Yjs or Automerge.

        Args:
            user_id: User applying the operation
            operation: Operation to apply

        Returns:
            Transformed operation
        """
        # Check permissions
        if not self.check_permission(user_id, PermissionLevel.EDIT):
            raise PermissionError("User does not have edit permission")

        # Store operation in history
        operation['user_id'] = user_id
        operation['timestamp'] = datetime.now().isoformat()
        self.operation_history.append(operation)

        # In production, implement proper OT/CRDT transformation here
        # For now, just return the operation as-is
        return operation

    def sync_state(self) -> Dict[str, Any]:
        """
        Get the current collaboration state for syncing.

        Returns:
            Dictionary containing collaboration state
        """
        return {
            'document_id': self.document_id,
            'active_users': [user.to_dict() for user in self.get_active_users()],
            'cursor_positions': {
                uid: cursor.to_dict()
                for uid, cursor in self.cursor_positions.items()
            },
            'comments': [comment.to_dict() for comment in self.get_comments()],
            'tracked_changes': [
                change.to_dict()
                for change in self.get_tracked_changes(pending_only=False)
            ],
            'track_changes_enabled': self.track_changes_enabled,
            'operation_history_length': len(self.operation_history)
        }
