"""
In-app notification provider
Stores notifications in database for display within the application
"""
from typing import Dict, Any, Optional
from datetime import datetime

from backend.services.notifications.providers.base import (
    BaseNotificationProvider,
    NotificationResult,
)


class InAppProvider(BaseNotificationProvider):
    """
    In-app notification provider
    Stores notifications in the database for retrieval by the frontend
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize in-app notification provider

        Config options:
            - ttl_days: Time-to-live for notifications in days (default: 30)
            - max_notifications_per_user: Maximum notifications to keep per user (default: 100)
        """
        super().__init__(config)
        self.ttl_days = config.get("ttl_days", 30) if config else 30
        self.max_notifications_per_user = config.get("max_notifications_per_user", 100) if config else 100

    async def send(
        self,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> NotificationResult:
        """
        Send in-app notification (store in database)

        Args:
            recipient: User ID
            title: Notification title
            message: Notification message
            data: Additional data (action_url, icon, etc.)
            **kwargs: Additional parameters

        Returns:
            NotificationResult
        """
        start_time = datetime.utcnow()

        try:
            # Validate recipient
            if not self.validate_recipient(recipient):
                return NotificationResult(
                    success=False,
                    error_message=f"Invalid user ID: {recipient}",
                    error_code="INVALID_USER_ID",
                )

            # In-app notifications are stored in the database
            # The actual storage happens in the NotificationService
            # This provider just validates and returns success

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return NotificationResult(
                success=True,
                provider_message_id=f"in_app_{datetime.utcnow().timestamp()}",
                provider_response={
                    "backend": "in_app",
                    "recipient": recipient,
                    "stored": True,
                },
                processing_time_ms=processing_time,
            )

        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return NotificationResult(
                success=False,
                error_message=str(e),
                error_code="SEND_FAILED",
                processing_time_ms=processing_time,
            )

    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate user ID format
        Basic validation - just checks if it's not empty
        """
        return bool(recipient and len(recipient) > 0)

    def is_configured(self) -> bool:
        """In-app provider is always configured (uses database)"""
        return True

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark an in-app notification as read

        Args:
            notification_id: Notification ID
            user_id: User ID

        Returns:
            True if successful
        """
        # This would be implemented in the NotificationService
        # with database access
        return True

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user

        Args:
            user_id: User ID

        Returns:
            Count of unread notifications
        """
        # This would be implemented in the NotificationService
        # with database access
        return 0

    async def cleanup_old_notifications(self, user_id: str) -> int:
        """
        Clean up old notifications for a user

        Args:
            user_id: User ID

        Returns:
            Number of notifications deleted
        """
        # This would be implemented in the NotificationService
        # with database access
        return 0
