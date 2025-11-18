"""
Delivery tracking service
Tracks and logs notification delivery status
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from backend.models.delivery import DeliveryLog, DeliveryStatus
from backend.models.notification import Notification, NotificationStatus


class DeliveryTracker:
    """
    Delivery tracking service
    Manages delivery logs and provides analytics
    """

    def __init__(self):
        """Initialize delivery tracker"""
        pass

    def log_delivery(
        self,
        db: Session,
        notification_id: str,
        channel: str,
        recipient: str,
        status: DeliveryStatus,
        provider: Optional[str] = None,
        provider_message_id: Optional[str] = None,
        provider_response: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[float] = None,
    ) -> DeliveryLog:
        """
        Create a delivery log entry

        Args:
            db: Database session
            notification_id: Notification ID
            channel: Delivery channel
            recipient: Recipient identifier
            status: Delivery status
            provider: Provider name
            provider_message_id: Provider's message ID
            provider_response: Provider's response data
            error_code: Error code if failed
            error_message: Error message if failed
            processing_time_ms: Processing time in milliseconds

        Returns:
            Created DeliveryLog instance
        """
        log = DeliveryLog(
            notification_id=notification_id,
            channel=channel,
            recipient=recipient,
            status=status,
            provider=provider,
            provider_message_id=provider_message_id,
            provider_response=provider_response,
            error_code=error_code,
            error_message=error_message,
            processing_time_ms=processing_time_ms,
        )

        # Set appropriate timestamps
        if status == DeliveryStatus.SENT:
            log.sent_at = datetime.utcnow()
        elif status == DeliveryStatus.DELIVERED:
            log.delivered_at = datetime.utcnow()
        elif status == DeliveryStatus.FAILED:
            log.failed_at = datetime.utcnow()

        db.add(log)
        db.commit()
        db.refresh(log)

        return log

    def update_delivery_status(
        self,
        db: Session,
        delivery_log_id: str,
        status: DeliveryStatus,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[DeliveryLog]:
        """
        Update delivery status (e.g., from sent to delivered)

        Args:
            db: Database session
            delivery_log_id: Delivery log ID
            status: New status
            metadata: Additional metadata

        Returns:
            Updated DeliveryLog or None if not found
        """
        log = db.query(DeliveryLog).filter(DeliveryLog.id == delivery_log_id).first()
        if not log:
            return None

        log.status = status

        # Update timestamps
        now = datetime.utcnow()
        if status == DeliveryStatus.DELIVERED:
            log.delivered_at = now
        elif status == DeliveryStatus.FAILED:
            log.failed_at = now
        elif status == DeliveryStatus.OPENED:
            log.opened_at = now
            log.open_count += 1
        elif status == DeliveryStatus.CLICKED:
            log.clicked_at = now
            log.click_count += 1

        if metadata:
            if log.metadata:
                log.metadata.update(metadata)
            else:
                log.metadata = metadata

        db.commit()
        db.refresh(log)

        return log

    def track_webhook(
        self,
        db: Session,
        provider_message_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> bool:
        """
        Track webhook events from providers (e.g., email opened, link clicked)

        Args:
            db: Database session
            provider_message_id: Provider's message ID
            event_type: Event type (opened, clicked, bounced, etc.)
            event_data: Event data from provider

        Returns:
            True if tracked successfully
        """
        # Find delivery log by provider message ID
        log = db.query(DeliveryLog).filter(
            DeliveryLog.provider_message_id == provider_message_id
        ).first()

        if not log:
            return False

        # Update based on event type
        now = datetime.utcnow()

        if event_type == "opened":
            log.opened_at = now
            log.open_count += 1
            log.status = DeliveryStatus.OPENED
        elif event_type == "clicked":
            log.clicked_at = now
            log.click_count += 1
            log.status = DeliveryStatus.CLICKED
        elif event_type == "bounced":
            log.status = DeliveryStatus.BOUNCED
        elif event_type == "delivered":
            log.delivered_at = now
            log.status = DeliveryStatus.DELIVERED

        # Store event data
        if log.metadata:
            if "events" not in log.metadata:
                log.metadata["events"] = []
            log.metadata["events"].append({
                "type": event_type,
                "timestamp": now.isoformat(),
                "data": event_data
            })
        else:
            log.metadata = {
                "events": [{
                    "type": event_type,
                    "timestamp": now.isoformat(),
                    "data": event_data
                }]
            }

        db.commit()
        return True

    def get_delivery_status(
        self,
        db: Session,
        notification_id: str
    ) -> Optional[DeliveryLog]:
        """
        Get delivery status for a notification

        Args:
            db: Database session
            notification_id: Notification ID

        Returns:
            DeliveryLog or None
        """
        return db.query(DeliveryLog).filter(
            DeliveryLog.notification_id == notification_id
        ).first()

    def get_delivery_analytics(
        self,
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get delivery analytics

        Args:
            db: Database session
            start_date: Start date for analytics
            end_date: End date for analytics
            channel: Optional channel filter

        Returns:
            Dictionary with analytics data
        """
        # Default to last 30 days
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        query = db.query(DeliveryLog).filter(
            and_(
                DeliveryLog.created_at >= start_date,
                DeliveryLog.created_at <= end_date
            )
        )

        if channel:
            query = query.filter(DeliveryLog.channel == channel)

        # Get counts by status
        status_counts = {}
        for status in DeliveryStatus:
            count = query.filter(DeliveryLog.status == status).count()
            status_counts[status.value] = count

        # Get total counts
        total = query.count()
        sent = query.filter(DeliveryLog.status.in_([
            DeliveryStatus.SENT,
            DeliveryStatus.DELIVERED,
            DeliveryStatus.OPENED,
            DeliveryStatus.CLICKED
        ])).count()

        # Calculate rates
        delivery_rate = (status_counts.get("delivered", 0) / sent * 100) if sent > 0 else 0
        open_rate = (status_counts.get("opened", 0) / sent * 100) if sent > 0 else 0
        click_rate = (status_counts.get("clicked", 0) / sent * 100) if sent > 0 else 0
        bounce_rate = (status_counts.get("bounced", 0) / sent * 100) if sent > 0 else 0

        # Get average processing time
        avg_processing_time = db.query(
            func.avg(DeliveryLog.processing_time_ms)
        ).filter(
            and_(
                DeliveryLog.created_at >= start_date,
                DeliveryLog.created_at <= end_date
            )
        ).scalar() or 0

        return {
            "total": total,
            "sent": sent,
            "status_counts": status_counts,
            "rates": {
                "delivery_rate": round(delivery_rate, 2),
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
                "bounce_rate": round(bounce_rate, 2),
            },
            "avg_processing_time_ms": round(avg_processing_time, 2),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "channel": channel,
        }

    def get_failed_deliveries(
        self,
        db: Session,
        limit: int = 100
    ) -> List[DeliveryLog]:
        """
        Get failed deliveries for retry

        Args:
            db: Database session
            limit: Maximum number to return

        Returns:
            List of failed delivery logs
        """
        return db.query(DeliveryLog).filter(
            DeliveryLog.status == DeliveryStatus.FAILED
        ).order_by(DeliveryLog.created_at.desc()).limit(limit).all()
