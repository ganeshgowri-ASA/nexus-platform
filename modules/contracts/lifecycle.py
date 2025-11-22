"""Contract lifecycle management.

This module handles all contract lifecycle operations including drafting,
negotiation, approval, execution, tracking, renewal, and termination.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from shared.cache import async_cache_delete, async_cache_get, async_cache_set
from shared.exceptions import (
    ContractNotFoundError,
    ContractPermissionError,
    ContractStateError,
    ContractValidationError,
)
from .contract_types import Contract, ContractStatus, Party, Clause
from .models import ContractModel, AuditLogModel

logger = structlog.get_logger(__name__)


class ContractLifecycleManager:
    """Manages contract lifecycle operations."""

    VALID_TRANSITIONS = {
        ContractStatus.DRAFT: [ContractStatus.IN_NEGOTIATION, ContractStatus.PENDING_APPROVAL],
        ContractStatus.IN_NEGOTIATION: [ContractStatus.DRAFT, ContractStatus.PENDING_APPROVAL],
        ContractStatus.PENDING_APPROVAL: [ContractStatus.APPROVED, ContractStatus.IN_NEGOTIATION, ContractStatus.DRAFT],
        ContractStatus.APPROVED: [ContractStatus.IN_EXECUTION],
        ContractStatus.IN_EXECUTION: [ContractStatus.EXECUTED],
        ContractStatus.EXECUTED: [ContractStatus.ACTIVE],
        ContractStatus.ACTIVE: [ContractStatus.EXPIRING, ContractStatus.TERMINATED, ContractStatus.RENEWED],
        ContractStatus.EXPIRING: [ContractStatus.EXPIRED, ContractStatus.RENEWED, ContractStatus.ACTIVE],
        ContractStatus.EXPIRED: [ContractStatus.RENEWED, ContractStatus.ARCHIVED],
        ContractStatus.TERMINATED: [ContractStatus.ARCHIVED],
        ContractStatus.RENEWED: [ContractStatus.ACTIVE],
        ContractStatus.ARCHIVED: [],
    }

    def __init__(self, db: Session):
        """Initialize lifecycle manager.

        Args:
            db: Database session
        """
        self.db = db

    def create_draft(
        self,
        title: str,
        contract_type: str,
        parties: List[Dict],
        user_id: UUID,
        **kwargs
    ) -> Contract:
        """Create a new contract draft.

        Args:
            title: Contract title
            contract_type: Type of contract
            parties: List of party dictionaries
            user_id: User creating the contract
            **kwargs: Additional contract fields

        Returns:
            Created contract

        Raises:
            ContractValidationError: If validation fails
        """
        logger.info("Creating contract draft", title=title, contract_type=contract_type)

        try:
            # Create contract instance
            contract_data = {
                "title": title,
                "contract_type": contract_type,
                "status": ContractStatus.DRAFT,
                "created_by": user_id,
                **kwargs
            }

            contract = Contract(**contract_data)

            # Add parties
            for party_data in parties:
                party = Party(**party_data)
                contract.parties.append(party)

            # Save to database
            db_contract = self._to_db_model(contract)
            self.db.add(db_contract)
            self.db.commit()
            self.db.refresh(db_contract)

            # Create audit log
            self._create_audit_log(
                contract_id=db_contract.id,
                user_id=user_id,
                action="create_draft",
                entity_type="contract",
                entity_id=db_contract.id,
            )

            logger.info("Contract draft created", contract_id=db_contract.id)
            return self._from_db_model(db_contract)

        except Exception as e:
            logger.error("Failed to create contract draft", error=str(e))
            self.db.rollback()
            raise ContractValidationError(f"Failed to create contract: {str(e)}")

    def start_negotiation(self, contract_id: UUID, user_id: UUID) -> Contract:
        """Move contract to negotiation phase.

        Args:
            contract_id: Contract ID
            user_id: User starting negotiation

        Returns:
            Updated contract

        Raises:
            ContractNotFoundError: If contract not found
            ContractStateError: If invalid state transition
        """
        logger.info("Starting contract negotiation", contract_id=contract_id)

        contract = self._get_contract(contract_id)
        self._validate_transition(contract.status, ContractStatus.IN_NEGOTIATION)

        contract.status = ContractStatus.IN_NEGOTIATION
        contract.updated_by = user_id
        contract.updated_at = datetime.utcnow()

        self._update_contract(contract, user_id, "start_negotiation")
        logger.info("Contract negotiation started", contract_id=contract_id)

        return contract

    def submit_for_approval(self, contract_id: UUID, user_id: UUID) -> Contract:
        """Submit contract for approval.

        Args:
            contract_id: Contract ID
            user_id: User submitting for approval

        Returns:
            Updated contract

        Raises:
            ContractNotFoundError: If contract not found
            ContractStateError: If invalid state transition
        """
        logger.info("Submitting contract for approval", contract_id=contract_id)

        contract = self._get_contract(contract_id)
        self._validate_transition(contract.status, ContractStatus.PENDING_APPROVAL)

        contract.status = ContractStatus.PENDING_APPROVAL
        contract.updated_by = user_id
        contract.updated_at = datetime.utcnow()

        self._update_contract(contract, user_id, "submit_for_approval")
        logger.info("Contract submitted for approval", contract_id=contract_id)

        return contract

    def approve(self, contract_id: UUID, user_id: UUID) -> Contract:
        """Approve a contract.

        Args:
            contract_id: Contract ID
            user_id: User approving the contract

        Returns:
            Approved contract

        Raises:
            ContractNotFoundError: If contract not found
            ContractStateError: If invalid state transition
        """
        logger.info("Approving contract", contract_id=contract_id)

        contract = self._get_contract(contract_id)
        self._validate_transition(contract.status, ContractStatus.APPROVED)

        contract.status = ContractStatus.APPROVED
        contract.updated_by = user_id
        contract.updated_at = datetime.utcnow()

        self._update_contract(contract, user_id, "approve")
        logger.info("Contract approved", contract_id=contract_id)

        return contract

    def execute(self, contract_id: UUID, user_id: UUID) -> Contract:
        """Execute a contract.

        Args:
            contract_id: Contract ID
            user_id: User executing the contract

        Returns:
            Executed contract

        Raises:
            ContractNotFoundError: If contract not found
            ContractStateError: If not fully signed or invalid state
        """
        logger.info("Executing contract", contract_id=contract_id)

        contract = self._get_contract(contract_id)

        # Check if fully signed
        if not contract.is_fully_signed():
            raise ContractStateError("Contract must be fully signed before execution")

        self._validate_transition(contract.status, ContractStatus.IN_EXECUTION)

        contract.status = ContractStatus.EXECUTED
        contract.execution_date = datetime.utcnow()
        contract.updated_by = user_id
        contract.updated_at = datetime.utcnow()

        self._update_contract(contract, user_id, "execute")
        logger.info("Contract executed", contract_id=contract_id)

        return contract

    def activate(self, contract_id: UUID, user_id: UUID) -> Contract:
        """Activate an executed contract.

        Args:
            contract_id: Contract ID
            user_id: User activating the contract

        Returns:
            Activated contract
        """
        logger.info("Activating contract", contract_id=contract_id)

        contract = self._get_contract(contract_id)
        self._validate_transition(contract.status, ContractStatus.ACTIVE)

        contract.status = ContractStatus.ACTIVE
        if not contract.effective_date:
            contract.effective_date = datetime.utcnow()
        contract.updated_by = user_id
        contract.updated_at = datetime.utcnow()

        self._update_contract(contract, user_id, "activate")
        logger.info("Contract activated", contract_id=contract_id)

        return contract

    def renew(
        self,
        contract_id: UUID,
        user_id: UUID,
        new_end_date: Optional[datetime] = None,
    ) -> Contract:
        """Renew a contract.

        Args:
            contract_id: Contract ID
            user_id: User renewing the contract
            new_end_date: New end date (optional)

        Returns:
            Renewed contract
        """
        logger.info("Renewing contract", contract_id=contract_id)

        contract = self._get_contract(contract_id)
        self._validate_transition(contract.status, ContractStatus.RENEWED)

        contract.status = ContractStatus.RENEWED
        contract.renewal_count += 1

        if new_end_date:
            contract.end_date = new_end_date
        elif contract.end_date:
            # Extend by original duration
            duration = contract.end_date - contract.start_date
            contract.end_date = contract.end_date + duration

        contract.updated_by = user_id
        contract.updated_at = datetime.utcnow()

        self._update_contract(contract, user_id, "renew")
        logger.info("Contract renewed", contract_id=contract_id, renewal_count=contract.renewal_count)

        return contract

    def terminate(
        self,
        contract_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> Contract:
        """Terminate a contract.

        Args:
            contract_id: Contract ID
            user_id: User terminating the contract
            reason: Termination reason

        Returns:
            Terminated contract
        """
        logger.info("Terminating contract", contract_id=contract_id)

        contract = self._get_contract(contract_id)
        self._validate_transition(contract.status, ContractStatus.TERMINATED)

        contract.status = ContractStatus.TERMINATED
        contract.updated_by = user_id
        contract.updated_at = datetime.utcnow()

        if reason:
            contract.metadata["termination_reason"] = reason
            contract.metadata["termination_date"] = datetime.utcnow().isoformat()

        self._update_contract(contract, user_id, "terminate")
        logger.info("Contract terminated", contract_id=contract_id)

        return contract

    def archive(self, contract_id: UUID, user_id: UUID) -> Contract:
        """Archive a contract.

        Args:
            contract_id: Contract ID
            user_id: User archiving the contract

        Returns:
            Archived contract
        """
        logger.info("Archiving contract", contract_id=contract_id)

        contract = self._get_contract(contract_id)
        self._validate_transition(contract.status, ContractStatus.ARCHIVED)

        contract.status = ContractStatus.ARCHIVED
        contract.updated_by = user_id
        contract.updated_at = datetime.utcnow()

        self._update_contract(contract, user_id, "archive")
        logger.info("Contract archived", contract_id=contract_id)

        return contract

    def check_expiration(self, days_threshold: int = 30) -> List[Contract]:
        """Check for expiring contracts.

        Args:
            days_threshold: Days before expiration to flag

        Returns:
            List of expiring contracts
        """
        logger.info("Checking for expiring contracts", days_threshold=days_threshold)

        threshold_date = datetime.utcnow() + timedelta(days=days_threshold)

        stmt = select(ContractModel).where(
            ContractModel.status == ContractStatus.ACTIVE,
            ContractModel.end_date.isnot(None),
            ContractModel.end_date <= threshold_date,
        )

        result = self.db.execute(stmt)
        db_contracts = result.scalars().all()

        # Update status to EXPIRING
        expiring_contracts = []
        for db_contract in db_contracts:
            if db_contract.status != ContractStatus.EXPIRING:
                db_contract.status = ContractStatus.EXPIRING
                db_contract.updated_at = datetime.utcnow()
                expiring_contracts.append(self._from_db_model(db_contract))

        if expiring_contracts:
            self.db.commit()
            logger.info("Found expiring contracts", count=len(expiring_contracts))

        return expiring_contracts

    def _get_contract(self, contract_id: UUID) -> Contract:
        """Get contract by ID."""
        stmt = select(ContractModel).where(ContractModel.id == contract_id)
        result = self.db.execute(stmt)
        db_contract = result.scalar_one_or_none()

        if not db_contract:
            raise ContractNotFoundError(f"Contract {contract_id} not found")

        return self._from_db_model(db_contract)

    def _validate_transition(self, current: ContractStatus, target: ContractStatus) -> None:
        """Validate status transition."""
        valid_targets = self.VALID_TRANSITIONS.get(current, [])
        if target not in valid_targets:
            raise ContractStateError(
                f"Invalid transition from {current} to {target}",
                details={"current": current, "target": target, "valid": valid_targets}
            )

    def _update_contract(self, contract: Contract, user_id: UUID, action: str) -> None:
        """Update contract in database."""
        stmt = select(ContractModel).where(ContractModel.id == contract.id)
        result = self.db.execute(stmt)
        db_contract = result.scalar_one()

        # Update fields
        for key, value in contract.dict(exclude_unset=True).items():
            if hasattr(db_contract, key):
                setattr(db_contract, key, value)

        self.db.commit()

        # Create audit log
        self._create_audit_log(
            contract_id=contract.id,
            user_id=user_id,
            action=action,
            entity_type="contract",
            entity_id=contract.id,
        )

        # Invalidate cache
        async_cache_delete(f"contract:{contract.id}")

    def _create_audit_log(
        self,
        contract_id: UUID,
        user_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
    ) -> None:
        """Create audit log entry."""
        audit_log = AuditLogModel(
            contract_id=contract_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(audit_log)
        self.db.commit()

    def _to_db_model(self, contract: Contract) -> ContractModel:
        """Convert Contract to database model."""
        data = contract.dict(exclude={"parties", "clauses", "obligations", "milestones", "amendments", "signatures"})
        return ContractModel(**data)

    def _from_db_model(self, db_contract: ContractModel) -> Contract:
        """Convert database model to Contract."""
        data = {
            "id": db_contract.id,
            "title": db_contract.title,
            "description": db_contract.description,
            "contract_type": db_contract.contract_type,
            "status": db_contract.status,
            # Add other fields...
        }
        return Contract(**data)
