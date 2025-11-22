"""
Notification API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from backend.database import get_db_session
from backend.services.notifications.notification_service import NotificationService
from backend.models.notification import Notification, NotificationChannel, NotificationPriority
from backend.models.template import NotificationTemplate
from backend.models.preference import NotificationPreference


router = APIRouter(prefix="/api/notifications", tags=["notifications"])

# Initialize notification service (in production, this would be dependency injection)
notification_service = NotificationService()


# Pydantic models for request/response
class SendNotificationRequest(BaseModel):
    """Request model for sending a notification"""
    user_id: str
    channel: str = Field(..., description="Channel: email, sms, push, in_app")
    recipient: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    priority: str = Field(default="normal", description="Priority: low, normal, high, urgent")
    template_id: Optional[str] = None
    template_vars: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None


class SendBulkNotificationRequest(BaseModel):
    """Request model for bulk notifications"""
    user_ids: List[str]
    channel: str
    title: str
    message: str
    category: Optional[str] = None
    template_id: Optional[str] = None


class SendTemplateNotificationRequest(BaseModel):
    """Request model for template-based notification"""
    user_id: str
    channel: str
    recipient: str
    template_name: str
    template_vars: Dict[str, Any]
    category: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class CreateTemplateRequest(BaseModel):
    """Request model for creating a template"""
    name: str
    description: Optional[str] = None
    category: str
    subject: Optional[str] = None
    body: str
    html_body: Optional[str] = None
    variables: Optional[List[str]] = None


class UpdatePreferenceRequest(BaseModel):
    """Request model for updating preferences"""
    category: str
    channel: str
    enabled: bool
    settings: Optional[Dict[str, Any]] = None


# Notification endpoints
@router.post("/send", response_model=Dict[str, Any])
async def send_notification(
    request: SendNotificationRequest,
    db: Session = Depends(get_db_session)
):
    """
    Send a notification

    Args:
        request: Notification details
        db: Database session

    Returns:
        Created notification details
    """
    try:
        notification = await notification_service.send(
            db=db,
            user_id=request.user_id,
            channel=request.channel,
            recipient=request.recipient,
            title=request.title,
            message=request.message,
            data=request.data,
            category=request.category,
            priority=request.priority,
            template_id=request.template_id,
            template_vars=request.template_vars,
            scheduled_at=request.scheduled_at,
        )

        return {
            "success": True,
            "notification_id": notification.id,
            "status": notification.status.value,
            "scheduled_at": notification.scheduled_at.isoformat() if notification.scheduled_at else None,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-bulk", response_model=Dict[str, Any])
async def send_bulk_notifications(
    request: SendBulkNotificationRequest,
    db: Session = Depends(get_db_session)
):
    """
    Send bulk notifications to multiple users

    Args:
        request: Bulk notification details
        db: Database session

    Returns:
        Bulk send results
    """
    try:
        results = await notification_service.send_bulk(
            db=db,
            user_ids=request.user_ids,
            channel=request.channel,
            title=request.title,
            message=request.message,
            category=request.category,
            template_id=request.template_id,
        )

        return {
            "success": True,
            **results
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/send-template", response_model=Dict[str, Any])
async def send_with_template(
    request: SendTemplateNotificationRequest,
    db: Session = Depends(get_db_session)
):
    """
    Send notification using a template

    Args:
        request: Template notification details
        db: Database session

    Returns:
        Created notification details
    """
    try:
        notification = await notification_service.send_with_template(
            db=db,
            user_id=request.user_id,
            channel=request.channel,
            recipient=request.recipient,
            template_name=request.template_name,
            template_vars=request.template_vars,
            category=request.category,
            scheduled_at=request.scheduled_at,
        )

        return {
            "success": True,
            "notification_id": notification.id,
            "status": notification.status.value,
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user/{user_id}", response_model=List[Dict[str, Any]])
def get_user_notifications(
    user_id: str,
    channel: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db_session)
):
    """
    Get notifications for a user

    Args:
        user_id: User ID
        channel: Optional channel filter
        category: Optional category filter
        unread_only: Only return unread notifications
        limit: Maximum number to return
        db: Database session

    Returns:
        List of notifications
    """
    notifications = notification_service.get_notifications(
        db=db,
        user_id=user_id,
        channel=channel,
        category=category,
        unread_only=unread_only,
        limit=limit
    )

    return [notif.to_dict() for notif in notifications]


@router.post("/{notification_id}/read")
def mark_as_read(
    notification_id: str,
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db_session)
):
    """
    Mark a notification as read

    Args:
        notification_id: Notification ID
        user_id: User ID
        db: Database session

    Returns:
        Success status
    """
    success = notification_service.mark_as_read(db, notification_id, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")

    return {"success": True}


@router.get("/user/{user_id}/unread-count")
def get_unread_count(
    user_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get unread notification count

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Unread count
    """
    count = notification_service.get_unread_count(db, user_id)
    return {"count": count}


# Template endpoints
@router.post("/templates", response_model=Dict[str, Any])
def create_template(
    request: CreateTemplateRequest,
    db: Session = Depends(get_db_session)
):
    """
    Create a notification template

    Args:
        request: Template details
        db: Database session

    Returns:
        Created template
    """
    try:
        template = NotificationTemplate(
            name=request.name,
            description=request.description,
            category=request.category,
            subject=request.subject,
            body=request.body,
            html_body=request.html_body,
            variables=request.variables,
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        return {
            "success": True,
            "template": template.to_dict()
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates", response_model=List[Dict[str, Any]])
def get_templates(
    category: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db_session)
):
    """
    Get notification templates

    Args:
        category: Optional category filter
        active_only: Only return active templates
        db: Database session

    Returns:
        List of templates
    """
    query = db.query(NotificationTemplate)

    if category:
        query = query.filter(NotificationTemplate.category == category)

    if active_only:
        query = query.filter(NotificationTemplate.active == True)

    templates = query.all()
    return [template.to_dict() for template in templates]


@router.get("/templates/{template_id}", response_model=Dict[str, Any])
def get_template(
    template_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get a specific template

    Args:
        template_id: Template ID
        db: Database session

    Returns:
        Template details
    """
    template = db.query(NotificationTemplate).filter(
        NotificationTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template.to_dict()


# Preference endpoints
@router.get("/preferences/{user_id}", response_model=List[Dict[str, Any]])
def get_user_preferences(
    user_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get user notification preferences

    Args:
        user_id: User ID
        db: Database session

    Returns:
        List of preferences
    """
    preferences = notification_service.unsubscribe_manager.get_user_preferences(db, user_id)
    return [pref.to_dict() for pref in preferences]


@router.put("/preferences/{user_id}", response_model=Dict[str, Any])
def update_preference(
    user_id: str,
    request: UpdatePreferenceRequest,
    db: Session = Depends(get_db_session)
):
    """
    Update user notification preference

    Args:
        user_id: User ID
        request: Preference details
        db: Database session

    Returns:
        Updated preference
    """
    try:
        preference = notification_service.unsubscribe_manager.update_preference(
            db=db,
            user_id=user_id,
            category=request.category,
            channel=request.channel,
            enabled=request.enabled,
            settings=request.settings,
        )

        return {
            "success": True,
            "preference": preference.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Unsubscribe endpoints
@router.post("/unsubscribe/{token}")
def unsubscribe(
    token: str,
    db: Session = Depends(get_db_session)
):
    """
    Process unsubscribe request

    Args:
        token: Unsubscribe token
        db: Database session

    Returns:
        Unsubscribe result
    """
    result = notification_service.unsubscribe_manager.process_unsubscribe(db, token)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.get("/unsubscribe-url/{user_id}")
def get_unsubscribe_url(
    user_id: str,
    category: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    db: Session = Depends(get_db_session)
):
    """
    Generate unsubscribe URL for a user

    Args:
        user_id: User ID
        category: Optional category
        channel: Optional channel
        db: Database session

    Returns:
        Unsubscribe URL
    """
    url = notification_service.unsubscribe_manager.get_unsubscribe_url(
        db=db,
        user_id=user_id,
        category=category,
        channel=channel,
    )

    return {"unsubscribe_url": url}


# Analytics endpoints
@router.get("/analytics/delivery")
def get_delivery_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    channel: Optional[str] = Query(None),
    db: Session = Depends(get_db_session)
):
    """
    Get delivery analytics

    Args:
        start_date: Start date
        end_date: End date
        channel: Optional channel filter
        db: Database session

    Returns:
        Analytics data
    """
    analytics = notification_service.delivery_tracker.get_delivery_analytics(
        db=db,
        start_date=start_date,
        end_date=end_date,
        channel=channel
    )

    return analytics


@router.post("/webhook/{provider}")
async def webhook_handler(
    provider: str,
    event_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db_session)
):
    """
    Handle webhook events from notification providers

    Args:
        provider: Provider name (sendgrid, twilio, fcm, etc.)
        event_data: Event data from provider
        db: Database session

    Returns:
        Success status
    """
    try:
        # Extract common fields (this would vary by provider)
        provider_message_id = event_data.get("message_id")
        event_type = event_data.get("event")

        if provider_message_id and event_type:
            success = notification_service.delivery_tracker.track_webhook(
                db=db,
                provider_message_id=provider_message_id,
                event_type=event_type,
                event_data=event_data
            )

            return {"success": success}

        return {"success": False, "error": "Invalid webhook data"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
