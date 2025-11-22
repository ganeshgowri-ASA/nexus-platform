"""Contract data types and models.

This module defines all core data structures for contract management,
including contracts, templates, clauses, parties, obligations, and more.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class ContractStatus(str, Enum):
    """Contract lifecycle status."""

    DRAFT = "draft"
    IN_NEGOTIATION = "in_negotiation"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_EXECUTION = "in_execution"
    EXECUTED = "executed"
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"
    ARCHIVED = "archived"


class ContractType(str, Enum):
    """Types of contracts."""

    NDA = "nda"
    MSA = "msa"
    SOW = "sow"
    EMPLOYMENT = "employment"
    VENDOR = "vendor"
    SALES = "sales"
    PURCHASE = "purchase"
    LEASE = "lease"
    SERVICE = "service"
    LICENSE = "license"
    PARTNERSHIP = "partnership"
    CONSULTING = "consulting"
    SUBSCRIPTION = "subscription"
    OTHER = "other"


class PartyRole(str, Enum):
    """Roles that parties can have in a contract."""

    BUYER = "buyer"
    SELLER = "seller"
    VENDOR = "vendor"
    CLIENT = "client"
    EMPLOYER = "employer"
    EMPLOYEE = "employee"
    LICENSOR = "licensor"
    LICENSEE = "licensee"
    LESSOR = "lessor"
    LESSEE = "lessee"
    PARTNER = "partner"
    OTHER = "other"


class ObligationType(str, Enum):
    """Types of contractual obligations."""

    PAYMENT = "payment"
    DELIVERY = "delivery"
    PERFORMANCE = "performance"
    REPORTING = "reporting"
    COMPLIANCE = "compliance"
    CONFIDENTIALITY = "confidentiality"
    NON_COMPETE = "non_compete"
    INSURANCE = "insurance"
    WARRANTY = "warranty"
    OTHER = "other"


class ObligationStatus(str, Enum):
    """Status of an obligation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    WAIVED = "waived"


class MilestoneStatus(str, Enum):
    """Status of a milestone."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class SignatureStatus(str, Enum):
    """Status of a signature."""

    PENDING = "pending"
    REQUESTED = "requested"
    SIGNED = "signed"
    DECLINED = "declined"
    EXPIRED = "expired"


class RiskLevel(str, Enum):
    """Risk assessment levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"
    INR = "INR"
    CAD = "CAD"
    AUD = "AUD"


class Party(BaseModel):
    """Represents a party in a contract."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    role: PartyRole
    organization: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    tax_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class Clause(BaseModel):
    """Represents a contract clause."""

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: str = Field(..., max_length=100)
    is_standard: bool = False
    is_mandatory: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    position: int = 0
    parent_id: Optional[UUID] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class Template(BaseModel):
    """Represents a contract template."""

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    contract_type: ContractType
    clauses: List[Clause] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    version: str = "1.0"
    category: Optional[str] = None
    jurisdiction: Optional[str] = None
    language: str = "en"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class Obligation(BaseModel):
    """Represents a contractual obligation."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    obligation_type: ObligationType
    status: ObligationStatus = ObligationStatus.PENDING
    responsible_party: UUID
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    amount: Optional[Decimal] = None
    currency: Optional[Currency] = None
    recurrence: Optional[str] = None  # cron expression
    dependencies: List[UUID] = Field(default_factory=list)
    alerts_enabled: bool = True
    alert_days_before: int = 7
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError("Amount must be non-negative")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            Decimal: lambda v: str(v),
        }


class Milestone(BaseModel):
    """Represents a contract milestone."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: MilestoneStatus = MilestoneStatus.PENDING
    due_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    progress_percentage: int = Field(0, ge=0, le=100)
    payment_trigger: bool = False
    payment_amount: Optional[Decimal] = None
    currency: Optional[Currency] = None
    deliverables: List[str] = Field(default_factory=list)
    dependencies: List[UUID] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            Decimal: lambda v: str(v),
        }


class Amendment(BaseModel):
    """Represents a contract amendment."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    changes: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None
    effective_date: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    version: str = "1.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_by: UUID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class Signature(BaseModel):
    """Represents a contract signature."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    signer_id: UUID
    signer_name: str
    signer_email: str
    signer_role: PartyRole
    status: SignatureStatus = SignatureStatus.PENDING
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    signed_at: Optional[datetime] = None
    signature_data: Optional[str] = None  # Base64 encoded signature
    ip_address: Optional[str] = None
    location: Optional[str] = None
    device_info: Optional[str] = None
    witness_name: Optional[str] = None
    witness_email: Optional[str] = None
    notarized: bool = False
    notary_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class Contract(BaseModel):
    """Represents a complete contract."""

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    contract_type: ContractType
    status: ContractStatus = ContractStatus.DRAFT
    template_id: Optional[UUID] = None

    # Parties
    parties: List[Party] = Field(default_factory=list)

    # Content
    clauses: List[Clause] = Field(default_factory=list)
    content: Optional[str] = None

    # Dates
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    execution_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None

    # Financial
    total_value: Optional[Decimal] = None
    currency: Currency = Currency.USD

    # Auto-renewal
    auto_renew: bool = False
    renewal_notice_days: int = 30
    renewal_count: int = 0

    # Compliance & Risk
    risk_level: RiskLevel = RiskLevel.LOW
    compliance_status: str = "pending"
    compliance_issues: List[str] = Field(default_factory=list)

    # Version Control
    version: str = "1.0"
    parent_id: Optional[UUID] = None
    is_latest: bool = True

    # Metadata
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    jurisdiction: Optional[str] = None
    governing_law: Optional[str] = None
    language: str = "en"
    confidential: bool = False

    # Relations
    obligations: List[Obligation] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    amendments: List[Amendment] = Field(default_factory=list)
    signatures: List[Signature] = Field(default_factory=list)

    # File references
    file_url: Optional[str] = None
    file_hash: Optional[str] = None

    # Audit
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Custom fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @validator('parties')
    def validate_parties(cls, v):
        if len(v) < 2:
            raise ValueError("Contract must have at least 2 parties")
        return v

    @validator('end_date')
    def validate_dates(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError("End date must be after start date")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
            Decimal: lambda v: str(v),
        }

    def is_expiring(self, days: int = 30) -> bool:
        """Check if contract is expiring within specified days.

        Args:
            days: Number of days to check

        Returns:
            True if contract expires within specified days
        """
        if not self.end_date:
            return False
        from datetime import timedelta
        return (self.end_date - datetime.utcnow()) <= timedelta(days=days)

    def is_expired(self) -> bool:
        """Check if contract has expired.

        Returns:
            True if contract is expired
        """
        if not self.end_date:
            return False
        return self.end_date < datetime.utcnow()

    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until contract expiry.

        Returns:
            Number of days until expiry, or None if no end date
        """
        if not self.end_date:
            return None
        delta = self.end_date - datetime.utcnow()
        return delta.days

    def get_party_by_role(self, role: PartyRole) -> Optional[Party]:
        """Get first party with specified role.

        Args:
            role: Party role to find

        Returns:
            Party instance or None
        """
        for party in self.parties:
            if party.role == role:
                return party
        return None

    def get_pending_signatures(self) -> List[Signature]:
        """Get all pending signatures.

        Returns:
            List of pending signatures
        """
        return [
            sig for sig in self.signatures
            if sig.status in [SignatureStatus.PENDING, SignatureStatus.REQUESTED]
        ]

    def is_fully_signed(self) -> bool:
        """Check if all signatures are completed.

        Returns:
            True if all signatures are signed
        """
        if not self.signatures:
            return False
        return all(sig.status == SignatureStatus.SIGNED for sig in self.signatures)

    def get_overdue_obligations(self) -> List[Obligation]:
        """Get all overdue obligations.

        Returns:
            List of overdue obligations
        """
        now = datetime.utcnow()
        return [
            obl for obl in self.obligations
            if obl.due_date and obl.due_date < now
            and obl.status not in [ObligationStatus.COMPLETED, ObligationStatus.WAIVED]
        ]
