"""
Document Retention and Compliance Module

Provides comprehensive retention policy management, automatic archival,
legal hold support, and compliance reporting.

Features:
- Retention policy management
- Automatic archival and disposal
- Legal hold support
- Disposition scheduling
- Compliance reporting
- Audit trail
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class RetentionPeriod(Enum):
    """Standard retention periods."""
    DAYS_30 = 30
    DAYS_90 = 90
    DAYS_180 = 180
    YEAR_1 = 365
    YEARS_3 = 1095
    YEARS_5 = 1825
    YEARS_7 = 2555
    YEARS_10 = 3650
    PERMANENT = -1  # Never expire


class DispositionAction(Enum):
    """Actions to take when retention period expires."""
    DELETE = "delete"
    ARCHIVE = "archive"
    REVIEW = "review"
    TRANSFER = "transfer"


class RetentionStatus(Enum):
    """Document retention status."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    LEGAL_HOLD = "legal_hold"
    PENDING_DISPOSAL = "pending_disposal"
    DISPOSED = "disposed"
    PERMANENT = "permanent"


class ComplianceLevel(Enum):
    """Compliance requirement levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetentionPolicyError(Exception):
    """Base exception for retention policy errors."""
    pass


class LegalHoldError(Exception):
    """Exception for legal hold errors."""
    pass


class RetentionPolicy:
    """
    Represents a document retention policy.
    """

    def __init__(
        self,
        policy_id: str,
        name: str,
        retention_period: RetentionPeriod,
        disposition_action: DispositionAction,
        description: Optional[str] = None,
        document_types: Optional[List[str]] = None,
        compliance_level: ComplianceLevel = ComplianceLevel.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize retention policy.

        Args:
            policy_id: Unique policy identifier
            name: Policy name
            retention_period: How long to retain documents
            disposition_action: Action to take after retention period
            description: Policy description
            document_types: Document types this policy applies to
            compliance_level: Compliance requirement level
            metadata: Additional policy metadata
        """
        self.policy_id = policy_id
        self.name = name
        self.retention_period = retention_period
        self.disposition_action = disposition_action
        self.description = description
        self.document_types = document_types or []
        self.compliance_level = compliance_level
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.active = True

    def calculate_expiration_date(self, start_date: datetime) -> Optional[datetime]:
        """
        Calculate when a document expires under this policy.

        Args:
            start_date: Document creation or effective date

        Returns:
            Expiration datetime, or None for permanent retention
        """
        if self.retention_period == RetentionPeriod.PERMANENT:
            return None

        days = self.retention_period.value
        return start_date + timedelta(days=days)

    def is_expired(self, start_date: datetime) -> bool:
        """
        Check if retention period has expired.

        Args:
            start_date: Document start date

        Returns:
            True if expired
        """
        if self.retention_period == RetentionPeriod.PERMANENT:
            return False

        expiration = self.calculate_expiration_date(start_date)
        return datetime.now() >= expiration if expiration else False

    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary."""
        return {
            'policy_id': self.policy_id,
            'name': self.name,
            'retention_period': self.retention_period.name,
            'disposition_action': self.disposition_action.value,
            'description': self.description,
            'document_types': self.document_types,
            'compliance_level': self.compliance_level.value,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'active': self.active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RetentionPolicy':
        """Create policy from dictionary."""
        policy = cls(
            policy_id=data['policy_id'],
            name=data['name'],
            retention_period=RetentionPeriod[data['retention_period']],
            disposition_action=DispositionAction(data['disposition_action']),
            description=data.get('description'),
            document_types=data.get('document_types', []),
            compliance_level=ComplianceLevel(data.get('compliance_level', 'medium')),
            metadata=data.get('metadata', {})
        )

        policy.created_at = datetime.fromisoformat(data['created_at'])
        policy.updated_at = datetime.fromisoformat(data['updated_at'])
        policy.active = data.get('active', True)

        return policy


class LegalHold:
    """
    Represents a legal hold on documents.
    """

    def __init__(
        self,
        hold_id: str,
        name: str,
        reason: str,
        custodian: str,
        document_ids: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize legal hold.

        Args:
            hold_id: Unique hold identifier
            name: Hold name/case name
            reason: Reason for the hold
            custodian: Person responsible for the hold
            document_ids: Set of document IDs under hold
            metadata: Additional hold metadata
        """
        self.hold_id = hold_id
        self.name = name
        self.reason = reason
        self.custodian = custodian
        self.document_ids = document_ids or set()
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.released_at: Optional[datetime] = None
        self.active = True

    def add_document(self, document_id: str) -> None:
        """Add a document to the legal hold."""
        self.document_ids.add(document_id)
        logger.info(f"Document {document_id} added to legal hold {self.name}")

    def remove_document(self, document_id: str) -> None:
        """Remove a document from the legal hold."""
        self.document_ids.discard(document_id)
        logger.info(f"Document {document_id} removed from legal hold {self.name}")

    def release(self) -> None:
        """Release the legal hold."""
        self.active = False
        self.released_at = datetime.now()
        logger.info(f"Legal hold released: {self.name}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert hold to dictionary."""
        return {
            'hold_id': self.hold_id,
            'name': self.name,
            'reason': self.reason,
            'custodian': self.custodian,
            'document_ids': list(self.document_ids),
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'released_at': self.released_at.isoformat() if self.released_at else None,
            'active': self.active
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegalHold':
        """Create hold from dictionary."""
        hold = cls(
            hold_id=data['hold_id'],
            name=data['name'],
            reason=data['reason'],
            custodian=data['custodian'],
            document_ids=set(data.get('document_ids', [])),
            metadata=data.get('metadata', {})
        )

        hold.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('released_at'):
            hold.released_at = datetime.fromisoformat(data['released_at'])
        hold.active = data.get('active', True)

        return hold


class DocumentRetentionRecord:
    """
    Tracks retention information for a specific document.
    """

    def __init__(
        self,
        document_id: str,
        policy_id: str,
        effective_date: datetime,
        status: RetentionStatus = RetentionStatus.ACTIVE
    ):
        """
        Initialize retention record.

        Args:
            document_id: Document identifier
            policy_id: Applied retention policy ID
            effective_date: Date retention period starts from
            status: Current retention status
        """
        self.document_id = document_id
        self.policy_id = policy_id
        self.effective_date = effective_date
        self.status = status
        self.legal_holds: Set[str] = set()
        self.disposition_date: Optional[datetime] = None
        self.archived_at: Optional[datetime] = None
        self.disposed_at: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}

    def add_legal_hold(self, hold_id: str) -> None:
        """Add a legal hold to this document."""
        self.legal_holds.add(hold_id)
        self.status = RetentionStatus.LEGAL_HOLD
        logger.info(f"Legal hold {hold_id} applied to document {self.document_id}")

    def remove_legal_hold(self, hold_id: str) -> None:
        """Remove a legal hold from this document."""
        self.legal_holds.discard(hold_id)

        if not self.legal_holds:
            # Revert to appropriate status
            if self.disposed_at:
                self.status = RetentionStatus.DISPOSED
            elif self.archived_at:
                self.status = RetentionStatus.ARCHIVED
            else:
                self.status = RetentionStatus.ACTIVE

        logger.info(f"Legal hold {hold_id} removed from document {self.document_id}")

    def has_legal_hold(self) -> bool:
        """Check if document has any active legal holds."""
        return len(self.legal_holds) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary."""
        return {
            'document_id': self.document_id,
            'policy_id': self.policy_id,
            'effective_date': self.effective_date.isoformat(),
            'status': self.status.value,
            'legal_holds': list(self.legal_holds),
            'disposition_date': self.disposition_date.isoformat() if self.disposition_date else None,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'disposed_at': self.disposed_at.isoformat() if self.disposed_at else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentRetentionRecord':
        """Create record from dictionary."""
        record = cls(
            document_id=data['document_id'],
            policy_id=data['policy_id'],
            effective_date=datetime.fromisoformat(data['effective_date']),
            status=RetentionStatus(data['status'])
        )

        record.legal_holds = set(data.get('legal_holds', []))

        if data.get('disposition_date'):
            record.disposition_date = datetime.fromisoformat(data['disposition_date'])
        if data.get('archived_at'):
            record.archived_at = datetime.fromisoformat(data['archived_at'])
        if data.get('disposed_at'):
            record.disposed_at = datetime.fromisoformat(data['disposed_at'])

        record.metadata = data.get('metadata', {})

        return record


class RetentionManager:
    """
    Manages document retention policies, legal holds, and compliance.
    """

    def __init__(self, storage_path: Union[str, Path]):
        """
        Initialize retention manager.

        Args:
            storage_path: Path to retention data storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.policies_file = self.storage_path / "policies.json"
        self.holds_file = self.storage_path / "legal_holds.json"
        self.records_file = self.storage_path / "retention_records.json"
        self.audit_log_file = self.storage_path / "audit_log.jsonl"

        self.policies: Dict[str, RetentionPolicy] = {}
        self.legal_holds: Dict[str, LegalHold] = {}
        self.retention_records: Dict[str, DocumentRetentionRecord] = {}

        self._load_data()

        logger.info(
            f"RetentionManager initialized: {len(self.policies)} policies, "
            f"{len(self.legal_holds)} holds, {len(self.retention_records)} records"
        )

    def create_policy(
        self,
        name: str,
        retention_period: RetentionPeriod,
        disposition_action: DispositionAction,
        **kwargs
    ) -> RetentionPolicy:
        """
        Create a retention policy.

        Args:
            name: Policy name
            retention_period: Retention period
            disposition_action: Disposition action
            **kwargs: Additional policy parameters

        Returns:
            Created RetentionPolicy
        """
        policy_id = str(uuid.uuid4())

        policy = RetentionPolicy(
            policy_id=policy_id,
            name=name,
            retention_period=retention_period,
            disposition_action=disposition_action,
            **kwargs
        )

        self.policies[policy_id] = policy
        self._save_policies()

        self._audit_log('policy_created', {
            'policy_id': policy_id,
            'name': name,
            'retention_period': retention_period.name
        })

        logger.info(f"Retention policy created: {name}")

        return policy

    def update_policy(
        self,
        policy_id: str,
        **updates
    ) -> RetentionPolicy:
        """
        Update a retention policy.

        Args:
            policy_id: Policy identifier
            **updates: Fields to update

        Returns:
            Updated RetentionPolicy

        Raises:
            RetentionPolicyError: If policy not found
        """
        if policy_id not in self.policies:
            raise RetentionPolicyError(f"Policy not found: {policy_id}")

        policy = self.policies[policy_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)

        policy.updated_at = datetime.now()
        self._save_policies()

        self._audit_log('policy_updated', {
            'policy_id': policy_id,
            'updates': updates
        })

        logger.info(f"Policy updated: {policy.name}")

        return policy

    def get_policy(self, policy_id: str) -> Optional[RetentionPolicy]:
        """Get a retention policy by ID."""
        return self.policies.get(policy_id)

    def list_policies(self, active_only: bool = True) -> List[RetentionPolicy]:
        """
        List retention policies.

        Args:
            active_only: Only return active policies

        Returns:
            List of policies
        """
        policies = list(self.policies.values())

        if active_only:
            policies = [p for p in policies if p.active]

        return policies

    def delete_policy(self, policy_id: str) -> bool:
        """
        Delete a retention policy.

        Args:
            policy_id: Policy identifier

        Returns:
            True if deleted, False if not found
        """
        if policy_id not in self.policies:
            return False

        # Check if policy is in use
        in_use = any(
            record.policy_id == policy_id
            for record in self.retention_records.values()
        )

        if in_use:
            logger.warning(f"Policy {policy_id} is in use, marking as inactive")
            self.policies[policy_id].active = False
        else:
            del self.policies[policy_id]

        self._save_policies()

        self._audit_log('policy_deleted', {'policy_id': policy_id})

        return True

    def create_legal_hold(
        self,
        name: str,
        reason: str,
        custodian: str,
        document_ids: Optional[List[str]] = None,
        **kwargs
    ) -> LegalHold:
        """
        Create a legal hold.

        Args:
            name: Hold name
            reason: Reason for hold
            custodian: Responsible person
            document_ids: Initial document IDs to hold
            **kwargs: Additional hold parameters

        Returns:
            Created LegalHold
        """
        hold_id = str(uuid.uuid4())

        hold = LegalHold(
            hold_id=hold_id,
            name=name,
            reason=reason,
            custodian=custodian,
            document_ids=set(document_ids or []),
            **kwargs
        )

        self.legal_holds[hold_id] = hold

        # Apply hold to documents
        for doc_id in hold.document_ids:
            if doc_id in self.retention_records:
                self.retention_records[doc_id].add_legal_hold(hold_id)

        self._save_holds()
        self._save_records()

        self._audit_log('legal_hold_created', {
            'hold_id': hold_id,
            'name': name,
            'document_count': len(hold.document_ids)
        })

        logger.info(f"Legal hold created: {name}")

        return hold

    def release_legal_hold(self, hold_id: str) -> bool:
        """
        Release a legal hold.

        Args:
            hold_id: Hold identifier

        Returns:
            True if released, False if not found
        """
        if hold_id not in self.legal_holds:
            return False

        hold = self.legal_holds[hold_id]
        hold.release()

        # Remove hold from documents
        for doc_id in hold.document_ids:
            if doc_id in self.retention_records:
                self.retention_records[doc_id].remove_legal_hold(hold_id)

        self._save_holds()
        self._save_records()

        self._audit_log('legal_hold_released', {
            'hold_id': hold_id,
            'name': hold.name
        })

        logger.info(f"Legal hold released: {hold.name}")

        return True

    def add_document_to_hold(self, hold_id: str, document_id: str) -> bool:
        """
        Add a document to a legal hold.

        Args:
            hold_id: Hold identifier
            document_id: Document identifier

        Returns:
            True if added
        """
        if hold_id not in self.legal_holds:
            raise LegalHoldError(f"Legal hold not found: {hold_id}")

        hold = self.legal_holds[hold_id]
        hold.add_document(document_id)

        if document_id in self.retention_records:
            self.retention_records[document_id].add_legal_hold(hold_id)

        self._save_holds()
        self._save_records()

        return True

    def apply_policy_to_document(
        self,
        document_id: str,
        policy_id: str,
        effective_date: Optional[datetime] = None
    ) -> DocumentRetentionRecord:
        """
        Apply a retention policy to a document.

        Args:
            document_id: Document identifier
            policy_id: Policy to apply
            effective_date: Effective date (defaults to now)

        Returns:
            Created DocumentRetentionRecord

        Raises:
            RetentionPolicyError: If policy not found
        """
        if policy_id not in self.policies:
            raise RetentionPolicyError(f"Policy not found: {policy_id}")

        effective_date = effective_date or datetime.now()

        record = DocumentRetentionRecord(
            document_id=document_id,
            policy_id=policy_id,
            effective_date=effective_date
        )

        # Calculate disposition date
        policy = self.policies[policy_id]
        record.disposition_date = policy.calculate_expiration_date(effective_date)

        # Set status based on policy
        if policy.retention_period == RetentionPeriod.PERMANENT:
            record.status = RetentionStatus.PERMANENT

        self.retention_records[document_id] = record
        self._save_records()

        self._audit_log('policy_applied', {
            'document_id': document_id,
            'policy_id': policy_id,
            'disposition_date': record.disposition_date.isoformat() if record.disposition_date else None
        })

        logger.info(f"Policy {policy.name} applied to document {document_id}")

        return record

    def get_retention_record(self, document_id: str) -> Optional[DocumentRetentionRecord]:
        """Get retention record for a document."""
        return self.retention_records.get(document_id)

    def get_documents_for_disposition(
        self,
        before_date: Optional[datetime] = None
    ) -> List[DocumentRetentionRecord]:
        """
        Get documents ready for disposition.

        Args:
            before_date: Only include documents with disposition date before this

        Returns:
            List of retention records
        """
        before_date = before_date or datetime.now()
        ready_for_disposition = []

        for record in self.retention_records.values():
            # Skip if on legal hold
            if record.has_legal_hold():
                continue

            # Skip if already disposed
            if record.status == RetentionStatus.DISPOSED:
                continue

            # Skip permanent records
            if record.status == RetentionStatus.PERMANENT:
                continue

            # Check if disposition date has passed
            if record.disposition_date and record.disposition_date <= before_date:
                ready_for_disposition.append(record)

        logger.info(f"Found {len(ready_for_disposition)} documents ready for disposition")

        return ready_for_disposition

    def execute_disposition(
        self,
        document_id: str,
        callback: Optional[Callable[[str, DispositionAction], bool]] = None
    ) -> bool:
        """
        Execute disposition action for a document.

        Args:
            document_id: Document identifier
            callback: Optional callback function to execute the actual disposition

        Returns:
            True if disposition executed
        """
        record = self.get_retention_record(document_id)

        if not record:
            logger.warning(f"No retention record for document {document_id}")
            return False

        if record.has_legal_hold():
            logger.warning(f"Cannot dispose document {document_id}: under legal hold")
            return False

        policy = self.get_policy(record.policy_id)

        if not policy:
            logger.error(f"Policy not found for document {document_id}")
            return False

        logger.info(
            f"Executing disposition for {document_id}: {policy.disposition_action.value}"
        )

        # Execute callback if provided
        if callback:
            success = callback(document_id, policy.disposition_action)
            if not success:
                logger.error(f"Disposition callback failed for {document_id}")
                return False

        # Update record based on action
        if policy.disposition_action == DispositionAction.ARCHIVE:
            record.status = RetentionStatus.ARCHIVED
            record.archived_at = datetime.now()
        elif policy.disposition_action == DispositionAction.DELETE:
            record.status = RetentionStatus.DISPOSED
            record.disposed_at = datetime.now()
        elif policy.disposition_action == DispositionAction.REVIEW:
            record.status = RetentionStatus.PENDING_DISPOSAL

        self._save_records()

        self._audit_log('disposition_executed', {
            'document_id': document_id,
            'action': policy.disposition_action.value,
            'policy_id': policy.policy_id
        })

        return True

    def generate_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Report data
        """
        end_date = end_date or datetime.now()
        start_date = start_date or (end_date - timedelta(days=90))

        report = {
            'generated_at': datetime.now().isoformat(),
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'summary': {
                'total_policies': len(self.policies),
                'active_policies': len([p for p in self.policies.values() if p.active]),
                'total_documents': len(self.retention_records),
                'documents_on_hold': len([r for r in self.retention_records.values() if r.has_legal_hold()]),
                'active_legal_holds': len([h for h in self.legal_holds.values() if h.active]),
                'pending_disposition': len(self.get_documents_for_disposition(end_date))
            },
            'policies': {},
            'compliance_issues': []
        }

        # Policy breakdown
        for policy in self.policies.values():
            if not policy.active:
                continue

            policy_docs = [
                r for r in self.retention_records.values()
                if r.policy_id == policy.policy_id
            ]

            report['policies'][policy.name] = {
                'policy_id': policy.policy_id,
                'document_count': len(policy_docs),
                'retention_period': policy.retention_period.name,
                'compliance_level': policy.compliance_level.value
            }

        # Check for compliance issues
        for record in self.retention_records.values():
            # Check if policy exists
            if record.policy_id not in self.policies:
                report['compliance_issues'].append({
                    'type': 'missing_policy',
                    'document_id': record.document_id,
                    'policy_id': record.policy_id
                })

            # Check for overdue dispositions
            if record.disposition_date and record.disposition_date < start_date:
                if not record.has_legal_hold() and record.status == RetentionStatus.ACTIVE:
                    report['compliance_issues'].append({
                        'type': 'overdue_disposition',
                        'document_id': record.document_id,
                        'disposition_date': record.disposition_date.isoformat()
                    })

        logger.info(f"Compliance report generated: {len(report['compliance_issues'])} issues")

        return report

    def _audit_log(self, action: str, details: Dict[str, Any]) -> None:
        """Write entry to audit log."""
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'details': details
            }

            with open(self.audit_log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def _load_data(self) -> None:
        """Load all retention data from storage."""
        # Load policies
        if self.policies_file.exists():
            try:
                with open(self.policies_file, 'r') as f:
                    data = json.load(f)
                    for policy_data in data:
                        policy = RetentionPolicy.from_dict(policy_data)
                        self.policies[policy.policy_id] = policy
            except Exception as e:
                logger.error(f"Failed to load policies: {e}")

        # Load legal holds
        if self.holds_file.exists():
            try:
                with open(self.holds_file, 'r') as f:
                    data = json.load(f)
                    for hold_data in data:
                        hold = LegalHold.from_dict(hold_data)
                        self.legal_holds[hold.hold_id] = hold
            except Exception as e:
                logger.error(f"Failed to load legal holds: {e}")

        # Load retention records
        if self.records_file.exists():
            try:
                with open(self.records_file, 'r') as f:
                    data = json.load(f)
                    for record_data in data:
                        record = DocumentRetentionRecord.from_dict(record_data)
                        self.retention_records[record.document_id] = record
            except Exception as e:
                logger.error(f"Failed to load retention records: {e}")

    def _save_policies(self) -> None:
        """Save policies to storage."""
        try:
            data = [policy.to_dict() for policy in self.policies.values()]
            with open(self.policies_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save policies: {e}")

    def _save_holds(self) -> None:
        """Save legal holds to storage."""
        try:
            data = [hold.to_dict() for hold in self.legal_holds.values()]
            with open(self.holds_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save legal holds: {e}")

    def _save_records(self) -> None:
        """Save retention records to storage."""
        try:
            data = [record.to_dict() for record in self.retention_records.values()]
            with open(self.records_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save retention records: {e}")


# Convenience functions
def create_retention_policy(
    storage_path: Union[str, Path],
    name: str,
    retention_period: str,
    disposition_action: str,
    **kwargs
) -> RetentionPolicy:
    """
    Convenience function to create a retention policy.

    Args:
        storage_path: Storage path
        name: Policy name
        retention_period: Retention period name (e.g., 'YEARS_7')
        disposition_action: Disposition action (e.g., 'archive')
        **kwargs: Additional policy parameters

    Returns:
        Created RetentionPolicy
    """
    manager = RetentionManager(storage_path)
    period = RetentionPeriod[retention_period.upper()]
    action = DispositionAction(disposition_action.lower())

    return manager.create_policy(name, period, action, **kwargs)


def apply_retention_policy(
    storage_path: Union[str, Path],
    document_id: str,
    policy_name: str
) -> DocumentRetentionRecord:
    """
    Convenience function to apply a retention policy to a document.

    Args:
        storage_path: Storage path
        document_id: Document identifier
        policy_name: Policy name

    Returns:
        DocumentRetentionRecord
    """
    manager = RetentionManager(storage_path)

    # Find policy by name
    policy = None
    for p in manager.policies.values():
        if p.name == policy_name:
            policy = p
            break

    if not policy:
        raise RetentionPolicyError(f"Policy not found: {policy_name}")

    return manager.apply_policy_to_document(document_id, policy.policy_id)
