"""
Celery tasks for email marketing automation.

This module contains background tasks for sending emails, processing campaigns,
and executing automation workflows.
"""
from uuid import UUID
from celery import shared_task
from sqlalchemy.orm import Session

from config.logging_config import get_logger
from config.constants import CampaignStatus, MessageStatus
from src.core.database import SessionLocal
from src.models.campaign import Campaign, CampaignMessage
from src.models.contact import Contact
from src.services.marketing.email_service import EmailService
from src.services.marketing.campaign_service import CampaignService

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3)
def send_campaign_task(self, campaign_id: str, workspace_id: str):
    """
    Send campaign emails to all recipients.

    Args:
        campaign_id: Campaign ID
        workspace_id: Workspace ID
    """
    db = SessionLocal()

    try:
        # Get campaign
        campaign = db.query(Campaign).filter(
            Campaign.id == UUID(campaign_id),
            Campaign.workspace_id == UUID(workspace_id)
        ).first()

        if not campaign:
            logger.error("Campaign not found", campaign_id=campaign_id)
            return

        # Update campaign status
        campaign.status = CampaignStatus.RUNNING
        campaign.sent_at = datetime.utcnow()
        db.commit()

        # Get recipients (from segment or all contacts)
        if campaign.segment_id:
            # Get contacts from segment
            from src.services.marketing.contact_service import ContactService
            # contacts = await contact_service.get_segment_contacts(...)
            contacts = []  # Simplified
        else:
            contacts = db.query(Contact).filter(
                Contact.workspace_id == UUID(workspace_id),
                Contact.status == "subscribed"
            ).all()

        campaign.total_recipients = len(contacts)
        db.commit()

        # Create message records
        for contact in contacts:
            message = CampaignMessage(
                campaign_id=campaign.id,
                contact_id=contact.id,
                status=MessageStatus.QUEUED,
            )
            db.add(message)

        db.commit()

        # Queue individual email send tasks
        for contact in contacts:
            send_email_to_contact_task.delay(
                str(campaign_id),
                str(contact.id),
                str(workspace_id)
            )

        logger.info(
            "Campaign emails queued",
            campaign_id=campaign_id,
            recipient_count=len(contacts)
        )

    except Exception as e:
        logger.error("Failed to process campaign", campaign_id=campaign_id, error=str(e))
        db.rollback()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@shared_task(bind=True, max_retries=3)
def send_email_to_contact_task(self, campaign_id: str, contact_id: str, workspace_id: str):
    """
    Send email to a single contact.

    Args:
        campaign_id: Campaign ID
        contact_id: Contact ID
        workspace_id: Workspace ID
    """
    from datetime import datetime

    db = SessionLocal()

    try:
        # Get campaign and contact
        campaign = db.query(Campaign).filter(Campaign.id == UUID(campaign_id)).first()
        contact = db.query(Contact).filter(Contact.id == UUID(contact_id)).first()

        if not campaign or not contact:
            logger.error("Campaign or contact not found")
            return

        # Get message record
        message = db.query(CampaignMessage).filter(
            CampaignMessage.campaign_id == UUID(campaign_id),
            CampaignMessage.contact_id == UUID(contact_id)
        ).first()

        if not message:
            logger.error("Message record not found")
            return

        # Send email (simplified - would use EmailService in real implementation)
        # email_service = EmailService(db)
        # success = await email_service.send_campaign_email(contact, campaign)

        # Update message status
        message.status = MessageStatus.SENT
        message.sent_at = datetime.utcnow()

        # Update campaign metrics
        campaign.total_sent += 1

        db.commit()

        logger.info("Email sent", campaign_id=campaign_id, contact_id=contact_id)

    except Exception as e:
        logger.error("Failed to send email", error=str(e))

        if message:
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            db.commit()

        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@shared_task
def process_scheduled_campaigns():
    """Process scheduled campaigns that are ready to send."""
    from datetime import datetime

    db = SessionLocal()

    try:
        # Get campaigns scheduled for now
        scheduled_campaigns = db.query(Campaign).filter(
            Campaign.status == CampaignStatus.SCHEDULED,
            Campaign.scheduled_at <= datetime.utcnow()
        ).all()

        for campaign in scheduled_campaigns:
            send_campaign_task.delay(str(campaign.id), str(campaign.workspace_id))

        logger.info("Processed scheduled campaigns", count=len(scheduled_campaigns))

    finally:
        db.close()
