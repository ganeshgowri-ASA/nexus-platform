"""
Collaboration module for team assignments, comments, and version control.

This module provides:
- Team member management
- Comment and discussion threads
- Content reviews
- Version control and history
- Real-time collaboration
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from loguru import logger

from database import (
    ContentItem,
    Comment as DBComment,
    ContentVersion,
    User,
    Assignment,
)
from .calendar_types import Comment, NotificationType


class CollaborationManager:
    """Collaboration manager for team features."""

    def __init__(self, db: Session):
        """
        Initialize collaboration manager.

        Args:
            db: Database session
        """
        self.db = db
        logger.info("CollaborationManager initialized")

    # Comments and Discussions
    def add_comment(
        self,
        content_id: int,
        author_id: int,
        text: str,
        parent_id: Optional[int] = None,
    ) -> Comment:
        """
        Add comment to content.

        Args:
            content_id: Content ID
            author_id: Comment author user ID
            text: Comment text
            parent_id: Parent comment ID (for replies)

        Returns:
            Created comment
        """
        try:
            # Get author info
            author = self.db.query(User).filter(User.id == author_id).first()

            comment = DBComment(
                content_item_id=content_id,
                author_id=author_id,
                content=text,
                parent_id=parent_id,
                is_resolved=False,
            )

            self.db.add(comment)
            self.db.commit()
            self.db.refresh(comment)

            # Update content comment count
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )
            if content_item:
                content_item.comments_count += 1
                self.db.commit()

            result = Comment(
                id=comment.id,
                content_id=content_id,
                author_id=author_id,
                author_name=author.full_name if author else None,
                text=text,
                parent_id=parent_id,
                is_resolved=False,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )

            logger.info(f"Added comment to content {content_id} by user {author_id}")
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding comment: {e}")
            raise

    def get_comments(
        self,
        content_id: int,
        include_resolved: bool = True,
    ) -> list[Comment]:
        """
        Get comments for content.

        Args:
            content_id: Content ID
            include_resolved: Include resolved comments

        Returns:
            List of comments
        """
        try:
            query = self.db.query(DBComment).filter(
                DBComment.content_item_id == content_id
            )

            if not include_resolved:
                query = query.filter(DBComment.is_resolved == False)

            comments = query.order_by(DBComment.created_at).all()

            # Build comment tree
            result = []
            for comment in comments:
                author = self.db.query(User).filter(User.id == comment.author_id).first()

                result.append(
                    Comment(
                        id=comment.id,
                        content_id=content_id,
                        author_id=comment.author_id,
                        author_name=author.full_name if author else "Unknown",
                        text=comment.content,
                        parent_id=comment.parent_id,
                        is_resolved=comment.is_resolved,
                        created_at=comment.created_at,
                        updated_at=comment.updated_at,
                    )
                )

            logger.info(f"Retrieved {len(result)} comments for content {content_id}")
            return result

        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            raise

    def update_comment(
        self,
        comment_id: int,
        text: str,
    ) -> Comment:
        """
        Update comment text.

        Args:
            comment_id: Comment ID
            text: New comment text

        Returns:
            Updated comment
        """
        try:
            comment = (
                self.db.query(DBComment)
                .filter(DBComment.id == comment_id)
                .first()
            )

            if not comment:
                raise ValueError(f"Comment {comment_id} not found")

            comment.content = text
            comment.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(comment)

            author = self.db.query(User).filter(User.id == comment.author_id).first()

            result = Comment(
                id=comment.id,
                content_id=comment.content_item_id,
                author_id=comment.author_id,
                author_name=author.full_name if author else None,
                text=text,
                parent_id=comment.parent_id,
                is_resolved=comment.is_resolved,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )

            logger.info(f"Updated comment {comment_id}")
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating comment: {e}")
            raise

    def delete_comment(self, comment_id: int) -> bool:
        """
        Delete comment.

        Args:
            comment_id: Comment ID

        Returns:
            True if deleted successfully
        """
        try:
            comment = (
                self.db.query(DBComment)
                .filter(DBComment.id == comment_id)
                .first()
            )

            if not comment:
                raise ValueError(f"Comment {comment_id} not found")

            content_id = comment.content_item_id

            self.db.delete(comment)
            self.db.commit()

            # Update content comment count
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )
            if content_item and content_item.comments_count > 0:
                content_item.comments_count -= 1
                self.db.commit()

            logger.info(f"Deleted comment {comment_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting comment: {e}")
            raise

    def resolve_comment(self, comment_id: int) -> Comment:
        """
        Mark comment as resolved.

        Args:
            comment_id: Comment ID

        Returns:
            Updated comment
        """
        try:
            comment = (
                self.db.query(DBComment)
                .filter(DBComment.id == comment_id)
                .first()
            )

            if not comment:
                raise ValueError(f"Comment {comment_id} not found")

            comment.is_resolved = True
            comment.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(comment)

            author = self.db.query(User).filter(User.id == comment.author_id).first()

            result = Comment(
                id=comment.id,
                content_id=comment.content_item_id,
                author_id=comment.author_id,
                author_name=author.full_name if author else None,
                text=comment.content,
                parent_id=comment.parent_id,
                is_resolved=True,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )

            logger.info(f"Resolved comment {comment_id}")
            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resolving comment: {e}")
            raise

    # Version Control
    def create_version(
        self,
        content_id: int,
        user_id: int,
        changes_summary: Optional[str] = None,
    ) -> dict:
        """
        Create new version of content.

        Args:
            content_id: Content ID
            user_id: User creating version
            changes_summary: Summary of changes

        Returns:
            Version data
        """
        try:
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            version = ContentVersion(
                content_item_id=content_id,
                version_number=content_item.version,
                title=content_item.title,
                content=content_item.content,
                changes_summary=changes_summary,
                created_by=user_id,
            )

            self.db.add(version)
            self.db.commit()
            self.db.refresh(version)

            logger.info(
                f"Created version {version.version_number} for content {content_id}"
            )

            return {
                "id": version.id,
                "content_id": content_id,
                "version_number": version.version_number,
                "title": version.title,
                "changes_summary": changes_summary,
                "created_by": user_id,
                "created_at": version.created_at,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating version: {e}")
            raise

    def get_version_history(self, content_id: int) -> list[dict]:
        """
        Get version history for content.

        Args:
            content_id: Content ID

        Returns:
            List of versions
        """
        try:
            versions = (
                self.db.query(ContentVersion)
                .filter(ContentVersion.content_item_id == content_id)
                .order_by(desc(ContentVersion.version_number))
                .all()
            )

            result = []
            for version in versions:
                user = self.db.query(User).filter(User.id == version.created_by).first()

                result.append(
                    {
                        "id": version.id,
                        "version_number": version.version_number,
                        "title": version.title,
                        "changes_summary": version.changes_summary,
                        "created_by": version.created_by,
                        "created_by_name": user.full_name if user else "Unknown",
                        "created_at": version.created_at,
                    }
                )

            logger.info(f"Retrieved {len(result)} versions for content {content_id}")
            return result

        except Exception as e:
            logger.error(f"Error getting version history: {e}")
            raise

    def restore_version(
        self,
        content_id: int,
        version_id: int,
        user_id: int,
    ) -> dict:
        """
        Restore content to a previous version.

        Args:
            content_id: Content ID
            version_id: Version ID to restore
            user_id: User performing restore

        Returns:
            Updated content data
        """
        try:
            version = (
                self.db.query(ContentVersion)
                .filter(ContentVersion.id == version_id)
                .first()
            )

            if not version:
                raise ValueError(f"Version {version_id} not found")

            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            # Create version of current state before restoring
            self.create_version(
                content_id=content_id,
                user_id=user_id,
                changes_summary=f"Before restoring to version {version.version_number}",
            )

            # Restore content
            content_item.title = version.title
            content_item.content = version.content
            content_item.version += 1
            content_item.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(content_item)

            logger.info(f"Restored content {content_id} to version {version.version_number}")

            return {
                "id": content_item.id,
                "title": content_item.title,
                "content": content_item.content,
                "version": content_item.version,
                "updated_at": content_item.updated_at,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error restoring version: {e}")
            raise

    def compare_versions(
        self,
        content_id: int,
        version1_id: int,
        version2_id: int,
    ) -> dict:
        """
        Compare two versions of content.

        Args:
            content_id: Content ID
            version1_id: First version ID
            version2_id: Second version ID

        Returns:
            Comparison data
        """
        try:
            version1 = (
                self.db.query(ContentVersion)
                .filter(ContentVersion.id == version1_id)
                .first()
            )

            version2 = (
                self.db.query(ContentVersion)
                .filter(ContentVersion.id == version2_id)
                .first()
            )

            if not version1 or not version2:
                raise ValueError("One or both versions not found")

            # Simple comparison (in production, use a diff library)
            title_changed = version1.title != version2.title
            content_changed = version1.content != version2.content

            return {
                "version1": {
                    "id": version1.id,
                    "version_number": version1.version_number,
                    "title": version1.title,
                    "content": version1.content,
                    "created_at": version1.created_at,
                },
                "version2": {
                    "id": version2.id,
                    "version_number": version2.version_number,
                    "title": version2.title,
                    "content": version2.content,
                    "created_at": version2.created_at,
                },
                "differences": {
                    "title_changed": title_changed,
                    "content_changed": content_changed,
                },
            }

        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            raise

    # Team Collaboration
    def get_team_members(self, content_id: int) -> list[dict]:
        """
        Get team members working on content.

        Args:
            content_id: Content ID

        Returns:
            List of team members
        """
        try:
            # Get content creator
            content_item = (
                self.db.query(ContentItem)
                .filter(ContentItem.id == content_id)
                .first()
            )

            if not content_item:
                raise ValueError(f"Content {content_id} not found")

            team_members = []

            # Add creator
            creator = (
                self.db.query(User)
                .filter(User.id == content_item.creator_id)
                .first()
            )
            if creator:
                team_members.append(
                    {
                        "user_id": creator.id,
                        "name": creator.full_name,
                        "email": creator.email,
                        "role": "Creator",
                        "avatar_url": creator.avatar_url,
                    }
                )

            # Add assignees
            assignments = (
                self.db.query(Assignment)
                .filter(Assignment.content_item_id == content_id)
                .all()
            )

            for assignment in assignments:
                user = (
                    self.db.query(User)
                    .filter(User.id == assignment.assignee_id)
                    .first()
                )
                if user:
                    team_members.append(
                        {
                            "user_id": user.id,
                            "name": user.full_name,
                            "email": user.email,
                            "role": assignment.role or "Contributor",
                            "avatar_url": user.avatar_url,
                        }
                    )

            logger.info(f"Retrieved {len(team_members)} team members for content {content_id}")
            return team_members

        except Exception as e:
            logger.error(f"Error getting team members: {e}")
            raise

    def get_user_activity(
        self,
        content_id: int,
        days: int = 7,
    ) -> list[dict]:
        """
        Get recent user activity on content.

        Args:
            content_id: Content ID
            days: Number of days to look back

        Returns:
            List of activity records
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            activity = []

            # Get comments
            comments = (
                self.db.query(DBComment)
                .filter(
                    and_(
                        DBComment.content_item_id == content_id,
                        DBComment.created_at >= since_date,
                    )
                )
                .all()
            )

            for comment in comments:
                user = self.db.query(User).filter(User.id == comment.author_id).first()
                activity.append(
                    {
                        "type": "comment",
                        "user_id": comment.author_id,
                        "user_name": user.full_name if user else "Unknown",
                        "description": f"Added comment: {comment.content[:50]}...",
                        "timestamp": comment.created_at,
                    }
                )

            # Get versions
            versions = (
                self.db.query(ContentVersion)
                .filter(
                    and_(
                        ContentVersion.content_item_id == content_id,
                        ContentVersion.created_at >= since_date,
                    )
                )
                .all()
            )

            for version in versions:
                user = self.db.query(User).filter(User.id == version.created_by).first()
                activity.append(
                    {
                        "type": "version",
                        "user_id": version.created_by,
                        "user_name": user.full_name if user else "Unknown",
                        "description": f"Created version {version.version_number}",
                        "timestamp": version.created_at,
                    }
                )

            # Sort by timestamp
            activity.sort(key=lambda x: x["timestamp"], reverse=True)

            logger.info(f"Retrieved {len(activity)} activity records for content {content_id}")
            return activity

        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            raise

    def mention_user(
        self,
        content_id: int,
        mentioned_user_id: int,
        author_id: int,
        comment_id: int,
    ) -> bool:
        """
        Handle user mention in comment.

        Args:
            content_id: Content ID
            mentioned_user_id: User being mentioned
            author_id: User who mentioned
            comment_id: Comment ID with mention

        Returns:
            True if notification sent
        """
        try:
            # In production, this would send a notification
            logger.info(
                f"User {mentioned_user_id} mentioned in comment {comment_id} by user {author_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Error handling mention: {e}")
            return False
