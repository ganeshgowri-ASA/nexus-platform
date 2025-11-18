"""
WebSocket Server

Main WebSocket server implementation with FastAPI integration.
Handles connections, routing, and event distribution.
"""

import asyncio
import logging
import uuid
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.routing import APIRouter
import json

from .connection_manager import ConnectionManager
from .events import (
    EventType,
    WebSocketEvent,
    ChatEvent,
    DocumentEvent,
    NotificationEvent,
    PresenceEvent,
)
from .handlers.chat_handler import ChatHandler
from .handlers.document_handler import DocumentHandler
from .handlers.notification_handler import NotificationHandler
from .handlers.presence_handler import PresenceHandler

logger = logging.getLogger(__name__)


class WebSocketServer:
    """
    WebSocket Server with advanced features:
    - FastAPI integration
    - Event-based routing
    - Automatic heartbeat/ping-pong
    - Handler registration
    - Error handling and recovery
    """

    def __init__(
        self,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 60,
        enable_auto_ping: bool = True,
    ):
        self.connection_manager = ConnectionManager(heartbeat_interval, heartbeat_timeout)
        self.heartbeat_interval = heartbeat_interval
        self.enable_auto_ping = enable_auto_ping

        # Event handlers
        self.event_handlers: Dict[EventType, list] = {}

        # Initialize handlers
        self.chat_handler = ChatHandler(self.connection_manager)
        self.document_handler = DocumentHandler(self.connection_manager)
        self.notification_handler = NotificationHandler(self.connection_manager)
        self.presence_handler = PresenceHandler(self.connection_manager)

        # Register handlers
        self._register_handlers()

        # Background tasks
        self._tasks = []

        logger.info("WebSocketServer initialized")

    def _register_handlers(self):
        """Register all event handlers"""
        # Chat handlers
        self.register_handler(EventType.CHAT_MESSAGE, self.chat_handler.handle_message)
        self.register_handler(EventType.CHAT_TYPING, self.chat_handler.handle_typing)
        self.register_handler(EventType.CHAT_READ, self.chat_handler.handle_read_receipt)
        self.register_handler(EventType.CHAT_EDIT, self.chat_handler.handle_edit)
        self.register_handler(EventType.CHAT_DELETE, self.chat_handler.handle_delete)

        # Document handlers
        self.register_handler(EventType.DOC_OPEN, self.document_handler.handle_open)
        self.register_handler(EventType.DOC_CLOSE, self.document_handler.handle_close)
        self.register_handler(EventType.DOC_EDIT, self.document_handler.handle_edit)
        self.register_handler(EventType.DOC_CURSOR, self.document_handler.handle_cursor)
        self.register_handler(EventType.DOC_SAVE, self.document_handler.handle_save)

        # Notification handlers
        self.register_handler(
            EventType.NOTIFICATION_READ, self.notification_handler.handle_read
        )
        self.register_handler(
            EventType.NOTIFICATION_CLEAR, self.notification_handler.handle_clear
        )

        # Presence handlers
        self.register_handler(
            EventType.PRESENCE_UPDATE, self.presence_handler.handle_status_update
        )

        # Room handlers
        self.register_handler(EventType.ROOM_JOIN, self.handle_room_join)
        self.register_handler(EventType.ROOM_LEAVE, self.handle_room_leave)

        # System handlers
        self.register_handler(EventType.PING, self.handle_ping)
        self.register_handler(EventType.PONG, self.handle_pong)

    def register_handler(self, event_type: EventType, handler: Callable):
        """
        Register an event handler

        Args:
            event_type: Event type to handle
            handler: Async function to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for {event_type}")

    async def handle_websocket(
        self,
        websocket: WebSocket,
        user_id: str,
        token: Optional[str] = None,
    ):
        """
        Main WebSocket connection handler

        Args:
            websocket: FastAPI WebSocket instance
            user_id: Authenticated user ID
            token: Optional authentication token
        """
        connection_id = f"conn_{uuid.uuid4().hex[:12]}"

        metadata = {
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "connected_at": datetime.utcnow().isoformat(),
        }

        connection = None

        try:
            # Connect
            connection = await self.connection_manager.connect(
                websocket, connection_id, user_id, metadata
            )

            # Send welcome message
            await self._send_welcome_message(connection)

            # Update user presence
            await self.presence_handler.user_connected(user_id, connection_id, metadata)

            # Start heartbeat if enabled
            if self.enable_auto_ping:
                heartbeat_task = asyncio.create_task(
                    self._heartbeat_loop(connection_id)
                )
            else:
                heartbeat_task = None

            # Message receive loop
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_json()

                    # Update heartbeat
                    await self.connection_manager.update_heartbeat(connection_id)

                    # Process message
                    await self._process_message(connection_id, user_id, data)

                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected: {connection_id}")
                    break
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {connection_id}: {e}")
                    await self._send_error(connection, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error processing message from {connection_id}: {e}")
                    await self._send_error(connection, "Error processing message")

        except Exception as e:
            logger.error(f"WebSocket error for {connection_id}: {e}")
        finally:
            # Cleanup
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

            # Update presence
            await self.presence_handler.user_disconnected(user_id, connection_id)

            # Disconnect
            await self.connection_manager.disconnect(connection_id)

    async def _process_message(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """
        Process incoming WebSocket message

        Args:
            connection_id: Connection identifier
            user_id: User ID
            data: Message data
        """
        try:
            # Validate event type
            event_type_str = data.get("event_type")
            if not event_type_str:
                logger.warning(f"Missing event_type in message from {connection_id}")
                return

            # Parse event type
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                logger.warning(f"Invalid event_type '{event_type_str}' from {connection_id}")
                return

            # Get handlers for this event type
            handlers = self.event_handlers.get(event_type, [])

            if not handlers:
                logger.warning(f"No handlers for event type {event_type}")
                return

            # Execute handlers
            for handler in handlers:
                try:
                    await handler(connection_id, user_id, data)
                except Exception as e:
                    logger.error(f"Handler error for {event_type}: {e}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _send_welcome_message(self, connection):
        """Send welcome message to newly connected client"""
        welcome_event = WebSocketEvent(
            event_type=EventType.SYSTEM_MESSAGE,
            sender_id="system",
            data={
                "message": "Connected to NEXUS Platform WebSocket Server",
                "connection_id": connection.connection_id,
                "server_time": datetime.utcnow().isoformat(),
                "heartbeat_interval": self.heartbeat_interval,
            },
        )
        await connection.send_event(welcome_event)

    async def _send_error(self, connection, error_message: str):
        """Send error message to connection"""
        error_event = WebSocketEvent(
            event_type=EventType.ERROR,
            sender_id="system",
            data={"error": error_message, "timestamp": datetime.utcnow().isoformat()},
        )
        await connection.send_event(error_event)

    async def _heartbeat_loop(self, connection_id: str):
        """
        Automatic heartbeat/ping loop

        Args:
            connection_id: Connection to ping
        """
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)

                connection = self.connection_manager.get_connection(connection_id)
                if not connection:
                    break

                # Send ping
                ping_event = WebSocketEvent(
                    event_type=EventType.PING,
                    sender_id="system",
                    data={"timestamp": datetime.utcnow().isoformat()},
                )

                if not await connection.send_event(ping_event):
                    logger.warning(f"Failed to send ping to {connection_id}")
                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Heartbeat error for {connection_id}: {e}")

    async def handle_ping(self, connection_id: str, user_id: str, data: Dict[str, Any]):
        """Handle ping event"""
        connection = self.connection_manager.get_connection(connection_id)
        if connection:
            pong_event = WebSocketEvent(
                event_type=EventType.PONG,
                sender_id="system",
                data={"timestamp": datetime.utcnow().isoformat()},
            )
            await connection.send_event(pong_event)

    async def handle_pong(self, connection_id: str, user_id: str, data: Dict[str, Any]):
        """Handle pong event"""
        await self.connection_manager.update_heartbeat(connection_id)

    async def handle_room_join(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """Handle room join event"""
        room_id = data.get("room_id")
        if not room_id:
            logger.warning(f"Missing room_id in ROOM_JOIN from {connection_id}")
            return

        success = await self.connection_manager.join_room(connection_id, room_id)

        if success:
            # Notify room members
            join_event = WebSocketEvent(
                event_type=EventType.ROOM_JOIN,
                sender_id=user_id,
                room_id=room_id,
                data={
                    "user_id": user_id,
                    "username": data.get("username", "Unknown"),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            await self.connection_manager.broadcast_to_room(
                room_id, join_event.dict(), exclude={connection_id}
            )

    async def handle_room_leave(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """Handle room leave event"""
        room_id = data.get("room_id")
        if not room_id:
            logger.warning(f"Missing room_id in ROOM_LEAVE from {connection_id}")
            return

        success = await self.connection_manager.leave_room(connection_id, room_id)

        if success:
            # Notify room members
            leave_event = WebSocketEvent(
                event_type=EventType.ROOM_LEAVE,
                sender_id=user_id,
                room_id=room_id,
                data={
                    "user_id": user_id,
                    "username": data.get("username", "Unknown"),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            await self.connection_manager.broadcast_to_room(room_id, leave_event.dict())

    async def start_background_tasks(self):
        """Start background maintenance tasks"""
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._tasks.append(cleanup_task)
        logger.info("Background tasks started")

    async def _cleanup_loop(self):
        """Periodic cleanup of stale connections"""
        try:
            while True:
                await asyncio.sleep(60)  # Run every minute
                removed = await self.connection_manager.cleanup_stale_connections()
                if removed > 0:
                    logger.info(f"Cleaned up {removed} stale connections")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Cleanup loop error: {e}")

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down WebSocket server...")

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Disconnect all connections
        for connection_id in list(self.connection_manager.connections.keys()):
            await self.connection_manager.disconnect(connection_id)

        logger.info("WebSocket server shut down")

    def get_router(self) -> APIRouter:
        """
        Get FastAPI router for WebSocket endpoints

        Returns:
            APIRouter with WebSocket routes
        """
        router = APIRouter()

        @router.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            user_id: str = Query(...),
            token: Optional[str] = Query(None),
        ):
            """Main WebSocket endpoint"""
            await self.handle_websocket(websocket, user_id, token)

        @router.get("/ws/stats")
        async def get_stats():
            """Get WebSocket server statistics"""
            return self.connection_manager.get_stats()

        @router.get("/ws/online")
        async def get_online_users():
            """Get list of online users"""
            return {"users": self.connection_manager.get_online_users()}

        @router.get("/ws/rooms/{room_id}")
        async def get_room_members(room_id: str):
            """Get members of a specific room"""
            return {"members": self.connection_manager.get_room_members(room_id)}

        return router

    # Public API for sending messages
    async def send_notification(self, user_id: str, notification: NotificationEvent):
        """Send notification to user"""
        await self.notification_handler.send_notification(user_id, notification)

    async def broadcast_to_room(self, room_id: str, event: WebSocketEvent):
        """Broadcast event to room"""
        await self.connection_manager.broadcast_to_room(room_id, event.dict())

    async def send_to_user(self, user_id: str, event: WebSocketEvent):
        """Send event to specific user"""
        await self.connection_manager.send_to_user(user_id, event.dict())
