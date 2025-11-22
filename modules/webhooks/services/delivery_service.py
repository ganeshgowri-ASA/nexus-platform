"""Webhook delivery service"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from modules.webhooks.models import WebhookDelivery, Webhook
from modules.webhooks.models.webhook_delivery import DeliveryStatus
from modules.webhooks.schemas import WebhookStats


class DeliveryService:
    """Service for managing webhook deliveries"""

    @staticmethod
    def create_delivery(
        db: Session,
        webhook_id: int,
        event_type: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        max_attempts: int = 5
    ) -> WebhookDelivery:
        """Create a new webhook delivery"""
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            event_id=event_id,
            payload=payload,
            status=DeliveryStatus.PENDING,
            attempt_count=0,
            max_attempts=max_attempts
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return delivery

    @staticmethod
    def get_delivery(db: Session, delivery_id: int) -> Optional[WebhookDelivery]:
        """Get a delivery by ID"""
        return db.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).first()

    @staticmethod
    def list_deliveries(
        db: Session,
        webhook_id: Optional[int] = None,
        status: Optional[DeliveryStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """List deliveries with filters"""
        query = db.query(WebhookDelivery).order_by(WebhookDelivery.created_at.desc())

        if webhook_id:
            query = query.filter(WebhookDelivery.webhook_id == webhook_id)
        if status:
            query = query.filter(WebhookDelivery.status == status)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_delivery_status(
        db: Session,
        delivery_id: int,
        status: DeliveryStatus,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        response_headers: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[WebhookDelivery]:
        """Update delivery status and response details"""
        delivery = db.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).first()
        if not delivery:
            return None

        delivery.status = status
        delivery.status_code = status_code
        delivery.response_body = response_body
        delivery.response_headers = response_headers
        delivery.error_message = error_message

        if status == DeliveryStatus.SENDING:
            delivery.sent_at = datetime.utcnow()
        elif status in [DeliveryStatus.SUCCESS, DeliveryStatus.FAILED]:
            delivery.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(delivery)
        return delivery

    @staticmethod
    def increment_attempt(db: Session, delivery_id: int, next_retry_delay: int) -> Optional[WebhookDelivery]:
        """Increment delivery attempt count and set next retry time"""
        delivery = db.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).first()
        if not delivery:
            return None

        delivery.attempt_count += 1
        delivery.status = DeliveryStatus.RETRYING
        delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=next_retry_delay)

        db.commit()
        db.refresh(delivery)
        return delivery

    @staticmethod
    def get_pending_retries(db: Session) -> List[WebhookDelivery]:
        """Get deliveries that are ready for retry"""
        now = datetime.utcnow()
        return db.query(WebhookDelivery).filter(
            and_(
                WebhookDelivery.status == DeliveryStatus.RETRYING,
                WebhookDelivery.next_retry_at <= now,
                WebhookDelivery.attempt_count < WebhookDelivery.max_attempts
            )
        ).all()

    @staticmethod
    def get_webhook_stats(db: Session, webhook_id: int, days: int = 7) -> WebhookStats:
        """Get webhook delivery statistics"""
        since_date = datetime.utcnow() - timedelta(days=days)

        # Total deliveries
        total = db.query(func.count(WebhookDelivery.id)).filter(
            and_(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.created_at >= since_date
            )
        ).scalar() or 0

        # Successful deliveries
        successful = db.query(func.count(WebhookDelivery.id)).filter(
            and_(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.status == DeliveryStatus.SUCCESS,
                WebhookDelivery.created_at >= since_date
            )
        ).scalar() or 0

        # Failed deliveries
        failed = db.query(func.count(WebhookDelivery.id)).filter(
            and_(
                WebhookDelivery.webhook_id == webhook_id,
                WebhookDelivery.status == DeliveryStatus.FAILED,
                WebhookDelivery.created_at >= since_date
            )
        ).scalar() or 0

        # Pending deliveries
        pending = db.query(func.count(WebhookDelivery.id)).filter(
            and_(
                WebhookDelivery.webhook_id == webhook_id,
                or_(
                    WebhookDelivery.status == DeliveryStatus.PENDING,
                    WebhookDelivery.status == DeliveryStatus.RETRYING
                ),
                WebhookDelivery.created_at >= since_date
            )
        ).scalar() or 0

        # Success rate
        success_rate = (successful / total * 100) if total > 0 else 0.0

        # Average response time (placeholder - would need to track timing)
        average_response_time = None

        return WebhookStats(
            total_deliveries=total,
            successful_deliveries=successful,
            failed_deliveries=failed,
            pending_deliveries=pending,
            success_rate=round(success_rate, 2),
            average_response_time=average_response_time
        )

    @staticmethod
    def cleanup_old_deliveries(db: Session, days: int = 30) -> int:
        """Delete old delivery logs"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(WebhookDelivery).filter(
            WebhookDelivery.created_at < cutoff_date
        ).delete()
        db.commit()
        return deleted
