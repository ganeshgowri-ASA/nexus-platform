"""
Threads - Handles message threading and replies.

Manages threaded conversations, reply tracking, and thread organization.
Supports nested discussions while keeping channels organized.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID, uuid4

from .models import Thread, Message

logger = logging.getLogger(__name__)


class Threads:
    """
    Manages message threads and replies.

    Handles:
    - Thread creation
    - Reply management
    - Thread participants
    - Thread notifications
    - Thread summaries

    Example:
        >>> threads = Threads(engine)
        >>> await threads.create_reply(parent_msg_id, user_id, "Reply text")
        >>> thread_msgs = await threads.get_thread_messages(parent_msg_id)
    """

    def __init__(self, engine):
        """
        Initialize threads manager.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine
        self._threads: Dict[UUID, Thread] = {}  # parent_message_id -> Thread
        logger.info("Threads initialized")

    async def create_reply(
        self,
        parent_message_id: UUID,
        user_id: UUID,
        content: str,
        **kwargs
    ) -> Message:
        """
        Create a reply in a thread.

        Args:
            parent_message_id: ID of the parent message
            user_id: ID of the user replying
            content: Reply content
            **kwargs: Additional message options

        Returns:
            Created reply Message object
        """
        # Get parent message
        parent = await self.engine.message_manager.get_message(parent_message_id)

        if not parent:
            raise ValueError(f"Parent message {parent_message_id} not found")

        # Create thread if it doesn't exist
        thread = await self._get_or_create_thread(parent_message_id, parent.channel_id)

        # Create reply message
        from .models import SendMessageRequest

        request = SendMessageRequest(
            channel_id=parent.channel_id,
            content=content,
            parent_id=parent_message_id,
            **kwargs
        )

        reply = await self.engine.message_manager.create_message(
            user_id=user_id,
            request=request
        )

        # Update thread
        thread.message_count += 1
        thread.last_reply_at = datetime.utcnow()

        if user_id not in thread.participant_ids:
            thread.participant_ids.append(user_id)

        self._threads[parent_message_id] = thread

        # In production: update thread in database
        # UPDATE threads SET message_count = ..., last_reply_at = ... WHERE parent_message_id = ...

        # Notify thread participants
        await self._notify_thread_participants(thread, reply, user_id)

        logger.info(f"Reply created in thread {parent_message_id} by user {user_id}")
        return reply

    async def get_thread_messages(
        self,
        parent_message_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """
        Get all messages in a thread.

        Args:
            parent_message_id: ID of the parent message
            limit: Maximum messages to return
            offset: Number of messages to skip

        Returns:
            List of Message objects in thread
        """
        # Get all replies
        messages = [
            msg for msg in self.engine.message_manager._message_cache.values()
            if msg.parent_id == parent_message_id and not msg.deleted_at
        ]

        # Sort by created_at ascending
        messages.sort(key=lambda x: x.created_at)

        # Apply pagination
        return messages[offset:offset + limit]

    async def get_thread_info(self, parent_message_id: UUID) -> Optional[Thread]:
        """
        Get thread information.

        Args:
            parent_message_id: ID of the parent message

        Returns:
            Thread object or None
        """
        return self._threads.get(parent_message_id)

    async def get_thread_count(self, parent_message_id: UUID) -> int:
        """
        Get number of replies in a thread.

        Args:
            parent_message_id: ID of the parent message

        Returns:
            Count of replies
        """
        thread = self._threads.get(parent_message_id)
        return thread.message_count if thread else 0

    async def get_thread_participants(
        self,
        parent_message_id: UUID
    ) -> List[UUID]:
        """
        Get all participants in a thread.

        Args:
            parent_message_id: ID of the parent message

        Returns:
            List of user IDs who participated
        """
        thread = self._threads.get(parent_message_id)
        return thread.participant_ids.copy() if thread else []

    async def mark_thread_read(
        self,
        parent_message_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Mark all messages in a thread as read.

        Args:
            parent_message_id: ID of the parent message
            user_id: ID of the user

        Returns:
            True if successful
        """
        # Get thread messages
        messages = await self.get_thread_messages(parent_message_id)

        # Mark each as read
        # In production: batch update
        # UPDATE messages SET is_read = TRUE
        # WHERE parent_id = parent_message_id AND user_id != user_id

        logger.info(f"Thread {parent_message_id} marked as read by user {user_id}")
        return True

    async def get_unread_thread_count(
        self,
        parent_message_id: UUID,
        user_id: UUID
    ) -> int:
        """
        Get count of unread messages in a thread.

        Args:
            parent_message_id: ID of the parent message
            user_id: ID of the user

        Returns:
            Count of unread messages
        """
        # In production: query from database with last_read_at
        # SELECT COUNT(*) FROM messages
        # WHERE parent_id = parent_message_id
        # AND created_at > (SELECT last_read_at FROM channel_members WHERE ...)

        return 0

    async def subscribe_to_thread(
        self,
        parent_message_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Subscribe to thread notifications.

        Args:
            parent_message_id: ID of the parent message
            user_id: ID of the user

        Returns:
            True if successful
        """
        thread = await self._get_or_create_thread(
            parent_message_id,
            # Need to get channel_id from parent message
            uuid4()  # placeholder
        )

        if user_id not in thread.participant_ids:
            thread.participant_ids.append(user_id)
            self._threads[parent_message_id] = thread

        logger.info(f"User {user_id} subscribed to thread {parent_message_id}")
        return True

    async def unsubscribe_from_thread(
        self,
        parent_message_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Unsubscribe from thread notifications.

        Args:
            parent_message_id: ID of the parent message
            user_id: ID of the user

        Returns:
            True if successful
        """
        thread = self._threads.get(parent_message_id)

        if thread and user_id in thread.participant_ids:
            thread.participant_ids.remove(user_id)
            self._threads[parent_message_id] = thread

        logger.info(f"User {user_id} unsubscribed from thread {parent_message_id}")
        return True

    async def get_active_threads(
        self,
        channel_id: UUID,
        limit: int = 20
    ) -> List[Thread]:
        """
        Get most active threads in a channel.

        Args:
            channel_id: ID of the channel
            limit: Maximum threads to return

        Returns:
            List of Thread objects sorted by activity
        """
        # Filter threads by channel
        threads = [
            t for t in self._threads.values()
            if t.channel_id == channel_id
        ]

        # Sort by last_reply_at descending
        threads.sort(
            key=lambda x: x.last_reply_at or x.created_at,
            reverse=True
        )

        return threads[:limit]

    async def get_user_threads(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> List[Thread]:
        """
        Get threads a user is participating in.

        Args:
            user_id: ID of the user
            limit: Maximum threads to return

        Returns:
            List of Thread objects
        """
        # Find threads where user is a participant
        threads = [
            t for t in self._threads.values()
            if user_id in t.participant_ids
        ]

        # Sort by last_reply_at descending
        threads.sort(
            key=lambda x: x.last_reply_at or x.created_at,
            reverse=True
        )

        return threads[:limit]

    async def delete_thread(
        self,
        parent_message_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a thread and all its replies.

        Args:
            parent_message_id: ID of the parent message
            user_id: ID of the user deleting (must have permission)

        Returns:
            True if successful
        """
        # Check permissions
        parent = await self.engine.message_manager.get_message(parent_message_id)

        if not parent:
            return False

        if parent.user_id != user_id:
            # In production: check if user is admin
            raise PermissionError("Only message author or admins can delete threads")

        # Delete all replies
        replies = await self.get_thread_messages(parent_message_id, limit=1000)

        for reply in replies:
            await self.engine.message_manager.delete_message(
                reply.id,
                user_id,
                hard_delete=True
            )

        # Remove thread
        self._threads.pop(parent_message_id, None)

        logger.info(f"Thread {parent_message_id} deleted by user {user_id}")
        return True

    # Private helper methods
    async def _get_or_create_thread(
        self,
        parent_message_id: UUID,
        channel_id: UUID
    ) -> Thread:
        """Get existing thread or create new one."""
        if parent_message_id in self._threads:
            return self._threads[parent_message_id]

        # Create new thread
        thread = Thread(
            id=uuid4(),
            parent_message_id=parent_message_id,
            channel_id=channel_id,
            message_count=0,
            participant_ids=[],
            created_at=datetime.utcnow()
        )

        self._threads[parent_message_id] = thread

        # In production: insert into database
        # INSERT INTO threads ...

        return thread

    async def _notify_thread_participants(
        self,
        thread: Thread,
        reply: Message,
        replier_id: UUID
    ) -> None:
        """Notify thread participants of new reply."""
        # Notify all participants except the replier
        for participant_id in thread.participant_ids:
            if participant_id != replier_id:
                await self.engine.notifications.send_notification(
                    user_id=participant_id,
                    title="New Reply in Thread",
                    body=f"New reply: {reply.content[:50]}..."
                )
