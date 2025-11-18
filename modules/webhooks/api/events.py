"""Event subscription and triggering API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from modules.webhooks.models.base import get_db
from modules.webhooks.services import EventService, WebhookService, DeliveryService
from modules.webhooks.schemas import (
    WebhookEventSchema,
    EventSubscriptionCreate,
    EventSubscriptionUpdate,
    EventTrigger
)
from modules.webhooks.tasks.delivery_tasks import send_webhook

router = APIRouter(tags=["events"])


@router.get("/events/available", response_model=List[str])
def get_available_events():
    """Get list of available event types"""
    return EventService.get_available_event_types()


@router.get("/webhooks/{webhook_id}/events", response_model=List[WebhookEventSchema])
def list_webhook_events(webhook_id: int, db: Session = Depends(get_db)):
    """List all event subscriptions for a webhook"""
    webhook = WebhookService.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    return EventService.list_event_subscriptions(db, webhook_id)


@router.post("/webhooks/{webhook_id}/events", response_model=WebhookEventSchema, status_code=status.HTTP_201_CREATED)
def add_event_subscription(
    webhook_id: int,
    event: EventSubscriptionCreate,
    db: Session = Depends(get_db)
):
    """Add an event subscription to a webhook"""
    webhook = WebhookService.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    return EventService.add_event_subscription(db, webhook_id, event.event_type)


@router.delete("/webhooks/{webhook_id}/events/{event_type}", status_code=status.HTTP_204_NO_CONTENT)
def remove_event_subscription(
    webhook_id: int,
    event_type: str,
    db: Session = Depends(get_db)
):
    """Remove an event subscription from a webhook"""
    success = EventService.remove_event_subscription(db, webhook_id, event_type)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event subscription not found"
        )


@router.patch("/webhooks/{webhook_id}/events/{event_type}", response_model=WebhookEventSchema)
def toggle_event_subscription(
    webhook_id: int,
    event_type: str,
    update: EventSubscriptionUpdate,
    db: Session = Depends(get_db)
):
    """Toggle an event subscription on/off"""
    event = EventService.toggle_event_subscription(db, webhook_id, event_type, update.is_active)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event subscription not found"
        )
    return event


@router.post("/events/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_event(event: EventTrigger, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger an event and send to all subscribed webhooks

    This will queue webhook deliveries for all active webhooks
    subscribed to the event type.

    Returns the number of webhooks that will be notified.
    """
    # Get all webhooks subscribed to this event type
    webhooks = WebhookService.get_webhooks_by_event_type(db, event.event_type)

    if not webhooks:
        return {
            "event_type": event.event_type,
            "event_id": event.event_id,
            "webhooks_notified": 0,
            "message": "No active webhooks subscribed to this event"
        }

    # Create deliveries for each webhook
    delivery_ids = []
    for webhook in webhooks:
        delivery = DeliveryService.create_delivery(
            db,
            webhook_id=webhook.id,
            event_type=event.event_type,
            payload=event.payload,
            event_id=event.event_id
        )
        delivery_ids.append(delivery.id)

        # Queue delivery task
        send_webhook.delay(delivery.id)

    return {
        "event_type": event.event_type,
        "event_id": event.event_id,
        "webhooks_notified": len(webhooks),
        "delivery_ids": delivery_ids,
        "message": f"Event queued for delivery to {len(webhooks)} webhook(s)"
    }
