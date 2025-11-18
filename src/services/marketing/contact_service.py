"""
Contact service for marketing automation.

This module handles contact management, segmentation, lead scoring, and tagging.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging_config import get_logger
from config.constants import ContactStatus, LEAD_SCORE_COLD, LEAD_SCORE_WARM, LEAD_SCORE_HOT
from src.core.exceptions import NotFoundError, ValidationError
from src.core.utils import validate_email, calculate_lead_score
from src.models.contact import Contact, ContactList, Tag, Segment, ContactEvent
from src.schemas.marketing.contact_schema import ContactCreate, ContactUpdate

logger = get_logger(__name__)


class ContactService:
    """
    Service for managing contacts and leads.

    Provides methods for contact CRUD, segmentation, tagging, and lead scoring.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize contact service."""
        self.db = db

    async def create_contact(
        self,
        contact_data: ContactCreate,
        workspace_id: UUID,
    ) -> Contact:
        """
        Create a new contact.

        Args:
            contact_data: Contact creation data
            workspace_id: Workspace ID

        Returns:
            Created contact

        Raises:
            ValidationError: If validation fails
        """
        # Check if contact already exists
        existing = await self.get_contact_by_email(contact_data.email, workspace_id)
        if existing:
            raise ValidationError(f"Contact with email {contact_data.email} already exists")

        contact = Contact(
            workspace_id=workspace_id,
            email=contact_data.email,
            first_name=contact_data.first_name,
            last_name=contact_data.last_name,
            phone=contact_data.phone,
            company=contact_data.company,
            job_title=contact_data.job_title,
            custom_attributes=contact_data.custom_attributes or {},
            status=ContactStatus.SUBSCRIBED,
            lead_score=0,
        )

        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)

        logger.info("Contact created", contact_id=str(contact.id), email=contact.email)

        return contact

    async def get_contact(self, contact_id: UUID, workspace_id: UUID) -> Contact:
        """Get contact by ID."""
        result = await self.db.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.workspace_id == workspace_id
            )
        )
        contact = result.scalar_one_or_none()

        if not contact:
            raise NotFoundError("Contact", str(contact_id))

        return contact

    async def get_contact_by_email(
        self,
        email: str,
        workspace_id: UUID,
    ) -> Optional[Contact]:
        """Get contact by email."""
        result = await self.db.execute(
            select(Contact).where(
                Contact.email == email,
                Contact.workspace_id == workspace_id
            )
        )
        return result.scalar_one_or_none()

    async def update_contact(
        self,
        contact_id: UUID,
        workspace_id: UUID,
        contact_data: ContactUpdate,
    ) -> Contact:
        """Update contact."""
        contact = await self.get_contact(contact_id, workspace_id)

        update_data = contact_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(contact, key, value)

        contact.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(contact)

        logger.info("Contact updated", contact_id=str(contact_id))

        return contact

    async def update_lead_score(
        self,
        contact_id: UUID,
        workspace_id: UUID,
        score_delta: int,
        reason: str,
    ) -> Contact:
        """Update contact lead score."""
        contact = await self.get_contact(contact_id, workspace_id)

        old_score = contact.lead_score
        new_score = max(0, min(1000, contact.lead_score + score_delta))
        contact.lead_score = new_score
        contact.updated_at = datetime.utcnow()

        # Log event
        event = ContactEvent(
            contact_id=contact_id,
            event_type="lead_score_updated",
            event_data={
                "old_score": old_score,
                "new_score": new_score,
                "delta": score_delta,
                "reason": reason,
            }
        )
        self.db.add(event)

        await self.db.commit()
        await self.db.refresh(contact)

        logger.info(
            "Lead score updated",
            contact_id=str(contact_id),
            old_score=old_score,
            new_score=new_score
        )

        return contact

    async def create_segment(
        self,
        name: str,
        conditions: Dict[str, Any],
        workspace_id: UUID,
        description: Optional[str] = None,
    ) -> Segment:
        """Create a new segment."""
        segment = Segment(
            workspace_id=workspace_id,
            name=name,
            description=description,
            conditions=conditions,
            is_dynamic=True,
            contact_count=0,
        )

        self.db.add(segment)
        await self.db.commit()
        await self.db.refresh(segment)

        # Update contact count
        await self.update_segment_count(segment.id, workspace_id)

        logger.info("Segment created", segment_id=str(segment.id), name=name)

        return segment

    async def update_segment_count(self, segment_id: UUID, workspace_id: UUID) -> int:
        """Update segment contact count."""
        segment = await self.get_segment(segment_id, workspace_id)
        contacts = await self.get_segment_contacts(segment_id, workspace_id)

        segment.contact_count = len(contacts)
        segment.updated_at = datetime.utcnow()

        await self.db.commit()

        return segment.contact_count

    async def get_segment(self, segment_id: UUID, workspace_id: UUID) -> Segment:
        """Get segment by ID."""
        result = await self.db.execute(
            select(Segment).where(
                Segment.id == segment_id,
                Segment.workspace_id == workspace_id
            )
        )
        segment = result.scalar_one_or_none()

        if not segment:
            raise NotFoundError("Segment", str(segment_id))

        return segment

    async def get_segment_contacts(
        self,
        segment_id: UUID,
        workspace_id: UUID,
    ) -> List[Contact]:
        """
        Get contacts matching segment conditions.

        Note: This is a simplified implementation. In production, you'd want
        to implement a more sophisticated query builder for complex conditions.
        """
        segment = await self.get_segment(segment_id, workspace_id)
        conditions = segment.conditions

        query = select(Contact).where(Contact.workspace_id == workspace_id)

        # Apply conditions (simplified)
        if "status" in conditions:
            query = query.where(Contact.status == ContactStatus(conditions["status"]))

        if "lead_score_min" in conditions:
            query = query.where(Contact.lead_score >= conditions["lead_score_min"])

        if "lead_score_max" in conditions:
            query = query.where(Contact.lead_score <= conditions["lead_score_max"])

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_tag_to_contact(
        self,
        contact_id: UUID,
        tag_name: str,
        workspace_id: UUID,
    ) -> Contact:
        """Add tag to contact."""
        contact = await self.get_contact(contact_id, workspace_id)

        # Get or create tag
        result = await self.db.execute(
            select(Tag).where(
                Tag.name == tag_name,
                Tag.workspace_id == workspace_id
            )
        )
        tag = result.scalar_one_or_none()

        if not tag:
            tag = Tag(workspace_id=workspace_id, name=tag_name)
            self.db.add(tag)
            await self.db.flush()

        # Add tag to contact
        if tag not in contact.tags:
            contact.tags.append(tag)
            await self.db.commit()
            await self.db.refresh(contact)

        logger.info("Tag added to contact", contact_id=str(contact_id), tag=tag_name)

        return contact

    async def track_event(
        self,
        contact_id: UUID,
        event_type: str,
        event_data: Dict[str, Any],
        workspace_id: UUID,
    ) -> ContactEvent:
        """Track contact event for behavioral triggers."""
        contact = await self.get_contact(contact_id, workspace_id)

        event = ContactEvent(
            contact_id=contact_id,
            event_type=event_type,
            event_data=event_data,
            occurred_at=datetime.utcnow(),
        )

        self.db.add(event)

        # Update last activity
        contact.last_activity_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(event)

        logger.info(
            "Event tracked",
            contact_id=str(contact_id),
            event_type=event_type
        )

        return event
