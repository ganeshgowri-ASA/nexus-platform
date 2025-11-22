"""
Chat Handler

Handles real-time chat messages, typing indicators, and read receipts.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..events import (
    EventType,
    WebSocketEvent,
    ChatEvent,
    TypingEvent,
    ReadReceiptEvent,
)

logger = logging.getLogger(__name__)


class ChatHandler:
    """
    Handles chat-related WebSocket events:
    - Real-time chat messages
    - Typing indicators
    - Read receipts
    - Message editing and deletion
    - Delivery confirmations
    """

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager

        # Typing indicator management
        self.typing_users: Dict[str, Dict[str, datetime]] = defaultdict(
            dict
        )  # conversation_id -> {user_id: timestamp}
        self.typing_timeout = 5  # seconds

        # Message cache for quick access
        self.message_cache: Dict[str, ChatEvent] = {}  # message_id -> ChatEvent
        self.max_cache_size = 1000

        # Read receipts
        self.read_receipts: Dict[str, Dict[str, datetime]] = defaultdict(
            dict
        )  # message_id -> {user_id: timestamp}

        logger.info("ChatHandler initialized")

    async def handle_message(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """
        Handle incoming chat message

        Args:
            connection_id: Sender's connection ID
            user_id: Sender's user ID
            data: Message data
        """
        try:
            # Extract message data
            conversation_id = data.get("conversation_id")
            content = data.get("content")

            if not conversation_id or not content:
                logger.warning(
                    f"Missing conversation_id or content in chat message from {user_id}"
                )
                return

            # Create chat event
            message_id = data.get("message_id", f"msg_{uuid.uuid4().hex[:16]}")
            chat_event = ChatEvent(
                message_id=message_id,
                conversation_id=conversation_id,
                sender_id=user_id,
                content=content,
                content_type=data.get("content_type", "text"),
                reply_to=data.get("reply_to"),
                mentions=data.get("mentions", []),
                attachments=data.get("attachments", []),
                metadata=data.get("metadata", {}),
            )

            # Cache message
            self._cache_message(message_id, chat_event)

            # Create WebSocket event
            ws_event = WebSocketEvent(
                event_type=EventType.CHAT_MESSAGE,
                sender_id=user_id,
                room_id=conversation_id,
                data=chat_event.dict(),
            )

            # Broadcast to conversation room
            sent_count = await self.connection_manager.broadcast_to_room(
                conversation_id, ws_event.dict()
            )

            logger.info(
                f"Chat message {message_id} sent to {sent_count} recipients "
                f"in conversation {conversation_id}"
            )

            # Send delivery confirmation to sender
            await self._send_delivery_confirmation(connection_id, message_id, sent_count)

            # Clear typing indicator for sender
            await self._clear_typing_indicator(user_id, conversation_id)

        except Exception as e:
            logger.error(f"Error handling chat message: {e}")

    async def handle_typing(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """
        Handle typing indicator

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Typing data
        """
        try:
            conversation_id = data.get("conversation_id")
            is_typing = data.get("is_typing", True)
            username = data.get("username", "Unknown")

            if not conversation_id:
                return

            # Update typing state
            if is_typing:
                self.typing_users[conversation_id][user_id] = datetime.utcnow()
            else:
                self.typing_users[conversation_id].pop(user_id, None)

            # Create typing event
            typing_event = TypingEvent(
                conversation_id=conversation_id,
                user_id=user_id,
                username=username,
                is_typing=is_typing,
            )

            # Create WebSocket event
            ws_event = WebSocketEvent(
                event_type=EventType.CHAT_TYPING,
                sender_id=user_id,
                room_id=conversation_id,
                data=typing_event.dict(),
            )

            # Broadcast to conversation room (exclude sender)
            await self.connection_manager.broadcast_to_room(
                conversation_id, ws_event.dict(), exclude={connection_id}
            )

            logger.debug(
                f"Typing indicator from {user_id} in {conversation_id}: {is_typing}"
            )

        except Exception as e:
            logger.error(f"Error handling typing indicator: {e}")

    async def handle_read_receipt(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """
        Handle read receipt

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Read receipt data
        """
        try:
            conversation_id = data.get("conversation_id")
            message_id = data.get("message_id")

            if not conversation_id or not message_id:
                return

            # Record read receipt
            read_at = datetime.utcnow()
            self.read_receipts[message_id][user_id] = read_at

            # Create read receipt event
            receipt_event = ReadReceiptEvent(
                conversation_id=conversation_id,
                message_id=message_id,
                user_id=user_id,
                read_at=read_at,
            )

            # Create WebSocket event
            ws_event = WebSocketEvent(
                event_type=EventType.CHAT_READ,
                sender_id=user_id,
                room_id=conversation_id,
                data=receipt_event.dict(),
            )

            # Broadcast to conversation room
            await self.connection_manager.broadcast_to_room(
                conversation_id, ws_event.dict()
            )

            logger.debug(f"Read receipt for message {message_id} from {user_id}")

        except Exception as e:
            logger.error(f"Error handling read receipt: {e}")

    async def handle_edit(self, connection_id: str, user_id: str, data: Dict[str, Any]):
        """
        Handle message edit

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Edit data
        """
        try:
            conversation_id = data.get("conversation_id")
            message_id = data.get("message_id")
            new_content = data.get("content")

            if not all([conversation_id, message_id, new_content]):
                return

            # Update cached message
            cached_message = self.message_cache.get(message_id)
            if cached_message and cached_message.sender_id == user_id:
                cached_message.content = new_content
                cached_message.edited = True

            # Create WebSocket event
            ws_event = WebSocketEvent(
                event_type=EventType.CHAT_EDIT,
                sender_id=user_id,
                room_id=conversation_id,
                data={
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "content": new_content,
                    "edited_at": datetime.utcnow().isoformat(),
                },
            )

            # Broadcast to conversation room
            await self.connection_manager.broadcast_to_room(
                conversation_id, ws_event.dict()
            )

            logger.info(f"Message {message_id} edited by {user_id}")

        except Exception as e:
            logger.error(f"Error handling message edit: {e}")

    async def handle_delete(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """
        Handle message deletion

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Delete data
        """
        try:
            conversation_id = data.get("conversation_id")
            message_id = data.get("message_id")

            if not conversation_id or not message_id:
                return

            # Update cached message
            cached_message = self.message_cache.get(message_id)
            if cached_message and cached_message.sender_id == user_id:
                cached_message.deleted = True

            # Create WebSocket event
            ws_event = WebSocketEvent(
                event_type=EventType.CHAT_DELETE,
                sender_id=user_id,
                room_id=conversation_id,
                data={
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                },
            )

            # Broadcast to conversation room
            await self.connection_manager.broadcast_to_room(
                conversation_id, ws_event.dict()
            )

            logger.info(f"Message {message_id} deleted by {user_id}")

        except Exception as e:
            logger.error(f"Error handling message deletion: {e}")

    async def _send_delivery_confirmation(
        self, connection_id: str, message_id: str, recipient_count: int
    ):
        """Send delivery confirmation to sender"""
        ws_event = WebSocketEvent(
            event_type=EventType.CHAT_DELIVERED,
            sender_id="system",
            data={
                "message_id": message_id,
                "delivered_to": recipient_count,
                "delivered_at": datetime.utcnow().isoformat(),
            },
        )

        await self.connection_manager.send_to_connection(
            connection_id, ws_event.dict()
        )

    async def _clear_typing_indicator(self, user_id: str, conversation_id: str):
        """Clear typing indicator for user"""
        if conversation_id in self.typing_users:
            self.typing_users[conversation_id].pop(user_id, None)

    def _cache_message(self, message_id: str, chat_event: ChatEvent):
        """Cache message for quick access"""
        self.message_cache[message_id] = chat_event

        # Limit cache size
        if len(self.message_cache) > self.max_cache_size:
            # Remove oldest message (simple FIFO)
            oldest_key = next(iter(self.message_cache))
            del self.message_cache[oldest_key]

    async def cleanup_typing_indicators(self):
        """Remove stale typing indicators"""
        now = datetime.utcnow()
        timeout_delta = timedelta(seconds=self.typing_timeout)

        for conversation_id in list(self.typing_users.keys()):
            users_to_remove = []

            for user_id, timestamp in self.typing_users[conversation_id].items():
                if now - timestamp > timeout_delta:
                    users_to_remove.append(user_id)

            for user_id in users_to_remove:
                del self.typing_users[conversation_id][user_id]

                # Send typing stopped event
                typing_event = TypingEvent(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    username="Unknown",
                    is_typing=False,
                )

                ws_event = WebSocketEvent(
                    event_type=EventType.CHAT_TYPING,
                    sender_id=user_id,
                    room_id=conversation_id,
                    data=typing_event.dict(),
                )

                await self.connection_manager.broadcast_to_room(
                    conversation_id, ws_event.dict()
                )

    def get_typing_users(self, conversation_id: str) -> list:
        """Get list of users currently typing in a conversation"""
        return list(self.typing_users.get(conversation_id, {}).keys())

    def get_message_read_receipts(self, message_id: str) -> Dict[str, datetime]:
        """Get read receipts for a message"""
        return self.read_receipts.get(message_id, {})
