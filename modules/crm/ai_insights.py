"""
CRM AI Insights Module - Lead prioritization, next best action, deal insights, and churn prediction.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from enum import Enum
import statistics
import random


class InsightType(Enum):
    """AI insight types."""
    LEAD_PRIORITY = "lead_priority"
    NEXT_BEST_ACTION = "next_best_action"
    DEAL_RISK = "deal_risk"
    CHURN_PREDICTION = "churn_prediction"
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    ENGAGEMENT_SCORE = "engagement_score"
    WIN_PROBABILITY = "win_probability"


class PriorityLevel(Enum):
    """Priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ChurnRisk(Enum):
    """Churn risk levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class AIInsight:
    """AI-generated insight."""
    id: str
    insight_type: InsightType
    entity_type: str  # contact, deal, company
    entity_id: str
    entity_name: str

    # Insight details
    title: str
    description: str
    priority: PriorityLevel
    confidence: float  # 0-100

    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)

    # Supporting data
    metrics: Dict[str, Any] = field(default_factory=dict)
    reasoning: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_dismissed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'insight_type': self.insight_type.value,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'entity_name': self.entity_name,
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'confidence': round(self.confidence, 2),
            'recommended_actions': self.recommended_actions,
            'metrics': self.metrics,
            'reasoning': self.reasoning,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_dismissed': self.is_dismissed,
        }


class AIInsightsEngine:
    """AI-powered insights and recommendations for CRM."""

    def __init__(
        self,
        contact_manager=None,
        company_manager=None,
        deal_manager=None,
        activity_manager=None,
        task_manager=None
    ):
        """Initialize AI insights engine."""
        self.contact_manager = contact_manager
        self.company_manager = company_manager
        self.deal_manager = deal_manager
        self.activity_manager = activity_manager
        self.task_manager = task_manager

        self.insights: Dict[str, AIInsight] = {}

    # Lead Prioritization

    def prioritize_leads(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Prioritize leads based on AI scoring."""
        if not self.contact_manager:
            return []

        from .contacts import ContactStatus

        # Get all leads and prospects
        leads = [
            c for c in self.contact_manager.contacts.values()
            if c.status in [ContactStatus.LEAD, ContactStatus.PROSPECT]
        ]

        # Score each lead
        scored_leads = []
        for contact in leads:
            score = self._calculate_lead_priority_score(contact)
            scored_leads.append({
                'contact_id': contact.id,
                'contact_name': contact.full_name,
                'company_name': contact.company_name,
                'priority_score': score,
                'lead_score': contact.lead_score,
                'email_engagement': contact.email_opens + contact.email_clicks,
                'last_contacted': contact.last_contacted.isoformat() if contact.last_contacted else None,
            })

        # Sort by priority score
        scored_leads.sort(key=lambda x: x['priority_score'], reverse=True)

        return scored_leads[:limit]

    def _calculate_lead_priority_score(self, contact) -> float:
        """Calculate priority score for a lead (0-100)."""
        score = 0.0

        # Base lead score (40% weight)
        score += (contact.lead_score / 100) * 40

        # Email engagement (20% weight)
        engagement = contact.email_opens + (contact.email_clicks * 2)
        engagement_score = min(engagement / 10, 1) * 20
        score += engagement_score

        # Recency (20% weight)
        if contact.last_contacted:
            days_since = (datetime.now() - contact.last_contacted).days
            if days_since < 7:
                score += 20
            elif days_since < 14:
                score += 15
            elif days_since < 30:
                score += 10
            elif days_since < 60:
                score += 5

        # Meeting count (10% weight)
        if contact.meetings_count > 0:
            score += min(contact.meetings_count * 3, 10)

        # Profile completeness (10% weight)
        completeness = 0
        if contact.phone:
            completeness += 2.5
        if contact.company_name:
            completeness += 2.5
        if contact.title:
            completeness += 2.5
        if contact.address:
            completeness += 2.5
        score += completeness

        return min(score, 100)

    # Next Best Action

    def get_next_best_action(
        self,
        entity_type: str,
        entity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Determine the next best action for a contact or deal."""
        if entity_type == "contact":
            return self._get_contact_next_action(entity_id)
        elif entity_type == "deal":
            return self._get_deal_next_action(entity_id)
        return None

    def _get_contact_next_action(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Determine next best action for a contact."""
        if not self.contact_manager:
            return None

        contact = self.contact_manager.get_contact(contact_id)
        if not contact:
            return None

        # Analyze contact state
        now = datetime.now()
        days_since_contact = None
        if contact.last_contacted:
            days_since_contact = (now - contact.last_contacted).days

        # Determine action
        action = None
        priority = PriorityLevel.MEDIUM
        reasoning = []

        if not contact.last_contacted:
            action = "send_initial_email"
            priority = PriorityLevel.HIGH
            reasoning.append("No previous contact recorded")
        elif days_since_contact and days_since_contact > 30:
            action = "schedule_follow_up_call"
            priority = PriorityLevel.HIGH
            reasoning.append(f"No contact in {days_since_contact} days")
        elif contact.email_opens > 3 and contact.meetings_count == 0:
            action = "schedule_meeting"
            priority = PriorityLevel.HIGH
            reasoning.append("High email engagement, no meetings scheduled")
        elif contact.lead_score > 70:
            action = "create_opportunity"
            priority = PriorityLevel.CRITICAL
            reasoning.append(f"High lead score: {contact.lead_score}")
        elif days_since_contact and days_since_contact > 14:
            action = "send_nurture_email"
            priority = PriorityLevel.MEDIUM
            reasoning.append("Periodic follow-up needed")
        else:
            action = "continue_nurturing"
            priority = PriorityLevel.LOW
            reasoning.append("Continue current engagement strategy")

        return {
            'action': action,
            'priority': priority.value,
            'reasoning': reasoning,
            'contact_id': contact_id,
            'contact_name': contact.full_name,
        }

    def _get_deal_next_action(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Determine next best action for a deal."""
        if not self.deal_manager:
            return None

        deal = self.deal_manager.get_deal(deal_id)
        if not deal:
            return None

        from .deals import DealStage

        now = datetime.now()
        days_in_stage = (now - deal.stage_changed_at).days

        action = None
        priority = PriorityLevel.MEDIUM
        reasoning = []

        # Check if stuck in stage
        if days_in_stage > 30:
            action = "review_deal_status"
            priority = PriorityLevel.HIGH
            reasoning.append(f"Deal stuck in {deal.stage.value} for {days_in_stage} days")
        elif deal.stage == DealStage.QUALIFICATION and days_in_stage > 7:
            action = "schedule_discovery_call"
            priority = PriorityLevel.HIGH
            reasoning.append("Move to needs analysis")
        elif deal.stage == DealStage.NEEDS_ANALYSIS and days_in_stage > 7:
            action = "prepare_proposal"
            priority = PriorityLevel.HIGH
            reasoning.append("Ready for proposal stage")
        elif deal.stage == DealStage.PROPOSAL:
            action = "follow_up_on_proposal"
            priority = PriorityLevel.CRITICAL
            reasoning.append("Critical stage - proposal sent")
        elif deal.stage == DealStage.NEGOTIATION:
            action = "address_objections"
            priority = PriorityLevel.CRITICAL
            reasoning.append("Final stage - close deal")
        elif deal.expected_close_date and deal.expected_close_date <= date.today() + timedelta(days=7):
            action = "accelerate_close"
            priority = PriorityLevel.CRITICAL
            reasoning.append("Close date approaching")
        else:
            action = "maintain_engagement"
            priority = PriorityLevel.MEDIUM
            reasoning.append("Deal progressing normally")

        return {
            'action': action,
            'priority': priority.value,
            'reasoning': reasoning,
            'deal_id': deal_id,
            'deal_name': deal.name,
            'stage': deal.stage.value,
        }

    # Deal Insights

    def analyze_deal_risk(self, deal_id: str) -> Dict[str, Any]:
        """Analyze risk factors for a deal."""
        if not self.deal_manager:
            return {}

        deal = self.deal_manager.get_deal(deal_id)
        if not deal:
            return {}

        risk_factors = []
        risk_score = 0  # 0-100, higher = more risk

        # Check activity level
        if self.activity_manager:
            activities = self.activity_manager.list_activities(deal_id=deal_id, limit=10)
            if len(activities) < 3:
                risk_factors.append("Low activity level")
                risk_score += 20

            # Check recent activity
            if activities:
                last_activity = activities[0].created_at
                days_since = (datetime.now() - last_activity).days
                if days_since > 14:
                    risk_factors.append(f"No activity in {days_since} days")
                    risk_score += 15

        # Check time in stage
        days_in_stage = (datetime.now() - deal.stage_changed_at).days
        if days_in_stage > 30:
            risk_factors.append(f"Stuck in {deal.stage.value} for {days_in_stage} days")
            risk_score += 25

        # Check close date
        if deal.expected_close_date:
            days_until_close = (datetime.now() - datetime.combine(deal.expected_close_date, datetime.min.time())).days
            if days_until_close > 0:
                risk_factors.append("Past expected close date")
                risk_score += 20

        # Check contact engagement
        if deal.contact_id and self.contact_manager:
            contact = self.contact_manager.get_contact(deal.contact_id)
            if contact:
                if contact.email_opens == 0:
                    risk_factors.append("No email engagement")
                    risk_score += 10

        # Determine risk level
        if risk_score >= 60:
            risk_level = ChurnRisk.HIGH
        elif risk_score >= 40:
            risk_level = ChurnRisk.MEDIUM
        elif risk_score >= 20:
            risk_level = ChurnRisk.LOW
        else:
            risk_level = ChurnRisk.NONE

        return {
            'deal_id': deal_id,
            'risk_level': risk_level.value,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'recommendations': self._get_risk_recommendations(risk_factors),
        }

    def _get_risk_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Get recommendations based on risk factors."""
        recommendations = []

        for factor in risk_factors:
            if "activity" in factor.lower():
                recommendations.append("Schedule immediate follow-up call")
            if "stuck" in factor.lower():
                recommendations.append("Review and address blockers")
            if "close date" in factor.lower():
                recommendations.append("Update close date or accelerate deal")
            if "engagement" in factor.lower():
                recommendations.append("Re-engage with personalized outreach")

        if not recommendations:
            recommendations.append("Continue current strategy")

        return list(set(recommendations))  # Remove duplicates

    def predict_win_probability(self, deal_id: str) -> Dict[str, Any]:
        """Predict win probability for a deal."""
        if not self.deal_manager:
            return {}

        deal = self.deal_manager.get_deal(deal_id)
        if not deal:
            return {}

        # Base probability from stage
        base_probability = deal.probability

        # Adjustment factors
        adjustments = []
        total_adjustment = 0

        # Activity level
        if self.activity_manager:
            activities = self.activity_manager.list_activities(deal_id=deal_id)
            if len(activities) > 10:
                adjustments.append(("High activity level", 10))
                total_adjustment += 10
            elif len(activities) < 3:
                adjustments.append(("Low activity level", -15))
                total_adjustment -= 15

        # Deal age
        days_old = (datetime.now() - deal.created_at).days
        if days_old < 30:
            adjustments.append(("Recent deal - high momentum", 5))
            total_adjustment += 5
        elif days_old > 90:
            adjustments.append(("Old deal - losing momentum", -10))
            total_adjustment -= 10

        # Contact engagement
        if deal.contact_id and self.contact_manager:
            contact = self.contact_manager.get_contact(deal.contact_id)
            if contact:
                if contact.email_opens > 5:
                    adjustments.append(("High email engagement", 8))
                    total_adjustment += 8
                if contact.meetings_count > 2:
                    adjustments.append(("Multiple meetings held", 12))
                    total_adjustment += 12

        # Company size (if available)
        if deal.company_id and self.company_manager:
            company = self.company_manager.get_company(deal.company_id)
            if company and company.employee_count:
                if company.employee_count > 1000:
                    adjustments.append(("Enterprise company - longer sales cycle", -5))
                    total_adjustment -= 5

        # Calculate final probability
        predicted_probability = base_probability + total_adjustment
        predicted_probability = max(0, min(100, predicted_probability))

        return {
            'deal_id': deal_id,
            'base_probability': base_probability,
            'predicted_probability': round(predicted_probability, 2),
            'adjustments': adjustments,
            'confidence': 75,  # AI confidence in prediction
        }

    # Churn Prediction

    def predict_customer_churn(self, company_id: str) -> Dict[str, Any]:
        """Predict churn risk for a customer."""
        if not self.company_manager:
            return {}

        company = self.company_manager.get_company(company_id)
        if not company:
            return {}

        from .companies import CompanyType

        # Only predict for customers
        if company.company_type != CompanyType.CUSTOMER:
            return {
                'company_id': company_id,
                'churn_risk': ChurnRisk.NONE.value,
                'message': 'Not a customer',
            }

        risk_factors = []
        churn_score = 0  # 0-100, higher = more risk

        # Check last interaction
        if company.last_interaction:
            days_since = (datetime.now() - company.last_interaction).days
            if days_since > 90:
                risk_factors.append(f"No interaction in {days_since} days")
                churn_score += 30
            elif days_since > 60:
                risk_factors.append(f"Limited interaction ({days_since} days)")
                churn_score += 20

        # Check health score
        if company.health_score < 50:
            risk_factors.append(f"Low health score: {company.health_score}")
            churn_score += 25

        # Check open deals
        if company.open_deals_count == 0:
            risk_factors.append("No active opportunities")
            churn_score += 15

        # Check support tickets or activities
        if self.activity_manager:
            recent_activities = self.activity_manager.list_activities(
                company_id=company_id,
                start_date=datetime.now() - timedelta(days=30)
            )
            if len(recent_activities) == 0:
                risk_factors.append("No recent activity")
                churn_score += 20

        # Determine risk level
        if churn_score >= 60:
            churn_risk = ChurnRisk.HIGH
        elif churn_score >= 40:
            churn_risk = ChurnRisk.MEDIUM
        elif churn_score >= 20:
            churn_risk = ChurnRisk.LOW
        else:
            churn_risk = ChurnRisk.NONE

        # Recommendations
        recommendations = []
        if churn_risk in [ChurnRisk.HIGH, ChurnRisk.MEDIUM]:
            recommendations.extend([
                "Schedule executive check-in call",
                "Review product usage and satisfaction",
                "Identify upsell or expansion opportunities",
                "Assign dedicated success manager",
            ])

        return {
            'company_id': company_id,
            'company_name': company.name,
            'churn_risk': churn_risk.value,
            'churn_score': churn_score,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'confidence': 70,
        }

    # Upsell Opportunities

    def identify_upsell_opportunities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Identify upsell and cross-sell opportunities."""
        if not self.company_manager:
            return []

        from .companies import CompanyType

        customers = [
            c for c in self.company_manager.companies.values()
            if c.company_type == CompanyType.CUSTOMER
        ]

        opportunities = []

        for company in customers:
            score = self._calculate_upsell_score(company)
            if score > 30:  # Threshold for opportunity
                opportunities.append({
                    'company_id': company.id,
                    'company_name': company.name,
                    'upsell_score': round(score, 2),
                    'current_revenue': company.total_revenue,
                    'health_score': company.health_score,
                    'reasons': self._get_upsell_reasons(company),
                })

        # Sort by score
        opportunities.sort(key=lambda x: x['upsell_score'], reverse=True)

        return opportunities[:limit]

    def _calculate_upsell_score(self, company) -> float:
        """Calculate upsell opportunity score."""
        score = 0.0

        # Health score
        if company.health_score > 80:
            score += 30
        elif company.health_score > 60:
            score += 20

        # Revenue
        if company.total_revenue > 50000:
            score += 25

        # Engagement
        if company.last_interaction:
            days_since = (datetime.now() - company.last_interaction).days
            if days_since < 30:
                score += 20

        # Won deals
        if company.won_deals_count > 3:
            score += 15

        # Company size
        if company.employee_count and company.employee_count > 100:
            score += 10

        return min(score, 100)

    def _get_upsell_reasons(self, company) -> List[str]:
        """Get reasons for upsell opportunity."""
        reasons = []

        if company.health_score > 80:
            reasons.append("High customer satisfaction")
        if company.total_revenue > 50000:
            reasons.append("Significant current investment")
        if company.won_deals_count > 3:
            reasons.append("Multiple successful deals")
        if company.employee_count and company.employee_count > 100:
            reasons.append("Large organization with expansion potential")

        return reasons

    # Insight Management

    def generate_insights(self, entity_type: str, entity_id: str) -> List[AIInsight]:
        """Generate all relevant insights for an entity."""
        insights = []

        if entity_type == "contact":
            # Generate lead priority insight
            if self.contact_manager:
                contact = self.contact_manager.get_contact(entity_id)
                if contact:
                    priority_score = self._calculate_lead_priority_score(contact)
                    if priority_score > 70:
                        insight = self._create_priority_insight(contact, priority_score)
                        insights.append(insight)

                    # Next action insight
                    next_action = self._get_contact_next_action(entity_id)
                    if next_action:
                        insight = self._create_action_insight("contact", contact.id, contact.full_name, next_action)
                        insights.append(insight)

        elif entity_type == "deal":
            if self.deal_manager:
                deal = self.deal_manager.get_deal(entity_id)
                if deal:
                    # Risk insight
                    risk_analysis = self.analyze_deal_risk(entity_id)
                    if risk_analysis.get('risk_score', 0) > 40:
                        insight = self._create_risk_insight(deal, risk_analysis)
                        insights.append(insight)

        return insights

    def _create_priority_insight(self, contact, score: float) -> AIInsight:
        """Create a priority insight for a contact."""
        return AIInsight(
            id=self._generate_id("insight"),
            insight_type=InsightType.LEAD_PRIORITY,
            entity_type="contact",
            entity_id=contact.id,
            entity_name=contact.full_name,
            title=f"High-priority lead: {contact.full_name}",
            description=f"This lead has a priority score of {score:.0f}/100 and should be contacted soon.",
            priority=PriorityLevel.HIGH,
            confidence=85,
            recommended_actions=["Schedule a call", "Send personalized email"],
            metrics={'priority_score': score, 'lead_score': contact.lead_score},
        )

    def _create_action_insight(
        self,
        entity_type: str,
        entity_id: str,
        entity_name: str,
        action_data: Dict[str, Any]
    ) -> AIInsight:
        """Create a next best action insight."""
        return AIInsight(
            id=self._generate_id("insight"),
            insight_type=InsightType.NEXT_BEST_ACTION,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            title=f"Next best action: {action_data['action']}",
            description=f"Recommended action based on current state and engagement patterns.",
            priority=PriorityLevel[action_data['priority'].upper()],
            confidence=75,
            recommended_actions=[action_data['action']],
            reasoning=action_data['reasoning'],
        )

    def _create_risk_insight(self, deal, risk_analysis: Dict[str, Any]) -> AIInsight:
        """Create a risk insight for a deal."""
        return AIInsight(
            id=self._generate_id("insight"),
            insight_type=InsightType.DEAL_RISK,
            entity_type="deal",
            entity_id=deal.id,
            entity_name=deal.name,
            title=f"Deal at risk: {deal.name}",
            description=f"This deal has a {risk_analysis['risk_level']} risk level.",
            priority=PriorityLevel.HIGH if risk_analysis['risk_level'] == 'high' else PriorityLevel.MEDIUM,
            confidence=70,
            recommended_actions=risk_analysis['recommendations'],
            metrics={'risk_score': risk_analysis['risk_score']},
            reasoning=risk_analysis['risk_factors'],
        )

    def get_insights(
        self,
        insight_type: Optional[InsightType] = None,
        entity_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get insights with filtering."""
        insights = list(self.insights.values())

        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]

        if entity_id:
            insights = [i for i in insights if i.entity_id == entity_id]

        if active_only:
            insights = [i for i in insights if not i.is_dismissed]
            # Filter expired insights
            now = datetime.now()
            insights = [i for i in insights if not i.expires_at or i.expires_at > now]

        # Sort by priority and created_at
        insights.sort(key=lambda i: (
            i.priority.value != 'critical',
            i.priority.value != 'high',
            -i.created_at.timestamp()
        ))

        return [i.to_dict() for i in insights]

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:12]}"
