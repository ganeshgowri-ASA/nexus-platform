"""
Notifications - Push notification system for chat events.

Manages desktop notifications, mobile push, email notifications,
and notification preferences with Do Not Disturb mode.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum

from .models import Notification, NotificationType, User

logger = logging.getLogger(__name__)


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    PUSH = "push"  # Desktop/mobile push
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"


class Notifications:
    """
    Manages notification system.

    Handles:
    - Push notifications (desktop/mobile)
    - Email notifications
    - In-app notifications
    - Notification preferences
    - Do Not Disturb mode
    - Notification grouping
    - Custom sounds

    Example:
        >>> notif = Notifications(engine)
        >>> await notif.send_notification(user_id, "New Message", "Hello!")
        >>> await notif.set_dnd_mode(user_id, True)
    """

    def __init__(self, engine):
        """
        Initialize notifications manager.

        Args:
            engine: Reference to the ChatEngine
        """
        self.engine = engine
        self._notifications: Dict[UUID, List[Notification]] = {}  # user_id -> notifications
        self._preferences: Dict[UUID, Dict] = {}  # user_id -> preferences
        self._dnd_mode: Dict[UUID, bool] = {}  # user_id -> is_dnd
        logger.info("Notifications initialized")

    async def send_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        notification_type: NotificationType = NotificationType.MESSAGE,
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None
    ) -> Notification:
        """
        Send a notification to a user.

        Args:
            user_id: ID of the user
            title: Notification title
            body: Notification body
            notification_type: Type of notification
            data: Additional data
            priority: Priority level
            channels: Delivery channels (default: all enabled)

        Returns:
            Created Notification object
        """
        # Check DND mode
        if self._dnd_mode.get(user_id, False):
            if priority != NotificationPriority.URGENT:
                logger.debug(f"Notification blocked by DND for user {user_id}")
                return None

        # Check user preferences
        prefs = await self.get_preferences(user_id)

        if not self._should_send(user_id, notification_type, prefs):
            logger.debug(f"Notification filtered by preferences for user {user_id}")
            return None

        # Create notification
        notification = Notification(
            id=uuid4(),
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data or {},
            created_at=datetime.utcnow()
        )

        # Store notification
        if user_id not in self._notifications:
            self._notifications[user_id] = []

        self._notifications[user_id].append(notification)

        # In production: save to database
        # INSERT INTO notifications ...

        # Determine delivery channels
        if not channels:
            channels = prefs.get('channels', [NotificationChannel.PUSH, NotificationChannel.IN_APP])

        # Send through channels
        for channel in channels:
            await self._send_through_channel(notification, channel, priority)

        logger.info(f"Notification sent to user {user_id}: {title}")
        return notification

    async def get_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: ID of the user
            unread_only: Only return unread notifications
            limit: Maximum notifications
            offset: Number to skip

        Returns:
            List of Notification objects
        """
        notifications = self._notifications.get(user_id, [])

        if unread_only:
            notifications = [n for n in notifications if not n.is_read]

        # Sort by created_at descending
        notifications.sort(key=lambda x: x.created_at, reverse=True)

        return notifications[offset:offset + limit]

    async def mark_as_read(
        self,
        user_id: UUID,
        notification_id: Optional[UUID] = None
    ) -> bool:
        """
        Mark notification(s) as read.

        Args:
            user_id: ID of the user
            notification_id: ID of notification (None = mark all as read)

        Returns:
            True if successful
        """
        if user_id not in self._notifications:
            return False

        if notification_id:
            # Mark specific notification
            for notif in self._notifications[user_id]:
                if notif.id == notification_id:
                    notif.is_read = True
                    notif.read_at = datetime.utcnow()
                    break
        else:
            # Mark all as read
            for notif in self._notifications[user_id]:
                notif.is_read = True
                notif.read_at = datetime.utcnow()

        # In production: update database
        # UPDATE notifications SET is_read = TRUE, read_at = NOW() WHERE ...

        logger.info(f"Notifications marked as read for user {user_id}")
        return True

    async def delete_notification(
        self,
        user_id: UUID,
        notification_id: UUID
    ) -> bool:
        """
        Delete a notification.

        Args:
            user_id: ID of the user
            notification_id: ID of the notification

        Returns:
            True if deleted
        """
        if user_id in self._notifications:
            self._notifications[user_id] = [
                n for n in self._notifications[user_id]
                if n.id != notification_id
            ]
            return True

        return False

    async def get_unread_count(self, user_id: UUID) -> int:
        """
        Get count of unread notifications.

        Args:
            user_id: ID of the user

        Returns:
            Count of unread notifications
        """
        notifications = self._notifications.get(user_id, [])
        return sum(1 for n in notifications if not n.is_read)

    async def set_dnd_mode(
        self,
        user_id: UUID,
        enabled: bool,
        until: Optional[datetime] = None
    ) -> bool:
        """
        Enable/disable Do Not Disturb mode.

        Args:
            user_id: ID of the user
            enabled: True to enable DND
            until: Optional time to auto-disable DND

        Returns:
            True if successful
        """
        self._dnd_mode[user_id] = enabled

        # In production: save to database and schedule auto-disable
        if until:
            # Schedule task to disable DND at 'until' time
            pass

        logger.info(f"DND mode {'enabled' if enabled else 'disabled'} for user {user_id}")
        return True

    async def is_dnd_enabled(self, user_id: UUID) -> bool:
        """
        Check if DND mode is enabled for a user.

        Args:
            user_id: ID of the user

        Returns:
            True if DND is enabled
        """
        return self._dnd_mode.get(user_id, False)

    async def set_preferences(
        self,
        user_id: UUID,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Set notification preferences for a user.

        Args:
            user_id: ID of the user
            preferences: Preferences dictionary

        Returns:
            Updated preferences
        """
        if user_id not in self._preferences:
            self._preferences[user_id] = self._get_default_preferences()

        self._preferences[user_id].update(preferences)

        # In production: save to database
        # UPDATE users SET notification_preferences = ... WHERE id = user_id

        logger.info(f"Notification preferences updated for user {user_id}")
        return self._preferences[user_id]

    async def get_preferences(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get notification preferences for a user.

        Args:
            user_id: ID of the user

        Returns:
            Preferences dictionary
        """
        if user_id not in self._preferences:
            self._preferences[user_id] = self._get_default_preferences()

        return self._preferences[user_id].copy()

    async def notify_mention(
        self,
        mentioned_user_id: UUID,
        mentioner_id: UUID,
        message_id: UUID,
        message_preview: str
    ) -> Notification:
        """
        Send notification for a mention.

        Args:
            mentioned_user_id: ID of user who was mentioned
            mentioner_id: ID of user who mentioned
            message_id: ID of the message
            message_preview: Preview of the message

        Returns:
            Created Notification object
        """
        return await self.send_notification(
            user_id=mentioned_user_id,
            title="You were mentioned",
            body=f"in a message: {message_preview[:50]}...",
            notification_type=NotificationType.MENTION,
            data={
                "mentioner_id": str(mentioner_id),
                "message_id": str(message_id)
            },
            priority=NotificationPriority.HIGH
        )

    async def notify_reply(
        self,
        user_id: UUID,
        replier_id: UUID,
        message_id: UUID,
        reply_preview: str
    ) -> Notification:
        """
        Send notification for a reply to user's message.

        Args:
            user_id: ID of original message author
            replier_id: ID of user who replied
            message_id: ID of the reply message
            reply_preview: Preview of the reply

        Returns:
            Created Notification object
        """
        return await self.send_notification(
            user_id=user_id,
            title="New Reply",
            body=f"Someone replied: {reply_preview[:50]}...",
            notification_type=NotificationType.REPLY,
            data={
                "replier_id": str(replier_id),
                "message_id": str(message_id)
            }
        )

    async def notify_channel_invite(
        self,
        user_id: UUID,
        inviter_id: UUID,
        channel_id: UUID,
        channel_name: str
    ) -> Notification:
        """
        Send notification for channel invitation.

        Args:
            user_id: ID of invited user
            inviter_id: ID of user who invited
            channel_id: ID of the channel
            channel_name: Name of the channel

        Returns:
            Created Notification object
        """
        return await self.send_notification(
            user_id=user_id,
            title=f"Invited to {channel_name}",
            body="You've been invited to join a channel",
            notification_type=NotificationType.INVITE,
            data={
                "inviter_id": str(inviter_id),
                "channel_id": str(channel_id)
            }
        )

    # Private helper methods
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default notification preferences."""
        return {
            "channels": [NotificationChannel.PUSH, NotificationChannel.IN_APP],
            "enabled_types": [
                NotificationType.MESSAGE,
                NotificationType.MENTION,
                NotificationType.REPLY,
                NotificationType.REACTION,
                NotificationType.INVITE
            ],
            "quiet_hours": {
                "enabled": False,
                "start": "22:00",
                "end": "08:00"
            },
            "sounds": {
                "enabled": True,
                "volume": 0.7
            },
            "email_digest": {
                "enabled": False,
                "frequency": "daily"
            }
        }

    def _should_send(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        preferences: Dict[str, Any]
    ) -> bool:
        """Check if notification should be sent based on preferences."""
        # Check if type is enabled
        enabled_types = preferences.get('enabled_types', [])

        if notification_type not in enabled_types:
            return False

        # Check quiet hours
        quiet_hours = preferences.get('quiet_hours', {})

        if quiet_hours.get('enabled', False):
            now = datetime.utcnow().time()
            start = datetime.strptime(quiet_hours['start'], '%H:%M').time()
            end = datetime.strptime(quiet_hours['end'], '%H:%M').time()

            if start <= now <= end:
                return False

        return True

    async def _send_through_channel(
        self,
        notification: Notification,
        channel: NotificationChannel,
        priority: NotificationPriority
    ) -> bool:
        """Send notification through specific channel."""
        if channel == NotificationChannel.PUSH:
            return await self._send_push_notification(notification, priority)
        elif channel == NotificationChannel.EMAIL:
            return await self._send_email_notification(notification)
        elif channel == NotificationChannel.SMS:
            return await self._send_sms_notification(notification)
        elif channel == NotificationChannel.IN_APP:
            # In-app notifications are just stored, already done
            return True

        return False

    async def _send_push_notification(
        self,
        notification: Notification,
        priority: NotificationPriority
    ) -> bool:
        """Send push notification (desktop/mobile)."""
        # In production: integrate with Firebase Cloud Messaging, APNs, etc.
        logger.debug(f"Push notification sent: {notification.title}")
        return True

    async def _send_email_notification(self, notification: Notification) -> bool:
        """Send email notification."""
        # In production: integrate with email service (SendGrid, SES, etc.)
        logger.debug(f"Email notification sent: {notification.title}")
        return True

    async def _send_sms_notification(self, notification: Notification) -> bool:
        """Send SMS notification."""
        # In production: integrate with SMS service (Twilio, etc.)
        logger.debug(f"SMS notification sent: {notification.title}")
        return True
