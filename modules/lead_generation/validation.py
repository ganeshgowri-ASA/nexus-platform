"""
Lead validation and data quality for lead generation.

This module handles email validation, phone validation,
duplicate detection, and data enrichment.
"""

from typing import Optional, Dict, Any
import re
from sqlalchemy.orm import Session

from .models import Lead as LeadModel
from shared.utils import validate_email as base_validate_email, validate_phone as base_validate_phone
from shared.exceptions import ValidationError
from config.logging_config import get_logger
from config.redis_config import redis_client

logger = get_logger(__name__)


class LeadValidator:
    """Lead data validation service."""

    def __init__(self, db: Session):
        """
        Initialize lead validator.

        Args:
            db: Database session.
        """
        self.db = db

    async def validate_lead_data(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate lead data.

        Args:
            lead_data: Lead data to validate.

        Returns:
            Validation results with errors if any.

        Raises:
            ValidationError: If validation fails.
        """
        errors = []
        warnings = []

        # Validate email (required)
        email = lead_data.get("email")
        if not email:
            errors.append("Email is required")
        elif not await self.validate_email(email):
            errors.append(f"Invalid email format: {email}")
        elif await self.is_disposable_email(email):
            warnings.append(f"Disposable email detected: {email}")

        # Validate phone (if provided)
        phone = lead_data.get("phone")
        if phone and not await self.validate_phone(phone):
            errors.append(f"Invalid phone format: {phone}")

        # Validate website (if provided)
        website = lead_data.get("website")
        if website and not await self.validate_website(website):
            warnings.append(f"Invalid website format: {website}")

        # Check for duplicate
        if email and await self.check_duplicate(email):
            warnings.append(f"Duplicate email detected: {email}")

        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

        if errors:
            logger.warning(f"Lead validation failed: {errors}")

        return result

    async def validate_email(self, email: str) -> bool:
        """
        Validate email address format and deliverability.

        Args:
            email: Email address to validate.

        Returns:
            True if valid, False otherwise.
        """
        # Basic format validation
        if not base_validate_email(email):
            return False

        # Check MX records (implement DNS lookup)
        # For now, just return basic validation
        return True

    async def validate_phone(self, phone: str) -> bool:
        """
        Validate phone number format.

        Args:
            phone: Phone number to validate.

        Returns:
            True if valid, False otherwise.
        """
        return base_validate_phone(phone)

    async def validate_website(self, website: str) -> bool:
        """
        Validate website URL format.

        Args:
            website: Website URL to validate.

        Returns:
            True if valid, False otherwise.
        """
        url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return bool(re.match(url_pattern, website))

    async def is_disposable_email(self, email: str) -> bool:
        """
        Check if email is from a disposable email provider.

        Args:
            email: Email address to check.

        Returns:
            True if disposable, False otherwise.
        """
        disposable_domains = [
            "tempmail.com", "guerrillamail.com", "10minutemail.com",
            "mailinator.com", "throwaway.email", "maildrop.cc",
        ]

        domain = email.split("@")[-1].lower()
        return domain in disposable_domains

    async def check_duplicate(self, email: str) -> bool:
        """
        Check if lead with email already exists.

        Args:
            email: Email to check.

        Returns:
            True if duplicate exists, False otherwise.
        """
        try:
            # Check cache first
            cache_key = f"lead_exists:{email}"
            cached = redis_client.get(cache_key)
            if cached is not None:
                return cached

            # Check database
            exists = self.db.query(LeadModel).filter(
                LeadModel.email == email
            ).first() is not None

            # Cache result
            redis_client.set(cache_key, exists, ttl=300)  # Cache for 5 minutes

            return exists

        except Exception as e:
            logger.error(f"Error checking duplicate: {e}")
            return False


class DuplicateDetection:
    """Duplicate lead detection service."""

    def __init__(self, db: Session):
        """
        Initialize duplicate detection.

        Args:
            db: Database session.
        """
        self.db = db

    async def find_duplicates(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        fuzzy: bool = False,
    ) -> list[LeadModel]:
        """
        Find duplicate leads.

        Args:
            email: Email to search for.
            phone: Phone to search for.
            fuzzy: Enable fuzzy matching.

        Returns:
            List of duplicate leads.
        """
        query = self.db.query(LeadModel)

        if email:
            if fuzzy:
                # Implement fuzzy email matching
                query = query.filter(LeadModel.email.ilike(f"%{email}%"))
            else:
                query = query.filter(LeadModel.email == email)

        if phone:
            # Clean phone number for comparison
            cleaned_phone = self._clean_phone(phone)
            query = query.filter(LeadModel.phone.contains(cleaned_phone))

        return query.all()

    async def merge_duplicates(
        self,
        primary_lead_id: str,
        duplicate_lead_ids: list[str],
    ) -> LeadModel:
        """
        Merge duplicate leads into primary lead.

        Args:
            primary_lead_id: Primary lead ID to merge into.
            duplicate_lead_ids: List of duplicate lead IDs to merge.

        Returns:
            Merged lead.
        """
        try:
            primary = self.db.query(LeadModel).filter(
                LeadModel.id == primary_lead_id
            ).first()

            if not primary:
                raise ValidationError(f"Primary lead not found: {primary_lead_id}")

            for dup_id in duplicate_lead_ids:
                duplicate = self.db.query(LeadModel).filter(
                    LeadModel.id == dup_id
                ).first()

                if duplicate:
                    # Merge data (keep most complete information)
                    self._merge_lead_data(primary, duplicate)

                    # Mark duplicate as merged
                    duplicate.is_duplicate = True
                    duplicate.status = "merged"

            self.db.commit()
            self.db.refresh(primary)

            logger.info(f"Merged {len(duplicate_lead_ids)} duplicates into lead {primary_lead_id}")

            return primary

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error merging duplicates: {e}")
            raise

    def _merge_lead_data(self, primary: LeadModel, duplicate: LeadModel) -> None:
        """
        Merge data from duplicate into primary lead.

        Args:
            primary: Primary lead.
            duplicate: Duplicate lead to merge from.
        """
        # Update fields if primary has null and duplicate has value
        fields_to_merge = [
            "first_name", "last_name", "phone", "company", "job_title",
            "website", "industry", "company_size", "country", "state", "city"
        ]

        for field in fields_to_merge:
            primary_value = getattr(primary, field)
            duplicate_value = getattr(duplicate, field)

            if not primary_value and duplicate_value:
                setattr(primary, field, duplicate_value)

        # Merge tags
        if primary.tags and duplicate.tags:
            primary.tags = list(set(primary.tags + duplicate.tags))
        elif duplicate.tags:
            primary.tags = duplicate.tags

        # Keep higher score
        if duplicate.score > primary.score:
            primary.score = duplicate.score

    def _clean_phone(self, phone: str) -> str:
        """
        Clean phone number for comparison.

        Args:
            phone: Phone number.

        Returns:
            Cleaned phone number.
        """
        return re.sub(r'[^\d]', '', phone)
