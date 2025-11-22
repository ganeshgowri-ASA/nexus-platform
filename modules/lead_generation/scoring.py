"""Lead scoring system for qualification."""

from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import Lead as LeadModel, LeadActivity, LeadScoreRecord
from .lead_types import LeadScoreType
from shared.utils import generate_uuid
from config.logging_config import get_logger

logger = get_logger(__name__)


class LeadScoring:
    """Lead scoring service for behavior and demographic scoring."""

    def __init__(self, db: Session):
        self.db = db

    async def calculate_score(self, lead_id: str) -> int:
        """Calculate comprehensive lead score."""
        lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if not lead:
            return 0

        total_score = 0

        # Demographic scoring (0-40 points)
        total_score += await self._demographic_score(lead)

        # Behavioral scoring (0-40 points)
        total_score += await self._behavioral_score(lead)

        # Firmographic scoring (0-20 points)
        total_score += await self._firmographic_score(lead)

        # Update lead score
        lead.score = min(total_score, 100)
        self.db.commit()

        # Record score
        score_record = LeadScoreRecord(
            id=generate_uuid(),
            lead_id=lead_id,
            type=LeadScoreType.CUSTOM.value,
            value=total_score,
            reason=f"Comprehensive scoring: Demographic + Behavioral + Firmographic",
        )
        self.db.add(score_record)
        self.db.commit()

        logger.info(f"Lead score calculated: {lead.email} = {total_score}")

        return total_score

    async def _demographic_score(self, lead: LeadModel) -> int:
        """Calculate demographic score based on lead profile completeness."""
        score = 0

        # Profile completeness (up to 25 points)
        if lead.first_name:
            score += 3
        if lead.last_name:
            score += 3
        if lead.phone:
            score += 5
        if lead.company:
            score += 5
        if lead.job_title:
            score += 5
        if lead.industry:
            score += 4

        # Job title relevance (up to 15 points)
        if lead.job_title:
            decision_maker_titles = ["ceo", "cto", "cfo", "director", "vp", "head", "manager"]
            title_lower = lead.job_title.lower()
            if any(title in title_lower for title in decision_maker_titles):
                score += 15

        return min(score, 40)

    async def _behavioral_score(self, lead: LeadModel) -> int:
        """Calculate behavioral score based on lead activities."""
        score = 0

        # Get recent activities (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        activities = self.db.query(LeadActivity).filter(
            LeadActivity.lead_id == lead.id,
            LeadActivity.created_at >= thirty_days_ago
        ).all()

        # Activity-based scoring
        activity_scores = {
            "form_submission": 10,
            "email_opened": 2,
            "email_clicked": 5,
            "download": 8,
            "page_view": 1,
            "call": 15,
            "meeting": 20,
        }

        for activity in activities:
            score += activity_scores.get(activity.type, 0)

        # Recency bonus (up to 10 points)
        if lead.last_activity_at:
            days_since_activity = (datetime.utcnow() - lead.last_activity_at).days
            if days_since_activity <= 7:
                score += 10
            elif days_since_activity <= 14:
                score += 5

        return min(score, 40)

    async def _firmographic_score(self, lead: LeadModel) -> int:
        """Calculate firmographic score based on company characteristics."""
        score = 0

        # Company size scoring
        if lead.company_size:
            size_scores = {
                "1-10": 5,
                "11-50": 10,
                "51-200": 15,
                "201-1000": 18,
                "1000+": 20,
            }
            score += size_scores.get(lead.company_size, 0)

        return min(score, 20)


class PredictiveScoring:
    """Predictive lead scoring using machine learning."""

    def __init__(self, db: Session):
        self.db = db

    async def predict_conversion_probability(self, lead_id: str) -> float:
        """Predict probability of lead conversion using ML model."""
        # Placeholder for ML model integration
        # In production, this would use a trained ML model
        
        lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if not lead:
            return 0.0

        # Simple rule-based prediction for now
        features = {
            "has_phone": 1 if lead.phone else 0,
            "has_company": 1 if lead.company else 0,
            "has_job_title": 1 if lead.job_title else 0,
            "score": lead.score / 100.0,
        }

        # Weighted sum (replace with actual ML model)
        probability = (
            features["has_phone"] * 0.2 +
            features["has_company"] * 0.3 +
            features["has_job_title"] * 0.2 +
            features["score"] * 0.3
        )

        return min(probability, 1.0)
