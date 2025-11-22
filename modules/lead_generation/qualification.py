"""Lead qualification system using BANT, CHAMP, and custom criteria."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from .models import Lead as LeadModel
from .lead_types import QualificationCriteria, LeadStatus
from config.logging_config import get_logger

logger = get_logger(__name__)


class LeadQualification:
    """Lead qualification service."""

    def __init__(self, db: Session):
        self.db = db

    async def qualify_lead(
        self,
        lead_id: str,
        criteria: QualificationCriteria = QualificationCriteria.BANT,
        custom_rules: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Qualify lead using specified criteria."""
        lead = self.db.query(LeadModel).filter(LeadModel.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}

        if criteria == QualificationCriteria.BANT:
            result = await self._qualify_bant(lead)
        elif criteria == QualificationCriteria.CHAMP:
            result = await self._qualify_champ(lead)
        elif criteria == QualificationCriteria.CUSTOM and custom_rules:
            result = await self._qualify_custom(lead, custom_rules)
        else:
            result = await self._qualify_score_based(lead)

        # Update lead status based on qualification
        if result["qualified"]:
            lead.status = LeadStatus.QUALIFIED.value
        else:
            lead.status = LeadStatus.UNQUALIFIED.value

        self.db.commit()

        logger.info(f"Lead qualified: {lead.email} - {result['qualified']}")

        return result

    async def _qualify_bant(self, lead: LeadModel) -> Dict[str, Any]:
        """Qualify lead using BANT criteria (Budget, Authority, Need, Timeline)."""
        score = 0
        max_score = 4
        details = {}

        # Budget (from custom fields or inferred from company size)
        if lead.company_size in ["51-200", "201-1000", "1000+"]:
            score += 1
            details["budget"] = "Likely has budget"
        else:
            details["budget"] = "Budget unknown"

        # Authority (from job title)
        if lead.job_title:
            authority_titles = ["ceo", "cfo", "director", "vp", "head", "owner"]
            if any(title in lead.job_title.lower() for title in authority_titles):
                score += 1
                details["authority"] = "Decision maker"
            else:
                details["authority"] = "Not decision maker"
        else:
            details["authority"] = "Title unknown"

        # Need (inferred from engagement score)
        if lead.score >= 50:
            score += 1
            details["need"] = "High engagement indicates need"
        else:
            details["need"] = "Low engagement"

        # Timeline (from recent activity)
        if lead.last_activity_at:
            score += 1
            details["timeline"] = "Recently active"
        else:
            details["timeline"] = "No recent activity"

        qualified = score >= 3  # Need 3/4 criteria

        return {
            "qualified": qualified,
            "score": score,
            "max_score": max_score,
            "criteria": "BANT",
            "details": details,
        }

    async def _qualify_champ(self, lead: LeadModel) -> Dict[str, Any]:
        """Qualify using CHAMP (Challenges, Authority, Money, Prioritization)."""
        # Similar to BANT but different focus
        return await self._qualify_bant(lead)  # Simplified for now

    async def _qualify_custom(self, lead: LeadModel, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Qualify using custom rules."""
        score = 0
        max_score = len(rules)

        for rule_name, rule_config in rules.items():
            field = rule_config.get("field")
            operator = rule_config.get("operator")
            value = rule_config.get("value")

            lead_value = getattr(lead, field, None)
            
            if self._evaluate_rule(lead_value, operator, value):
                score += 1

        qualified = score >= max_score * 0.7  # Need 70% of rules to pass

        return {
            "qualified": qualified,
            "score": score,
            "max_score": max_score,
            "criteria": "CUSTOM",
        }

    async def _qualify_score_based(self, lead: LeadModel) -> Dict[str, Any]:
        """Simple score-based qualification."""
        qualified = lead.score >= 60

        return {
            "qualified": qualified,
            "score": lead.score,
            "max_score": 100,
            "criteria": "SCORE",
            "details": {
                "threshold": 60,
                "actual_score": lead.score,
            },
        }

    def _evaluate_rule(self, lead_value: Any, operator: str, expected_value: Any) -> bool:
        """Evaluate a single qualification rule."""
        if operator == "eq":
            return lead_value == expected_value
        elif operator == "ne":
            return lead_value != expected_value
        elif operator == "gt":
            return lead_value > expected_value
        elif operator == "gte":
            return lead_value >= expected_value
        elif operator == "lt":
            return lead_value < expected_value
        elif operator == "lte":
            return lead_value <= expected_value
        elif operator == "in":
            return lead_value in expected_value
        elif operator == "contains":
            return expected_value in str(lead_value)
        return False
