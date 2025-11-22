"""
Collaboration Manager - Multi-User Editing

Handles real-time collaboration, comments, version history,
and change tracking for presentations.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class PermissionLevel(Enum):
    """User permission levels."""
    VIEWER = "viewer"
    COMMENTER = "commenter"
    EDITOR = "editor"
    OWNER = "owner"


class CommentStatus(Enum):
    """Comment status."""
    OPEN = "open"
    RESOLVED = "resolved"
    DELETED = "deleted"


class ChangeType(Enum):
    """Types of changes."""
    SLIDE_ADDED = "slide_added"
    SLIDE_DELETED = "slide_deleted"
    SLIDE_MODIFIED = "slide_modified"
    SLIDE_REORDERED = "slide_reordered"
    ELEMENT_ADDED = "element_added"
    ELEMENT_DELETED = "element_deleted"
    ELEMENT_MODIFIED = "element_modified"
    THEME_CHANGED = "theme_changed"
    ANIMATION_ADDED = "animation_added"
    ANIMATION_REMOVED = "animation_removed"


@dataclass
class User:
    """Represents a user."""
    id: str
    name: str
    email: str
    avatar: Optional[str] = None
    color: str = "#3498DB"  # User color for cursor/highlights

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "avatar": self.avatar,
            "color": self.color,
        }


@dataclass
class UserSession:
    """Active user session."""
    user: User
    permission: PermissionLevel
    joined_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    current_slide: Optional[int] = None
    cursor_position: Optional[Dict[str, float]] = None
    is_active: bool = True

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user": self.user.to_dict(),
            "permission": self.permission.value,
            "joined_at": self.joined_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "current_slide": self.current_slide,
            "cursor_position": self.cursor_position,
            "is_active": self.is_active,
        }


@dataclass
class Comment:
    """Slide or element comment."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user: User = field(default_factory=lambda: User("", "", ""))
    content: str = ""
    slide_id: Optional[str] = None
    element_id: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    status: CommentStatus = CommentStatus.OPEN
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_by: Optional[User] = None
    resolved_at: Optional[datetime] = None
    replies: List['Comment'] = field(default_factory=list)

    def add_reply(self, user: User, content: str) -> 'Comment':
        """Add a reply to this comment."""
        reply = Comment(
            user=user,
            content=content,
            slide_id=self.slide_id,
            element_id=self.element_id
        )
        self.replies.append(reply)
        self.updated_at = datetime.now()
        return reply

    def resolve(self, user: User) -> None:
        """Resolve the comment."""
        self.status = CommentStatus.RESOLVED
        self.resolved_by = user
        self.resolved_at = datetime.now()
        self.updated_at = datetime.now()

    def reopen(self) -> None:
        """Reopen a resolved comment."""
        self.status = CommentStatus.OPEN
        self.resolved_by = None
        self.resolved_at = None
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user": self.user.to_dict(),
            "content": self.content,
            "slide_id": self.slide_id,
            "element_id": self.element_id,
            "position": self.position,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_by": self.resolved_by.to_dict() if self.resolved_by else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "replies": [reply.to_dict() for reply in self.replies],
        }


@dataclass
class Change:
    """Represents a change to the presentation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user: User = field(default_factory=lambda: User("", "", ""))
    change_type: ChangeType = ChangeType.SLIDE_MODIFIED
    target_id: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user": self.user.to_dict(),
            "change_type": self.change_type.value,
            "target_id": self.target_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
        }


@dataclass
class Version:
    """Presentation version."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version_number: int = 1
    created_by: User = field(default_factory=lambda: User("", "", ""))
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    is_current: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "version_number": self.version_number,
            "created_by": self.created_by.to_dict(),
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "is_current": self.is_current,
        }


class CollaborationManager:
    """
    Manages multi-user collaboration.

    Features:
    - Real-time co-editing
    - User presence tracking
    - Comments and replies
    - Version history
    - Change tracking
    - Conflict resolution
    - Permission management
    """

    def __init__(self):
        """Initialize collaboration manager."""
        self.sessions: Dict[str, UserSession] = {}
        self.comments: Dict[str, Comment] = {}
        self.changes: List[Change] = []
        self.versions: List[Version] = []
        self.permissions: Dict[str, PermissionLevel] = {}

    # User Session Management

    def join_session(
        self,
        user: User,
        permission: PermissionLevel = PermissionLevel.EDITOR
    ) -> UserSession:
        """
        Add user to collaboration session.

        Args:
            user: User joining
            permission: User's permission level

        Returns:
            Created user session
        """
        session = UserSession(user=user, permission=permission)
        self.sessions[user.id] = session
        self.permissions[user.id] = permission
        return session

    def leave_session(self, user_id: str) -> bool:
        """
        Remove user from session.

        Args:
            user_id: User identifier

        Returns:
            True if removed, False if not found
        """
        if user_id in self.sessions:
            self.sessions[user_id].is_active = False
            return True
        return False

    def get_active_users(self) -> List[UserSession]:
        """Get all active users."""
        return [
            session for session in self.sessions.values()
            if session.is_active
        ]

    def update_user_cursor(
        self,
        user_id: str,
        slide_index: int,
        position: Dict[str, float]
    ) -> bool:
        """Update user's cursor position."""
        if user_id in self.sessions:
            session = self.sessions[user_id]
            session.current_slide = slide_index
            session.cursor_position = position
            session.update_activity()
            return True
        return False

    def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """Get user session."""
        return self.sessions.get(user_id)

    # Permission Management

    def set_permission(
        self,
        user_id: str,
        permission: PermissionLevel
    ) -> bool:
        """Set user permission level."""
        if user_id in self.sessions:
            self.sessions[user_id].permission = permission
            self.permissions[user_id] = permission
            return True
        return False

    def get_permission(self, user_id: str) -> Optional[PermissionLevel]:
        """Get user permission level."""
        return self.permissions.get(user_id)

    def can_edit(self, user_id: str) -> bool:
        """Check if user can edit."""
        permission = self.get_permission(user_id)
        return permission in [PermissionLevel.EDITOR, PermissionLevel.OWNER]

    def can_comment(self, user_id: str) -> bool:
        """Check if user can comment."""
        permission = self.get_permission(user_id)
        return permission in [
            PermissionLevel.COMMENTER,
            PermissionLevel.EDITOR,
            PermissionLevel.OWNER
        ]

    # Comment Management

    def add_comment(
        self,
        user: User,
        content: str,
        slide_id: Optional[str] = None,
        element_id: Optional[str] = None,
        position: Optional[Dict[str, float]] = None
    ) -> Optional[Comment]:
        """
        Add a comment.

        Args:
            user: User adding comment
            content: Comment content
            slide_id: Optional slide ID
            element_id: Optional element ID
            position: Optional position on slide

        Returns:
            Created comment or None if not allowed
        """
        if not self.can_comment(user.id):
            return None

        comment = Comment(
            user=user,
            content=content,
            slide_id=slide_id,
            element_id=element_id,
            position=position
        )

        self.comments[comment.id] = comment
        return comment

    def reply_to_comment(
        self,
        comment_id: str,
        user: User,
        content: str
    ) -> Optional[Comment]:
        """Reply to a comment."""
        if not self.can_comment(user.id):
            return None

        if comment_id in self.comments:
            return self.comments[comment_id].add_reply(user, content)
        return None

    def resolve_comment(self, comment_id: str, user: User) -> bool:
        """Resolve a comment."""
        if comment_id in self.comments:
            self.comments[comment_id].resolve(user)
            return True
        return False

    def reopen_comment(self, comment_id: str) -> bool:
        """Reopen a resolved comment."""
        if comment_id in self.comments:
            self.comments[comment_id].reopen()
            return True
        return False

    def delete_comment(self, comment_id: str, user_id: str) -> bool:
        """Delete a comment (only by owner or comment author)."""
        if comment_id in self.comments:
            comment = self.comments[comment_id]
            permission = self.get_permission(user_id)

            if (comment.user.id == user_id or
                permission == PermissionLevel.OWNER):
                comment.status = CommentStatus.DELETED
                return True
        return False

    def get_comments(
        self,
        slide_id: Optional[str] = None,
        element_id: Optional[str] = None,
        status: Optional[CommentStatus] = None
    ) -> List[Comment]:
        """
        Get comments with optional filters.

        Args:
            slide_id: Filter by slide
            element_id: Filter by element
            status: Filter by status

        Returns:
            List of matching comments
        """
        comments = list(self.comments.values())

        if slide_id:
            comments = [c for c in comments if c.slide_id == slide_id]
        if element_id:
            comments = [c for c in comments if c.element_id == element_id]
        if status:
            comments = [c for c in comments if c.status == status]

        return comments

    # Change Tracking

    def record_change(
        self,
        user: User,
        change_type: ChangeType,
        target_id: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        description: str = ""
    ) -> Change:
        """Record a change to the presentation."""
        change = Change(
            user=user,
            change_type=change_type,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            description=description
        )

        self.changes.append(change)
        return change

    def get_changes(
        self,
        user_id: Optional[str] = None,
        change_type: Optional[ChangeType] = None,
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Change]:
        """
        Get changes with optional filters.

        Args:
            user_id: Filter by user
            change_type: Filter by change type
            since: Filter by timestamp
            limit: Maximum number of changes to return

        Returns:
            List of matching changes
        """
        changes = self.changes

        if user_id:
            changes = [c for c in changes if c.user.id == user_id]
        if change_type:
            changes = [c for c in changes if c.change_type == change_type]
        if since:
            changes = [c for c in changes if c.timestamp >= since]

        # Sort by timestamp (newest first)
        changes.sort(key=lambda c: c.timestamp, reverse=True)

        if limit:
            changes = changes[:limit]

        return changes

    def get_recent_changes(self, limit: int = 50) -> List[Change]:
        """Get most recent changes."""
        return self.get_changes(limit=limit)

    # Version History

    def create_version(
        self,
        user: User,
        presentation_data: Dict[str, Any],
        description: str = ""
    ) -> Version:
        """
        Create a new version.

        Args:
            user: User creating version
            presentation_data: Complete presentation data
            description: Version description

        Returns:
            Created version
        """
        # Mark all previous versions as not current
        for version in self.versions:
            version.is_current = False

        version_number = len(self.versions) + 1

        version = Version(
            version_number=version_number,
            created_by=user,
            description=description or f"Version {version_number}",
            data=presentation_data,
            is_current=True
        )

        self.versions.append(version)
        return version

    def get_version(self, version_id: str) -> Optional[Version]:
        """Get version by ID."""
        for version in self.versions:
            if version.id == version_id:
                return version
        return None

    def get_version_by_number(self, version_number: int) -> Optional[Version]:
        """Get version by number."""
        for version in self.versions:
            if version.version_number == version_number:
                return version
        return None

    def get_all_versions(self) -> List[Version]:
        """Get all versions."""
        return sorted(self.versions, key=lambda v: v.version_number, reverse=True)

    def get_current_version(self) -> Optional[Version]:
        """Get current version."""
        for version in self.versions:
            if version.is_current:
                return version
        return None

    def restore_version(self, version_id: str, user: User) -> Optional[Version]:
        """
        Restore a previous version.

        Args:
            version_id: Version to restore
            user: User performing restore

        Returns:
            New version created from restore
        """
        version = self.get_version(version_id)
        if not version:
            return None

        # Create new version from restored data
        return self.create_version(
            user=user,
            presentation_data=version.data,
            description=f"Restored from version {version.version_number}"
        )

    # Conflict Resolution

    def detect_conflicts(
        self,
        user_id: str,
        target_id: str,
        timestamp: datetime
    ) -> List[Change]:
        """
        Detect conflicting changes.

        Args:
            user_id: Current user
            target_id: Element/slide being edited
            timestamp: When user started editing

        Returns:
            List of conflicting changes
        """
        conflicts = []

        for change in self.changes:
            # Find changes to same target by other users after timestamp
            if (change.target_id == target_id and
                change.user.id != user_id and
                change.timestamp >= timestamp):
                conflicts.append(change)

        return conflicts

    # Statistics

    def get_collaboration_stats(self) -> Dict[str, Any]:
        """Get collaboration statistics."""
        active_users = self.get_active_users()
        total_comments = len(self.comments)
        open_comments = len([
            c for c in self.comments.values()
            if c.status == CommentStatus.OPEN
        ])

        return {
            "active_users": len(active_users),
            "total_users": len(self.sessions),
            "total_comments": total_comments,
            "open_comments": open_comments,
            "resolved_comments": total_comments - open_comments,
            "total_changes": len(self.changes),
            "total_versions": len(self.versions),
            "users": [session.to_dict() for session in active_users],
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sessions": {
                uid: session.to_dict()
                for uid, session in self.sessions.items()
            },
            "comments": {
                cid: comment.to_dict()
                for cid, comment in self.comments.items()
            },
            "changes": [change.to_dict() for change in self.changes],
            "versions": [version.to_dict() for version in self.versions],
            "permissions": {
                uid: perm.value
                for uid, perm in self.permissions.items()
            },
        }
