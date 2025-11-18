"""
Lead capture functionality for NEXUS platform.

This module handles lead capture from various sources including forms,
landing pages, popups, chatbots, and lead magnets.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .lead_types import (
    Lead,
    LeadCreate,
    LeadActivity,
    LeadActivityCreate,
    LeadActivityType,
    LeadStatus,
)
from .models import Lead as LeadModel, LeadActivity as LeadActivityModel
from shared.utils import generate_uuid, validate_email
from shared.exceptions import ValidationError, DatabaseError
from config.logging_config import get_logger
from config.redis_config import redis_client

logger = get_logger(__name__)


class LeadCapture:
    """Lead capture service for handling lead submissions."""

    def __init__(self, db: Session):
        """
        Initialize lead capture service.

        Args:
            db: Database session.
        """
        self.db = db

    async def capture_lead(
        self,
        lead_data: LeadCreate,
        source: str = "form",
        form_id: Optional[str] = None,
    ) -> Lead:
        """
        Capture a new lead from any source.

        Args:
            lead_data: Lead data to capture.
            source: Source of the lead (form, popup, chatbot, etc.).
            form_id: Optional form ID if from a form submission.

        Returns:
            Created lead object.

        Raises:
            ValidationError: If lead data is invalid.
            DatabaseError: If database operation fails.
        """
        try:
            # Validate email
            if not validate_email(lead_data.email):
                raise ValidationError(f"Invalid email address: {lead_data.email}")

            # Check for duplicates
            existing_lead = await self._check_duplicate(lead_data.email)
            if existing_lead:
                logger.info(f"Duplicate lead detected: {lead_data.email}")
                return await self._update_existing_lead(existing_lead, lead_data)

            # Create new lead
            lead = LeadModel(
                id=generate_uuid(),
                email=lead_data.email,
                first_name=lead_data.first_name,
                last_name=lead_data.last_name,
                phone=lead_data.phone,
                company=lead_data.company,
                job_title=lead_data.job_title,
                website=lead_data.website,
                industry=lead_data.industry,
                company_size=lead_data.company_size,
                country=lead_data.country,
                state=lead_data.state,
                city=lead_data.city,
                status=lead_data.status,
                source_id=lead_data.source_id,
                custom_fields=lead_data.custom_fields,
                tags=[],
            )

            self.db.add(lead)
            self.db.commit()
            self.db.refresh(lead)

            # Create activity record
            await self._create_activity(
                lead_id=lead.id,
                activity_type=LeadActivityType.FORM_SUBMISSION,
                description=f"Lead captured from {source}",
                metadata={
                    "source": source,
                    "form_id": form_id,
                    "utm_source": lead_data.utm_source,
                    "utm_medium": lead_data.utm_medium,
                    "utm_campaign": lead_data.utm_campaign,
                },
            )

            # Cache the lead
            await self._cache_lead(lead)

            logger.info(f"Lead captured successfully: {lead.email} (ID: {lead.id})")

            return Lead.model_validate(lead)

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database integrity error: {e}")
            raise DatabaseError("Failed to create lead due to database constraint")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error capturing lead: {e}")
            raise

    async def capture_form_submission(
        self,
        form_id: str,
        form_data: dict,
        metadata: Optional[dict] = None,
    ) -> Lead:
        """
        Capture lead from form submission.

        Args:
            form_id: Form ID.
            form_data: Submitted form data.
            metadata: Additional metadata (UTM params, referrer, etc.).

        Returns:
            Created lead object.
        """
        try:
            # Extract standard fields from form data
            lead_data = LeadCreate(
                email=form_data.get("email"),
                first_name=form_data.get("first_name"),
                last_name=form_data.get("last_name"),
                phone=form_data.get("phone"),
                company=form_data.get("company"),
                job_title=form_data.get("job_title"),
                website=form_data.get("website"),
                industry=form_data.get("industry"),
                company_size=form_data.get("company_size"),
                country=form_data.get("country"),
                state=form_data.get("state"),
                city=form_data.get("city"),
                utm_source=metadata.get("utm_source") if metadata else None,
                utm_medium=metadata.get("utm_medium") if metadata else None,
                utm_campaign=metadata.get("utm_campaign") if metadata else None,
                utm_content=metadata.get("utm_content") if metadata else None,
                custom_fields=form_data,  # Store all form data as custom fields
            )

            return await self.capture_lead(
                lead_data=lead_data,
                source="form",
                form_id=form_id,
            )

        except Exception as e:
            logger.error(f"Error capturing form submission: {e}")
            raise

    async def capture_popup_submission(
        self,
        popup_id: str,
        form_data: dict,
        metadata: Optional[dict] = None,
    ) -> Lead:
        """
        Capture lead from popup submission.

        Args:
            popup_id: Popup ID.
            form_data: Submitted form data.
            metadata: Additional metadata.

        Returns:
            Created lead object.
        """
        try:
            lead_data = LeadCreate(
                email=form_data.get("email"),
                first_name=form_data.get("first_name"),
                last_name=form_data.get("last_name"),
                phone=form_data.get("phone"),
                utm_source=metadata.get("utm_source") if metadata else None,
                utm_medium=metadata.get("utm_medium") if metadata else None,
                utm_campaign=metadata.get("utm_campaign") if metadata else None,
                custom_fields=form_data,
            )

            return await self.capture_lead(
                lead_data=lead_data,
                source="popup",
                form_id=popup_id,
            )

        except Exception as e:
            logger.error(f"Error capturing popup submission: {e}")
            raise

    async def capture_chatbot_lead(
        self,
        email: str,
        conversation_data: dict,
        metadata: Optional[dict] = None,
    ) -> Lead:
        """
        Capture lead from chatbot interaction.

        Args:
            email: Lead email address.
            conversation_data: Chatbot conversation data.
            metadata: Additional metadata.

        Returns:
            Created lead object.
        """
        try:
            # Extract information from conversation
            lead_data = LeadCreate(
                email=email,
                first_name=conversation_data.get("first_name"),
                last_name=conversation_data.get("last_name"),
                phone=conversation_data.get("phone"),
                company=conversation_data.get("company"),
                custom_fields=conversation_data,
            )

            lead = await self.capture_lead(
                lead_data=lead_data,
                source="chatbot",
            )

            # Store conversation history
            await self._create_activity(
                lead_id=lead.id,
                activity_type=LeadActivityType.NOTE,
                description="Chatbot conversation",
                metadata={"conversation": conversation_data},
            )

            return lead

        except Exception as e:
            logger.error(f"Error capturing chatbot lead: {e}")
            raise

    async def _check_duplicate(self, email: str) -> Optional[LeadModel]:
        """
        Check if lead already exists.

        Args:
            email: Email to check.

        Returns:
            Existing lead or None.
        """
        try:
            return self.db.query(LeadModel).filter(LeadModel.email == email).first()
        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return None

    async def _update_existing_lead(
        self,
        existing_lead: LeadModel,
        new_data: LeadCreate,
    ) -> Lead:
        """
        Update existing lead with new data.

        Args:
            existing_lead: Existing lead model.
            new_data: New lead data.

        Returns:
            Updated lead object.
        """
        try:
            # Update fields if new data provided
            if new_data.first_name:
                existing_lead.first_name = new_data.first_name
            if new_data.last_name:
                existing_lead.last_name = new_data.last_name
            if new_data.phone:
                existing_lead.phone = new_data.phone
            if new_data.company:
                existing_lead.company = new_data.company

            # Mark as duplicate
            existing_lead.is_duplicate = True
            existing_lead.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(existing_lead)

            # Create activity for duplicate submission
            await self._create_activity(
                lead_id=existing_lead.id,
                activity_type=LeadActivityType.FORM_SUBMISSION,
                description="Duplicate submission",
                metadata={"note": "Lead submitted form again"},
            )

            return Lead.model_validate(existing_lead)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating existing lead: {e}")
            raise

    async def _create_activity(
        self,
        lead_id: str,
        activity_type: LeadActivityType,
        description: str,
        metadata: Optional[dict] = None,
    ) -> LeadActivity:
        """
        Create activity record for lead.

        Args:
            lead_id: Lead ID.
            activity_type: Activity type.
            description: Activity description.
            metadata: Activity metadata.

        Returns:
            Created activity object.
        """
        try:
            activity = LeadActivityModel(
                id=generate_uuid(),
                lead_id=lead_id,
                type=activity_type.value,
                description=description,
                metadata=metadata,
            )

            self.db.add(activity)
            self.db.commit()
            self.db.refresh(activity)

            # Update lead's last activity timestamp
            lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
            if lead:
                lead.last_activity_at = datetime.utcnow()
                self.db.commit()

            return LeadActivity.model_validate(activity)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating activity: {e}")
            raise

    async def _cache_lead(self, lead: LeadModel) -> None:
        """
        Cache lead data in Redis.

        Args:
            lead: Lead model to cache.
        """
        try:
            cache_key = f"lead:{lead.id}"
            lead_data = {
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company": lead.company,
                "status": lead.status,
                "score": lead.score,
            }
            redis_client.set(cache_key, lead_data, ttl=3600)  # Cache for 1 hour
        except Exception as e:
            logger.warning(f"Failed to cache lead: {e}")


class LeadMagnet:
    """Lead magnet service for downloadable content."""

    def __init__(self, db: Session):
        """
        Initialize lead magnet service.

        Args:
            db: Database session.
        """
        self.db = db
        self.capture = LeadCapture(db)

    async def download_content(
        self,
        email: str,
        content_id: str,
        content_name: str,
        metadata: Optional[dict] = None,
    ) -> tuple[Lead, str]:
        """
        Process lead magnet download.

        Args:
            email: Lead email address.
            content_id: Content identifier.
            content_name: Content name.
            metadata: Additional metadata.

        Returns:
            Tuple of (lead object, download URL).
        """
        try:
            # Capture lead
            lead_data = LeadCreate(
                email=email,
                first_name=metadata.get("first_name") if metadata else None,
                last_name=metadata.get("last_name") if metadata else None,
                custom_fields={
                    "content_id": content_id,
                    "content_name": content_name,
                },
            )

            lead = await self.capture.capture_lead(
                lead_data=lead_data,
                source="lead_magnet",
            )

            # Create download activity
            await self.capture._create_activity(
                lead_id=lead.id,
                activity_type=LeadActivityType.DOWNLOAD,
                description=f"Downloaded: {content_name}",
                metadata={"content_id": content_id, "content_name": content_name},
            )

            # Generate download URL (implement your file storage logic here)
            download_url = f"/downloads/{content_id}?token={lead.id}"

            logger.info(f"Lead magnet download: {email} - {content_name}")

            return lead, download_url

        except Exception as e:
            logger.error(f"Error processing lead magnet download: {e}")
            raise
