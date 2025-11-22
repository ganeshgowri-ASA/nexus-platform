"""Webhook delivery API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from modules.webhooks.models.base import get_db
from modules.webhooks.models.webhook_delivery import DeliveryStatus
from modules.webhooks.services import DeliveryService
from modules.webhooks.schemas import (
    WebhookDeliveryResponse,
    WebhookDeliveryDetailResponse
)
from modules.webhooks.tasks.delivery_tasks import send_webhook

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.get("/", response_model=List[WebhookDeliveryResponse])
def list_deliveries(
    webhook_id: Optional[int] = None,
    status: Optional[DeliveryStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List webhook deliveries with filters

    - **webhook_id**: Filter by webhook ID
    - **status**: Filter by delivery status
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    return DeliveryService.list_deliveries(db, webhook_id, status, skip, limit)


@router.get("/{delivery_id}", response_model=WebhookDeliveryDetailResponse)
def get_delivery(delivery_id: int, db: Session = Depends(get_db)):
    """Get detailed delivery information"""
    delivery = DeliveryService.get_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery {delivery_id} not found"
        )
    return delivery


@router.post("/{delivery_id}/retry", response_model=WebhookDeliveryResponse)
def retry_delivery(delivery_id: int, db: Session = Depends(get_db)):
    """Manually retry a failed delivery"""
    delivery = DeliveryService.get_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Delivery {delivery_id} not found"
        )

    if delivery.status == DeliveryStatus.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot retry a successful delivery"
        )

    if delivery.attempt_count >= delivery.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Delivery has exceeded maximum retry attempts"
        )

    # Reset attempt count and queue for retry
    delivery.attempt_count = 0
    delivery.status = DeliveryStatus.PENDING
    db.commit()

    # Queue delivery task
    send_webhook.delay(delivery.id)

    db.refresh(delivery)
    return delivery


@router.get("/webhooks/{webhook_id}/deliveries", response_model=List[WebhookDeliveryResponse])
def get_webhook_deliveries(
    webhook_id: int,
    status: Optional[DeliveryStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all deliveries for a specific webhook"""
    return DeliveryService.list_deliveries(db, webhook_id, status, skip, limit)
