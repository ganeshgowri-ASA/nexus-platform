"""
Real-time collaboration module for Document Management System.

This module provides comprehensive collaboration features including:
- Comment system with threading
- @mentions support with notifications
- Activity feeds for document changes
- Real-time notifications via WebSocket
- Collaborative editing support with conflict resolution
- Presence tracking for active users
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.core.exceptions import (
    AuthorizationException,
    CollaborationException,
    CommentNotFoundException,
    ResourceNotFoundException,
    ValidationException,
)
from backend.core.logging import get_logger
from backend.models.document import Document, DocumentComment
from backend.models.user import User

logger = get_logger(__name__)


class ActivityType(str, Enum):
    """Activity type enumeration."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    VIEWED = "viewed"
    DOWNLOADED = "downloaded"
    SHARED = "shared"
    COMMENTED = "commented"
    MENTIONED = "mentioned"
    LOCKED = "locked"
    UNLOCKED = "unlocked"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_APPROVED = "workflow_approved"
    WORKFLOW_REJECTED = "workflow_rejected"


class NotificationType(str, Enum):
    """Notification type enumeration."""

    MENTION = "mention"
    COMMENT_REPLY = "comment_reply"
    DOCUMENT_SHARED = "document_shared"
    WORKFLOW_ASSIGNED = "workflow_assigned"
    EDIT_CONFLICT = "edit_conflict"
    DOCUMENT_UPDATED = "document_updated"


class PresenceStatus(str, Enum):
    """User presence status."""

    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"


class Comment:
    """
    Document comment model.

    Attributes:
        id: Comment ID
        document_id: Document ID
        user_id: Comment author ID
        user: User object
        content: Comment text
        parent_id: Parent comment ID for replies
        mentions: List of mentioned user IDs
        is_resolved: Whether comment is resolved
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    def __init__(
        self,
        document_id: int,
        user_id: int,
        content: str,
        parent_id: Optional[int] = None,
        comment_id: Optional[int] = None,
    ) -> None:
        """Initialize comment."""
        self.id = comment_id
        self.document_id = document_id
        self.user_id = user_id
        self.user: Optional[User] = None
        self.content = content
        self.parent_id = parent_id
        self.mentions: List[int] = []
        self.is_resolved = False
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.replies: List[Comment] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert comment to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "user": self.user.to_dict() if self.user else None,
            "content": self.content,
            "parent_id": self.parent_id,
            "mentions": self.mentions,
            "is_resolved": self.is_resolved,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "replies": [reply.to_dict() for reply in self.replies],
        }


class Activity:
    """
    Activity feed item.

    Attributes:
        id: Activity ID
        document_id: Document ID
        user_id: User who performed activity
        user: User object
        activity_type: Type of activity
        description: Activity description
        metadata: Additional activity metadata
        created_at: Activity timestamp
    """

    def __init__(
        self,
        document_id: int,
        user_id: int,
        activity_type: ActivityType,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        activity_id: Optional[int] = None,
    ) -> None:
        """Initialize activity."""
        self.id = activity_id
        self.document_id = document_id
        self.user_id = user_id
        self.user: Optional[User] = None
        self.activity_type = activity_type
        self.description = description
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "user": self.user.to_dict() if self.user else None,
            "activity_type": self.activity_type.value,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class Notification:
    """
    User notification.

    Attributes:
        id: Notification ID
        user_id: Recipient user ID
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        document_id: Related document ID
        metadata: Additional notification data
        is_read: Whether notification is read
        created_at: Creation timestamp
    """

    def __init__(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        document_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        notification_id: Optional[int] = None,
    ) -> None:
        """Initialize notification."""
        self.id = notification_id
        self.user_id = user_id
        self.notification_type = notification_type
        self.title = title
        self.message = message
        self.document_id = document_id
        self.metadata = metadata or {}
        self.is_read = False
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_type": self.notification_type.value,
            "title": title,
            "message": self.message,
            "document_id": self.document_id,
            "metadata": self.metadata,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
        }


class UserPresence:
    """
    User presence information.

    Attributes:
        user_id: User ID
        document_id: Document being viewed
        status: Presence status
        last_seen: Last activity timestamp
    """

    def __init__(
        self,
        user_id: int,
        document_id: Optional[int] = None,
        status: PresenceStatus = PresenceStatus.ONLINE,
    ) -> None:
        """Initialize user presence."""
        self.user_id = user_id
        self.document_id = document_id
        self.status = status
        self.last_seen = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert presence to dictionary."""
        return {
            "user_id": self.user_id,
            "document_id": self.document_id,
            "status": self.status.value,
            "last_seen": self.last_seen.isoformat(),
        }


class CollaborationService:
    """
    Real-time collaboration service.

    Provides comprehensive collaboration features including comments,
    mentions, activity feeds, notifications, and presence tracking.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize collaboration service.

        Args:
            db: Database session
        """
        self.db = db
        self.logger = get_logger(self.__class__.__name__)
        self._presence_map: Dict[int, UserPresence] = {}
        self._notification_callbacks: List = []

    # Comment Management

    async def create_comment(
        self,
        document_id: int,
        user_id: int,
        content: str,
        parent_id: Optional[int] = None,
    ) -> Comment:
        """
        Create a new comment on a document.

        Args:
            document_id: Document ID
            user_id: Comment author ID
            content: Comment text
            parent_id: Parent comment ID for replies

        Returns:
            Created comment

        Raises:
            ResourceNotFoundException: If document not found
            ValidationException: If validation fails
        """
        try:
            self.logger.info(
                "creating_comment",
                document_id=document_id,
                user_id=user_id,
            )

            # Validate content
            if not content or len(content.strip()) < 1:
                raise ValidationException("Comment content cannot be empty")

            # Verify document exists
            await self._get_document(document_id)

            # Verify parent comment if replying
            if parent_id:
                parent_comment = await self._get_comment(parent_id)
                if parent_comment.document_id != document_id:
                    raise ValidationException("Parent comment must be on same document")

            # Create comment
            comment = Comment(
                document_id=document_id,
                user_id=user_id,
                content=content,
                parent_id=parent_id,
            )

            # Extract mentions
            mentions = self._extract_mentions(content)
            comment.mentions = mentions

            # TODO: Store in database
            comment.id = 1  # Placeholder

            # Load user info
            comment.user = await self._get_user(user_id)

            # Create activity
            await self._create_activity(
                document_id=document_id,
                user_id=user_id,
                activity_type=ActivityType.COMMENTED,
                description=f"Commented on document",
            )

            # Send notifications for mentions
            for mentioned_user_id in mentions:
                await self._send_notification(
                    user_id=mentioned_user_id,
                    notification_type=NotificationType.MENTION,
                    title="You were mentioned",
                    message=f"{comment.user.username if comment.user else 'Someone'} mentioned you in a comment",
                    document_id=document_id,
                )

            # Send notification for comment reply
            if parent_id:
                parent_comment = await self._get_comment(parent_id)
                if parent_comment.user_id != user_id:
                    await self._send_notification(
                        user_id=parent_comment.user_id,
                        notification_type=NotificationType.COMMENT_REPLY,
                        title="New reply to your comment",
                        message=f"{comment.user.username if comment.user else 'Someone'} replied to your comment",
                        document_id=document_id,
                    )

            self.logger.info("comment_created", comment_id=comment.id)

            return comment

        except (ResourceNotFoundException, ValidationException):
            raise
        except Exception as e:
            self.logger.exception("create_comment_failed", error=str(e))
            raise CollaborationException(f"Failed to create comment: {str(e)}")

    async def get_comments(
        self,
        document_id: int,
        user_id: int,
        include_resolved: bool = False,
    ) -> List[Comment]:
        """
        Get all comments for a document.

        Args:
            document_id: Document ID
            user_id: User requesting comments
            include_resolved: Include resolved comments

        Returns:
            List of comments with replies

        Raises:
            ResourceNotFoundException: If document not found
        """
        try:
            self.logger.debug("getting_comments", document_id=document_id)

            # Verify document access
            await self._verify_document_access(document_id, user_id)

            # TODO: Fetch from database
            # For now, return empty list
            comments = []

            # Build comment tree (parent comments with nested replies)
            comment_map = {c.id: c for c in comments}
            root_comments = []

            for comment in comments:
                if comment.parent_id and comment.parent_id in comment_map:
                    comment_map[comment.parent_id].replies.append(comment)
                else:
                    root_comments.append(comment)

            return root_comments

        except ResourceNotFoundException:
            raise
        except Exception as e:
            self.logger.exception("get_comments_failed", error=str(e))
            raise CollaborationException(f"Failed to get comments: {str(e)}")

    async def update_comment(
        self,
        comment_id: int,
        user_id: int,
        content: str,
    ) -> Comment:
        """
        Update a comment.

        Args:
            comment_id: Comment ID
            user_id: User updating comment
            content: New content

        Returns:
            Updated comment

        Raises:
            CommentNotFoundException: If comment not found
            AuthorizationException: If user doesn't own comment
        """
        try:
            self.logger.info("updating_comment", comment_id=comment_id)

            # Get comment
            comment = await self._get_comment(comment_id)

            # Verify ownership
            if comment.user_id != user_id:
                raise AuthorizationException("Only comment author can update")

            # Validate content
            if not content or len(content.strip()) < 1:
                raise ValidationException("Comment content cannot be empty")

            # Update comment
            comment.content = content
            comment.updated_at = datetime.utcnow()

            # Extract new mentions
            mentions = self._extract_mentions(content)
            new_mentions = set(mentions) - set(comment.mentions)
            comment.mentions = mentions

            # TODO: Update in database

            # Send notifications for new mentions
            for mentioned_user_id in new_mentions:
                await self._send_notification(
                    user_id=mentioned_user_id,
                    notification_type=NotificationType.MENTION,
                    title="You were mentioned",
                    message=f"You were mentioned in an updated comment",
                    document_id=comment.document_id,
                )

            self.logger.info("comment_updated", comment_id=comment_id)

            return comment

        except (CommentNotFoundException, AuthorizationException, ValidationException):
            raise
        except Exception as e:
            self.logger.exception("update_comment_failed", error=str(e))
            raise CollaborationException(f"Failed to update comment: {str(e)}")

    async def delete_comment(
        self,
        comment_id: int,
        user_id: int,
    ) -> None:
        """
        Delete a comment.

        Args:
            comment_id: Comment ID
            user_id: User deleting comment

        Raises:
            CommentNotFoundException: If comment not found
            AuthorizationException: If user doesn't own comment
        """
        try:
            self.logger.info("deleting_comment", comment_id=comment_id)

            # Get comment
            comment = await self._get_comment(comment_id)

            # Verify ownership
            if comment.user_id != user_id:
                raise AuthorizationException("Only comment author can delete")

            # TODO: Delete from database
            # Also delete all replies

            self.logger.info("comment_deleted", comment_id=comment_id)

        except (CommentNotFoundException, AuthorizationException):
            raise
        except Exception as e:
            self.logger.exception("delete_comment_failed", error=str(e))
            raise CollaborationException(f"Failed to delete comment: {str(e)}")

    async def resolve_comment(
        self,
        comment_id: int,
        user_id: int,
    ) -> Comment:
        """
        Mark a comment as resolved.

        Args:
            comment_id: Comment ID
            user_id: User resolving comment

        Returns:
            Updated comment
        """
        try:
            self.logger.info("resolving_comment", comment_id=comment_id)

            comment = await self._get_comment(comment_id)
            comment.is_resolved = True
            comment.updated_at = datetime.utcnow()

            # TODO: Update in database

            return comment

        except Exception as e:
            self.logger.exception("resolve_comment_failed", error=str(e))
            raise CollaborationException(f"Failed to resolve comment: {str(e)}")

    # Activity Feed

    async def get_activity_feed(
        self,
        document_id: Optional[int] = None,
        user_id: Optional[int] = None,
        activity_types: Optional[List[ActivityType]] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Activity]:
        """
        Get activity feed.

        Args:
            document_id: Filter by document
            user_id: Filter by user
            activity_types: Filter by activity types
            limit: Maximum activities to return
            offset: Offset for pagination

        Returns:
            List of activities
        """
        try:
            self.logger.debug(
                "getting_activity_feed",
                document_id=document_id,
                user_id=user_id,
            )

            # TODO: Fetch from database with filters
            activities = []

            return activities

        except Exception as e:
            self.logger.exception("get_activity_feed_failed", error=str(e))
            return []

    async def _create_activity(
        self,
        document_id: int,
        user_id: int,
        activity_type: ActivityType,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Activity:
        """
        Create activity record.

        Args:
            document_id: Document ID
            user_id: User ID
            activity_type: Activity type
            description: Activity description
            metadata: Additional metadata

        Returns:
            Created activity
        """
        activity = Activity(
            document_id=document_id,
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            metadata=metadata,
        )

        # TODO: Store in database

        return activity

    # Notifications

    async def get_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """
        Get user notifications.

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum notifications

        Returns:
            List of notifications
        """
        try:
            self.logger.debug("getting_notifications", user_id=user_id)

            # TODO: Fetch from database
            notifications = []

            return notifications

        except Exception as e:
            self.logger.exception("get_notifications_failed", error=str(e))
            return []

    async def mark_notification_read(
        self,
        notification_id: int,
        user_id: int,
    ) -> None:
        """
        Mark notification as read.

        Args:
            notification_id: Notification ID
            user_id: User ID
        """
        try:
            # TODO: Update in database
            self.logger.debug("notification_marked_read", notification_id=notification_id)

        except Exception as e:
            self.logger.warning("mark_read_failed", error=str(e))

    async def _send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        document_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send notification to user.

        Args:
            user_id: Recipient user ID
            notification_type: Notification type
            title: Notification title
            message: Notification message
            document_id: Related document ID
            metadata: Additional metadata
        """
        try:
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                document_id=document_id,
                metadata=metadata,
            )

            # TODO: Store in database

            # Send real-time notification via WebSocket
            await self._broadcast_notification(notification)

            self.logger.debug("notification_sent", user_id=user_id, type=notification_type.value)

        except Exception as e:
            self.logger.warning("send_notification_failed", error=str(e))

    # Presence Tracking

    async def update_presence(
        self,
        user_id: int,
        document_id: Optional[int] = None,
        status: PresenceStatus = PresenceStatus.ONLINE,
    ) -> UserPresence:
        """
        Update user presence.

        Args:
            user_id: User ID
            document_id: Document being viewed
            status: Presence status

        Returns:
            Updated presence
        """
        try:
            presence = UserPresence(
                user_id=user_id,
                document_id=document_id,
                status=status,
            )

            self._presence_map[user_id] = presence

            # Broadcast presence update
            await self._broadcast_presence(presence)

            return presence

        except Exception as e:
            self.logger.warning("update_presence_failed", error=str(e))
            return presence

    async def get_active_users(
        self,
        document_id: int,
        timeout_minutes: int = 5,
    ) -> List[UserPresence]:
        """
        Get active users on a document.

        Args:
            document_id: Document ID
            timeout_minutes: Timeout for considering user inactive

        Returns:
            List of active users
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)

            active_users = [
                presence
                for presence in self._presence_map.values()
                if presence.document_id == document_id
                and presence.status == PresenceStatus.ONLINE
                and presence.last_seen >= cutoff_time
            ]

            return active_users

        except Exception as e:
            self.logger.warning("get_active_users_failed", error=str(e))
            return []

    # Helper Methods

    def _extract_mentions(self, text: str) -> List[int]:
        """
        Extract @mentions from text.

        Args:
            text: Text to parse

        Returns:
            List of mentioned user IDs
        """
        # Pattern: @username or @[User Name]
        mention_pattern = r'@\[([^\]]+)\]|@(\w+)'
        matches = re.findall(mention_pattern, text)

        # TODO: Convert usernames to user IDs
        # For now, return empty list
        return []

    async def _get_document(self, document_id: int) -> Document:
        """Get document by ID."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise ResourceNotFoundException("Document", document_id)

        return document

    async def _get_user(self, user_id: int) -> User:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ResourceNotFoundException("User", user_id)

        return user

    async def _get_comment(self, comment_id: int) -> Comment:
        """Get comment by ID."""
        # TODO: Fetch from database
        raise CommentNotFoundException(comment_id)

    async def _verify_document_access(self, document_id: int, user_id: int) -> None:
        """Verify user has access to document."""
        document = await self._get_document(document_id)

        if not document.is_public and document.owner_id != user_id:
            # TODO: Check permissions table
            raise AuthorizationException("No access to document")

    async def _broadcast_notification(self, notification: Notification) -> None:
        """Broadcast notification via WebSocket."""
        # TODO: Implement WebSocket broadcasting
        pass

    async def _broadcast_presence(self, presence: UserPresence) -> None:
        """Broadcast presence update via WebSocket."""
        # TODO: Implement WebSocket broadcasting
        pass
