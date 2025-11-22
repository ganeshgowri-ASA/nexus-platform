"""
Wiki Comments Service

Discussion and commenting system for wiki pages including threaded replies,
mentions, reactions, comment resolution, and notification triggers.

Author: NEXUS Platform Team
"""

import re
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from modules.wiki.models import WikiPage, WikiComment
from modules.wiki.wiki_types import NotificationType

logger = get_logger(__name__)


class CommentService:
    """Manages comments and discussions on wiki pages."""

    def __init__(self, db: Session):
        """
        Initialize CommentService.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_comment(
        self,
        page_id: int,
        author_id: int,
        content: str,
        parent_comment_id: Optional[int] = None
    ) -> Optional[WikiComment]:
        """
        Create a new comment on a wiki page.

        Args:
            page_id: ID of the page to comment on
            author_id: ID of the user creating the comment
            content: Comment content (markdown supported)
            parent_comment_id: ID of parent comment for threaded replies

        Returns:
            Created WikiComment instance or None if failed

        Raises:
            ValueError: If page not found or parent comment invalid
            SQLAlchemyError: If database operation fails

        Example:
            >>> service = CommentService(db)
            >>> comment = service.create_comment(
            ...     page_id=123,
            ...     author_id=1,
            ...     content="Great article! @john what do you think?"
            ... )
        """
        try:
            # Verify page exists and is not deleted
            page = self.db.query(WikiPage).filter(
                WikiPage.id == page_id,
                WikiPage.is_deleted == False
            ).first()

            if not page:
                raise ValueError(f"Page {page_id} not found")

            # Verify parent comment if specified
            if parent_comment_id:
                parent = self.get_comment(parent_comment_id)
                if not parent or parent.page_id != page_id:
                    raise ValueError(f"Invalid parent comment {parent_comment_id}")

            # Extract mentions from content
            mentions = self._extract_mentions(content)

            # Create comment
            comment = WikiComment(
                page_id=page_id,
                parent_comment_id=parent_comment_id,
                author_id=author_id,
                content=content,
                mentions=mentions,
                reactions={},
                is_resolved=False,
                is_deleted=False
            )

            self.db.add(comment)

            # Update page comment count
            page.comment_count += 1

            self.db.commit()
            self.db.refresh(comment)

            # Trigger notifications for mentions
            if mentions:
                self._trigger_mention_notifications(comment, mentions)

            # Trigger notification for page author
            if page.author_id != author_id:
                self._trigger_comment_notification(comment, page.author_id)

            logger.info(f"Created comment {comment.id} on page {page_id} by user {author_id}")
            return comment

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error creating comment: {str(e)}")
            raise

    def get_comment(
        self,
        comment_id: int,
        include_deleted: bool = False
    ) -> Optional[WikiComment]:
        """
        Get a comment by ID.

        Args:
            comment_id: ID of the comment
            include_deleted: Include deleted comments

        Returns:
            WikiComment instance or None if not found

        Example:
            >>> comment = service.get_comment(456)
        """
        try:
            query = self.db.query(WikiComment).filter(
                WikiComment.id == comment_id
            )

            if not include_deleted:
                query = query.filter(WikiComment.is_deleted == False)

            return query.first()

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving comment {comment_id}: {str(e)}")
            return None

    def get_page_comments(
        self,
        page_id: int,
        include_replies: bool = True,
        only_resolved: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WikiComment]:
        """
        Get comments for a page.

        Args:
            page_id: ID of the page
            include_replies: Include nested replies
            only_resolved: Filter by resolution status (None = all)
            limit: Maximum number of comments to return
            offset: Number of comments to skip

        Returns:
            List of WikiComment instances

        Example:
            >>> comments = service.get_page_comments(123, only_resolved=False)
        """
        try:
            query = self.db.query(WikiComment).filter(
                WikiComment.page_id == page_id,
                WikiComment.is_deleted == False
            )

            if not include_replies:
                query = query.filter(WikiComment.parent_comment_id.is_(None))

            if only_resolved is not None:
                query = query.filter(WikiComment.is_resolved == only_resolved)

            query = query.order_by(WikiComment.created_at.desc())
            query = query.limit(limit).offset(offset)

            comments = query.all()

            # Build threaded structure if including replies
            if include_replies:
                return self._build_comment_tree(comments, page_id)

            return comments

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving comments for page {page_id}: {str(e)}")
            return []

    def get_comment_thread(self, comment_id: int) -> List[WikiComment]:
        """
        Get full comment thread including parent and all replies.

        Args:
            comment_id: ID of any comment in the thread

        Returns:
            List of comments in the thread

        Example:
            >>> thread = service.get_comment_thread(456)
        """
        try:
            comment = self.get_comment(comment_id)
            if not comment:
                return []

            # Find root comment
            root_id = comment_id
            current = comment
            while current.parent_comment_id:
                current = self.get_comment(current.parent_comment_id)
                if current:
                    root_id = current.id
                else:
                    break

            # Get all replies recursively
            thread = []
            self._collect_replies(root_id, thread)

            return thread

        except Exception as e:
            logger.error(f"Error getting comment thread: {str(e)}")
            return []

    def update_comment(
        self,
        comment_id: int,
        user_id: int,
        content: str
    ) -> Optional[WikiComment]:
        """
        Update comment content.

        Args:
            comment_id: ID of the comment to update
            user_id: ID of user performing update (must be author)
            content: New comment content

        Returns:
            Updated WikiComment instance or None if failed

        Raises:
            ValueError: If user is not comment author

        Example:
            >>> comment = service.update_comment(
            ...     comment_id=456,
            ...     user_id=1,
            ...     content="Updated comment text"
            ... )
        """
        try:
            comment = self.get_comment(comment_id)
            if not comment:
                logger.warning(f"Comment {comment_id} not found")
                return None

            if comment.author_id != user_id:
                raise ValueError("Only comment author can update comment")

            # Extract new mentions
            mentions = self._extract_mentions(content)

            # Update comment
            comment.content = content
            comment.mentions = mentions
            comment.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(comment)

            # Trigger notifications for new mentions
            if mentions:
                self._trigger_mention_notifications(comment, mentions)

            logger.info(f"Updated comment {comment_id}")
            return comment

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error updating comment {comment_id}: {str(e)}")
            raise

    def delete_comment(
        self,
        comment_id: int,
        user_id: int,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a comment (soft delete by default).

        Args:
            comment_id: ID of the comment to delete
            user_id: ID of user performing deletion
            hard_delete: Permanently delete (True) or soft delete (False)

        Returns:
            True if successful, False otherwise

        Example:
            >>> success = service.delete_comment(456, user_id=1)
        """
        try:
            comment = self.get_comment(comment_id, include_deleted=True)
            if not comment:
                return False

            # Only author or admin can delete
            # TODO: Add admin check when permissions are implemented

            if hard_delete:
                # Delete all replies first
                self._delete_replies(comment_id)

                # Delete comment
                self.db.delete(comment)

                # Update page comment count
                page = self.db.query(WikiPage).filter(
                    WikiPage.id == comment.page_id
                ).first()
                if page:
                    page.comment_count = max(0, page.comment_count - 1)

                logger.warning(f"Hard deleted comment {comment_id}")
            else:
                # Soft delete
                comment.is_deleted = True
                comment.updated_at = datetime.utcnow()
                logger.info(f"Soft deleted comment {comment_id}")

            self.db.commit()
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error deleting comment {comment_id}: {str(e)}")
            return False

    def add_reaction(
        self,
        comment_id: int,
        user_id: int,
        reaction: str
    ) -> Optional[WikiComment]:
        """
        Add a reaction to a comment.

        Args:
            comment_id: ID of the comment
            user_id: ID of user adding reaction
            reaction: Reaction emoji (e.g., '👍', '❤️', '😄')

        Returns:
            Updated WikiComment instance or None if failed

        Example:
            >>> comment = service.add_reaction(456, user_id=1, reaction='👍')
        """
        try:
            comment = self.get_comment(comment_id)
            if not comment:
                return None

            # Initialize reactions dict if needed
            if not comment.reactions:
                comment.reactions = {}

            # Add user to reaction list
            if reaction not in comment.reactions:
                comment.reactions[reaction] = []

            if user_id not in comment.reactions[reaction]:
                comment.reactions[reaction].append(user_id)
                # Mark the object as modified for JSONB update
                self.db.query(WikiComment).filter(
                    WikiComment.id == comment_id
                ).update(
                    {'reactions': comment.reactions},
                    synchronize_session=False
                )

            self.db.commit()
            self.db.refresh(comment)

            logger.info(f"Added reaction '{reaction}' to comment {comment_id}")
            return comment

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error adding reaction: {str(e)}")
            return None

    def remove_reaction(
        self,
        comment_id: int,
        user_id: int,
        reaction: str
    ) -> Optional[WikiComment]:
        """
        Remove a reaction from a comment.

        Args:
            comment_id: ID of the comment
            user_id: ID of user removing reaction
            reaction: Reaction emoji to remove

        Returns:
            Updated WikiComment instance or None if failed

        Example:
            >>> comment = service.remove_reaction(456, user_id=1, reaction='👍')
        """
        try:
            comment = self.get_comment(comment_id)
            if not comment or not comment.reactions:
                return None

            if reaction in comment.reactions and user_id in comment.reactions[reaction]:
                comment.reactions[reaction].remove(user_id)

                # Remove reaction key if no users left
                if not comment.reactions[reaction]:
                    del comment.reactions[reaction]

                # Update database
                self.db.query(WikiComment).filter(
                    WikiComment.id == comment_id
                ).update(
                    {'reactions': comment.reactions},
                    synchronize_session=False
                )

                self.db.commit()
                self.db.refresh(comment)

            return comment

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error removing reaction: {str(e)}")
            return None

    def resolve_comment(
        self,
        comment_id: int,
        user_id: int,
        resolved: bool = True
    ) -> Optional[WikiComment]:
        """
        Mark a comment as resolved or unresolved.

        Args:
            comment_id: ID of the comment
            user_id: ID of user resolving the comment
            resolved: True to resolve, False to unresolve

        Returns:
            Updated WikiComment instance or None if failed

        Example:
            >>> comment = service.resolve_comment(456, user_id=1, resolved=True)
        """
        try:
            comment = self.get_comment(comment_id)
            if not comment:
                return None

            comment.is_resolved = resolved
            comment.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(comment)

            logger.info(f"{'Resolved' if resolved else 'Unresolved'} comment {comment_id}")
            return comment

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error resolving comment: {str(e)}")
            return None

    def get_user_comments(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[WikiComment]:
        """
        Get all comments by a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of comments
            offset: Number to skip

        Returns:
            List of WikiComment instances

        Example:
            >>> comments = service.get_user_comments(user_id=1, limit=10)
        """
        try:
            comments = self.db.query(WikiComment).filter(
                WikiComment.author_id == user_id,
                WikiComment.is_deleted == False
            ).order_by(
                WikiComment.created_at.desc()
            ).limit(limit).offset(offset).all()

            return comments

        except SQLAlchemyError as e:
            logger.error(f"Error getting user comments: {str(e)}")
            return []

    def get_comment_statistics(self, page_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comment statistics.

        Args:
            page_id: Optional page ID to get stats for specific page

        Returns:
            Dictionary with comment statistics

        Example:
            >>> stats = service.get_comment_statistics(page_id=123)
            >>> print(f"Total comments: {stats['total_comments']}")
        """
        try:
            query = self.db.query(WikiComment).filter(
                WikiComment.is_deleted == False
            )

            if page_id:
                query = query.filter(WikiComment.page_id == page_id)

            total_comments = query.count()

            # Count by resolution status
            resolved_count = query.filter(WikiComment.is_resolved == True).count()
            unresolved_count = total_comments - resolved_count

            # Count threaded vs top-level
            threaded_count = query.filter(
                WikiComment.parent_comment_id.isnot(None)
            ).count()
            top_level_count = total_comments - threaded_count

            # Get most active commenters
            top_commenters = self.db.query(
                WikiComment.author_id,
                func.count(WikiComment.id).label('comment_count')
            ).filter(
                WikiComment.is_deleted == False
            ).group_by(
                WikiComment.author_id
            ).order_by(
                func.count(WikiComment.id).desc()
            ).limit(10).all()

            return {
                'total_comments': total_comments,
                'resolved_comments': resolved_count,
                'unresolved_comments': unresolved_count,
                'threaded_replies': threaded_count,
                'top_level_comments': top_level_count,
                'top_commenters': [
                    {'user_id': user_id, 'count': count}
                    for user_id, count in top_commenters
                ]
            }

        except Exception as e:
            logger.error(f"Error getting comment statistics: {str(e)}")
            return {}

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _extract_mentions(self, content: str) -> List[int]:
        """
        Extract user mentions from comment content.

        Mentions are in format @username or @user:123 where 123 is user ID.
        """
        mentions = []

        # Pattern for @user:123 format
        id_pattern = r'@user:(\d+)'
        for match in re.finditer(id_pattern, content):
            user_id = int(match.group(1))
            if user_id not in mentions:
                mentions.append(user_id)

        # TODO: For @username format, implement user lookup by username
        # This requires access to user service/model

        return mentions

    def _build_comment_tree(
        self,
        comments: List[WikiComment],
        page_id: int
    ) -> List[WikiComment]:
        """Build threaded comment tree structure."""
        # Get all comments for the page
        all_comments = self.db.query(WikiComment).filter(
            WikiComment.page_id == page_id,
            WikiComment.is_deleted == False
        ).order_by(WikiComment.created_at.asc()).all()

        # Build lookup dictionary
        comment_dict = {c.id: c for c in all_comments}

        # Build tree
        root_comments = []
        for comment in all_comments:
            if comment.parent_comment_id is None:
                root_comments.append(comment)

        return root_comments

    def _collect_replies(self, comment_id: int, result: List[WikiComment]) -> None:
        """Recursively collect all replies to a comment."""
        comment = self.get_comment(comment_id)
        if comment:
            result.append(comment)

            # Get direct replies
            replies = self.db.query(WikiComment).filter(
                WikiComment.parent_comment_id == comment_id,
                WikiComment.is_deleted == False
            ).all()

            for reply in replies:
                self._collect_replies(reply.id, result)

    def _delete_replies(self, comment_id: int) -> None:
        """Recursively delete all replies to a comment."""
        replies = self.db.query(WikiComment).filter(
            WikiComment.parent_comment_id == comment_id
        ).all()

        for reply in replies:
            self._delete_replies(reply.id)
            self.db.delete(reply)

    def _trigger_mention_notifications(
        self,
        comment: WikiComment,
        mentioned_user_ids: List[int]
    ) -> None:
        """
        Trigger notifications for mentioned users.

        In production, integrate with notification service.
        """
        for user_id in mentioned_user_ids:
            logger.info(
                f"Triggering mention notification for user {user_id} "
                f"in comment {comment.id}"
            )
            # TODO: Integrate with notification service
            # notification_service.send_notification(
            #     user_id=user_id,
            #     type=NotificationType.MENTION,
            #     data={'comment_id': comment.id, 'page_id': comment.page_id}
            # )

    def _trigger_comment_notification(
        self,
        comment: WikiComment,
        recipient_user_id: int
    ) -> None:
        """
        Trigger notification for new comment.

        In production, integrate with notification service.
        """
        logger.info(
            f"Triggering comment notification for user {recipient_user_id} "
            f"on page {comment.page_id}"
        )
        # TODO: Integrate with notification service
