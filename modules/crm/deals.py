"""
CRM Deals Module - Deal/opportunity management with pipeline stages and forecasting.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal


class DealStage(Enum):
    """Deal pipeline stages."""
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class DealPriority(Enum):
    """Deal priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LossReason(Enum):
    """Reasons for losing a deal."""
    PRICE = "price"
    COMPETITION = "competition"
    NO_BUDGET = "no_budget"
    TIMING = "timing"
    NO_DECISION = "no_decision"
    LOST_TO_COMPETITOR = "lost_to_competitor"
    REQUIREMENTS_MISMATCH = "requirements_mismatch"
    OTHER = "other"


@dataclass
class DealProduct:
    """Product/service in a deal."""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    discount: float = 0.0  # Percentage

    @property
    def total_price(self) -> float:
        """Calculate total price with discount."""
        subtotal = self.quantity * self.unit_price
        return subtotal * (1 - self.discount / 100)


@dataclass
class Deal:
    """Deal/opportunity entity."""
    id: str
    name: str
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None

    # Deal details
    stage: DealStage = DealStage.QUALIFICATION
    priority: DealPriority = DealPriority.MEDIUM
    amount: float = 0.0
    currency: str = "USD"

    # Probability and forecasting
    probability: int = 10  # Percentage (0-100)
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None

    # Weighted value for forecasting
    @property
    def weighted_value(self) -> float:
        """Calculate weighted value (amount * probability)."""
        return self.amount * (self.probability / 100)

    # Products/line items
    products: List[DealProduct] = field(default_factory=list)

    # Deal source and competition
    source: Optional[str] = None
    competitors: List[str] = field(default_factory=list)

    # Ownership and team
    owner_id: Optional[str] = None
    team_members: List[str] = field(default_factory=list)

    # Status tracking
    is_closed: bool = False
    is_won: bool = False
    loss_reason: Optional[LossReason] = None
    loss_notes: Optional[str] = None

    # Additional info
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    # Metrics
    days_in_stage: int = 0
    total_activities: int = 0
    last_activity_date: Optional[datetime] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    stage_changed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'contact_id': self.contact_id,
            'contact_name': self.contact_name,
            'stage': self.stage.value,
            'priority': self.priority.value,
            'amount': self.amount,
            'currency': self.currency,
            'probability': self.probability,
            'weighted_value': self.weighted_value,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'actual_close_date': self.actual_close_date.isoformat() if self.actual_close_date else None,
            'products': [
                {
                    'product_id': p.product_id,
                    'product_name': p.product_name,
                    'quantity': p.quantity,
                    'unit_price': p.unit_price,
                    'discount': p.discount,
                    'total_price': p.total_price,
                }
                for p in self.products
            ],
            'source': self.source,
            'competitors': self.competitors,
            'owner_id': self.owner_id,
            'team_members': self.team_members,
            'is_closed': self.is_closed,
            'is_won': self.is_won,
            'loss_reason': self.loss_reason.value if self.loss_reason else None,
            'loss_notes': self.loss_notes,
            'description': self.description,
            'notes': self.notes,
            'tags': list(self.tags),
            'custom_fields': self.custom_fields,
            'days_in_stage': self.days_in_stage,
            'total_activities': self.total_activities,
            'last_activity_date': self.last_activity_date.isoformat() if self.last_activity_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'stage_changed_at': self.stage_changed_at.isoformat(),
        }


class DealManager:
    """Manage deals with pipeline tracking and forecasting."""

    # Default stage probabilities
    STAGE_PROBABILITIES = {
        DealStage.QUALIFICATION: 10,
        DealStage.NEEDS_ANALYSIS: 25,
        DealStage.PROPOSAL: 50,
        DealStage.NEGOTIATION: 75,
        DealStage.CLOSED_WON: 100,
        DealStage.CLOSED_LOST: 0,
    }

    def __init__(self):
        """Initialize deal manager."""
        self.deals: Dict[str, Deal] = {}
        self._company_index: Dict[str, List[str]] = {}  # company_id -> [deal_ids]
        self._contact_index: Dict[str, List[str]] = {}  # contact_id -> [deal_ids]
        self._owner_index: Dict[str, List[str]] = {}  # owner_id -> [deal_ids]
        self._stage_index: Dict[DealStage, Set[str]] = {}  # stage -> {deal_ids}
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> {deal_ids}

    def create_deal(self, deal: Deal) -> Deal:
        """Create a new deal."""
        # Set default probability based on stage
        if deal.probability == 10:  # Default value
            deal.probability = self.STAGE_PROBABILITIES.get(deal.stage, 10)

        self.deals[deal.id] = deal

        # Update indexes
        if deal.company_id:
            if deal.company_id not in self._company_index:
                self._company_index[deal.company_id] = []
            self._company_index[deal.company_id].append(deal.id)

        if deal.contact_id:
            if deal.contact_id not in self._contact_index:
                self._contact_index[deal.contact_id] = []
            self._contact_index[deal.contact_id].append(deal.id)

        if deal.owner_id:
            if deal.owner_id not in self._owner_index:
                self._owner_index[deal.owner_id] = []
            self._owner_index[deal.owner_id].append(deal.id)

        if deal.stage not in self._stage_index:
            self._stage_index[deal.stage] = set()
        self._stage_index[deal.stage].add(deal.id)

        for tag in deal.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(deal.id)

        return deal

    def get_deal(self, deal_id: str) -> Optional[Deal]:
        """Get a deal by ID."""
        return self.deals.get(deal_id)

    def update_deal(self, deal_id: str, updates: Dict[str, Any]) -> Optional[Deal]:
        """Update a deal."""
        deal = self.deals.get(deal_id)
        if not deal:
            return None

        # Track stage changes
        old_stage = deal.stage
        if 'stage' in updates:
            new_stage = updates['stage'] if isinstance(updates['stage'], DealStage) else DealStage(updates['stage'])
            if new_stage != old_stage:
                # Update stage index
                self._stage_index[old_stage].discard(deal_id)
                if new_stage not in self._stage_index:
                    self._stage_index[new_stage] = set()
                self._stage_index[new_stage].add(deal_id)

                # Update stage timestamp
                deal.stage_changed_at = datetime.now()

                # Update probability based on new stage
                deal.probability = self.STAGE_PROBABILITIES.get(new_stage, deal.probability)

                # Mark as closed if won or lost
                if new_stage == DealStage.CLOSED_WON:
                    deal.is_closed = True
                    deal.is_won = True
                    deal.actual_close_date = date.today()
                elif new_stage == DealStage.CLOSED_LOST:
                    deal.is_closed = True
                    deal.is_won = False
                    deal.actual_close_date = date.today()

        # Update fields
        for key, value in updates.items():
            if hasattr(deal, key):
                # Handle enum conversions
                if key == 'stage' and isinstance(value, str):
                    value = DealStage(value)
                elif key == 'priority' and isinstance(value, str):
                    value = DealPriority(value)
                elif key == 'loss_reason' and isinstance(value, str):
                    value = LossReason(value)
                setattr(deal, key, value)

        deal.updated_at = datetime.now()
        return deal

    def delete_deal(self, deal_id: str) -> bool:
        """Delete a deal."""
        deal = self.deals.get(deal_id)
        if not deal:
            return False

        # Remove from indexes
        if deal.company_id and deal.company_id in self._company_index:
            self._company_index[deal.company_id].remove(deal_id)

        if deal.contact_id and deal.contact_id in self._contact_index:
            self._contact_index[deal.contact_id].remove(deal_id)

        if deal.owner_id and deal.owner_id in self._owner_index:
            self._owner_index[deal.owner_id].remove(deal_id)

        if deal.stage in self._stage_index:
            self._stage_index[deal.stage].discard(deal_id)

        for tag in deal.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(deal_id)

        del self.deals[deal_id]
        return True

    def list_deals(
        self,
        stage: Optional[DealStage] = None,
        company_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        is_closed: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Deal]:
        """List deals with filtering."""
        results = list(self.deals.values())

        # Apply filters
        if stage:
            results = [d for d in results if d.stage == stage]

        if company_id:
            results = [d for d in results if d.company_id == company_id]

        if contact_id:
            results = [d for d in results if d.contact_id == contact_id]

        if owner_id:
            results = [d for d in results if d.owner_id == owner_id]

        if is_closed is not None:
            results = [d for d in results if d.is_closed == is_closed]

        if tags:
            results = [d for d in results if any(tag in d.tags for tag in tags)]

        if min_amount is not None:
            results = [d for d in results if d.amount >= min_amount]

        if max_amount is not None:
            results = [d for d in results if d.amount <= max_amount]

        # Sort by priority and updated_at
        results.sort(key=lambda d: (
            d.priority.value != 'critical',
            d.priority.value != 'high',
            d.priority.value != 'medium',
            -d.updated_at.timestamp()
        ))

        # Apply pagination
        if limit:
            results = results[offset:offset + limit]
        else:
            results = results[offset:]

        return results

    def move_to_stage(self, deal_id: str, new_stage: DealStage) -> Optional[Deal]:
        """Move a deal to a new stage."""
        return self.update_deal(deal_id, {'stage': new_stage})

    def win_deal(self, deal_id: str, actual_amount: Optional[float] = None) -> Optional[Deal]:
        """Mark a deal as won."""
        updates = {
            'stage': DealStage.CLOSED_WON,
            'is_closed': True,
            'is_won': True,
            'actual_close_date': date.today(),
        }
        if actual_amount is not None:
            updates['amount'] = actual_amount
        return self.update_deal(deal_id, updates)

    def lose_deal(
        self,
        deal_id: str,
        loss_reason: LossReason,
        loss_notes: Optional[str] = None
    ) -> Optional[Deal]:
        """Mark a deal as lost."""
        updates = {
            'stage': DealStage.CLOSED_LOST,
            'is_closed': True,
            'is_won': False,
            'actual_close_date': date.today(),
            'loss_reason': loss_reason,
            'loss_notes': loss_notes,
        }
        return self.update_deal(deal_id, updates)

    def add_product(self, deal_id: str, product: DealProduct) -> Optional[Deal]:
        """Add a product to a deal."""
        deal = self.deals.get(deal_id)
        if not deal:
            return None

        deal.products.append(product)
        # Recalculate total amount
        deal.amount = sum(p.total_price for p in deal.products)
        deal.updated_at = datetime.now()
        return deal

    def remove_product(self, deal_id: str, product_id: str) -> Optional[Deal]:
        """Remove a product from a deal."""
        deal = self.deals.get(deal_id)
        if not deal:
            return None

        deal.products = [p for p in deal.products if p.product_id != product_id]
        # Recalculate total amount
        deal.amount = sum(p.total_price for p in deal.products)
        deal.updated_at = datetime.now()
        return deal

    def get_deals_by_stage(self, stage: DealStage) -> List[Deal]:
        """Get all deals in a specific stage."""
        deal_ids = self._stage_index.get(stage, set())
        return [self.deals[did] for did in deal_ids if did in self.deals]

    def get_pipeline_view(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get deals organized by stage for Kanban view."""
        pipeline = {}
        for stage in DealStage:
            deals = self.get_deals_by_stage(stage)
            pipeline[stage.value] = [d.to_dict() for d in deals]
        return pipeline

    def get_forecast(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        owner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate sales forecast based on weighted deal values."""
        deals = list(self.deals.values())

        # Filter by date range
        if start_date:
            deals = [d for d in deals if d.expected_close_date and d.expected_close_date >= start_date]
        if end_date:
            deals = [d for d in deals if d.expected_close_date and d.expected_close_date <= end_date]

        # Filter by owner
        if owner_id:
            deals = [d for d in deals if d.owner_id == owner_id]

        # Calculate metrics
        open_deals = [d for d in deals if not d.is_closed]

        total_pipeline = sum(d.amount for d in open_deals)
        weighted_pipeline = sum(d.weighted_value for d in open_deals)
        best_case = sum(d.amount for d in open_deals)
        worst_case = sum(d.amount for d in open_deals if d.probability >= 75)

        # By stage
        by_stage = {}
        for stage in DealStage:
            stage_deals = [d for d in open_deals if d.stage == stage]
            by_stage[stage.value] = {
                'count': len(stage_deals),
                'total_value': sum(d.amount for d in stage_deals),
                'weighted_value': sum(d.weighted_value for d in stage_deals),
            }

        return {
            'total_pipeline_value': total_pipeline,
            'weighted_pipeline_value': weighted_pipeline,
            'best_case_scenario': best_case,
            'worst_case_scenario': worst_case,
            'total_deals': len(open_deals),
            'by_stage': by_stage,
        }

    def get_conversion_rates(self) -> Dict[str, Any]:
        """Calculate conversion rates between stages."""
        closed_deals = [d for d in self.deals.values() if d.is_closed]
        won_deals = [d for d in closed_deals if d.is_won]
        lost_deals = [d for d in closed_deals if not d.is_won]

        total_closed = len(closed_deals)
        win_rate = (len(won_deals) / total_closed * 100) if total_closed > 0 else 0

        # Loss reasons analysis
        loss_reasons = {}
        for deal in lost_deals:
            if deal.loss_reason:
                reason = deal.loss_reason.value
                loss_reasons[reason] = loss_reasons.get(reason, 0) + 1

        # Average deal size
        avg_deal_size = sum(d.amount for d in won_deals) / len(won_deals) if won_deals else 0

        # Average sales cycle
        cycle_days = []
        for deal in won_deals:
            if deal.actual_close_date:
                days = (datetime.combine(deal.actual_close_date, datetime.min.time()) - deal.created_at).days
                cycle_days.append(days)
        avg_cycle = sum(cycle_days) / len(cycle_days) if cycle_days else 0

        return {
            'total_closed_deals': total_closed,
            'won_deals': len(won_deals),
            'lost_deals': len(lost_deals),
            'win_rate': round(win_rate, 2),
            'loss_reasons': loss_reasons,
            'average_deal_size': round(avg_deal_size, 2),
            'average_sales_cycle_days': round(avg_cycle, 1),
        }

    def get_deals_at_risk(self, days_threshold: int = 30) -> List[Deal]:
        """Identify deals at risk based on activity and time in stage."""
        at_risk = []
        now = datetime.now()

        for deal in self.deals.values():
            if deal.is_closed:
                continue

            # Check if no recent activity
            if deal.last_activity_date:
                days_since_activity = (now - deal.last_activity_date).days
                if days_since_activity > days_threshold:
                    at_risk.append(deal)
                    continue

            # Check if stuck in stage too long
            days_in_stage = (now - deal.stage_changed_at).days
            if days_in_stage > days_threshold:
                at_risk.append(deal)

        return at_risk

    def update_days_in_stage(self):
        """Update days_in_stage for all deals."""
        now = datetime.now()
        for deal in self.deals.values():
            if not deal.is_closed:
                deal.days_in_stage = (now - deal.stage_changed_at).days

    def add_tags(self, deal_id: str, tags: List[str]) -> Optional[Deal]:
        """Add tags to a deal."""
        deal = self.deals.get(deal_id)
        if not deal:
            return None

        for tag in tags:
            deal.tags.add(tag)
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(deal_id)

        deal.updated_at = datetime.now()
        return deal

    def get_statistics(self) -> Dict[str, Any]:
        """Get deal statistics."""
        total = len(self.deals)
        open_deals = [d for d in self.deals.values() if not d.is_closed]
        closed_deals = [d for d in self.deals.values() if d.is_closed]

        by_stage = {}
        for stage in DealStage:
            stage_deals = [d for d in self.deals.values() if d.stage == stage]
            by_stage[stage.value] = {
                'count': len(stage_deals),
                'value': sum(d.amount for d in stage_deals)
            }

        return {
            'total_deals': total,
            'open_deals': len(open_deals),
            'closed_deals': len(closed_deals),
            'won_deals': len([d for d in closed_deals if d.is_won]),
            'lost_deals': len([d for d in closed_deals if not d.is_won]),
            'total_pipeline_value': sum(d.amount for d in open_deals),
            'total_won_value': sum(d.amount for d in closed_deals if d.is_won),
            'by_stage': by_stage,
        }

    def _generate_id(self) -> str:
        """Generate a unique deal ID."""
        import uuid
        return f"deal_{uuid.uuid4().hex[:12]}"
