"""Webhook CRUD service"""

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import secrets
from modules.webhooks.models import Webhook, WebhookEvent
from modules.webhooks.schemas import WebhookCreate, WebhookUpdate


class WebhookService:
    """Service for webhook CRUD operations"""

    @staticmethod
    def generate_secret(length: int = 32) -> str:
        """Generate a random secret for webhook signing"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def create_webhook(db: Session, webhook_data: WebhookCreate) -> Webhook:
        """Create a new webhook with event subscriptions"""
        # Create webhook
        webhook = Webhook(
            name=webhook_data.name,
            url=webhook_data.url,
            description=webhook_data.description,
            secret=WebhookService.generate_secret(),
            is_active=webhook_data.is_active,
            headers=webhook_data.headers or {},
            timeout=webhook_data.timeout,
            created_by=webhook_data.created_by,
        )
        db.add(webhook)
        db.flush()

        # Create event subscriptions
        for event_type in webhook_data.event_types:
            event = WebhookEvent(
                webhook_id=webhook.id,
                event_type=event_type,
                is_active=True
            )
            db.add(event)

        db.commit()
        db.refresh(webhook)
        return webhook

    @staticmethod
    def get_webhook(db: Session, webhook_id: int) -> Optional[Webhook]:
        """Get a webhook by ID with events"""
        return db.query(Webhook).options(
            joinedload(Webhook.events)
        ).filter(Webhook.id == webhook_id).first()

    @staticmethod
    def list_webhooks(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Webhook]:
        """List webhooks with pagination"""
        query = db.query(Webhook).options(joinedload(Webhook.events))

        if is_active is not None:
            query = query.filter(Webhook.is_active == is_active)

        return query.offset(skip).limit(limit).all()

    @staticmethod
    def update_webhook(db: Session, webhook_id: int, webhook_data: WebhookUpdate) -> Optional[Webhook]:
        """Update a webhook"""
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return None

        update_data = webhook_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(webhook, field, value)

        db.commit()
        db.refresh(webhook)
        return webhook

    @staticmethod
    def delete_webhook(db: Session, webhook_id: int) -> bool:
        """Delete a webhook"""
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return False

        db.delete(webhook)
        db.commit()
        return True

    @staticmethod
    def regenerate_secret(db: Session, webhook_id: int) -> Optional[str]:
        """Regenerate webhook secret"""
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return None

        new_secret = WebhookService.generate_secret()
        webhook.secret = new_secret
        db.commit()
        return new_secret

    @staticmethod
    def get_webhooks_by_event_type(db: Session, event_type: str) -> List[Webhook]:
        """Get all active webhooks subscribed to a specific event type"""
        return db.query(Webhook).join(
            WebhookEvent
        ).filter(
            Webhook.is_active == True,
            WebhookEvent.event_type == event_type,
            WebhookEvent.is_active == True
        ).all()
