"""Contract approval workflows.

This module handles multi-level approval chains, conditional routing,
escalation, and notifications.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class ApprovalStatus(str, Enum):
    """Approval request status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class ApprovalRequest(BaseModel):
    """Approval request for a contract."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    approver_id: UUID
    approver_name: str
    approver_email: str
    level: int = 1
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    responded_at: Optional[datetime] = None
    comments: Optional[str] = None
    due_date: Optional[datetime] = None
    escalated_to: Optional[UUID] = None
    escalated_at: Optional[datetime] = None
    metadata: Dict = Field(default_factory=dict)


class ApprovalChain(BaseModel):
    """Approval chain configuration."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    levels: List[Dict] = Field(default_factory=list)
    # Each level: {"level": 1, "approvers": [UUID], "required_count": 1, "timeout_hours": 24}
    conditions: Dict = Field(default_factory=dict)
    # Conditions: {"contract_value_threshold": 10000, "risk_level": "high"}
    auto_escalate: bool = True
    escalation_hours: int = 24
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalManager:
    """Manages contract approval workflows."""

    def __init__(self):
        """Initialize approval manager."""
        self.chains: Dict[UUID, ApprovalChain] = {}
        self.requests: Dict[UUID, List[ApprovalRequest]] = {}

    def create_approval_chain(
        self,
        name: str,
        levels: List[Dict],
        description: Optional[str] = None,
        conditions: Optional[Dict] = None,
        auto_escalate: bool = True,
        escalation_hours: int = 24,
    ) -> ApprovalChain:
        """Create an approval chain.

        Args:
            name: Chain name
            levels: List of approval levels
            description: Optional description
            conditions: Optional triggering conditions
            auto_escalate: Auto-escalate on timeout
            escalation_hours: Hours before escalation

        Returns:
            New approval chain
        """
        logger.info("Creating approval chain", name=name, levels=len(levels))

        chain = ApprovalChain(
            name=name,
            description=description,
            levels=levels,
            conditions=conditions or {},
            auto_escalate=auto_escalate,
            escalation_hours=escalation_hours,
        )

        self.chains[chain.id] = chain
        return chain

    def get_applicable_chain(
        self,
        contract_value: Optional[float] = None,
        risk_level: Optional[str] = None,
        contract_type: Optional[str] = None,
    ) -> Optional[ApprovalChain]:
        """Get applicable approval chain based on conditions.

        Args:
            contract_value: Contract value
            risk_level: Risk level
            contract_type: Contract type

        Returns:
            Applicable approval chain or None
        """
        for chain in self.chains.values():
            if not chain.is_active:
                continue

            # Check conditions
            conditions = chain.conditions
            if not conditions:
                return chain

            if contract_value and "contract_value_threshold" in conditions:
                if contract_value < conditions["contract_value_threshold"]:
                    continue

            if risk_level and "risk_level" in conditions:
                if risk_level != conditions["risk_level"]:
                    continue

            if contract_type and "contract_type" in conditions:
                if contract_type != conditions["contract_type"]:
                    continue

            return chain

        return None

    def initiate_approval(
        self,
        contract_id: UUID,
        chain_id: Optional[UUID] = None,
        contract_value: Optional[float] = None,
        risk_level: Optional[str] = None,
        contract_type: Optional[str] = None,
    ) -> List[ApprovalRequest]:
        """Initiate approval process for a contract.

        Args:
            contract_id: Contract ID
            chain_id: Optional specific chain ID
            contract_value: Contract value for chain selection
            risk_level: Risk level for chain selection
            contract_type: Contract type for chain selection

        Returns:
            List of approval requests created
        """
        logger.info("Initiating approval process", contract_id=contract_id)

        # Get approval chain
        if chain_id:
            chain = self.chains.get(chain_id)
        else:
            chain = self.get_applicable_chain(contract_value, risk_level, contract_type)

        if not chain:
            logger.warning("No applicable approval chain found", contract_id=contract_id)
            return []

        # Create requests for first level
        requests = []
        first_level = chain.levels[0] if chain.levels else None

        if first_level:
            approver_ids = first_level.get("approvers", [])
            timeout_hours = first_level.get("timeout_hours", 24)
            due_date = datetime.utcnow() + timedelta(hours=timeout_hours)

            for approver_id in approver_ids:
                request = ApprovalRequest(
                    contract_id=contract_id,
                    approver_id=approver_id,
                    approver_name=f"Approver {approver_id}",  # Would fetch from user service
                    approver_email=f"approver{approver_id}@example.com",
                    level=first_level["level"],
                    due_date=due_date,
                )
                requests.append(request)

        if contract_id not in self.requests:
            self.requests[contract_id] = []
        self.requests[contract_id].extend(requests)

        logger.info(
            "Approval requests created",
            contract_id=contract_id,
            count=len(requests),
        )

        return requests

    def approve(
        self,
        request_id: UUID,
        approver_id: UUID,
        comments: Optional[str] = None,
    ) -> ApprovalRequest:
        """Approve a contract.

        Args:
            request_id: Approval request ID
            approver_id: Approver's ID
            comments: Optional comments

        Returns:
            Updated approval request
        """
        logger.info("Approving contract", request_id=request_id, approver_id=approver_id)

        request = self._get_request(request_id)
        if request.approver_id != approver_id:
            raise ValueError("User not authorized to approve this request")

        request.status = ApprovalStatus.APPROVED
        request.responded_at = datetime.utcnow()
        request.comments = comments

        # Check if we need to advance to next level
        self._check_level_completion(request.contract_id, request.level)

        return request

    def reject(
        self,
        request_id: UUID,
        approver_id: UUID,
        comments: Optional[str] = None,
    ) -> ApprovalRequest:
        """Reject a contract.

        Args:
            request_id: Approval request ID
            approver_id: Approver's ID
            comments: Optional comments

        Returns:
            Updated approval request
        """
        logger.info("Rejecting contract", request_id=request_id, approver_id=approver_id)

        request = self._get_request(request_id)
        if request.approver_id != approver_id:
            raise ValueError("User not authorized to reject this request")

        request.status = ApprovalStatus.REJECTED
        request.responded_at = datetime.utcnow()
        request.comments = comments

        # Mark all other pending requests as expired
        for req in self.requests.get(request.contract_id, []):
            if req.status == ApprovalStatus.PENDING:
                req.status = ApprovalStatus.EXPIRED

        return request

    def escalate(
        self,
        request_id: UUID,
        escalate_to: UUID,
    ) -> ApprovalRequest:
        """Escalate an approval request.

        Args:
            request_id: Approval request ID
            escalate_to: User to escalate to

        Returns:
            Updated approval request
        """
        logger.info("Escalating approval", request_id=request_id, escalate_to=escalate_to)

        request = self._get_request(request_id)
        request.status = ApprovalStatus.ESCALATED
        request.escalated_to = escalate_to
        request.escalated_at = datetime.utcnow()

        # Create new request for escalated approver
        new_request = ApprovalRequest(
            contract_id=request.contract_id,
            approver_id=escalate_to,
            approver_name=f"Escalated Approver {escalate_to}",
            approver_email=f"escalated{escalate_to}@example.com",
            level=request.level,
            metadata={"escalated_from": str(request_id)},
        )

        self.requests[request.contract_id].append(new_request)

        return request

    def check_timeouts(self) -> List[ApprovalRequest]:
        """Check for timed out approval requests and auto-escalate.

        Returns:
            List of escalated requests
        """
        logger.info("Checking approval timeouts")

        escalated = []
        now = datetime.utcnow()

        for contract_requests in self.requests.values():
            for request in contract_requests:
                if request.status != ApprovalStatus.PENDING:
                    continue

                if request.due_date and request.due_date < now:
                    # Auto-escalate if enabled
                    # In production, would look up chain config
                    logger.warning(
                        "Approval request timed out",
                        request_id=request.id,
                        contract_id=request.contract_id,
                    )
                    escalated.append(request)

        return escalated

    def get_pending_approvals(
        self,
        approver_id: Optional[UUID] = None,
        contract_id: Optional[UUID] = None,
    ) -> List[ApprovalRequest]:
        """Get pending approval requests.

        Args:
            approver_id: Optional approver ID filter
            contract_id: Optional contract ID filter

        Returns:
            List of pending approval requests
        """
        all_requests = []

        if contract_id:
            all_requests = self.requests.get(contract_id, [])
        else:
            for requests in self.requests.values():
                all_requests.extend(requests)

        pending = [r for r in all_requests if r.status == ApprovalStatus.PENDING]

        if approver_id:
            pending = [r for r in pending if r.approver_id == approver_id]

        return sorted(pending, key=lambda r: r.requested_at)

    def is_approved(self, contract_id: UUID) -> bool:
        """Check if contract is fully approved.

        Args:
            contract_id: Contract ID

        Returns:
            True if fully approved
        """
        requests = self.requests.get(contract_id, [])
        if not requests:
            return False

        # Check if any rejected
        if any(r.status == ApprovalStatus.REJECTED for r in requests):
            return False

        # Check if all required approvals obtained
        pending = [r for r in requests if r.status == ApprovalStatus.PENDING]
        return len(pending) == 0

    def _get_request(self, request_id: UUID) -> ApprovalRequest:
        """Get approval request by ID."""
        for requests in self.requests.values():
            for request in requests:
                if request.id == request_id:
                    return request
        raise ValueError(f"Approval request {request_id} not found")

    def _check_level_completion(self, contract_id: UUID, level: int) -> None:
        """Check if approval level is complete and advance if needed."""
        requests = self.requests.get(contract_id, [])
        level_requests = [r for r in requests if r.level == level]

        # Check if all approved
        all_approved = all(
            r.status == ApprovalStatus.APPROVED for r in level_requests
        )

        if all_approved:
            logger.info(
                "Approval level completed",
                contract_id=contract_id,
                level=level,
            )
            # Would advance to next level in production
