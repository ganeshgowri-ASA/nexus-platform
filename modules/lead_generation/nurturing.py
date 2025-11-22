"""Lead nurturing system with drip campaigns and automated emails."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from .models import Lead as LeadModel, NurtureCampaign, LeadActivity
from .lead_types import LeadActivityType
from shared.utils import generate_uuid
from config.logging_config import get_logger

logger = get_logger(__name__)


class NurtureCampaignManager:
    """Nurture campaign management service."""

    def __init__(self, db: Session):
        self.db = db

    async def create_campaign(
        self,
        name: str,
        trigger_type: str,
        emails: List[Dict[str, Any]],
        trigger_conditions: Optional[Dict] = None,
    ) -> NurtureCampaign:
        """Create a new nurture campaign."""
        campaign = NurtureCampaign(
            id=generate_uuid(),
            name=name,
            trigger_type=trigger_type,
            trigger_conditions=trigger_conditions or {},
            emails=emails,
            is_active=True,
        )

        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)

        logger.info(f"Nurture campaign created: {name}")

        return campaign

    async def enroll_lead(
        self,
        campaign_id: str,
        lead_id: str,
    ) -> bool:
        """Enroll lead in nurture campaign."""
        campaign = self.db.query(NurtureCampaign).filter(
            NurtureCampaign.id == campaign_id
        ).first()

        if not campaign:
            return False

        lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if not lead:
            return False

        # Schedule first email
        await self._schedule_campaign_emails(campaign, lead)

        campaign.enrolled_count += 1
        self.db.commit()

        logger.info(f"Lead {lead.email} enrolled in campaign {campaign.name}")

        return True

    async def _schedule_campaign_emails(
        self,
        campaign: NurtureCampaign,
        lead: LeadModel,
    ) -> None:
        """Schedule all emails in the campaign for the lead."""
        # This would integrate with email service and Celery for scheduling
        # For now, just log the scheduling
        for idx, email in enumerate(campaign.emails):
            delay_days = email.get("delay_days", 0)
            send_date = datetime.utcnow() + timedelta(days=delay_days)
            logger.info(
                f"Scheduled email {idx + 1} for {lead.email} on {send_date}: {email.get('subject')}"
            )


class ProgressiveProfiling:
    """Progressive profiling to gradually collect lead information."""

    def __init__(self, db: Session):
        self.db = db

    async def get_next_questions(
        self,
        lead_id: str,
        max_questions: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get next profiling questions for lead based on existing data."""
        lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if not lead:
            return []

        all_questions = [
            {"field": "phone", "question": "What's your phone number?", "type": "phone"},
            {"field": "company", "question": "Which company do you work for?", "type": "text"},
            {"field": "job_title", "question": "What's your job title?", "type": "text"},
            {"field": "company_size", "question": "How large is your company?", "type": "select",
             "options": ["1-10", "11-50", "51-200", "201-1000", "1000+"]},
            {"field": "industry", "question": "What industry are you in?", "type": "text"},
        ]

        # Filter out questions for fields that already have values
        next_questions = []
        for q in all_questions:
            if not getattr(lead, q["field"], None):
                next_questions.append(q)
                if len(next_questions) >= max_questions:
                    break

        return next_questions
