"""
WebSocket Handler - Real-time communication for NEXUS Chat.

Manages WebSocket connections, broadcasts messages, and handles real-time events
like typing indicators, presence updates, and message delivery.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from uuid import UUID
from datetime import datetime
from collections import defaultdict

from .models import (
    Message, WSMessage, WSTypingEvent, WSStatusEvent, WSReactionEvent,
    UserStatus
)

logger = logging.getLogger(__name__)


class WebSocketConnection:
    """Represents a single WebSocket connection."""

    def __init__(self, user_id: UUID, websocket):
        """
        Initialize WebSocket connection.

        Args:
            user_id: ID of the connected user
            websocket: WebSocket connection object
        """
        self.user_id = user_id
        self.websocket = websocket
        self.connected_at = datetime.utcnow()
        self.subscribed_channels: Set[UUID] = set()
        self.is_alive = True

    async def send(self, data: Dict[str, Any]) -> bool:
        """
        Send data through the WebSocket.

        Args:
            data: Data to send

        Returns:
            True if sent successfully
        """
        try:
            await self.websocket.send(json.dumps(data, default=str))
            return True
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            self.is_alive = False
            return False

    async def close(self) -> None:
        """Close the WebSocket connection."""
        try:
            await self.websocket.close()
            self.is_alive = False
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")


class WebSocketHandler:
    """
    Manages all WebSocket connections and real-time communications.

    Handles:
    - Connection lifecycle
    - Message broadcasting
    - Channel subscriptions
    - Typing indicators
    - Presence updates
    - Delivery receipts

    Example:
        >>> handler = WebSocketHandler(engine)
        >>> await handler.connect(user_id, websocket)
        >>> await handler.broadcast_message(channel_id, message)
    """

    def __init__(self, engine):
        """
        Initialize WebSocket handler.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine

        # Connection management
        self.connections: Dict[UUID, Set[WebSocketConnection]] = defaultdict(set)
        self.channel_subscriptions: Dict[UUID, Set[UUID]] = defaultdict(set)

        # Typing indicators cache
        self.typing_users: Dict[UUID, Set[UUID]] = defaultdict(set)

        # User presence
        self.user_status: Dict[UUID, UserStatus] = {}

        logger.info("WebSocketHandler initialized")

    async def connect(
        self,
        user_id: UUID,
        websocket,
        channels: Optional[list[UUID]] = None
    ) -> WebSocketConnection:
        """
        Register a new WebSocket connection.

        Args:
            user_id: ID of the connecting user
            websocket: WebSocket connection object
            channels: Optional list of channels to auto-subscribe

        Returns:
            WebSocketConnection object
        """
        connection = WebSocketConnection(user_id, websocket)
        self.connections[user_id].add(connection)

        # Auto-subscribe to channels
        if channels:
            for channel_id in channels:
                await self.subscribe_channel(connection, channel_id)

        # Update user status to online
        await self.update_user_status(user_id, UserStatus.ONLINE)

        logger.info(f"User {user_id} connected via WebSocket")
        return connection

    async def disconnect(self, connection: WebSocketConnection) -> None:
        """
        Handle WebSocket disconnection.

        Args:
            connection: WebSocketConnection to disconnect
        """
        user_id = connection.user_id

        # Remove from connections
        if user_id in self.connections:
            self.connections[user_id].discard(connection)
            if not self.connections[user_id]:
                del self.connections[user_id]
                # Update status to offline if no more connections
                await self.update_user_status(user_id, UserStatus.OFFLINE)

        # Remove from channel subscriptions
        for channel_id in connection.subscribed_channels:
            self.channel_subscriptions[channel_id].discard(user_id)

        await connection.close()
        logger.info(f"User {user_id} disconnected")

    async def subscribe_channel(
        self,
        connection: WebSocketConnection,
        channel_id: UUID
    ) -> None:
        """
        Subscribe a connection to a channel.

        Args:
            connection: WebSocketConnection to subscribe
            channel_id: ID of the channel
        """
        connection.subscribed_channels.add(channel_id)
        self.channel_subscriptions[channel_id].add(connection.user_id)
        logger.debug(f"User {connection.user_id} subscribed to channel {channel_id}")

    async def unsubscribe_channel(
        self,
        connection: WebSocketConnection,
        channel_id: UUID
    ) -> None:
        """
        Unsubscribe a connection from a channel.

        Args:
            connection: WebSocketConnection to unsubscribe
            channel_id: ID of the channel
        """
        connection.subscribed_channels.discard(channel_id)
        self.channel_subscriptions[channel_id].discard(connection.user_id)
        logger.debug(f"User {connection.user_id} unsubscribed from channel {channel_id}")

    async def broadcast_message(
        self,
        channel_id: UUID,
        message: Message
    ) -> None:
        """
        Broadcast a message to all users in a channel.

        Args:
            channel_id: ID of the channel
            message: Message to broadcast
        """
        ws_message = WSMessage(
            type="message",
            data=message.dict()
        )

        await self._broadcast_to_channel(channel_id, ws_message.dict())
        logger.debug(f"Broadcasted message {message.id} to channel {channel_id}")

    async def broadcast_message_update(self, message: Message) -> None:
        """
        Broadcast a message update/edit.

        Args:
            message: Updated message
        """
        ws_message = WSMessage(
            type="message_update",
            data=message.dict()
        )

        await self._broadcast_to_channel(message.channel_id, ws_message.dict())

    async def broadcast_message_delete(self, message_id: UUID) -> None:
        """
        Broadcast a message deletion.

        Args:
            message_id: ID of deleted message
        """
        # Note: We'd need to store channel_id with the message_id
        # This is a simplified version
        ws_message = WSMessage(
            type="message_delete",
            data={"message_id": str(message_id)}
        )

        # In practice, look up channel from message_id
        # await self._broadcast_to_channel(channel_id, ws_message.dict())

    async def broadcast_typing(
        self,
        channel_id: UUID,
        user_id: UUID,
        is_typing: bool
    ) -> None:
        """
        Broadcast typing indicator.

        Args:
            channel_id: ID of the channel
            user_id: ID of the typing user
            is_typing: Whether user is typing
        """
        # Update typing cache
        if is_typing:
            self.typing_users[channel_id].add(user_id)
        else:
            self.typing_users[channel_id].discard(user_id)

        # Get user info
        # In practice, fetch from database
        username = f"User-{user_id}"

        event = WSTypingEvent(
            channel_id=channel_id,
            user_id=user_id,
            username=username,
            is_typing=is_typing
        )

        ws_message = WSMessage(
            type="typing",
            data=event.dict()
        )

        await self._broadcast_to_channel(channel_id, ws_message.dict(), exclude=user_id)

    async def broadcast_status_change(
        self,
        user_id: UUID,
        status: UserStatus
    ) -> None:
        """
        Broadcast user status change.

        Args:
            user_id: ID of the user
            status: New status
        """
        self.user_status[user_id] = status

        event = WSStatusEvent(
            user_id=user_id,
            status=status,
            last_seen=datetime.utcnow() if status == UserStatus.OFFLINE else None
        )

        ws_message = WSMessage(
            type="status",
            data=event.dict()
        )

        # Broadcast to all connected users
        await self._broadcast_to_all(ws_message.dict())

    async def broadcast_reaction(
        self,
        message_id: UUID,
        user_id: UUID,
        emoji: str,
        action: str  # "add" or "remove"
    ) -> None:
        """
        Broadcast emoji reaction.

        Args:
            message_id: ID of the message
            user_id: ID of the user reacting
            emoji: Emoji character
            action: "add" or "remove"
        """
        event = WSReactionEvent(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
            action=action
        )

        ws_message = WSMessage(
            type="reaction",
            data=event.dict()
        )

        # In practice, get channel_id from message_id
        # await self._broadcast_to_channel(channel_id, ws_message.dict())

    async def broadcast_user_joined(
        self,
        channel_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Broadcast user joined channel event.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user who joined
        """
        ws_message = WSMessage(
            type="user_joined",
            data={"channel_id": str(channel_id), "user_id": str(user_id)}
        )

        await self._broadcast_to_channel(channel_id, ws_message.dict())

    async def broadcast_user_left(
        self,
        channel_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Broadcast user left channel event.

        Args:
            channel_id: ID of the channel
            user_id: ID of the user who left
        """
        ws_message = WSMessage(
            type="user_left",
            data={"channel_id": str(channel_id), "user_id": str(user_id)}
        )

        await self._broadcast_to_channel(channel_id, ws_message.dict())

    async def send_to_user(
        self,
        user_id: UUID,
        data: Dict[str, Any]
    ) -> None:
        """
        Send data to a specific user.

        Args:
            user_id: ID of the user
            data: Data to send
        """
        if user_id not in self.connections:
            logger.warning(f"User {user_id} not connected")
            return

        # Send to all user's connections
        for connection in list(self.connections[user_id]):
            if connection.is_alive:
                await connection.send(data)
            else:
                await self.disconnect(connection)

    async def update_user_status(
        self,
        user_id: UUID,
        status: UserStatus
    ) -> None:
        """
        Update and broadcast user status.

        Args:
            user_id: ID of the user
            status: New status
        """
        old_status = self.user_status.get(user_id)
        if old_status != status:
            await self.broadcast_status_change(user_id, status)

    async def get_online_users(self, channel_id: UUID) -> Set[UUID]:
        """
        Get list of online users in a channel.

        Args:
            channel_id: ID of the channel

        Returns:
            Set of online user IDs
        """
        channel_users = self.channel_subscriptions.get(channel_id, set())
        return {
            user_id for user_id in channel_users
            if self.user_status.get(user_id) == UserStatus.ONLINE
        }

    async def get_typing_users(self, channel_id: UUID) -> Set[UUID]:
        """
        Get list of users currently typing in a channel.

        Args:
            channel_id: ID of the channel

        Returns:
            Set of typing user IDs
        """
        return self.typing_users.get(channel_id, set()).copy()

    async def close_all(self) -> None:
        """Close all WebSocket connections."""
        logger.info("Closing all WebSocket connections...")

        for user_connections in list(self.connections.values()):
            for connection in list(user_connections):
                await self.disconnect(connection)

        self.connections.clear()
        self.channel_subscriptions.clear()
        self.typing_users.clear()
        self.user_status.clear()

        logger.info("All WebSocket connections closed")

    # Private helper methods
    async def _broadcast_to_channel(
        self,
        channel_id: UUID,
        data: Dict[str, Any],
        exclude: Optional[UUID] = None
    ) -> None:
        """
        Broadcast data to all users in a channel.

        Args:
            channel_id: ID of the channel
            data: Data to broadcast
            exclude: Optional user ID to exclude from broadcast
        """
        if channel_id not in self.channel_subscriptions:
            return

        user_ids = self.channel_subscriptions[channel_id]

        for user_id in user_ids:
            if exclude and user_id == exclude:
                continue

            await self.send_to_user(user_id, data)

    async def _broadcast_to_all(self, data: Dict[str, Any]) -> None:
        """
        Broadcast data to all connected users.

        Args:
            data: Data to broadcast
        """
        for user_id in list(self.connections.keys()):
            await self.send_to_user(user_id, data)
