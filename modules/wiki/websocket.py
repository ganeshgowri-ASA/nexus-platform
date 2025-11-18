"""
NEXUS Wiki System - WebSocket Handler

Real-time collaboration features including:
- Live page editing notifications
- Active user tracking
- Edit conflict detection
- Collaborative editing support
- Connection management
- Message broadcasting
- Event-based updates
- Presence indicators

Author: NEXUS Platform Team
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.utils import get_logger
from database import get_db
from modules.wiki.models import WikiPage
from modules.wiki.wiki_types import PageStatus

logger = get_logger(__name__)


# ============================================================================
# MESSAGE TYPES AND MODELS
# ============================================================================

class WSMessageType(str, Enum):
    """WebSocket message types."""
    # Connection
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"

    # Presence
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    ACTIVE_USERS = "active_users"
    USER_TYPING = "user_typing"
    USER_STOPPED_TYPING = "user_stopped_typing"

    # Editing
    PAGE_OPENED = "page_opened"
    PAGE_CLOSED = "page_closed"
    CONTENT_CHANGED = "content_changed"
    CURSOR_MOVED = "cursor_moved"
    SELECTION_CHANGED = "selection_changed"

    # Updates
    PAGE_UPDATED = "page_updated"
    PAGE_SAVED = "page_saved"
    PAGE_DELETED = "page_deleted"
    PAGE_PUBLISHED = "page_published"

    # Collaboration
    EDIT_LOCK_ACQUIRED = "edit_lock_acquired"
    EDIT_LOCK_RELEASED = "edit_lock_released"
    CONFLICT_DETECTED = "conflict_detected"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"

    # Comments
    COMMENT_ADDED = "comment_added"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"

    # Notifications
    NOTIFICATION = "notification"
    ERROR = "error"


class WSMessage(BaseModel):
    """WebSocket message model."""
    type: WSMessageType
    page_id: Optional[int] = None
    user_id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserPresence(BaseModel):
    """User presence information."""
    user_id: int
    username: str
    page_id: Optional[int] = None
    is_editing: bool = False
    is_typing: bool = False
    cursor_position: Optional[int] = None
    selection_start: Optional[int] = None
    selection_end: Optional[int] = None
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)


class EditLock(BaseModel):
    """Edit lock for preventing conflicts."""
    page_id: int
    user_id: int
    section_id: Optional[str] = None
    acquired_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """
    Manages WebSocket connections for real-time collaboration.

    Handles:
    - Connection lifecycle (connect/disconnect)
    - Message broadcasting
    - Presence tracking
    - Edit lock management
    - Conflict detection
    """

    def __init__(self):
        """Initialize the connection manager."""
        # WebSocket connections: user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}

        # User presence: user_id -> UserPresence
        self.user_presence: Dict[int, UserPresence] = {}

        # Page subscriptions: page_id -> set of user_ids
        self.page_subscriptions: Dict[int, Set[int]] = defaultdict(set)

        # Edit locks: page_id -> EditLock
        self.edit_locks: Dict[int, EditLock] = {}

        # Typing indicators: page_id -> set of user_ids currently typing
        self.typing_users: Dict[int, Set[int]] = defaultdict(set)

        # Content versions for conflict detection: page_id -> version
        self.content_versions: Dict[int, int] = {}

        # Message queue for offline users
        self.message_queue: Dict[int, List[WSMessage]] = defaultdict(list)

    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        username: str
    ) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID
            username: Username
        """
        await websocket.accept()

        # Store connection
        self.active_connections[user_id] = websocket

        # Create user presence
        self.user_presence[user_id] = UserPresence(
            user_id=user_id,
            username=username
        )

        logger.info(f"User {user_id} ({username}) connected via WebSocket")

        # Send queued messages if any
        if user_id in self.message_queue:
            for message in self.message_queue[user_id]:
                await self.send_personal_message(message, user_id)
            self.message_queue[user_id].clear()

        # Notify others
        await self.broadcast_message(
            WSMessage(
                type=WSMessageType.USER_JOINED,
                user_id=user_id,
                data={"username": username}
            )
        )

    async def disconnect(self, user_id: int) -> None:
        """
        Handle WebSocket disconnection.

        Args:
            user_id: User ID
        """
        if user_id in self.active_connections:
            # Remove connection
            del self.active_connections[user_id]

            # Get user info before removing
            username = self.user_presence.get(user_id, UserPresence(user_id=user_id, username="Unknown")).username

            # Clean up subscriptions
            for page_id in list(self.page_subscriptions.keys()):
                if user_id in self.page_subscriptions[page_id]:
                    self.page_subscriptions[page_id].remove(user_id)
                    if not self.page_subscriptions[page_id]:
                        del self.page_subscriptions[page_id]

            # Release edit locks
            for page_id, lock in list(self.edit_locks.items()):
                if lock.user_id == user_id:
                    del self.edit_locks[page_id]
                    await self.broadcast_to_page(
                        page_id,
                        WSMessage(
                            type=WSMessageType.EDIT_LOCK_RELEASED,
                            user_id=user_id,
                            page_id=page_id
                        )
                    )

            # Clear typing indicators
            for page_id in list(self.typing_users.keys()):
                if user_id in self.typing_users[page_id]:
                    self.typing_users[page_id].remove(user_id)

            # Remove presence
            if user_id in self.user_presence:
                del self.user_presence[user_id]

            logger.info(f"User {user_id} ({username}) disconnected")

            # Notify others
            await self.broadcast_message(
                WSMessage(
                    type=WSMessageType.USER_LEFT,
                    user_id=user_id,
                    data={"username": username}
                )
            )

    # ========================================================================
    # MESSAGE SENDING
    # ========================================================================

    async def send_personal_message(
        self,
        message: WSMessage,
        user_id: int
    ) -> None:
        """
        Send a message to a specific user.

        Args:
            message: Message to send
            user_id: Target user ID
        """
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(message.model_dump_json())
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                # Connection may be broken, remove it
                await self.disconnect(user_id)
        else:
            # Queue message for offline user
            self.message_queue[user_id].append(message)

    async def broadcast_message(
        self,
        message: WSMessage,
        exclude_user: Optional[int] = None
    ) -> None:
        """
        Broadcast a message to all connected users.

        Args:
            message: Message to broadcast
            exclude_user: User ID to exclude from broadcast
        """
        disconnected_users = []

        for user_id, websocket in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue

            try:
                await websocket.send_text(message.model_dump_json())
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(user_id)

    async def broadcast_to_page(
        self,
        page_id: int,
        message: WSMessage,
        exclude_user: Optional[int] = None
    ) -> None:
        """
        Broadcast a message to all users subscribed to a page.

        Args:
            page_id: Page ID
            message: Message to broadcast
            exclude_user: User ID to exclude from broadcast
        """
        if page_id not in self.page_subscriptions:
            return

        for user_id in self.page_subscriptions[page_id]:
            if exclude_user and user_id == exclude_user:
                continue

            await self.send_personal_message(message, user_id)

    # ========================================================================
    # PAGE SUBSCRIPTION
    # ========================================================================

    async def subscribe_to_page(
        self,
        user_id: int,
        page_id: int
    ) -> None:
        """
        Subscribe a user to page updates.

        Args:
            user_id: User ID
            page_id: Page ID
        """
        self.page_subscriptions[page_id].add(user_id)

        # Update user presence
        if user_id in self.user_presence:
            self.user_presence[user_id].page_id = page_id
            self.user_presence[user_id].last_activity = datetime.utcnow()

        # Get active users on this page
        active_users = self.get_active_users_on_page(page_id)

        # Notify user of active users
        await self.send_personal_message(
            WSMessage(
                type=WSMessageType.ACTIVE_USERS,
                user_id=user_id,
                page_id=page_id,
                data={
                    "users": [
                        {
                            "user_id": u.user_id,
                            "username": u.username,
                            "is_editing": u.is_editing,
                            "is_typing": u.is_typing
                        }
                        for u in active_users
                    ]
                }
            ),
            user_id
        )

        # Notify others
        await self.broadcast_to_page(
            page_id,
            WSMessage(
                type=WSMessageType.PAGE_OPENED,
                user_id=user_id,
                page_id=page_id,
                data={
                    "username": self.user_presence[user_id].username
                }
            ),
            exclude_user=user_id
        )

    async def unsubscribe_from_page(
        self,
        user_id: int,
        page_id: int
    ) -> None:
        """
        Unsubscribe a user from page updates.

        Args:
            user_id: User ID
            page_id: Page ID
        """
        if page_id in self.page_subscriptions:
            self.page_subscriptions[page_id].discard(user_id)

            if not self.page_subscriptions[page_id]:
                del self.page_subscriptions[page_id]

        # Update user presence
        if user_id in self.user_presence:
            self.user_presence[user_id].page_id = None
            self.user_presence[user_id].is_editing = False

        # Release edit lock if held
        if page_id in self.edit_locks and self.edit_locks[page_id].user_id == user_id:
            del self.edit_locks[page_id]
            await self.broadcast_to_page(
                page_id,
                WSMessage(
                    type=WSMessageType.EDIT_LOCK_RELEASED,
                    user_id=user_id,
                    page_id=page_id
                )
            )

        # Notify others
        await self.broadcast_to_page(
            page_id,
            WSMessage(
                type=WSMessageType.PAGE_CLOSED,
                user_id=user_id,
                page_id=page_id
            ),
            exclude_user=user_id
        )

    # ========================================================================
    # EDIT LOCK MANAGEMENT
    # ========================================================================

    async def acquire_edit_lock(
        self,
        user_id: int,
        page_id: int,
        section_id: Optional[str] = None
    ) -> bool:
        """
        Acquire an edit lock for a page or section.

        Args:
            user_id: User ID
            page_id: Page ID
            section_id: Optional section ID for fine-grained locking

        Returns:
            True if lock acquired, False otherwise
        """
        # Check if lock already exists
        if page_id in self.edit_locks:
            existing_lock = self.edit_locks[page_id]

            # Allow same user to re-acquire
            if existing_lock.user_id == user_id:
                return True

            # Check if lock has expired
            if existing_lock.expires_at and existing_lock.expires_at < datetime.utcnow():
                # Lock expired, remove it
                del self.edit_locks[page_id]
            else:
                # Lock held by another user
                await self.send_personal_message(
                    WSMessage(
                        type=WSMessageType.ERROR,
                        user_id=user_id,
                        page_id=page_id,
                        data={
                            "message": f"Page is being edited by user {existing_lock.user_id}",
                            "locked_by": existing_lock.user_id
                        }
                    ),
                    user_id
                )
                return False

        # Acquire lock
        self.edit_locks[page_id] = EditLock(
            page_id=page_id,
            user_id=user_id,
            section_id=section_id
        )

        # Update user presence
        if user_id in self.user_presence:
            self.user_presence[user_id].is_editing = True

        # Notify others
        await self.broadcast_to_page(
            page_id,
            WSMessage(
                type=WSMessageType.EDIT_LOCK_ACQUIRED,
                user_id=user_id,
                page_id=page_id,
                data={"section_id": section_id}
            ),
            exclude_user=user_id
        )

        return True

    async def release_edit_lock(
        self,
        user_id: int,
        page_id: int
    ) -> None:
        """
        Release an edit lock.

        Args:
            user_id: User ID
            page_id: Page ID
        """
        if page_id in self.edit_locks and self.edit_locks[page_id].user_id == user_id:
            del self.edit_locks[page_id]

            # Update user presence
            if user_id in self.user_presence:
                self.user_presence[user_id].is_editing = False

            # Notify others
            await self.broadcast_to_page(
                page_id,
                WSMessage(
                    type=WSMessageType.EDIT_LOCK_RELEASED,
                    user_id=user_id,
                    page_id=page_id
                )
            )

    # ========================================================================
    # TYPING INDICATORS
    # ========================================================================

    async def set_typing(
        self,
        user_id: int,
        page_id: int,
        is_typing: bool
    ) -> None:
        """
        Set typing indicator for a user.

        Args:
            user_id: User ID
            page_id: Page ID
            is_typing: Whether user is typing
        """
        if is_typing:
            self.typing_users[page_id].add(user_id)
            message_type = WSMessageType.USER_TYPING
        else:
            self.typing_users[page_id].discard(user_id)
            message_type = WSMessageType.USER_STOPPED_TYPING

        # Update user presence
        if user_id in self.user_presence:
            self.user_presence[user_id].is_typing = is_typing
            self.user_presence[user_id].last_activity = datetime.utcnow()

        # Notify others
        await self.broadcast_to_page(
            page_id,
            WSMessage(
                type=message_type,
                user_id=user_id,
                page_id=page_id,
                data={
                    "username": self.user_presence[user_id].username
                }
            ),
            exclude_user=user_id
        )

    # ========================================================================
    # CONTENT SYNC AND CONFLICT DETECTION
    # ========================================================================

    async def sync_content(
        self,
        user_id: int,
        page_id: int,
        content: str,
        version: int,
        cursor_position: Optional[int] = None
    ) -> None:
        """
        Synchronize content changes across users.

        Args:
            user_id: User ID
            page_id: Page ID
            content: Updated content
            version: Content version
            cursor_position: Cursor position
        """
        # Check for version conflict
        current_version = self.content_versions.get(page_id, 0)

        if version < current_version:
            # Conflict detected
            await self.send_personal_message(
                WSMessage(
                    type=WSMessageType.CONFLICT_DETECTED,
                    user_id=user_id,
                    page_id=page_id,
                    data={
                        "current_version": current_version,
                        "your_version": version,
                        "message": "Your changes conflict with recent updates. Please refresh."
                    }
                ),
                user_id
            )
            return

        # Update version
        self.content_versions[page_id] = version

        # Update user presence cursor position
        if user_id in self.user_presence:
            self.user_presence[user_id].cursor_position = cursor_position
            self.user_presence[user_id].last_activity = datetime.utcnow()

        # Broadcast changes to other users
        await self.broadcast_to_page(
            page_id,
            WSMessage(
                type=WSMessageType.CONTENT_CHANGED,
                user_id=user_id,
                page_id=page_id,
                data={
                    "content": content,
                    "version": version,
                    "cursor_position": cursor_position
                }
            ),
            exclude_user=user_id
        )

    async def handle_page_saved(
        self,
        user_id: int,
        page_id: int,
        new_version: int
    ) -> None:
        """
        Handle page save event.

        Args:
            user_id: User ID who saved
            page_id: Page ID
            new_version: New page version
        """
        # Update content version
        self.content_versions[page_id] = new_version

        # Notify all users on the page
        await self.broadcast_to_page(
            page_id,
            WSMessage(
                type=WSMessageType.PAGE_SAVED,
                user_id=user_id,
                page_id=page_id,
                data={
                    "version": new_version,
                    "saved_by": self.user_presence.get(user_id, UserPresence(user_id=user_id, username="Unknown")).username
                }
            )
        )

    # ========================================================================
    # PRESENCE AND STATUS
    # ========================================================================

    def get_active_users_on_page(self, page_id: int) -> List[UserPresence]:
        """
        Get list of active users on a page.

        Args:
            page_id: Page ID

        Returns:
            List of user presence objects
        """
        if page_id not in self.page_subscriptions:
            return []

        return [
            self.user_presence[user_id]
            for user_id in self.page_subscriptions[page_id]
            if user_id in self.user_presence
        ]

    def get_user_presence(self, user_id: int) -> Optional[UserPresence]:
        """
        Get presence information for a user.

        Args:
            user_id: User ID

        Returns:
            User presence or None
        """
        return self.user_presence.get(user_id)

    def is_page_locked(self, page_id: int) -> bool:
        """
        Check if a page is currently locked for editing.

        Args:
            page_id: Page ID

        Returns:
            True if locked, False otherwise
        """
        return page_id in self.edit_locks

    def get_lock_holder(self, page_id: int) -> Optional[int]:
        """
        Get the user ID holding the lock for a page.

        Args:
            page_id: Page ID

        Returns:
            User ID or None
        """
        if page_id in self.edit_locks:
            return self.edit_locks[page_id].user_id
        return None

    # ========================================================================
    # NOTIFICATIONS
    # ========================================================================

    async def notify_comment_added(
        self,
        page_id: int,
        comment_id: int,
        author_id: int,
        content: str,
        mentions: Optional[List[int]] = None
    ) -> None:
        """
        Notify users of a new comment.

        Args:
            page_id: Page ID
            comment_id: Comment ID
            author_id: Comment author ID
            content: Comment content
            mentions: List of mentioned user IDs
        """
        message = WSMessage(
            type=WSMessageType.COMMENT_ADDED,
            user_id=author_id,
            page_id=page_id,
            data={
                "comment_id": comment_id,
                "content": content,
                "author_id": author_id
            }
        )

        # Notify users on the page
        await self.broadcast_to_page(page_id, message)

        # Send personal notifications to mentioned users
        if mentions:
            for user_id in mentions:
                if user_id != author_id:
                    await self.send_personal_message(
                        WSMessage(
                            type=WSMessageType.NOTIFICATION,
                            user_id=user_id,
                            page_id=page_id,
                            data={
                                "type": "mention",
                                "message": f"You were mentioned in a comment on page {page_id}",
                                "comment_id": comment_id
                            }
                        ),
                        user_id
                    )

    async def notify_page_updated(
        self,
        page_id: int,
        updated_by: int,
        change_type: str
    ) -> None:
        """
        Notify users of page updates.

        Args:
            page_id: Page ID
            updated_by: User ID who made the update
            change_type: Type of change
        """
        await self.broadcast_to_page(
            page_id,
            WSMessage(
                type=WSMessageType.PAGE_UPDATED,
                user_id=updated_by,
                page_id=page_id,
                data={
                    "change_type": change_type,
                    "updated_by": updated_by
                }
            )
        )


# ============================================================================
# GLOBAL CONNECTION MANAGER INSTANCE
# ============================================================================

# Single global instance
connection_manager = ConnectionManager()


# ============================================================================
# WEBSOCKET MESSAGE HANDLER
# ============================================================================

async def handle_websocket_message(
    message: WSMessage,
    user_id: int,
    db: Session
) -> None:
    """
    Handle incoming WebSocket message.

    Args:
        message: WebSocket message
        user_id: User ID
        db: Database session
    """
    try:
        msg_type = message.type

        # Ping/Pong
        if msg_type == WSMessageType.PING:
            await connection_manager.send_personal_message(
                WSMessage(
                    type=WSMessageType.PONG,
                    user_id=user_id
                ),
                user_id
            )

        # Page subscription
        elif msg_type == WSMessageType.PAGE_OPENED:
            page_id = message.page_id
            if page_id:
                await connection_manager.subscribe_to_page(user_id, page_id)

        elif msg_type == WSMessageType.PAGE_CLOSED:
            page_id = message.page_id
            if page_id:
                await connection_manager.unsubscribe_from_page(user_id, page_id)

        # Edit lock
        elif msg_type == WSMessageType.EDIT_LOCK_ACQUIRED:
            page_id = message.page_id
            if page_id:
                section_id = message.data.get("section_id")
                await connection_manager.acquire_edit_lock(user_id, page_id, section_id)

        elif msg_type == WSMessageType.EDIT_LOCK_RELEASED:
            page_id = message.page_id
            if page_id:
                await connection_manager.release_edit_lock(user_id, page_id)

        # Typing indicators
        elif msg_type in [WSMessageType.USER_TYPING, WSMessageType.USER_STOPPED_TYPING]:
            page_id = message.page_id
            if page_id:
                is_typing = msg_type == WSMessageType.USER_TYPING
                await connection_manager.set_typing(user_id, page_id, is_typing)

        # Content sync
        elif msg_type == WSMessageType.CONTENT_CHANGED:
            page_id = message.page_id
            if page_id:
                content = message.data.get("content", "")
                version = message.data.get("version", 0)
                cursor_position = message.data.get("cursor_position")
                await connection_manager.sync_content(
                    user_id, page_id, content, version, cursor_position
                )

        # Sync request
        elif msg_type == WSMessageType.SYNC_REQUEST:
            page_id = message.page_id
            if page_id:
                # Fetch current page content from database
                page = db.query(WikiPage).get(page_id)
                if page:
                    await connection_manager.send_personal_message(
                        WSMessage(
                            type=WSMessageType.SYNC_RESPONSE,
                            user_id=user_id,
                            page_id=page_id,
                            data={
                                "content": page.content,
                                "version": page.current_version,
                                "status": page.status.value
                            }
                        ),
                        user_id
                    )

        else:
            logger.warning(f"Unhandled message type: {msg_type}")

    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}", exc_info=True)
        await connection_manager.send_personal_message(
            WSMessage(
                type=WSMessageType.ERROR,
                user_id=user_id,
                data={"message": "Internal server error"}
            ),
            user_id
        )


# ============================================================================
# WEBSOCKET ENDPOINT HANDLER
# ============================================================================

async def websocket_endpoint(
    websocket: WebSocket,
    user_id: int,
    username: str
) -> None:
    """
    WebSocket endpoint handler.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        username: Username
    """
    await connection_manager.connect(websocket, user_id, username)

    try:
        # Get database session
        db = next(get_db())

        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                # Parse message
                message_dict = json.loads(data)
                message = WSMessage(**message_dict)

                # Handle message
                await handle_websocket_message(message, user_id, db)

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user {user_id}")
                await connection_manager.send_personal_message(
                    WSMessage(
                        type=WSMessageType.ERROR,
                        user_id=user_id,
                        data={"message": "Invalid message format"}
                    ),
                    user_id
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

    except WebSocketDisconnect:
        logger.info(f"User {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}", exc_info=True)
    finally:
        # Clean up
        await connection_manager.disconnect(user_id)
        if 'db' in locals():
            db.close()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.

    Returns:
        Connection manager instance
    """
    return connection_manager


async def broadcast_page_event(
    page_id: int,
    event_type: str,
    user_id: int,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Broadcast a page event to all subscribed users.

    Args:
        page_id: Page ID
        event_type: Event type
        user_id: User ID who triggered the event
        data: Additional event data
    """
    message = WSMessage(
        type=WSMessageType.PAGE_UPDATED,
        user_id=user_id,
        page_id=page_id,
        data={
            "event_type": event_type,
            **(data or {})
        }
    )

    await connection_manager.broadcast_to_page(page_id, message)


async def notify_users(
    user_ids: List[int],
    notification_type: str,
    message: str,
    data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Send notifications to specific users.

    Args:
        user_ids: List of user IDs to notify
        notification_type: Notification type
        message: Notification message
        data: Additional notification data
    """
    notification = WSMessage(
        type=WSMessageType.NOTIFICATION,
        user_id=0,  # System notification
        data={
            "notification_type": notification_type,
            "message": message,
            **(data or {})
        }
    )

    for user_id in user_ids:
        await connection_manager.send_personal_message(notification, user_id)
