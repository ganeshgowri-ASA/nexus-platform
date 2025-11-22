"""Webhook management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from modules.webhooks.models.base import get_db
from modules.webhooks.services import WebhookService, DeliveryService
from modules.webhooks.schemas import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookStats
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(webhook: WebhookCreate, db: Session = Depends(get_db)):
    """
    Create a new webhook endpoint with event subscriptions

    - **name**: Webhook name
    - **url**: Webhook endpoint URL
    - **event_types**: List of event types to subscribe to
    - **headers**: Optional custom headers
    - **timeout**: Request timeout in seconds
    """
    try:
        return WebhookService.create_webhook(db, webhook)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create webhook: {str(e)}"
        )


@router.get("/", response_model=List[WebhookResponse])
def list_webhooks(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    List all webhooks with pagination

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **is_active**: Filter by active status
    """
    return WebhookService.list_webhooks(db, skip, limit, is_active)


@router.get("/{webhook_id}", response_model=WebhookResponse)
def get_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Get a webhook by ID"""
    webhook = WebhookService.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    return webhook


@router.patch("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: int,
    webhook_update: WebhookUpdate,
    db: Session = Depends(get_db)
):
    """Update a webhook"""
    webhook = WebhookService.update_webhook(db, webhook_id, webhook_update)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    return webhook


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Delete a webhook and all associated data"""
    success = WebhookService.delete_webhook(db, webhook_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )


@router.post("/{webhook_id}/regenerate-secret")
def regenerate_secret(webhook_id: int, db: Session = Depends(get_db)):
    """Regenerate webhook secret for signature verification"""
    new_secret = WebhookService.regenerate_secret(db, webhook_id)
    if not new_secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    return {"webhook_id": webhook_id, "secret": new_secret}


@router.get("/{webhook_id}/stats", response_model=WebhookStats)
def get_webhook_stats(
    webhook_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get webhook delivery statistics

    - **days**: Number of days to include in statistics (default: 7)
    """
    webhook = WebhookService.get_webhook(db, webhook_id)
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found"
        )
    return DeliveryService.get_webhook_stats(db, webhook_id, days)
