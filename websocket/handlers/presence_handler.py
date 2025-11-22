"""
Presence Handler

Handles user presence tracking and status updates.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

from ..events import (
    EventType,
    WebSocketEvent,
    PresenceEvent,
)

logger = logging.getLogger(__name__)


class UserPresence:
    """Represents a user's presence state"""

    def __init__(self, user_id: str, username: str):
        self.user_id = user_id
        self.username = username
        self.status = "offline"  # online, offline, away, busy
        self.status_message: Optional[str] = None
        self.last_seen = datetime.utcnow()
        self.connections: List[str] = []  # connection_ids
        self.location: Optional[str] = None  # Current page/module
        self.device_info: Dict[str, str] = {}

    def add_connection(self, connection_id: str, device_info: Optional[Dict[str, str]] = None):
        """Add a connection"""
        if connection_id not in self.connections:
            self.connections.append(connection_id)
        if device_info:
            self.device_info.update(device_info)
        self.status = "online"
        self.last_seen = datetime.utcnow()

    def remove_connection(self, connection_id: str):
        """Remove a connection"""
        if connection_id in self.connections:
            self.connections.remove(connection_id)
        if not self.connections:
            self.status = "offline"
        self.last_seen = datetime.utcnow()

    def is_online(self) -> bool:
        """Check if user is online"""
        return len(self.connections) > 0 and self.status != "offline"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "status": self.status,
            "status_message": self.status_message,
            "last_seen": self.last_seen.isoformat(),
            "location": self.location,
            "device_info": self.device_info,
            "connection_count": len(self.connections),
        }


class PresenceHandler:
    """
    Handles user presence and status tracking:
    - Online/offline status
    - Custom status messages
    - Last seen tracking
    - Location tracking (current page/module)
    - Device information
    - Status broadcasts
    """

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager

        # Presence storage
        self.user_presence: Dict[str, UserPresence] = {}  # user_id -> UserPresence

        # Subscriptions (who is interested in whose presence)
        self.presence_subscriptions: Dict[str, set] = defaultdict(
            set
        )  # user_id -> {watching_user_ids}

        # Stats
        self.presence_stats = {
            "total_online": 0,
            "total_away": 0,
            "total_busy": 0,
            "total_offline": 0,
        }

        logger.info("PresenceHandler initialized")

    async def user_connected(
        self, user_id: str, connection_id: str, metadata: Dict[str, Any]
    ):
        """
        Handle user connection

        Args:
            user_id: User ID
            connection_id: Connection ID
            metadata: Connection metadata
        """
        try:
            # Get or create presence
            if user_id not in self.user_presence:
                self.user_presence[user_id] = UserPresence(
                    user_id, metadata.get("username", "Unknown")
                )

            presence = self.user_presence[user_id]
            device_info = {"user_agent": metadata.get("user_agent", "unknown")}

            # Add connection
            presence.add_connection(connection_id, device_info)

            # Create presence event
            presence_event = PresenceEvent(
                user_id=user_id,
                username=presence.username,
                status="online",
                device_info=device_info,
            )

            # Broadcast to subscribers
            await self._broadcast_presence_update(user_id, presence_event)

            self._update_stats()

            logger.info(
                f"User {user_id} online (connections: {len(presence.connections)})"
            )

        except Exception as e:
            logger.error(f"Error handling user connection: {e}")

    async def user_disconnected(self, user_id: str, connection_id: str):
        """
        Handle user disconnection

        Args:
            user_id: User ID
            connection_id: Connection ID
        """
        try:
            if user_id not in self.user_presence:
                return

            presence = self.user_presence[user_id]
            presence.remove_connection(connection_id)

            # If user has no more connections, mark as offline
            if not presence.is_online():
                presence_event = PresenceEvent(
                    user_id=user_id,
                    username=presence.username,
                    status="offline",
                    last_seen=presence.last_seen,
                )

                # Broadcast to subscribers
                await self._broadcast_presence_update(user_id, presence_event)

                logger.info(f"User {user_id} offline")
            else:
                logger.info(
                    f"User {user_id} disconnected (remaining connections: {len(presence.connections)})"
                )

            self._update_stats()

        except Exception as e:
            logger.error(f"Error handling user disconnection: {e}")

    async def handle_status_update(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """
        Handle user status update

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Status update data
        """
        try:
            if user_id not in self.user_presence:
                return

            presence = self.user_presence[user_id]

            # Update status
            new_status = data.get("status")
            if new_status in ["online", "away", "busy"]:
                presence.status = new_status

            # Update status message
            if "status_message" in data:
                presence.status_message = data.get("status_message")

            # Update location
            if "location" in data:
                presence.location = data.get("location")

            # Update last seen
            presence.last_seen = datetime.utcnow()

            # Create presence event
            presence_event = PresenceEvent(
                user_id=user_id,
                username=presence.username,
                status=presence.status,
                status_message=presence.status_message,
                location=presence.location,
                last_seen=presence.last_seen,
            )

            # Broadcast to subscribers
            await self._broadcast_presence_update(user_id, presence_event)

            self._update_stats()

            logger.debug(
                f"User {user_id} status updated: {presence.status} "
                f"({presence.status_message or 'no message'})"
            )

        except Exception as e:
            logger.error(f"Error handling status update: {e}")

    async def subscribe_to_presence(self, subscriber_id: str, user_ids: List[str]):
        """
        Subscribe to presence updates for specific users

        Args:
            subscriber_id: User who wants to receive updates
            user_ids: List of user IDs to watch
        """
        try:
            for user_id in user_ids:
                self.presence_subscriptions[user_id].add(subscriber_id)

            # Send current presence state for all subscribed users
            for user_id in user_ids:
                presence = self.user_presence.get(user_id)
                if presence:
                    presence_event = PresenceEvent(
                        user_id=user_id,
                        username=presence.username,
                        status=presence.status,
                        status_message=presence.status_message,
                        location=presence.location,
                        last_seen=presence.last_seen,
                    )

                    ws_event = WebSocketEvent(
                        event_type=EventType.PRESENCE_UPDATE,
                        sender_id=user_id,
                        data=presence_event.dict(),
                    )

                    await self.connection_manager.send_to_user(
                        subscriber_id, ws_event.dict()
                    )

            logger.debug(
                f"User {subscriber_id} subscribed to presence of {len(user_ids)} users"
            )

        except Exception as e:
            logger.error(f"Error subscribing to presence: {e}")

    async def unsubscribe_from_presence(self, subscriber_id: str, user_ids: List[str]):
        """
        Unsubscribe from presence updates

        Args:
            subscriber_id: User who wants to stop receiving updates
            user_ids: List of user IDs to stop watching
        """
        try:
            for user_id in user_ids:
                self.presence_subscriptions[user_id].discard(subscriber_id)

            logger.debug(
                f"User {subscriber_id} unsubscribed from presence of {len(user_ids)} users"
            )

        except Exception as e:
            logger.error(f"Error unsubscribing from presence: {e}")

    async def _broadcast_presence_update(
        self, user_id: str, presence_event: PresenceEvent
    ):
        """
        Broadcast presence update to subscribers

        Args:
            user_id: User whose presence changed
            presence_event: Presence event to broadcast
        """
        subscribers = self.presence_subscriptions.get(user_id, set())

        if not subscribers:
            return

        ws_event = WebSocketEvent(
            event_type=EventType.PRESENCE_UPDATE,
            sender_id=user_id,
            data=presence_event.dict(),
        )

        # Send to all subscribers
        for subscriber_id in subscribers:
            await self.connection_manager.send_to_user(subscriber_id, ws_event.dict())

        logger.debug(
            f"Presence update for {user_id} sent to {len(subscribers)} subscribers"
        )

    def _update_stats(self):
        """Update presence statistics"""
        stats = {"online": 0, "away": 0, "busy": 0, "offline": 0}

        for presence in self.user_presence.values():
            status = presence.status
            if status in stats:
                stats[status] += 1

        self.presence_stats = {
            "total_online": stats["online"],
            "total_away": stats["away"],
            "total_busy": stats["busy"],
            "total_offline": stats["offline"],
        }

    def get_user_presence(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get presence information for a user

        Args:
            user_id: User ID

        Returns:
            Presence data or None
        """
        presence = self.user_presence.get(user_id)
        return presence.to_dict() if presence else None

    def get_online_users(self) -> List[Dict[str, Any]]:
        """Get list of all online users with their presence info"""
        return [
            presence.to_dict()
            for presence in self.user_presence.values()
            if presence.is_online()
        ]

    def get_users_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get users with specific status

        Args:
            status: Status to filter by (online, offline, away, busy)

        Returns:
            List of user presence data
        """
        return [
            presence.to_dict()
            for presence in self.user_presence.values()
            if presence.status == status
        ]

    def is_user_online(self, user_id: str) -> bool:
        """Check if user is online"""
        presence = self.user_presence.get(user_id)
        return presence.is_online() if presence else False

    def get_stats(self) -> Dict[str, Any]:
        """Get presence statistics"""
        return {
            **self.presence_stats,
            "total_tracked_users": len(self.user_presence),
            "total_subscriptions": sum(
                len(subs) for subs in self.presence_subscriptions.values()
            ),
        }

    async def broadcast_bulk_presence(self, user_ids: List[str]):
        """
        Broadcast presence info for multiple users to all subscribers

        Args:
            user_ids: List of user IDs to broadcast
        """
        try:
            for user_id in user_ids:
                presence = self.user_presence.get(user_id)
                if presence:
                    presence_event = PresenceEvent(
                        user_id=user_id,
                        username=presence.username,
                        status=presence.status,
                        status_message=presence.status_message,
                        location=presence.location,
                        last_seen=presence.last_seen,
                    )

                    await self._broadcast_presence_update(user_id, presence_event)

        except Exception as e:
            logger.error(f"Error broadcasting bulk presence: {e}")

    def cleanup_offline_users(self, max_offline_age_days: int = 30):
        """
        Remove presence records for users who have been offline for too long

        Args:
            max_offline_age_days: Maximum days to keep offline user presence
        """
        cutoff_time = datetime.utcnow() - timedelta(days=max_offline_age_days)
        removed_count = 0

        for user_id in list(self.user_presence.keys()):
            presence = self.user_presence[user_id]
            if not presence.is_online() and presence.last_seen < cutoff_time:
                del self.user_presence[user_id]
                removed_count += 1

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} stale presence records")

        return removed_count
