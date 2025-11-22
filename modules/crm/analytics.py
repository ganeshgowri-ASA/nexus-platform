"""
CRM Analytics Module - Dashboards, sales metrics, conversion rates, and revenue analytics.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics


class MetricPeriod(Enum):
    """Time period for metrics."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    ALL_TIME = "all_time"


class ReportType(Enum):
    """Report types."""
    SALES_PERFORMANCE = "sales_performance"
    PIPELINE_ANALYSIS = "pipeline_analysis"
    ACTIVITY_REPORT = "activity_report"
    CONVERSION_FUNNEL = "conversion_funnel"
    REVENUE_FORECAST = "revenue_forecast"
    TEAM_PERFORMANCE = "team_performance"
    CONTACT_ENGAGEMENT = "contact_engagement"
    EMAIL_PERFORMANCE = "email_performance"


@dataclass
class MetricValue:
    """A metric value with comparison."""
    current: float
    previous: Optional[float] = None
    change_percent: Optional[float] = None
    change_absolute: Optional[float] = None
    trend: str = "neutral"  # up, down, neutral

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'current': round(self.current, 2),
            'previous': round(self.previous, 2) if self.previous is not None else None,
            'change_percent': round(self.change_percent, 2) if self.change_percent is not None else None,
            'change_absolute': round(self.change_absolute, 2) if self.change_absolute is not None else None,
            'trend': self.trend,
        }


@dataclass
class Dashboard:
    """Dashboard configuration."""
    id: str
    name: str
    description: Optional[str] = None
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    owner_id: Optional[str] = None
    is_shared: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'widgets': self.widgets,
            'owner_id': self.owner_id,
            'is_shared': self.is_shared,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class CRMAnalytics:
    """Comprehensive CRM analytics and reporting."""

    def __init__(
        self,
        contact_manager=None,
        company_manager=None,
        deal_manager=None,
        activity_manager=None,
        task_manager=None,
        email_manager=None
    ):
        """Initialize analytics with CRM managers."""
        self.contact_manager = contact_manager
        self.company_manager = company_manager
        self.deal_manager = deal_manager
        self.activity_manager = activity_manager
        self.task_manager = task_manager
        self.email_manager = email_manager

        self.dashboards: Dict[str, Dashboard] = {}

    # Key Metrics

    def get_key_metrics(self, period: MetricPeriod = MetricPeriod.MONTH) -> Dict[str, MetricValue]:
        """Get key CRM metrics with period comparison."""
        current_start, current_end = self._get_period_dates(period)
        previous_start, previous_end = self._get_previous_period_dates(period)

        metrics = {}

        # Total Revenue
        current_revenue = self._calculate_revenue(current_start, current_end)
        previous_revenue = self._calculate_revenue(previous_start, previous_end)
        metrics['total_revenue'] = self._create_metric(current_revenue, previous_revenue)

        # New Deals
        current_deals = self._count_new_deals(current_start, current_end)
        previous_deals = self._count_new_deals(previous_start, previous_end)
        metrics['new_deals'] = self._create_metric(current_deals, previous_deals)

        # Win Rate
        current_win_rate = self._calculate_win_rate(current_start, current_end)
        previous_win_rate = self._calculate_win_rate(previous_start, previous_end)
        metrics['win_rate'] = self._create_metric(current_win_rate, previous_win_rate)

        # Average Deal Size
        current_avg_deal = self._calculate_avg_deal_size(current_start, current_end)
        previous_avg_deal = self._calculate_avg_deal_size(previous_start, previous_end)
        metrics['avg_deal_size'] = self._create_metric(current_avg_deal, previous_avg_deal)

        # Sales Cycle Length
        current_cycle = self._calculate_avg_sales_cycle(current_start, current_end)
        previous_cycle = self._calculate_avg_sales_cycle(previous_start, previous_end)
        metrics['avg_sales_cycle_days'] = self._create_metric(current_cycle, previous_cycle, inverse=True)

        # New Contacts
        current_contacts = self._count_new_contacts(current_start, current_end)
        previous_contacts = self._count_new_contacts(previous_start, previous_end)
        metrics['new_contacts'] = self._create_metric(current_contacts, previous_contacts)

        # Pipeline Value
        pipeline_value = self._calculate_pipeline_value()
        metrics['pipeline_value'] = MetricValue(current=pipeline_value)

        return {k: v.to_dict() for k, v in metrics.items()}

    def get_sales_performance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive sales performance metrics."""
        if not self.deal_manager:
            return {}

        deals = list(self.deal_manager.deals.values())

        # Filter by date range
        if start_date:
            deals = [d for d in deals if d.created_at >= start_date]
        if end_date:
            deals = [d for d in deals if d.created_at <= end_date]

        # Filter by owner
        if owner_id:
            deals = [d for d in deals if d.owner_id == owner_id]

        # Calculate metrics
        total_deals = len(deals)
        open_deals = [d for d in deals if not d.is_closed]
        closed_deals = [d for d in deals if d.is_closed]
        won_deals = [d for d in closed_deals if d.is_won]
        lost_deals = [d for d in closed_deals if not d.is_won]

        total_revenue = sum(d.amount for d in won_deals)
        pipeline_value = sum(d.amount for d in open_deals)
        weighted_pipeline = sum(d.weighted_value for d in open_deals)

        win_rate = (len(won_deals) / len(closed_deals) * 100) if closed_deals else 0
        avg_deal_size = (total_revenue / len(won_deals)) if won_deals else 0

        # Calculate average sales cycle
        cycle_days = []
        for deal in won_deals:
            if deal.actual_close_date:
                close_dt = datetime.combine(deal.actual_close_date, datetime.min.time())
                days = (close_dt - deal.created_at).days
                cycle_days.append(days)
        avg_sales_cycle = statistics.mean(cycle_days) if cycle_days else 0

        return {
            'total_deals': total_deals,
            'open_deals': len(open_deals),
            'closed_deals': len(closed_deals),
            'won_deals': len(won_deals),
            'lost_deals': len(lost_deals),
            'win_rate': round(win_rate, 2),
            'total_revenue': round(total_revenue, 2),
            'pipeline_value': round(pipeline_value, 2),
            'weighted_pipeline': round(weighted_pipeline, 2),
            'avg_deal_size': round(avg_deal_size, 2),
            'avg_sales_cycle_days': round(avg_sales_cycle, 1),
        }

    def get_pipeline_analysis(self) -> Dict[str, Any]:
        """Analyze pipeline health and distribution."""
        if not self.deal_manager:
            return {}

        open_deals = [d for d in self.deal_manager.deals.values() if not d.is_closed]

        # By stage
        by_stage = defaultdict(lambda: {'count': 0, 'value': 0, 'weighted_value': 0})
        for deal in open_deals:
            stage = deal.stage.value
            by_stage[stage]['count'] += 1
            by_stage[stage]['value'] += deal.amount
            by_stage[stage]['weighted_value'] += deal.weighted_value

        # By age
        now = datetime.now()
        age_buckets = {
            '0-30 days': 0,
            '31-60 days': 0,
            '61-90 days': 0,
            '90+ days': 0,
        }
        for deal in open_deals:
            days_old = (now - deal.created_at).days
            if days_old <= 30:
                age_buckets['0-30 days'] += 1
            elif days_old <= 60:
                age_buckets['31-60 days'] += 1
            elif days_old <= 90:
                age_buckets['61-90 days'] += 1
            else:
                age_buckets['90+ days'] += 1

        # At-risk deals
        at_risk = self.deal_manager.get_deals_at_risk(days_threshold=30)

        return {
            'total_open_deals': len(open_deals),
            'total_pipeline_value': sum(d.amount for d in open_deals),
            'by_stage': dict(by_stage),
            'by_age': age_buckets,
            'at_risk_count': len(at_risk),
            'at_risk_value': sum(d.amount for d in at_risk),
        }

    def get_conversion_funnel(self) -> List[Dict[str, Any]]:
        """Get conversion funnel data."""
        if not self.deal_manager:
            return []

        from .deals import DealStage

        funnel_stages = [
            DealStage.QUALIFICATION,
            DealStage.NEEDS_ANALYSIS,
            DealStage.PROPOSAL,
            DealStage.NEGOTIATION,
            DealStage.CLOSED_WON,
        ]

        all_deals = list(self.deal_manager.deals.values())
        funnel = []

        for i, stage in enumerate(funnel_stages):
            # Count deals that reached this stage
            stage_deals = [d for d in all_deals if d.stage == stage or (d.is_closed and d.is_won)]

            stage_data = {
                'stage': stage.value,
                'stage_name': stage.value.replace('_', ' ').title(),
                'count': len([d for d in all_deals if d.stage == stage]),
                'value': sum(d.amount for d in all_deals if d.stage == stage),
                'conversion_rate': 0.0,
            }

            # Calculate conversion from previous stage
            if i > 0:
                prev_count = funnel[i-1]['count']
                if prev_count > 0:
                    stage_data['conversion_rate'] = round(
                        (stage_data['count'] / prev_count) * 100, 2
                    )

            funnel.append(stage_data)

        return funnel

    def get_revenue_forecast(
        self,
        months_ahead: int = 3
    ) -> Dict[str, Any]:
        """Generate revenue forecast."""
        if not self.deal_manager:
            return {}

        forecast = self.deal_manager.get_forecast()

        # Monthly projections
        monthly_projections = []
        current_date = date.today()

        for i in range(months_ahead):
            month_start = current_date.replace(day=1) + timedelta(days=32*i)
            month_start = month_start.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            # Get deals expected to close in this month
            month_deals = [
                d for d in self.deal_manager.deals.values()
                if d.expected_close_date
                and month_start <= d.expected_close_date <= month_end
                and not d.is_closed
            ]

            monthly_projections.append({
                'month': month_start.strftime('%Y-%m'),
                'best_case': sum(d.amount for d in month_deals),
                'most_likely': sum(d.weighted_value for d in month_deals),
                'worst_case': sum(d.amount for d in month_deals if d.probability >= 75),
                'deal_count': len(month_deals),
            })

        return {
            'forecast': forecast,
            'monthly_projections': monthly_projections,
        }

    def get_activity_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get activity metrics and trends."""
        if not self.activity_manager:
            return {}

        activities = list(self.activity_manager.activities.values())

        # Filter by date range
        if start_date:
            activities = [a for a in activities if a.created_at >= start_date]
        if end_date:
            activities = [a for a in activities if a.created_at <= end_date]

        # Filter by owner
        if owner_id:
            activities = [a for a in activities if a.owner_id == owner_id]

        # By type
        from .activities import ActivityType
        by_type = {}
        for activity_type in ActivityType:
            count = len([a for a in activities if a.activity_type == activity_type])
            by_type[activity_type.value] = count

        # Daily activity trend
        daily_counts = defaultdict(int)
        for activity in activities:
            day = activity.created_at.date().isoformat()
            daily_counts[day] += 1

        return {
            'total_activities': len(activities),
            'by_type': by_type,
            'daily_trend': dict(daily_counts),
            'avg_per_day': round(len(activities) / max(len(daily_counts), 1), 2),
        }

    def get_team_performance(self) -> List[Dict[str, Any]]:
        """Get performance metrics by team member."""
        if not self.deal_manager:
            return []

        # Get unique owners
        owners = set()
        for deal in self.deal_manager.deals.values():
            if deal.owner_id:
                owners.add(deal.owner_id)

        team_stats = []
        for owner_id in owners:
            owner_deals = [d for d in self.deal_manager.deals.values() if d.owner_id == owner_id]
            won_deals = [d for d in owner_deals if d.is_closed and d.is_won]
            closed_deals = [d for d in owner_deals if d.is_closed]

            total_revenue = sum(d.amount for d in won_deals)
            win_rate = (len(won_deals) / len(closed_deals) * 100) if closed_deals else 0

            # Activity count
            activity_count = 0
            if self.activity_manager:
                activity_count = len([a for a in self.activity_manager.activities.values() if a.owner_id == owner_id])

            team_stats.append({
                'owner_id': owner_id,
                'total_deals': len(owner_deals),
                'won_deals': len(won_deals),
                'win_rate': round(win_rate, 2),
                'total_revenue': round(total_revenue, 2),
                'activities': activity_count,
            })

        # Sort by revenue descending
        team_stats.sort(key=lambda x: x['total_revenue'], reverse=True)
        return team_stats

    def get_contact_engagement(self) -> Dict[str, Any]:
        """Analyze contact engagement metrics."""
        if not self.contact_manager:
            return {}

        contacts = list(self.contact_manager.contacts.values())

        # Engagement tiers
        high_engagement = []
        medium_engagement = []
        low_engagement = []
        no_engagement = []

        for contact in contacts:
            score = contact.email_opens + contact.email_clicks + (contact.meetings_count * 3)
            if score >= 10:
                high_engagement.append(contact)
            elif score >= 5:
                medium_engagement.append(contact)
            elif score > 0:
                low_engagement.append(contact)
            else:
                no_engagement.append(contact)

        return {
            'total_contacts': len(contacts),
            'high_engagement': len(high_engagement),
            'medium_engagement': len(medium_engagement),
            'low_engagement': len(low_engagement),
            'no_engagement': len(no_engagement),
            'avg_lead_score': round(statistics.mean([c.lead_score for c in contacts]) if contacts else 0, 2),
        }

    def get_email_performance(self) -> Dict[str, Any]:
        """Get email marketing performance metrics."""
        if not self.email_manager:
            return {}

        # Template performance
        templates = list(self.email_manager.templates.values())
        templates.sort(key=lambda t: t.open_rate, reverse=True)

        top_templates = [
            {
                'id': t.id,
                'name': t.name,
                'sent': t.total_sent,
                'open_rate': round(t.open_rate, 2),
                'click_rate': round(t.click_rate, 2),
                'reply_rate': round(t.reply_rate, 2),
            }
            for t in templates[:10]
        ]

        # Overall stats
        total_sent = sum(t.total_sent for t in templates)
        total_opened = sum(t.total_opened for t in templates)
        total_clicked = sum(t.total_clicked for t in templates)
        total_replied = sum(t.total_replied for t in templates)

        return {
            'total_templates': len(templates),
            'total_sent': total_sent,
            'overall_open_rate': round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2),
            'overall_click_rate': round((total_clicked / total_sent * 100) if total_sent > 0 else 0, 2),
            'overall_reply_rate': round((total_replied / total_sent * 100) if total_sent > 0 else 0, 2),
            'top_templates': top_templates,
        }

    # Dashboard Management

    def create_dashboard(self, dashboard: Dashboard) -> Dashboard:
        """Create a dashboard."""
        self.dashboards[dashboard.id] = dashboard
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get a dashboard by ID."""
        return self.dashboards.get(dashboard_id)

    def update_dashboard(self, dashboard_id: str, updates: Dict[str, Any]) -> Optional[Dashboard]:
        """Update a dashboard."""
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard:
            return None

        for key, value in updates.items():
            if hasattr(dashboard, key):
                setattr(dashboard, key, value)

        dashboard.updated_at = datetime.now()
        return dashboard

    # Helper Methods

    def _get_period_dates(self, period: MetricPeriod) -> Tuple[datetime, datetime]:
        """Get start and end dates for a period."""
        end = datetime.now()

        if period == MetricPeriod.DAY:
            start = end.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == MetricPeriod.WEEK:
            start = end - timedelta(days=7)
        elif period == MetricPeriod.MONTH:
            start = end - timedelta(days=30)
        elif period == MetricPeriod.QUARTER:
            start = end - timedelta(days=90)
        elif period == MetricPeriod.YEAR:
            start = end - timedelta(days=365)
        else:  # ALL_TIME
            start = datetime.min

        return start, end

    def _get_previous_period_dates(self, period: MetricPeriod) -> Tuple[datetime, datetime]:
        """Get dates for the previous period for comparison."""
        current_start, current_end = self._get_period_dates(period)
        duration = current_end - current_start

        previous_end = current_start
        previous_start = previous_end - duration

        return previous_start, previous_end

    def _create_metric(
        self,
        current: float,
        previous: Optional[float],
        inverse: bool = False
    ) -> MetricValue:
        """Create a metric value with comparison."""
        metric = MetricValue(current=current, previous=previous)

        if previous is not None and previous > 0:
            metric.change_absolute = current - previous
            metric.change_percent = (metric.change_absolute / previous) * 100

            # Determine trend
            if metric.change_percent > 1:
                metric.trend = "down" if inverse else "up"
            elif metric.change_percent < -1:
                metric.trend = "up" if inverse else "down"
            else:
                metric.trend = "neutral"

        return metric

    def _calculate_revenue(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate revenue for a period."""
        if not self.deal_manager:
            return 0.0

        won_deals = [
            d for d in self.deal_manager.deals.values()
            if d.is_won
            and d.actual_close_date
            and start_date.date() <= d.actual_close_date <= end_date.date()
        ]
        return sum(d.amount for d in won_deals)

    def _count_new_deals(self, start_date: datetime, end_date: datetime) -> int:
        """Count new deals created in a period."""
        if not self.deal_manager:
            return 0

        return len([
            d for d in self.deal_manager.deals.values()
            if start_date <= d.created_at <= end_date
        ])

    def _calculate_win_rate(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate win rate for a period."""
        if not self.deal_manager:
            return 0.0

        closed_deals = [
            d for d in self.deal_manager.deals.values()
            if d.is_closed
            and d.actual_close_date
            and start_date.date() <= d.actual_close_date <= end_date.date()
        ]

        if not closed_deals:
            return 0.0

        won_deals = [d for d in closed_deals if d.is_won]
        return (len(won_deals) / len(closed_deals)) * 100

    def _calculate_avg_deal_size(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate average deal size for a period."""
        if not self.deal_manager:
            return 0.0

        won_deals = [
            d for d in self.deal_manager.deals.values()
            if d.is_won
            and d.actual_close_date
            and start_date.date() <= d.actual_close_date <= end_date.date()
        ]

        if not won_deals:
            return 0.0

        return sum(d.amount for d in won_deals) / len(won_deals)

    def _calculate_avg_sales_cycle(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate average sales cycle length for a period."""
        if not self.deal_manager:
            return 0.0

        won_deals = [
            d for d in self.deal_manager.deals.values()
            if d.is_won
            and d.actual_close_date
            and start_date.date() <= d.actual_close_date <= end_date.date()
        ]

        if not won_deals:
            return 0.0

        cycle_days = []
        for deal in won_deals:
            close_dt = datetime.combine(deal.actual_close_date, datetime.min.time())
            days = (close_dt - deal.created_at).days
            cycle_days.append(days)

        return statistics.mean(cycle_days)

    def _count_new_contacts(self, start_date: datetime, end_date: datetime) -> int:
        """Count new contacts created in a period."""
        if not self.contact_manager:
            return 0

        return len([
            c for c in self.contact_manager.contacts.values()
            if start_date <= c.created_at <= end_date
        ])

    def _calculate_pipeline_value(self) -> float:
        """Calculate current pipeline value."""
        if not self.deal_manager:
            return 0.0

        open_deals = [d for d in self.deal_manager.deals.values() if not d.is_closed]
        return sum(d.amount for d in open_deals)

    def _generate_id(self) -> str:
        """Generate a unique ID."""
        import uuid
        return f"dashboard_{uuid.uuid4().hex[:12]}"
