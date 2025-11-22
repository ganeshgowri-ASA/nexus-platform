"""Event subscription service"""

from sqlalchemy.orm import Session
from typing import List, Optional
from modules.webhooks.models import WebhookEvent


class EventService:
    """Service for managing webhook event subscriptions"""

    @staticmethod
    def add_event_subscription(db: Session, webhook_id: int, event_type: str) -> WebhookEvent:
        """Add an event subscription to a webhook"""
        # Check if subscription already exists
        existing = db.query(WebhookEvent).filter(
            WebhookEvent.webhook_id == webhook_id,
            WebhookEvent.event_type == event_type
        ).first()

        if existing:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing

        # Create new subscription
        event = WebhookEvent(
            webhook_id=webhook_id,
            event_type=event_type,
            is_active=True
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def remove_event_subscription(db: Session, webhook_id: int, event_type: str) -> bool:
        """Remove an event subscription"""
        event = db.query(WebhookEvent).filter(
            WebhookEvent.webhook_id == webhook_id,
            WebhookEvent.event_type == event_type
        ).first()

        if not event:
            return False

        db.delete(event)
        db.commit()
        return True

    @staticmethod
    def toggle_event_subscription(db: Session, webhook_id: int, event_type: str, is_active: bool) -> Optional[WebhookEvent]:
        """Toggle an event subscription on/off"""
        event = db.query(WebhookEvent).filter(
            WebhookEvent.webhook_id == webhook_id,
            WebhookEvent.event_type == event_type
        ).first()

        if not event:
            return None

        event.is_active = is_active
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def list_event_subscriptions(db: Session, webhook_id: int) -> List[WebhookEvent]:
        """List all event subscriptions for a webhook"""
        return db.query(WebhookEvent).filter(
            WebhookEvent.webhook_id == webhook_id
        ).all()

    @staticmethod
    def get_available_event_types() -> List[str]:
        """Get list of available event types"""
        return [
            "user.created",
            "user.updated",
            "user.deleted",
            "order.created",
            "order.updated",
            "order.completed",
            "order.cancelled",
            "payment.completed",
            "payment.failed",
            "project.created",
            "project.updated",
            "project.completed",
            "document.created",
            "document.updated",
            "document.shared",
            "meeting.scheduled",
            "meeting.started",
            "meeting.ended",
            "email.received",
            "email.sent",
            "task.created",
            "task.completed",
            "analytics.report_generated",
        ]
