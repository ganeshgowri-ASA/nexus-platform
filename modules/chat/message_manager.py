"""
Message Manager - Handles all message CRUD operations.

Manages message creation, retrieval, updates, deletion, and querying.
Supports pagination, filtering, and message history.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from .models import (
    Message, SendMessageRequest, MessageType, MessageStatus,
    MessageWithReactions
)

logger = logging.getLogger(__name__)


class MessageManager:
    """
    Manages all message operations.

    Handles:
    - Message creation
    - Message retrieval
    - Message updates/edits
    - Message deletion (soft and hard)
    - Message history and pagination
    - Message status updates

    Example:
        >>> manager = MessageManager(engine)
        >>> message = await manager.create_message(user_id, request)
        >>> messages = await manager.get_messages(channel_id, limit=50)
    """

    def __init__(self, engine):
        """
        Initialize message manager.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine
        self._message_cache: Dict[UUID, Message] = {}
        logger.info("MessageManager initialized")

    async def create_message(
        self,
        user_id: UUID,
        request: SendMessageRequest
    ) -> Message:
        """
        Create a new message.

        Args:
            user_id: ID of the user sending the message
            request: Message creation request

        Returns:
            Created Message object

        Raises:
            ValueError: If request is invalid
        """
        # Validate content
        if not request.content.strip() and not request.attachments:
            raise ValueError("Message must have content or attachments")

        # Create message object
        message = Message(
            id=uuid4(),
            channel_id=request.channel_id,
            user_id=user_id,
            content=request.content,
            message_type=request.message_type,
            status=MessageStatus.SENT,
            parent_id=request.parent_id,
            mentions=request.mentions,
            attachments=request.attachments,
            created_at=datetime.utcnow()
        )

        # In production, save to database
        # await self._save_to_db(message)

        # Cache the message
        self._message_cache[message.id] = message

        # Update thread count if reply
        if message.parent_id:
            await self._increment_thread_count(message.parent_id)

        logger.info(f"Message {message.id} created by user {user_id}")
        return message

    async def get_message(self, message_id: UUID) -> Optional[Message]:
        """
        Get a message by ID.

        Args:
            message_id: ID of the message

        Returns:
            Message object or None if not found
        """
        # Check cache first
        if message_id in self._message_cache:
            return self._message_cache[message_id]

        # In production, query from database
        # message = await self._fetch_from_db(message_id)

        return None

    async def get_messages(
        self,
        channel_id: UUID,
        limit: int = 50,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
        user_id: Optional[UUID] = None,
        message_type: Optional[MessageType] = None
    ) -> List[Message]:
        """
        Get messages from a channel.

        Args:
            channel_id: ID of the channel
            limit: Maximum number of messages (default 50)
            before: Get messages before this timestamp
            after: Get messages after this timestamp
            user_id: Filter by user ID
            message_type: Filter by message type

        Returns:
            List of Message objects
        """
        # In production, query from database with filters
        messages = [
            msg for msg in self._message_cache.values()
            if msg.channel_id == channel_id and not msg.deleted_at
        ]

        # Apply filters
        if user_id:
            messages = [msg for msg in messages if msg.user_id == user_id]

        if message_type:
            messages = [msg for msg in messages if msg.message_type == message_type]

        if before:
            messages = [msg for msg in messages if msg.created_at < before]

        if after:
            messages = [msg for msg in messages if msg.created_at > after]

        # Sort by created_at descending
        messages.sort(key=lambda x: x.created_at, reverse=True)

        # Apply limit
        messages = messages[:limit]

        logger.debug(f"Retrieved {len(messages)} messages from channel {channel_id}")
        return messages

    async def update_message(
        self,
        message_id: UUID,
        user_id: UUID,
        content: str,
        **kwargs
    ) -> Message:
        """
        Update/edit a message.

        Args:
            message_id: ID of the message to update
            user_id: ID of the user updating (must be owner)
            content: New content
            **kwargs: Additional fields to update

        Returns:
            Updated Message object

        Raises:
            ValueError: If message not found
            PermissionError: If user doesn't own the message
        """
        message = await self.get_message(message_id)

        if not message:
            raise ValueError(f"Message {message_id} not found")

        if message.user_id != user_id:
            raise PermissionError("You can only edit your own messages")

        # Update fields
        message.content = content
        message.is_edited = True
        message.updated_at = datetime.utcnow()

        for key, value in kwargs.items():
            if hasattr(message, key):
                setattr(message, key, value)

        # In production, update in database
        # await self._update_in_db(message)

        # Update cache
        self._message_cache[message_id] = message

        logger.info(f"Message {message_id} updated by user {user_id}")
        return message

    async def delete_message(
        self,
        message_id: UUID,
        user_id: UUID,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a message.

        Args:
            message_id: ID of the message
            user_id: ID of the user deleting (must be owner or admin)
            hard_delete: If True, permanently delete; otherwise soft delete

        Returns:
            True if successful

        Raises:
            ValueError: If message not found
            PermissionError: If user doesn't have permission
        """
        message = await self.get_message(message_id)

        if not message:
            raise ValueError(f"Message {message_id} not found")

        if message.user_id != user_id:
            # In production, check if user is admin
            raise PermissionError("You can only delete your own messages")

        if hard_delete:
            # In production, delete from database
            # await self._delete_from_db(message_id)

            # Remove from cache
            self._message_cache.pop(message_id, None)
        else:
            # Soft delete
            message.deleted_at = datetime.utcnow()
            message.content = "[deleted]"

            # In production, update in database
            # await self._update_in_db(message)

            # Update cache
            self._message_cache[message_id] = message

        logger.info(f"Message {message_id} deleted by user {user_id} (hard={hard_delete})")
        return True

    async def pin_message(
        self,
        message_id: UUID,
        user_id: UUID,
        pinned: bool = True
    ) -> Message:
        """
        Pin or unpin a message.

        Args:
            message_id: ID of the message
            user_id: ID of the user (must have permission)
            pinned: True to pin, False to unpin

        Returns:
            Updated Message object
        """
        message = await self.get_message(message_id)

        if not message:
            raise ValueError(f"Message {message_id} not found")

        message.is_pinned = pinned
        message.updated_at = datetime.utcnow()

        # In production, update in database
        # await self._update_in_db(message)

        self._message_cache[message_id] = message

        logger.info(f"Message {message_id} {'pinned' if pinned else 'unpinned'} by user {user_id}")
        return message

    async def get_pinned_messages(self, channel_id: UUID) -> List[Message]:
        """
        Get all pinned messages in a channel.

        Args:
            channel_id: ID of the channel

        Returns:
            List of pinned Message objects
        """
        # In production, query from database
        messages = [
            msg for msg in self._message_cache.values()
            if msg.channel_id == channel_id and msg.is_pinned and not msg.deleted_at
        ]

        messages.sort(key=lambda x: x.created_at, reverse=True)

        logger.debug(f"Retrieved {len(messages)} pinned messages from channel {channel_id}")
        return messages

    async def update_message_status(
        self,
        message_id: UUID,
        status: MessageStatus
    ) -> None:
        """
        Update message delivery status.

        Args:
            message_id: ID of the message
            status: New status
        """
        message = await self.get_message(message_id)

        if message:
            message.status = status
            self._message_cache[message_id] = message

            # In production, update in database
            # await self._update_status_in_db(message_id, status)

    async def mark_as_read(
        self,
        channel_id: UUID,
        user_id: UUID,
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Mark all messages in a channel as read for a user.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user
            timestamp: Mark messages read up to this time (default: now)
        """
        if not timestamp:
            timestamp = datetime.utcnow()

        # In production, update channel_members table
        # UPDATE channel_members SET last_read_at = timestamp
        # WHERE channel_id = channel_id AND user_id = user_id

        logger.debug(f"Marked messages as read for user {user_id} in channel {channel_id}")

    async def get_unread_count(
        self,
        channel_id: UUID,
        user_id: UUID
    ) -> int:
        """
        Get count of unread messages in a channel for a user.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user

        Returns:
            Count of unread messages
        """
        # In production, query from database
        # SELECT COUNT(*) FROM messages m
        # JOIN channel_members cm ON m.channel_id = cm.channel_id
        # WHERE m.channel_id = channel_id
        # AND cm.user_id = user_id
        # AND m.created_at > cm.last_read_at

        return 0

    async def get_message_with_reactions(
        self,
        message_id: UUID
    ) -> Optional[MessageWithReactions]:
        """
        Get a message with its reactions.

        Args:
            message_id: ID of the message

        Returns:
            MessageWithReactions object or None
        """
        message = await self.get_message(message_id)

        if not message:
            return None

        # Get reactions from reactions manager
        reactions = []
        # In production: reactions = await self.engine.reactions.get_message_reactions(message_id)

        # Create MessageWithReactions
        message_with_reactions = MessageWithReactions(
            **message.dict(),
            reactions=reactions
        )

        return message_with_reactions

    # Private helper methods
    async def _increment_thread_count(self, parent_id: UUID) -> None:
        """Increment thread count for a parent message."""
        parent = await self.get_message(parent_id)
        if parent:
            parent.thread_count += 1
            self._message_cache[parent_id] = parent

            # In production, update in database
            # UPDATE messages SET thread_count = thread_count + 1 WHERE id = parent_id

    async def _save_to_db(self, message: Message) -> None:
        """Save message to database (production implementation)."""
        pass

    async def _fetch_from_db(self, message_id: UUID) -> Optional[Message]:
        """Fetch message from database (production implementation)."""
        pass

    async def _update_in_db(self, message: Message) -> None:
        """Update message in database (production implementation)."""
        pass

    async def _delete_from_db(self, message_id: UUID) -> None:
        """Delete message from database (production implementation)."""
        pass
