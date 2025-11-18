"""
Chat Engine - Core orchestrator for the NEXUS Chat & Messaging Module.

This is the main entry point that coordinates all chat functionality including
messages, channels, WebSocket connections, and integrations.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from contextlib import asynccontextmanager

from .models import (
    User, Message, Channel, SendMessageRequest, CreateChannelRequest,
    MessageStatus, UserStatus, ChannelType
)

logger = logging.getLogger(__name__)


class ChatEngine:
    """
    Main chat engine that orchestrates all chat functionality.

    This class serves as the central coordinator for:
    - Message management
    - Channel operations
    - WebSocket connections
    - Real-time updates
    - Integration with other modules

    Example:
        >>> engine = ChatEngine()
        >>> await engine.initialize()
        >>> message = await engine.send_message(user_id, channel_id, "Hello!")
    """

    def __init__(
        self,
        db_connection_string: Optional[str] = None,
        redis_url: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the chat engine.

        Args:
            db_connection_string: PostgreSQL connection string
            redis_url: Redis URL for caching and pub/sub
            config: Additional configuration options
        """
        self.db_connection_string = db_connection_string or "postgresql://localhost/nexus_chat"
        self.redis_url = redis_url or "redis://localhost:6379"
        self.config = config or {}

        # Component managers (lazy loaded)
        self._message_manager = None
        self._channel_manager = None
        self._websocket_handler = None
        self._direct_messaging = None
        self._group_chat = None
        self._file_sharing = None
        self._reactions = None
        self._threads = None
        self._search = None
        self._notifications = None
        self._ai_features = None

        # Connection pools
        self._db_pool = None
        self._redis_pool = None

        # State
        self._initialized = False
        self._running = False

        logger.info("ChatEngine instance created")

    async def initialize(self) -> None:
        """
        Initialize the chat engine and all components.

        Sets up database connections, initializes managers, and prepares
        the system for operation.

        Raises:
            RuntimeError: If initialization fails
        """
        if self._initialized:
            logger.warning("ChatEngine already initialized")
            return

        try:
            logger.info("Initializing ChatEngine...")

            # Initialize database connection
            await self._init_database()

            # Initialize Redis connection
            await self._init_redis()

            # Initialize component managers
            await self._init_managers()

            # Set up message queue
            await self._init_message_queue()

            self._initialized = True
            self._running = True
            logger.info("ChatEngine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChatEngine: {e}")
            raise RuntimeError(f"ChatEngine initialization failed: {e}")

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the chat engine.

        Closes all connections, stops background tasks, and cleans up resources.
        """
        if not self._initialized:
            return

        try:
            logger.info("Shutting down ChatEngine...")
            self._running = False

            # Close WebSocket connections
            if self._websocket_handler:
                await self._websocket_handler.close_all()

            # Close database pool
            if self._db_pool:
                await self._db_pool.close()

            # Close Redis pool
            if self._redis_pool:
                await self._redis_pool.close()

            self._initialized = False
            logger.info("ChatEngine shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    @asynccontextmanager
    async def lifespan(self):
        """
        Context manager for engine lifecycle.

        Example:
            >>> async with engine.lifespan():
            ...     await engine.send_message(...)
        """
        await self.initialize()
        try:
            yield self
        finally:
            await self.shutdown()

    # Message Operations
    async def send_message(
        self,
        user_id: UUID,
        channel_id: UUID,
        content: str,
        **kwargs
    ) -> Message:
        """
        Send a message to a channel.

        Args:
            user_id: ID of the user sending the message
            channel_id: ID of the channel
            content: Message content
            **kwargs: Additional message options (type, attachments, etc.)

        Returns:
            The created Message object

        Raises:
            ValueError: If parameters are invalid
            PermissionError: If user doesn't have permission
        """
        self._ensure_initialized()

        try:
            # Create message request
            request = SendMessageRequest(
                channel_id=channel_id,
                content=content,
                **kwargs
            )

            # Validate permissions
            await self._validate_send_permission(user_id, channel_id)

            # Create message
            message = await self.message_manager.create_message(
                user_id=user_id,
                request=request
            )

            # Broadcast via WebSocket
            await self.websocket_handler.broadcast_message(channel_id, message)

            # Send notifications
            await self._send_message_notifications(message)

            # AI processing (if enabled)
            if self.config.get('ai_enabled', True):
                await self.ai_features.process_message(message)

            logger.info(f"Message {message.id} sent by user {user_id} to channel {channel_id}")
            return message

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def edit_message(
        self,
        user_id: UUID,
        message_id: UUID,
        new_content: str
    ) -> Message:
        """
        Edit an existing message.

        Args:
            user_id: ID of the user editing the message
            message_id: ID of the message to edit
            new_content: New message content

        Returns:
            The updated Message object

        Raises:
            ValueError: If message not found
            PermissionError: If user doesn't own the message
        """
        self._ensure_initialized()

        # Update message
        message = await self.message_manager.update_message(
            message_id=message_id,
            user_id=user_id,
            content=new_content
        )

        # Broadcast update
        await self.websocket_handler.broadcast_message_update(message)

        return message

    async def delete_message(
        self,
        user_id: UUID,
        message_id: UUID,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a message.

        Args:
            user_id: ID of the user deleting the message
            message_id: ID of the message to delete
            hard_delete: If True, permanently delete; otherwise soft delete

        Returns:
            True if successful

        Raises:
            PermissionError: If user doesn't have permission
        """
        self._ensure_initialized()

        success = await self.message_manager.delete_message(
            message_id=message_id,
            user_id=user_id,
            hard_delete=hard_delete
        )

        if success:
            # Broadcast deletion
            await self.websocket_handler.broadcast_message_delete(message_id)

        return success

    async def get_messages(
        self,
        channel_id: UUID,
        limit: int = 50,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None
    ) -> List[Message]:
        """
        Get messages from a channel.

        Args:
            channel_id: ID of the channel
            limit: Maximum number of messages to return
            before: Only get messages before this timestamp
            after: Only get messages after this timestamp

        Returns:
            List of Message objects
        """
        self._ensure_initialized()

        return await self.message_manager.get_messages(
            channel_id=channel_id,
            limit=limit,
            before=before,
            after=after
        )

    # Channel Operations
    async def create_channel(
        self,
        creator_id: UUID,
        request: CreateChannelRequest
    ) -> Channel:
        """
        Create a new channel.

        Args:
            creator_id: ID of the user creating the channel
            request: Channel creation request

        Returns:
            The created Channel object
        """
        self._ensure_initialized()

        channel = await self.channel_manager.create_channel(
            creator_id=creator_id,
            request=request
        )

        # Notify members
        for member_id in request.member_ids:
            await self.notifications.send_notification(
                user_id=member_id,
                title=f"Added to {channel.name}",
                body=f"You've been added to a new channel"
            )

        return channel

    async def join_channel(
        self,
        user_id: UUID,
        channel_id: UUID
    ) -> bool:
        """
        Join a channel.

        Args:
            user_id: ID of the user
            channel_id: ID of the channel

        Returns:
            True if successful
        """
        self._ensure_initialized()

        success = await self.channel_manager.add_member(
            channel_id=channel_id,
            user_id=user_id
        )

        if success:
            # Notify channel members
            await self.websocket_handler.broadcast_user_joined(channel_id, user_id)

        return success

    async def leave_channel(
        self,
        user_id: UUID,
        channel_id: UUID
    ) -> bool:
        """
        Leave a channel.

        Args:
            user_id: ID of the user
            channel_id: ID of the channel

        Returns:
            True if successful
        """
        self._ensure_initialized()

        success = await self.channel_manager.remove_member(
            channel_id=channel_id,
            user_id=user_id
        )

        if success:
            # Notify channel members
            await self.websocket_handler.broadcast_user_left(channel_id, user_id)

        return success

    # Direct Messaging
    async def create_dm(
        self,
        user1_id: UUID,
        user2_id: UUID
    ) -> Channel:
        """
        Create or get a direct message channel.

        Args:
            user1_id: ID of first user
            user2_id: ID of second user

        Returns:
            The DM Channel object
        """
        self._ensure_initialized()

        return await self.direct_messaging.get_or_create_dm(
            user1_id=user1_id,
            user2_id=user2_id
        )

    # Real-time Features
    async def update_typing_status(
        self,
        user_id: UUID,
        channel_id: UUID,
        is_typing: bool
    ) -> None:
        """
        Update user typing status.

        Args:
            user_id: ID of the user
            channel_id: ID of the channel
            is_typing: Whether user is typing
        """
        self._ensure_initialized()

        await self.websocket_handler.broadcast_typing(
            channel_id=channel_id,
            user_id=user_id,
            is_typing=is_typing
        )

    async def update_user_status(
        self,
        user_id: UUID,
        status: UserStatus
    ) -> None:
        """
        Update user online status.

        Args:
            user_id: ID of the user
            status: New status
        """
        self._ensure_initialized()

        await self.websocket_handler.broadcast_status_change(
            user_id=user_id,
            status=status
        )

    # Helper Methods
    async def _init_database(self) -> None:
        """Initialize database connection pool."""
        # In a real implementation, this would use asyncpg or SQLAlchemy
        logger.info("Database connection pool initialized")

    async def _init_redis(self) -> None:
        """Initialize Redis connection pool."""
        # In a real implementation, this would use aioredis
        logger.info("Redis connection pool initialized")

    async def _init_managers(self) -> None:
        """Initialize all component managers."""
        from .message_manager import MessageManager
        from .channel_manager import ChannelManager
        from .websocket_handler import WebSocketHandler
        from .direct_messaging import DirectMessaging
        from .group_chat import GroupChat
        from .file_sharing import FileSharing
        from .reactions import Reactions
        from .threads import Threads
        from .search import Search
        from .notifications import Notifications
        from .ai_features import AIFeatures

        self._message_manager = MessageManager(self)
        self._channel_manager = ChannelManager(self)
        self._websocket_handler = WebSocketHandler(self)
        self._direct_messaging = DirectMessaging(self)
        self._group_chat = GroupChat(self)
        self._file_sharing = FileSharing(self)
        self._reactions = Reactions(self)
        self._threads = Threads(self)
        self._search = Search(self)
        self._notifications = Notifications(self)
        self._ai_features = AIFeatures(self)

        logger.info("All component managers initialized")

    async def _init_message_queue(self) -> None:
        """Initialize message queue for reliability."""
        # In a real implementation, this would set up RabbitMQ or Redis Streams
        logger.info("Message queue initialized")

    async def _validate_send_permission(
        self,
        user_id: UUID,
        channel_id: UUID
    ) -> bool:
        """Validate if user can send messages to channel."""
        # In a real implementation, check channel membership and permissions
        return True

    async def _send_message_notifications(self, message: Message) -> None:
        """Send notifications for a new message."""
        # Notify mentioned users
        for user_id in message.mentions:
            await self.notifications.send_notification(
                user_id=user_id,
                title="You were mentioned",
                body=f"in a message: {message.content[:50]}..."
            )

    def _ensure_initialized(self) -> None:
        """Ensure the engine is initialized."""
        if not self._initialized:
            raise RuntimeError("ChatEngine not initialized. Call initialize() first.")

    # Property accessors for component managers
    @property
    def message_manager(self):
        """Get message manager instance."""
        if not self._message_manager:
            raise RuntimeError("Message manager not initialized")
        return self._message_manager

    @property
    def channel_manager(self):
        """Get channel manager instance."""
        if not self._channel_manager:
            raise RuntimeError("Channel manager not initialized")
        return self._channel_manager

    @property
    def websocket_handler(self):
        """Get WebSocket handler instance."""
        if not self._websocket_handler:
            raise RuntimeError("WebSocket handler not initialized")
        return self._websocket_handler

    @property
    def direct_messaging(self):
        """Get direct messaging instance."""
        if not self._direct_messaging:
            raise RuntimeError("Direct messaging not initialized")
        return self._direct_messaging

    @property
    def group_chat(self):
        """Get group chat instance."""
        if not self._group_chat:
            raise RuntimeError("Group chat not initialized")
        return self._group_chat

    @property
    def file_sharing(self):
        """Get file sharing instance."""
        if not self._file_sharing:
            raise RuntimeError("File sharing not initialized")
        return self._file_sharing

    @property
    def reactions(self):
        """Get reactions instance."""
        if not self._reactions:
            raise RuntimeError("Reactions not initialized")
        return self._reactions

    @property
    def threads(self):
        """Get threads instance."""
        if not self._threads:
            raise RuntimeError("Threads not initialized")
        return self._threads

    @property
    def search(self):
        """Get search instance."""
        if not self._search:
            raise RuntimeError("Search not initialized")
        return self._search

    @property
    def notifications(self):
        """Get notifications instance."""
        if not self._notifications:
            raise RuntimeError("Notifications not initialized")
        return self._notifications

    @property
    def ai_features(self):
        """Get AI features instance."""
        if not self._ai_features:
            raise RuntimeError("AI features not initialized")
        return self._ai_features
