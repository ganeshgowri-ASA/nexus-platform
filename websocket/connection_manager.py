"""
WebSocket Connection Manager

Manages WebSocket connections, connection pooling, rooms, and message queuing.
"""

import asyncio
import logging
from typing import Dict, Set, Optional, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import WebSocket, WebSocketDisconnect
import json

from .events import WebSocketEvent, EventType

logger = logging.getLogger(__name__)


class Connection:
    """Represents a single WebSocket connection"""

    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.connected_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.rooms: Set[str] = set()
        self.is_active = True

    async def send(self, message: Dict[str, Any]) -> bool:
        """Send message to this connection"""
        try:
            await self.websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Error sending message to {self.connection_id}: {e}")
            self.is_active = False
            return False

    async def send_event(self, event: WebSocketEvent) -> bool:
        """Send WebSocket event to this connection"""
        return await self.send(event.dict())

    def update_heartbeat(self):
        """Update last heartbeat timestamp"""
        self.last_heartbeat = datetime.utcnow()

    def is_alive(self, timeout: int = 60) -> bool:
        """Check if connection is alive based on heartbeat"""
        elapsed = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return elapsed < timeout and self.is_active


class ConnectionManager:
    """
    Manages all WebSocket connections with advanced features:
    - Connection pooling
    - Room/channel support
    - Message queuing for offline users
    - Heartbeat monitoring
    - Broadcasting capabilities
    """

    def __init__(self, heartbeat_interval: int = 30, heartbeat_timeout: int = 60):
        # Connection storage
        self.connections: Dict[str, Connection] = {}  # connection_id -> Connection
        self.user_connections: Dict[str, Set[str]] = defaultdict(
            set
        )  # user_id -> {connection_ids}

        # Room management
        self.rooms: Dict[str, Set[str]] = defaultdict(set)  # room_id -> {connection_ids}
        self.room_metadata: Dict[str, Dict[str, Any]] = {}  # room_id -> metadata

        # Offline message queue
        self.offline_queue: Dict[str, List[Dict[str, Any]]] = defaultdict(
            list
        )  # user_id -> [messages]
        self.max_queue_size = 100

        # Heartbeat settings
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout

        # Statistics
        self.stats = {
            "total_connections": 0,
            "total_messages": 0,
            "total_broadcasts": 0,
            "total_rooms": 0,
        }

        logger.info("ConnectionManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Connection:
        """
        Register a new WebSocket connection

        Args:
            websocket: FastAPI WebSocket instance
            connection_id: Unique connection identifier
            user_id: User ID associated with this connection
            metadata: Optional connection metadata

        Returns:
            Connection object
        """
        await websocket.accept()

        connection = Connection(websocket, connection_id, user_id, metadata)
        self.connections[connection_id] = connection
        self.user_connections[user_id].add(connection_id)

        self.stats["total_connections"] += 1

        logger.info(
            f"New connection: {connection_id} for user {user_id} "
            f"(total active: {len(self.connections)})"
        )

        # Send queued offline messages
        await self._send_queued_messages(user_id, connection)

        return connection

    async def disconnect(self, connection_id: str):
        """
        Disconnect and cleanup a WebSocket connection

        Args:
            connection_id: Connection identifier to disconnect
        """
        connection = self.connections.get(connection_id)
        if not connection:
            return

        user_id = connection.user_id

        # Remove from all rooms
        for room_id in list(connection.rooms):
            await self.leave_room(connection_id, room_id)

        # Remove from user connections
        self.user_connections[user_id].discard(connection_id)
        if not self.user_connections[user_id]:
            del self.user_connections[user_id]

        # Remove connection
        del self.connections[connection_id]

        logger.info(
            f"Disconnected: {connection_id} for user {user_id} "
            f"(total active: {len(self.connections)})"
        )

    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get connection by ID"""
        return self.connections.get(connection_id)

    def get_user_connections(self, user_id: str) -> List[Connection]:
        """Get all active connections for a user"""
        connection_ids = self.user_connections.get(user_id, set())
        return [self.connections[cid] for cid in connection_ids if cid in self.connections]

    def is_user_online(self, user_id: str) -> bool:
        """Check if user has any active connections"""
        return user_id in self.user_connections and len(self.user_connections[user_id]) > 0

    async def send_to_connection(
        self, connection_id: str, message: Dict[str, Any]
    ) -> bool:
        """Send message to specific connection"""
        connection = self.get_connection(connection_id)
        if connection:
            success = await connection.send(message)
            if success:
                self.stats["total_messages"] += 1
            return success
        return False

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> int:
        """
        Send message to all connections of a user

        Args:
            user_id: Target user ID
            message: Message to send

        Returns:
            Number of successful sends
        """
        connections = self.get_user_connections(user_id)

        if not connections:
            # Queue message for offline user
            await self._queue_message(user_id, message)
            return 0

        sent_count = 0
        for connection in connections:
            if await connection.send(message):
                sent_count += 1

        self.stats["total_messages"] += sent_count
        return sent_count

    async def send_private_message(
        self, from_user_id: str, to_user_id: str, message: Dict[str, Any]
    ) -> bool:
        """
        Send private message from one user to another

        Args:
            from_user_id: Sender user ID
            to_user_id: Recipient user ID
            message: Message to send

        Returns:
            True if sent successfully
        """
        message["sender_id"] = from_user_id
        message["recipient_id"] = to_user_id
        message["timestamp"] = datetime.utcnow().isoformat()

        sent_count = await self.send_to_user(to_user_id, message)
        return sent_count > 0

    async def join_room(self, connection_id: str, room_id: str) -> bool:
        """
        Add connection to a room

        Args:
            connection_id: Connection to add
            room_id: Room identifier

        Returns:
            True if joined successfully
        """
        connection = self.get_connection(connection_id)
        if not connection:
            return False

        self.rooms[room_id].add(connection_id)
        connection.rooms.add(room_id)

        if room_id not in self.room_metadata:
            self.room_metadata[room_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "member_count": 0,
            }
            self.stats["total_rooms"] += 1

        self.room_metadata[room_id]["member_count"] = len(self.rooms[room_id])

        logger.info(
            f"Connection {connection_id} joined room {room_id} "
            f"(members: {len(self.rooms[room_id])})"
        )
        return True

    async def leave_room(self, connection_id: str, room_id: str) -> bool:
        """
        Remove connection from a room

        Args:
            connection_id: Connection to remove
            room_id: Room identifier

        Returns:
            True if left successfully
        """
        connection = self.get_connection(connection_id)
        if not connection:
            return False

        self.rooms[room_id].discard(connection_id)
        connection.rooms.discard(room_id)

        if not self.rooms[room_id]:
            # Room is empty, cleanup
            del self.rooms[room_id]
            del self.room_metadata[room_id]
        else:
            self.room_metadata[room_id]["member_count"] = len(self.rooms[room_id])

        logger.info(f"Connection {connection_id} left room {room_id}")
        return True

    async def broadcast_to_room(
        self, room_id: str, message: Dict[str, Any], exclude: Optional[Set[str]] = None
    ) -> int:
        """
        Broadcast message to all connections in a room

        Args:
            room_id: Target room ID
            message: Message to broadcast
            exclude: Set of connection IDs to exclude

        Returns:
            Number of successful sends
        """
        exclude = exclude or set()
        connection_ids = self.rooms.get(room_id, set())

        sent_count = 0
        for connection_id in connection_ids:
            if connection_id in exclude:
                continue

            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        if sent_count > 0:
            self.stats["total_broadcasts"] += 1

        return sent_count

    async def broadcast_to_all(
        self, message: Dict[str, Any], exclude: Optional[Set[str]] = None
    ) -> int:
        """
        Broadcast message to all active connections

        Args:
            message: Message to broadcast
            exclude: Set of connection IDs to exclude

        Returns:
            Number of successful sends
        """
        exclude = exclude or set()

        sent_count = 0
        for connection_id in list(self.connections.keys()):
            if connection_id in exclude:
                continue

            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        if sent_count > 0:
            self.stats["total_broadcasts"] += 1

        return sent_count

    async def update_heartbeat(self, connection_id: str):
        """Update heartbeat for a connection"""
        connection = self.get_connection(connection_id)
        if connection:
            connection.update_heartbeat()

    async def cleanup_stale_connections(self):
        """Remove connections that haven't sent heartbeat"""
        stale_connections = []

        for connection_id, connection in self.connections.items():
            if not connection.is_alive(self.heartbeat_timeout):
                stale_connections.append(connection_id)

        for connection_id in stale_connections:
            logger.warning(f"Removing stale connection: {connection_id}")
            await self.disconnect(connection_id)

        return len(stale_connections)

    async def _queue_message(self, user_id: str, message: Dict[str, Any]):
        """Queue message for offline user"""
        queue = self.offline_queue[user_id]

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        queue.append(message)

        # Limit queue size
        if len(queue) > self.max_queue_size:
            queue.pop(0)  # Remove oldest message

        logger.debug(f"Queued message for offline user {user_id} (queue size: {len(queue)})")

    async def _send_queued_messages(self, user_id: str, connection: Connection):
        """Send all queued messages to newly connected user"""
        if user_id not in self.offline_queue:
            return

        queue = self.offline_queue[user_id]
        sent_count = 0

        for message in queue:
            if await connection.send(message):
                sent_count += 1

        # Clear queue after sending
        del self.offline_queue[user_id]

        if sent_count > 0:
            logger.info(f"Sent {sent_count} queued messages to user {user_id}")

    def get_room_members(self, room_id: str) -> List[str]:
        """Get list of user IDs in a room"""
        connection_ids = self.rooms.get(room_id, set())
        user_ids = []

        for connection_id in connection_ids:
            connection = self.get_connection(connection_id)
            if connection and connection.user_id not in user_ids:
                user_ids.append(connection.user_id)

        return user_ids

    def get_online_users(self) -> List[str]:
        """Get list of all online user IDs"""
        return list(self.user_connections.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics"""
        return {
            **self.stats,
            "active_connections": len(self.connections),
            "active_users": len(self.user_connections),
            "active_rooms": len(self.rooms),
            "queued_messages": sum(len(q) for q in self.offline_queue.values()),
        }
