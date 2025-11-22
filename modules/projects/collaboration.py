"""
NEXUS Collaboration Module
Team collaboration features including comments, mentions, and activity feeds.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import uuid
import re


class ActivityType(Enum):
    """Activity types for activity feed."""
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    TASK_ASSIGNED = "task_assigned"
    COMMENT_ADDED = "comment_added"
    FILE_ATTACHED = "file_attached"
    MILESTONE_REACHED = "milestone_reached"
    PROJECT_UPDATED = "project_updated"


class Comment:
    """
    Represents a comment on a task or project.

    Attributes:
        id: Unique comment identifier
        entity_type: Type of entity (task, project, etc.)
        entity_id: ID of the entity being commented on
        user_id: User who created the comment
        content: Comment content
        mentions: List of mentioned user IDs
        attachments: List of attachment URLs
        parent_comment_id: Parent comment ID (for replies)
        reactions: Dictionary of reactions (emoji -> [user_ids])
        is_edited: Whether comment was edited
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str,
        content: str,
        parent_comment_id: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        comment_id: Optional[str] = None
    ):
        """Initialize a comment."""
        self.id: str = comment_id or str(uuid.uuid4())
        self.entity_type: str = entity_type
        self.entity_id: str = entity_id
        self.user_id: str = user_id
        self.content: str = content
        self.mentions: List[str] = self._extract_mentions(content)
        self.attachments: List[str] = attachments or []
        self.parent_comment_id: Optional[str] = parent_comment_id
        self.reactions: Dict[str, List[str]] = {}
        self.is_edited: bool = False
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

    def _extract_mentions(self, content: str) -> List[str]:
        """Extract @mentions from comment content."""
        # Match @username or @user_id patterns
        pattern = r'@(\w+)'
        matches = re.findall(pattern, content)
        return list(set(matches))  # Remove duplicates

    def to_dict(self) -> Dict[str, Any]:
        """Convert comment to dictionary."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "content": self.content,
            "mentions": self.mentions,
            "attachments": self.attachments,
            "parent_comment_id": self.parent_comment_id,
            "reactions": self.reactions,
            "is_edited": self.is_edited,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    def add_reaction(self, emoji: str, user_id: str) -> None:
        """Add a reaction to the comment."""
        if emoji not in self.reactions:
            self.reactions[emoji] = []
        if user_id not in self.reactions[emoji]:
            self.reactions[emoji].append(user_id)

    def remove_reaction(self, emoji: str, user_id: str) -> None:
        """Remove a reaction from the comment."""
        if emoji in self.reactions and user_id in self.reactions[emoji]:
            self.reactions[emoji].remove(user_id)
            if not self.reactions[emoji]:
                del self.reactions[emoji]


class Activity:
    """
    Represents an activity in the activity feed.

    Attributes:
        id: Unique activity identifier
        project_id: Associated project ID
        activity_type: Type of activity
        user_id: User who performed the activity
        entity_type: Type of entity affected
        entity_id: ID of affected entity
        title: Activity title
        description: Activity description
        metadata: Additional metadata
        created_at: Activity timestamp
    """

    def __init__(
        self,
        project_id: str,
        activity_type: ActivityType,
        user_id: str,
        entity_type: str,
        entity_id: str,
        title: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        activity_id: Optional[str] = None
    ):
        """Initialize an activity."""
        self.id: str = activity_id or str(uuid.uuid4())
        self.project_id: str = project_id
        self.activity_type: ActivityType = activity_type
        self.user_id: str = user_id
        self.entity_type: str = entity_type
        self.entity_id: str = entity_id
        self.title: str = title
        self.description: str = description
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "activity_type": self.activity_type.value,
            "user_id": self.user_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "title": self.title,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class Attachment:
    """
    Represents a file attachment.

    Attributes:
        id: Unique attachment identifier
        entity_type: Type of entity (task, project, comment)
        entity_id: ID of the entity
        user_id: User who uploaded the file
        filename: Original filename
        file_url: URL to the file
        file_size: File size in bytes
        file_type: MIME type
        metadata: Additional metadata
        created_at: Upload timestamp
    """

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str,
        filename: str,
        file_url: str,
        file_size: int = 0,
        file_type: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        attachment_id: Optional[str] = None
    ):
        """Initialize an attachment."""
        self.id: str = attachment_id or str(uuid.uuid4())
        self.entity_type: str = entity_type
        self.entity_id: str = entity_id
        self.user_id: str = user_id
        self.filename: str = filename
        self.file_url: str = file_url
        self.file_size: int = file_size
        self.file_type: str = file_type
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert attachment to dictionary."""
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_url": self.file_url,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


class CollaborationManager:
    """
    Collaboration features manager.
    Handles comments, mentions, activity feeds, and file attachments.
    """

    def __init__(self):
        """Initialize the collaboration manager."""
        self.comments: Dict[str, Comment] = {}
        self.activities: Dict[str, Activity] = {}
        self.attachments: Dict[str, Attachment] = {}

    # Comment Management

    def add_comment(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str,
        content: str,
        parent_comment_id: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> Comment:
        """
        Add a comment to an entity.

        Args:
            entity_type: Type of entity (task, project, etc.)
            entity_id: Entity identifier
            user_id: User identifier
            content: Comment content
            parent_comment_id: Parent comment ID for replies
            attachments: List of attachment URLs

        Returns:
            Created comment
        """
        comment = Comment(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            content=content,
            parent_comment_id=parent_comment_id,
            attachments=attachments
        )

        self.comments[comment.id] = comment
        return comment

    def get_comment(self, comment_id: str) -> Optional[Comment]:
        """Get a comment by ID."""
        return self.comments.get(comment_id)

    def update_comment(self, comment_id: str, content: str) -> Optional[Comment]:
        """Update a comment's content."""
        comment = self.get_comment(comment_id)
        if not comment:
            return None

        comment.content = content
        comment.mentions = comment._extract_mentions(content)
        comment.is_edited = True
        comment.updated_at = datetime.now()

        return comment

    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment."""
        if comment_id in self.comments:
            # Delete all replies
            replies = self.get_comment_replies(comment_id)
            for reply in replies:
                del self.comments[reply.id]

            del self.comments[comment_id]
            return True
        return False

    def get_entity_comments(
        self,
        entity_type: str,
        entity_id: str,
        include_replies: bool = True
    ) -> List[Comment]:
        """
        Get all comments for an entity.

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            include_replies: Include comment replies

        Returns:
            List of comments
        """
        comments = [
            c for c in self.comments.values()
            if c.entity_type == entity_type and c.entity_id == entity_id
        ]

        if not include_replies:
            comments = [c for c in comments if c.parent_comment_id is None]

        return sorted(comments, key=lambda c: c.created_at)

    def get_comment_replies(self, comment_id: str) -> List[Comment]:
        """Get all replies to a comment."""
        return [
            c for c in self.comments.values()
            if c.parent_comment_id == comment_id
        ]

    def get_user_mentions(self, user_id: str) -> List[Comment]:
        """Get all comments that mention a user."""
        return [
            c for c in self.comments.values()
            if user_id in c.mentions
        ]

    # Activity Feed

    def log_activity(
        self,
        project_id: str,
        activity_type: ActivityType,
        user_id: str,
        entity_type: str,
        entity_id: str,
        title: str,
        description: str = "",
        **metadata
    ) -> Activity:
        """
        Log an activity to the feed.

        Args:
            project_id: Project identifier
            activity_type: Type of activity
            user_id: User who performed the activity
            entity_type: Type of entity
            entity_id: Entity identifier
            title: Activity title
            description: Activity description
            **metadata: Additional metadata

        Returns:
            Created activity
        """
        activity = Activity(
            project_id=project_id,
            activity_type=activity_type,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            description=description,
            metadata=metadata
        )

        self.activities[activity.id] = activity
        return activity

    def get_project_activity_feed(
        self,
        project_id: str,
        limit: int = 50,
        activity_types: Optional[List[ActivityType]] = None
    ) -> List[Activity]:
        """
        Get activity feed for a project.

        Args:
            project_id: Project identifier
            limit: Maximum number of activities
            activity_types: Filter by activity types

        Returns:
            List of activities
        """
        activities = [
            a for a in self.activities.values()
            if a.project_id == project_id
        ]

        if activity_types:
            activities = [
                a for a in activities
                if a.activity_type in activity_types
            ]

        # Sort by timestamp (newest first)
        activities = sorted(activities, key=lambda a: a.created_at, reverse=True)

        return activities[:limit]

    def get_user_activity_feed(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Activity]:
        """Get activity feed for a user's activities."""
        activities = [
            a for a in self.activities.values()
            if a.user_id == user_id
        ]

        return sorted(activities, key=lambda a: a.created_at, reverse=True)[:limit]

    # Attachment Management

    def add_attachment(
        self,
        entity_type: str,
        entity_id: str,
        user_id: str,
        filename: str,
        file_url: str,
        **kwargs
    ) -> Attachment:
        """
        Add a file attachment.

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            user_id: User identifier
            filename: File name
            file_url: URL to file
            **kwargs: Additional attachment attributes

        Returns:
            Created attachment
        """
        attachment = Attachment(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            filename=filename,
            file_url=file_url,
            **kwargs
        )

        self.attachments[attachment.id] = attachment
        return attachment

    def get_attachment(self, attachment_id: str) -> Optional[Attachment]:
        """Get an attachment by ID."""
        return self.attachments.get(attachment_id)

    def delete_attachment(self, attachment_id: str) -> bool:
        """Delete an attachment."""
        if attachment_id in self.attachments:
            del self.attachments[attachment_id]
            return True
        return False

    def get_entity_attachments(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[Attachment]:
        """Get all attachments for an entity."""
        return [
            a for a in self.attachments.values()
            if a.entity_type == entity_type and a.entity_id == entity_id
        ]

    # Notifications

    def get_user_notifications(
        self,
        user_id: str,
        include_mentions: bool = True,
        include_assignments: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.

        Args:
            user_id: User identifier
            include_mentions: Include @mentions
            include_assignments: Include task assignments

        Returns:
            List of notification dictionaries
        """
        notifications = []

        # Add mentions
        if include_mentions:
            mentions = self.get_user_mentions(user_id)
            for comment in mentions:
                notifications.append({
                    "type": "mention",
                    "comment_id": comment.id,
                    "entity_type": comment.entity_type,
                    "entity_id": comment.entity_id,
                    "user_id": comment.user_id,
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat()
                })

        # Add activities
        if include_assignments:
            activities = [
                a for a in self.activities.values()
                if a.activity_type == ActivityType.TASK_ASSIGNED
                and a.metadata.get("assignee_id") == user_id
            ]

            for activity in activities:
                notifications.append({
                    "type": "assignment",
                    "activity_id": activity.id,
                    "project_id": activity.project_id,
                    "entity_type": activity.entity_type,
                    "entity_id": activity.entity_id,
                    "title": activity.title,
                    "description": activity.description,
                    "created_at": activity.created_at.isoformat()
                })

        # Sort by timestamp (newest first)
        notifications.sort(key=lambda n: n["created_at"], reverse=True)

        return notifications

    def get_collaboration_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Get collaboration statistics for a project.

        Args:
            project_id: Project identifier

        Returns:
            Statistics dictionary
        """
        activities = self.get_project_activity_feed(project_id, limit=10000)

        # Count comments
        comment_count = sum(
            1 for a in activities
            if a.activity_type == ActivityType.COMMENT_ADDED
        )

        # Count active users
        active_users = set(a.user_id for a in activities)

        # Count attachments
        attachment_count = sum(
            1 for a in activities
            if a.activity_type == ActivityType.FILE_ATTACHED
        )

        return {
            "total_activities": len(activities),
            "comment_count": comment_count,
            "active_user_count": len(active_users),
            "attachment_count": attachment_count
        }
