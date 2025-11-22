"""
Lead service for managing leads.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import phonenumbers

from modules.lead_generation.models import Lead, LeadActivity, LeadStatus
from modules.lead_generation.schemas import LeadCreate, LeadUpdate, LeadActivityCreate


class LeadService:
    """Service for managing leads."""

    @staticmethod
    async def create_lead(db: AsyncSession, lead_data: LeadCreate) -> Lead:
        """
        Create a new lead.

        Args:
            db: Database session
            lead_data: Lead creation data

        Returns:
            Created lead
        """
        try:
            # Check for duplicates
            existing_lead = await LeadService.find_duplicate(db, lead_data.email)
            if existing_lead:
                logger.warning(f"Duplicate lead found: {lead_data.email}")
                # Mark as duplicate but still create
                lead = Lead(**lead_data.model_dump())
                lead.is_duplicate = True
                lead.duplicate_of = existing_lead.id
            else:
                lead = Lead(**lead_data.model_dump())

            db.add(lead)
            await db.commit()
            await db.refresh(lead)

            # Create initial activity
            await LeadService.add_activity(
                db,
                lead.id,
                "lead_created",
                "Lead created",
                f"Lead created from {lead.source.value}"
            )

            logger.info(f"Lead created: {lead.id}")
            return lead
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating lead: {e}")
            raise

    @staticmethod
    async def find_duplicate(db: AsyncSession, email: str) -> Optional[Lead]:
        """
        Find duplicate lead by email.

        Args:
            db: Database session
            email: Email address

        Returns:
            Existing lead or None
        """
        try:
            result = await db.execute(
                select(Lead).where(
                    func.lower(Lead.email) == email.lower(),
                    Lead.is_duplicate == False
                ).order_by(Lead.created_at.asc())
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error finding duplicate: {e}")
            return None

    @staticmethod
    async def get_lead(db: AsyncSession, lead_id: UUID) -> Optional[Lead]:
        """
        Get a lead by ID.

        Args:
            db: Database session
            lead_id: Lead ID

        Returns:
            Lead or None
        """
        try:
            result = await db.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting lead: {e}")
            raise

    @staticmethod
    async def list_leads(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[LeadStatus] = None,
        is_qualified: Optional[bool] = None
    ) -> List[Lead]:
        """
        List leads with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            is_qualified: Filter by qualification status

        Returns:
            List of leads
        """
        try:
            query = select(Lead)

            if status:
                query = query.where(Lead.status == status)

            if is_qualified is not None:
                query = query.where(Lead.is_qualified == is_qualified)

            query = query.offset(skip).limit(limit).order_by(Lead.created_at.desc())

            result = await db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing leads: {e}")
            raise

    @staticmethod
    async def update_lead(
        db: AsyncSession,
        lead_id: UUID,
        lead_data: LeadUpdate
    ) -> Optional[Lead]:
        """
        Update a lead.

        Args:
            db: Database session
            lead_id: Lead ID
            lead_data: Lead update data

        Returns:
            Updated lead or None
        """
        try:
            result = await db.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            lead = result.scalar_one_or_none()

            if not lead:
                return None

            update_data = lead_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(lead, field, value)

            lead.last_activity_at = datetime.utcnow()
            await db.commit()
            await db.refresh(lead)

            logger.info(f"Lead updated: {lead.id}")
            return lead
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating lead: {e}")
            raise

    @staticmethod
    async def validate_email(db: AsyncSession, lead_id: UUID) -> bool:
        """
        Validate lead email address.

        Args:
            db: Database session
            lead_id: Lead ID

        Returns:
            True if valid
        """
        try:
            result = await db.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            lead = result.scalar_one_or_none()

            if not lead:
                return False

            # Simple email validation (can be enhanced with external API)
            if "@" in lead.email and "." in lead.email:
                lead.email_validated = True
                lead.email_validation_score = 1.0
                await db.commit()
                logger.info(f"Email validated for lead: {lead_id}")
                return True

            return False
        except Exception as e:
            logger.error(f"Error validating email: {e}")
            return False

    @staticmethod
    async def validate_phone(db: AsyncSession, lead_id: UUID) -> bool:
        """
        Validate lead phone number.

        Args:
            db: Database session
            lead_id: Lead ID

        Returns:
            True if valid
        """
        try:
            result = await db.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            lead = result.scalar_one_or_none()

            if not lead or not lead.phone:
                return False

            try:
                parsed = phonenumbers.parse(lead.phone, None)
                is_valid = phonenumbers.is_valid_number(parsed)

                lead.phone_validated = is_valid
                await db.commit()

                if is_valid:
                    logger.info(f"Phone validated for lead: {lead_id}")
                return is_valid
            except phonenumbers.NumberParseException:
                return False
        except Exception as e:
            logger.error(f"Error validating phone: {e}")
            return False

    @staticmethod
    async def add_activity(
        db: AsyncSession,
        lead_id: UUID,
        activity_type: str,
        title: str,
        description: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> LeadActivity:
        """
        Add activity to lead.

        Args:
            db: Database session
            lead_id: Lead ID
            activity_type: Type of activity
            title: Activity title
            description: Activity description
            metadata: Additional metadata

        Returns:
            Created activity
        """
        try:
            activity = LeadActivity(
                lead_id=lead_id,
                activity_type=activity_type,
                title=title,
                description=description,
                metadata=metadata or {}
            )

            db.add(activity)

            # Update lead's last activity time
            result = await db.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            lead = result.scalar_one_or_none()
            if lead:
                lead.last_activity_at = datetime.utcnow()

            await db.commit()
            await db.refresh(activity)

            logger.info(f"Activity added for lead {lead_id}: {activity_type}")
            return activity
        except Exception as e:
            await db.rollback()
            logger.error(f"Error adding activity: {e}")
            raise

    @staticmethod
    async def get_lead_activities(
        db: AsyncSession,
        lead_id: UUID,
        limit: int = 50
    ) -> List[LeadActivity]:
        """
        Get lead activities.

        Args:
            db: Database session
            lead_id: Lead ID
            limit: Maximum number of activities

        Returns:
            List of activities
        """
        try:
            result = await db.execute(
                select(LeadActivity)
                .where(LeadActivity.lead_id == lead_id)
                .order_by(LeadActivity.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting lead activities: {e}")
            raise
