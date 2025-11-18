"""
Main notification service
Orchestrates all notification channels and features
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.notification import (
    Notification,
    NotificationStatus,
    NotificationChannel,
    NotificationPriority,
)
from backend.models.template import NotificationTemplate
from backend.models.delivery import DeliveryLog, DeliveryStatus

from backend.services.notifications.providers import (
    EmailProvider,
    SMSProvider,
    PushNotificationProvider,
    InAppProvider,
)
from backend.services.notifications.template_engine import TemplateEngine
from backend.services.notifications.scheduler import NotificationScheduler
from backend.services.notifications.delivery_tracker import DeliveryTracker
from backend.services.notifications.unsubscribe_manager import UnsubscribeManager


class NotificationService:
    """
    Main notification service
    Provides a unified interface for sending notifications across all channels
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize notification service

        Args:
            config: Configuration dictionary with provider settings
        """
        self.config = config or {}

        # Initialize providers
        email_config = self.config.get("email", {})
        sms_config = self.config.get("sms", {})
        push_config = self.config.get("push", {})
        in_app_config = self.config.get("in_app", {})

        self.providers = {
            NotificationChannel.EMAIL: EmailProvider(email_config),
            NotificationChannel.SMS: SMSProvider(sms_config),
            NotificationChannel.PUSH: PushNotificationProvider(push_config),
            NotificationChannel.IN_APP: InAppProvider(in_app_config),
        }

        # Initialize supporting services
        self.template_engine = TemplateEngine()
        self.scheduler = NotificationScheduler()
        self.delivery_tracker = DeliveryTracker()
        self.unsubscribe_manager = UnsubscribeManager()

    async def send(
        self,
        db: Session,
        user_id: str,
        channel: str,
        recipient: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        priority: str = "normal",
        template_id: Optional[str] = None,
        template_vars: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None,
        **kwargs
    ) -> Notification:
        """
        Send a notification

        Args:
            db: Database session
            user_id: User ID
            channel: Notification channel (email, sms, push, in_app)
            recipient: Recipient identifier (email, phone, device token, user_id)
            title: Notification title
            message: Notification message
            data: Additional structured data
            category: Notification category
            priority: Priority level (low, normal, high, urgent)
            template_id: Optional template ID
            template_vars: Variables for template rendering
            scheduled_at: Optional scheduled send time
            **kwargs: Additional channel-specific parameters

        Returns:
            Created Notification instance
        """
        # Check user preferences
        if category and not self.unsubscribe_manager.is_enabled(db, user_id, category, channel):
            raise NotificationBlockedError(
                f"User {user_id} has disabled {channel} notifications for {category}"
            )

        # Create notification record
        notification = Notification(
            user_id=user_id,
            channel=NotificationChannel(channel),
            recipient=recipient,
            title=title,
            message=message,
            data=data,
            category=category,
            priority=NotificationPriority(priority),
            template_id=template_id,
            template_vars=template_vars,
            scheduled_at=scheduled_at,
            status=NotificationStatus.SCHEDULED if scheduled_at else NotificationStatus.PENDING,
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        # If scheduled, let scheduler handle it
        if scheduled_at:
            return notification

        # Send immediately
        await self.send_notification(notification.id, db)

        return notification

    async def send_notification(self, notification_id: str, db: Session) -> bool:
        """
        Send a notification by ID

        Args:
            notification_id: Notification ID
            db: Database session

        Returns:
            True if sent successfully
        """
        # Get notification
        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notification:
            return False

        # Update status
        notification.status = NotificationStatus.PROCESSING
        db.commit()

        try:
            # Prepare content
            title = notification.title
            message = notification.message

            # Apply template if specified
            if notification.template_id:
                template = db.query(NotificationTemplate).filter(
                    NotificationTemplate.id == notification.template_id
                ).first()

                if template:
                    rendered = self.template_engine.render_template_from_db(
                        template,
                        notification.template_vars or {}
                    )
                    title = rendered.get("subject", title)
                    message = rendered.get("body", message)

            # Get provider
            provider = self.providers.get(notification.channel)
            if not provider:
                raise NotificationError(f"Unknown channel: {notification.channel}")

            # Send via provider
            result = await provider.send(
                recipient=notification.recipient,
                title=title,
                message=message,
                data=notification.data,
            )

            # Update notification status
            if result.success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                delivery_status = DeliveryStatus.SENT
            else:
                notification.status = NotificationStatus.FAILED
                notification.last_error = result.error_message
                notification.retry_count += 1
                delivery_status = DeliveryStatus.FAILED

            db.commit()

            # Log delivery
            self.delivery_tracker.log_delivery(
                db=db,
                notification_id=notification.id,
                channel=notification.channel.value,
                recipient=notification.recipient,
                status=delivery_status,
                provider=provider.get_provider_name(),
                provider_message_id=result.provider_message_id,
                provider_response=result.provider_response,
                error_code=result.error_code,
                error_message=result.error_message,
                processing_time_ms=result.processing_time_ms,
            )

            return result.success

        except Exception as e:
            # Mark as failed
            notification.status = NotificationStatus.FAILED
            notification.last_error = str(e)
            notification.retry_count += 1
            db.commit()

            # Log failure
            self.delivery_tracker.log_delivery(
                db=db,
                notification_id=notification.id,
                channel=notification.channel.value,
                recipient=notification.recipient,
                status=DeliveryStatus.FAILED,
                error_message=str(e),
            )

            raise NotificationError(f"Failed to send notification: {str(e)}")

    async def send_bulk(
        self,
        db: Session,
        user_ids: List[str],
        channel: str,
        title: str,
        message: str,
        category: Optional[str] = None,
        template_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send bulk notifications to multiple users

        Args:
            db: Database session
            user_ids: List of user IDs
            channel: Notification channel
            title: Notification title
            message: Notification message
            category: Notification category
            template_id: Optional template ID
            **kwargs: Additional parameters

        Returns:
            Dictionary with results
        """
        results = {
            "total": len(user_ids),
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "notifications": []
        }

        for user_id in user_ids:
            try:
                # Get recipient based on channel
                # This would typically query user profile for email/phone/device token
                recipient = user_id  # Placeholder

                notification = await self.send(
                    db=db,
                    user_id=user_id,
                    channel=channel,
                    recipient=recipient,
                    title=title,
                    message=message,
                    category=category,
                    template_id=template_id,
                    **kwargs
                )

                results["sent"] += 1
                results["notifications"].append(notification.id)

            except NotificationBlockedError:
                results["skipped"] += 1
            except Exception:
                results["failed"] += 1

        return results

    async def send_with_template(
        self,
        db: Session,
        user_id: str,
        channel: str,
        recipient: str,
        template_name: str,
        template_vars: Dict[str, Any],
        category: Optional[str] = None,
        **kwargs
    ) -> Notification:
        """
        Send notification using a template name

        Args:
            db: Database session
            user_id: User ID
            channel: Notification channel
            recipient: Recipient identifier
            template_name: Template name
            template_vars: Variables for template
            category: Notification category
            **kwargs: Additional parameters

        Returns:
            Created Notification
        """
        # Get template by name
        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.name == template_name,
            NotificationTemplate.active == True
        ).first()

        if not template:
            raise NotificationError(f"Template not found: {template_name}")

        # Render template
        rendered = self.template_engine.render_template_from_db(template, template_vars)

        return await self.send(
            db=db,
            user_id=user_id,
            channel=channel,
            recipient=recipient,
            title=rendered.get("subject", ""),
            message=rendered.get("body", ""),
            data={"html_body": rendered.get("html_body")} if rendered.get("html_body") else None,
            category=category or template.category,
            template_id=template.id,
            template_vars=template_vars,
            **kwargs
        )

    def get_notifications(
        self,
        db: Session,
        user_id: str,
        channel: Optional[str] = None,
        category: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications for a user

        Args:
            db: Database session
            user_id: User ID
            channel: Optional channel filter
            category: Optional category filter
            unread_only: Only return unread notifications
            limit: Maximum number to return

        Returns:
            List of notifications
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if channel:
            query = query.filter(Notification.channel == NotificationChannel(channel))

        if category:
            query = query.filter(Notification.category == category)

        if unread_only:
            query = query.filter(Notification.read == False)

        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    def mark_as_read(self, db: Session, notification_id: str, user_id: str) -> bool:
        """
        Mark a notification as read

        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID (for security)

        Returns:
            True if marked as read
        """
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if not notification:
            return False

        notification.read = True
        notification.read_at = datetime.utcnow()
        db.commit()

        return True

    def get_unread_count(self, db: Session, user_id: str) -> int:
        """
        Get unread notification count

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Count of unread notifications
        """
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.channel == NotificationChannel.IN_APP,
            Notification.read == False
        ).count()


class NotificationError(Exception):
    """General notification error"""
    pass


class NotificationBlockedError(Exception):
    """Notification blocked by user preferences"""
    pass
