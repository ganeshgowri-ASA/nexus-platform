"""
Lead scoring service.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.lead_generation.models import Lead, LeadScoringRule


class ScoringService:
    """Service for lead scoring."""

    @staticmethod
    async def calculate_lead_score(db: AsyncSession, lead_id: UUID) -> int:
        """
        Calculate lead score based on rules.

        Args:
            db: Database session
            lead_id: Lead ID

        Returns:
            Calculated score
        """
        try:
            # Get lead
            result = await db.execute(
                select(Lead).where(Lead.id == lead_id)
            )
            lead = result.scalar_one_or_none()

            if not lead:
                logger.error(f"Lead not found: {lead_id}")
                return 0

            # Get all active scoring rules
            rules_result = await db.execute(
                select(LeadScoringRule)
                .where(LeadScoringRule.is_active == True)
                .order_by(LeadScoringRule.priority.desc())
            )
            rules = list(rules_result.scalars().all())

            total_score = 0
            score_breakdown = {}

            # Apply each rule
            for rule in rules:
                if ScoringService._evaluate_conditions(lead, rule.conditions):
                    total_score += rule.score_adjustment
                    score_breakdown[rule.name] = rule.score_adjustment
                    logger.debug(f"Rule '{rule.name}' applied: {rule.score_adjustment}")

            # Apply demographic scoring
            demo_score = ScoringService._calculate_demographic_score(lead)
            total_score += demo_score
            score_breakdown["demographic"] = demo_score

            # Apply engagement scoring
            engagement_score = ScoringService._calculate_engagement_score(lead)
            total_score += engagement_score
            score_breakdown["engagement"] = engagement_score

            # Apply firmographic scoring (company-based)
            if lead.enrichment_data:
                firm_score = ScoringService._calculate_firmographic_score(lead)
                total_score += firm_score
                score_breakdown["firmographic"] = firm_score

            # Ensure score is between 0 and 100
            total_score = max(0, min(100, total_score))

            # Assign grade based on score
            grade = ScoringService._assign_grade(total_score)

            # Update lead
            lead.score = total_score
            lead.score_breakdown = score_breakdown
            lead.grade = grade

            # Auto-qualify if score is high enough
            if total_score >= 70:
                lead.is_qualified = True

            await db.commit()
            await db.refresh(lead)

            logger.info(f"Lead score calculated: {lead_id} = {total_score} ({grade})")
            return total_score

        except Exception as e:
            logger.error(f"Error calculating lead score: {e}")
            raise

    @staticmethod
    def _evaluate_conditions(lead: Lead, conditions: Dict[str, Any]) -> bool:
        """
        Evaluate if lead meets rule conditions.

        Args:
            lead: Lead object
            conditions: Rule conditions

        Returns:
            True if conditions are met
        """
        try:
            for field, condition in conditions.items():
                lead_value = getattr(lead, field, None)

                if "equals" in condition:
                    if lead_value != condition["equals"]:
                        return False

                if "contains" in condition:
                    if not lead_value or condition["contains"] not in str(lead_value):
                        return False

                if "in" in condition:
                    if lead_value not in condition["in"]:
                        return False

                if "gt" in condition:
                    if not lead_value or lead_value <= condition["gt"]:
                        return False

                if "lt" in condition:
                    if not lead_value or lead_value >= condition["lt"]:
                        return False

            return True
        except Exception as e:
            logger.error(f"Error evaluating conditions: {e}")
            return False

    @staticmethod
    def _calculate_demographic_score(lead: Lead) -> int:
        """
        Calculate demographic score.

        Args:
            lead: Lead object

        Returns:
            Demographic score
        """
        score = 0

        # Has email (required)
        if lead.email:
            score += 5

        # Has phone
        if lead.phone:
            score += 5

        # Has name
        if lead.first_name and lead.last_name:
            score += 5

        # Has job title
        if lead.job_title:
            score += 5

            # Executive titles get bonus
            exec_keywords = ["ceo", "cto", "cfo", "vp", "director", "head"]
            if any(keyword in lead.job_title.lower() for keyword in exec_keywords):
                score += 10

        # Has company
        if lead.company:
            score += 5

        # Email validated
        if lead.email_validated:
            score += 5

        # Phone validated
        if lead.phone_validated:
            score += 5

        return score

    @staticmethod
    def _calculate_engagement_score(lead: Lead) -> int:
        """
        Calculate engagement score.

        Args:
            lead: Lead object

        Returns:
            Engagement score
        """
        score = 0

        # Recent activity
        if lead.last_activity_at:
            days_since_activity = (datetime.utcnow() - lead.last_activity_at).days
            if days_since_activity <= 1:
                score += 15
            elif days_since_activity <= 7:
                score += 10
            elif days_since_activity <= 30:
                score += 5

        # Source quality
        high_quality_sources = ["chatbot", "form"]
        if lead.source.value in high_quality_sources:
            score += 5

        # UTM campaign tracking
        if lead.utm_campaign:
            score += 5

        return score

    @staticmethod
    def _calculate_firmographic_score(lead: Lead) -> int:
        """
        Calculate firmographic score based on company data.

        Args:
            lead: Lead object

        Returns:
            Firmographic score
        """
        score = 0

        if not lead.enrichment_data or "company" not in lead.enrichment_data:
            return score

        company = lead.enrichment_data["company"]

        # Company size
        employees = company.get("employees")
        if employees:
            if employees >= 1000:
                score += 15
            elif employees >= 500:
                score += 10
            elif employees >= 100:
                score += 5

        # Revenue
        revenue = company.get("revenue")
        if revenue:
            if revenue >= 100000000:  # $100M+
                score += 15
            elif revenue >= 10000000:  # $10M+
                score += 10
            elif revenue >= 1000000:  # $1M+
                score += 5

        # Industry relevance (can be customized)
        target_industries = ["technology", "software", "saas"]
        industry = company.get("industry", "").lower()
        if any(target in industry for target in target_industries):
            score += 10

        return score

    @staticmethod
    def _assign_grade(score: int) -> str:
        """
        Assign letter grade based on score.

        Args:
            score: Lead score

        Returns:
            Grade (A+, A, B+, B, C+, C, D, F)
        """
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C+"
        elif score >= 40:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"
