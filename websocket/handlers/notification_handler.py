"""
Notification Handler

Handles real-time notifications and alerts.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..events import (
    EventType,
    WebSocketEvent,
    NotificationEvent,
)

logger = logging.getLogger(__name__)


class NotificationHandler:
    """
    Handles notification-related WebSocket events:
    - Real-time notifications
    - Notification delivery
    - Read/unread status
    - Notification clearing
    - Priority-based routing
    """

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager

        # Notification storage (in-memory cache)
        self.user_notifications: Dict[str, List[NotificationEvent]] = defaultdict(
            list
        )  # user_id -> [notifications]
        self.max_notifications_per_user = 100

        # Notification stats
        self.notification_stats = {
            "total_sent": 0,
            "total_read": 0,
            "total_cleared": 0,
        }

        logger.info("NotificationHandler initialized")

    async def send_notification(self, user_id: str, notification: NotificationEvent):
        """
        Send notification to a user

        Args:
            user_id: Target user ID
            notification: Notification event to send
        """
        try:
            # Store notification
            self._store_notification(user_id, notification)

            # Create WebSocket event
            ws_event = WebSocketEvent(
                event_type=EventType.NOTIFICATION,
                sender_id="system",
                data=notification.dict(),
            )

            # Send to user
            sent_count = await self.connection_manager.send_to_user(
                user_id, ws_event.dict()
            )

            self.notification_stats["total_sent"] += 1

            if sent_count > 0:
                logger.info(
                    f"Notification {notification.notification_id} sent to user {user_id} "
                    f"(priority: {notification.priority}, type: {notification.notification_type})"
                )
            else:
                logger.info(
                    f"Notification {notification.notification_id} queued for offline user {user_id}"
                )

        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    async def send_bulk_notifications(
        self, user_ids: List[str], notification_template: Dict[str, Any]
    ):
        """
        Send same notification to multiple users

        Args:
            user_ids: List of target user IDs
            notification_template: Base notification data
        """
        try:
            sent_count = 0

            for user_id in user_ids:
                # Create unique notification for each user
                notification = NotificationEvent(
                    notification_id=f"notif_{uuid.uuid4().hex[:16]}",
                    user_id=user_id,
                    **notification_template,
                )

                await self.send_notification(user_id, notification)
                sent_count += 1

            logger.info(
                f"Bulk notification sent to {sent_count} users "
                f"(type: {notification_template.get('notification_type')})"
            )

        except Exception as e:
            logger.error(f"Error sending bulk notifications: {e}")

    async def handle_read(self, connection_id: str, user_id: str, data: Dict[str, Any]):
        """
        Handle notification read event

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Read event data
        """
        try:
            notification_id = data.get("notification_id")

            if not notification_id:
                return

            # Mark notification as read
            notifications = self.user_notifications.get(user_id, [])
            for notif in notifications:
                if notif.notification_id == notification_id:
                    notif.read = True
                    break

            self.notification_stats["total_read"] += 1

            # Send confirmation
            ws_event = WebSocketEvent(
                event_type=EventType.NOTIFICATION_READ,
                sender_id=user_id,
                data={
                    "notification_id": notification_id,
                    "read_at": datetime.utcnow().isoformat(),
                },
            )

            await self.connection_manager.send_to_connection(
                connection_id, ws_event.dict()
            )

            logger.debug(f"Notification {notification_id} marked as read by {user_id}")

        except Exception as e:
            logger.error(f"Error handling notification read: {e}")

    async def handle_clear(
        self, connection_id: str, user_id: str, data: Dict[str, Any]
    ):
        """
        Handle notification clear event

        Args:
            connection_id: Connection ID
            user_id: User ID
            data: Clear event data
        """
        try:
            notification_id = data.get("notification_id")
            clear_all = data.get("clear_all", False)

            if clear_all:
                # Clear all notifications for user
                cleared_count = len(self.user_notifications.get(user_id, []))
                self.user_notifications[user_id] = []

                self.notification_stats["total_cleared"] += cleared_count

                logger.info(f"Cleared {cleared_count} notifications for user {user_id}")
            elif notification_id:
                # Clear specific notification
                notifications = self.user_notifications.get(user_id, [])
                self.user_notifications[user_id] = [
                    n for n in notifications if n.notification_id != notification_id
                ]

                self.notification_stats["total_cleared"] += 1

                logger.debug(f"Notification {notification_id} cleared for user {user_id}")

            # Send confirmation
            ws_event = WebSocketEvent(
                event_type=EventType.NOTIFICATION_CLEAR,
                sender_id=user_id,
                data={
                    "notification_id": notification_id if not clear_all else None,
                    "clear_all": clear_all,
                    "cleared_at": datetime.utcnow().isoformat(),
                },
            )

            await self.connection_manager.send_to_connection(
                connection_id, ws_event.dict()
            )

        except Exception as e:
            logger.error(f"Error handling notification clear: {e}")

    def _store_notification(self, user_id: str, notification: NotificationEvent):
        """Store notification in cache"""
        notifications = self.user_notifications[user_id]
        notifications.append(notification)

        # Limit notifications per user
        if len(notifications) > self.max_notifications_per_user:
            # Remove oldest read notifications first
            read_notifs = [n for n in notifications if n.read]
            if read_notifs:
                notifications.remove(read_notifs[0])
            else:
                # If no read notifications, remove oldest
                notifications.pop(0)

    async def cleanup_expired_notifications(self):
        """Remove expired notifications"""
        now = datetime.utcnow()
        removed_count = 0

        for user_id in list(self.user_notifications.keys()):
            notifications = self.user_notifications[user_id]
            original_count = len(notifications)

            # Filter out expired notifications
            self.user_notifications[user_id] = [
                n
                for n in notifications
                if not n.expires_at or n.expires_at > now
            ]

            removed_count += original_count - len(self.user_notifications[user_id])

        if removed_count > 0:
            logger.info(f"Removed {removed_count} expired notifications")

        return removed_count

    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        priority: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[NotificationEvent]:
        """
        Get notifications for a user

        Args:
            user_id: User ID
            unread_only: Return only unread notifications
            priority: Filter by priority level
            limit: Maximum number of notifications to return

        Returns:
            List of notifications
        """
        notifications = self.user_notifications.get(user_id, [])

        # Filter unread
        if unread_only:
            notifications = [n for n in notifications if not n.read]

        # Filter by priority
        if priority:
            notifications = [n for n in notifications if n.priority == priority]

        # Sort by timestamp (newest first)
        notifications.sort(key=lambda n: n.timestamp, reverse=True)

        # Apply limit
        if limit:
            notifications = notifications[:limit]

        return notifications

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        notifications = self.user_notifications.get(user_id, [])
        return sum(1 for n in notifications if not n.read)

    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        total_notifications = sum(
            len(notifs) for notifs in self.user_notifications.values()
        )
        total_users = len(self.user_notifications)

        return {
            **self.notification_stats,
            "total_cached": total_notifications,
            "users_with_notifications": total_users,
        }

    async def send_system_alert(
        self,
        message: str,
        severity: str = "info",
        target_users: Optional[List[str]] = None,
    ):
        """
        Send system-wide alert

        Args:
            message: Alert message
            severity: Alert severity (info, warning, critical)
            target_users: Optional list of specific users, or None for all online users
        """
        try:
            if target_users is None:
                # Send to all online users
                target_users = self.connection_manager.get_online_users()

            notification_template = {
                "title": "System Alert",
                "message": message,
                "notification_type": "alert",
                "priority": "high" if severity == "critical" else "normal",
                "data": {"severity": severity},
            }

            await self.send_bulk_notifications(target_users, notification_template)

            logger.info(
                f"System alert sent: {message} (severity: {severity}, "
                f"recipients: {len(target_users)})"
            )

        except Exception as e:
            logger.error(f"Error sending system alert: {e}")

    async def send_user_mention_notification(
        self, mentioned_user_id: str, mentioning_user: str, context: Dict[str, Any]
    ):
        """
        Send notification when user is mentioned

        Args:
            mentioned_user_id: User who was mentioned
            mentioning_user: User who made the mention
            context: Context information (message, location, etc.)
        """
        try:
            notification = NotificationEvent(
                notification_id=f"notif_{uuid.uuid4().hex[:16]}",
                user_id=mentioned_user_id,
                title=f"{mentioning_user} mentioned you",
                message=context.get("preview", "You were mentioned in a message"),
                notification_type="mention",
                priority="normal",
                action_url=context.get("url"),
                action_label="View",
                data=context,
            )

            await self.send_notification(mentioned_user_id, notification)

        except Exception as e:
            logger.error(f"Error sending mention notification: {e}")
