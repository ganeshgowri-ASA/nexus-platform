"""Database models for contracts module.

This module defines SQLAlchemy ORM models for persisting contracts
and related entities in PostgreSQL.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from shared.database import Base
from .contract_types import (
    ContractStatus,
    ContractType,
    Currency,
    MilestoneStatus,
    ObligationStatus,
    ObligationType,
    PartyRole,
    RiskLevel,
    SignatureStatus,
)


class ContractModel(Base):
    """Database model for contracts."""

    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    contract_type = Column(SQLEnum(ContractType), nullable=False, index=True)
    status = Column(SQLEnum(ContractStatus), nullable=False, default=ContractStatus.DRAFT, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("contract_templates.id"))

    # Content
    content = Column(Text)
    file_url = Column(String(500))
    file_hash = Column(String(64))

    # Dates
    start_date = Column(DateTime, index=True)
    end_date = Column(DateTime, index=True)
    execution_date = Column(DateTime)
    effective_date = Column(DateTime)

    # Financial
    total_value = Column(Numeric(15, 2))
    currency = Column(SQLEnum(Currency), default=Currency.USD)

    # Auto-renewal
    auto_renew = Column(Boolean, default=False)
    renewal_notice_days = Column(Integer, default=30)
    renewal_count = Column(Integer, default=0)

    # Compliance & Risk
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    compliance_status = Column(String(50), default="pending")
    compliance_issues = Column(JSON, default=list)

    # Version Control
    version = Column(String(20), default="1.0")
    parent_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    is_latest = Column(Boolean, default=True)

    # Metadata
    category = Column(String(100), index=True)
    tags = Column(JSON, default=list)
    jurisdiction = Column(String(100))
    governing_law = Column(String(100))
    language = Column(String(10), default="en")
    confidential = Column(Boolean, default=False)

    # Custom fields
    custom_fields = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)

    # Audit
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    parties = relationship("PartyModel", back_populates="contract", cascade="all, delete-orphan")
    clauses = relationship("ClauseModel", back_populates="contract", cascade="all, delete-orphan")
    obligations = relationship("ObligationModel", back_populates="contract", cascade="all, delete-orphan")
    milestones = relationship("MilestoneModel", back_populates="contract", cascade="all, delete-orphan")
    amendments = relationship("AmendmentModel", back_populates="contract", cascade="all, delete-orphan")
    signatures = relationship("SignatureModel", back_populates="contract", cascade="all, delete-orphan")
    template = relationship("TemplateModel", back_populates="contracts")
    versions = relationship("ContractModel", backref="parent", remote_side=[id])

    def __repr__(self) -> str:
        return f"<Contract(id={self.id}, title='{self.title}', status={self.status})>"


class PartyModel(Base):
    """Database model for contract parties."""

    __tablename__ = "contract_parties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(PartyRole), nullable=False)
    organization = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    contact_person = Column(String(255))
    tax_id = Column(String(50))
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contract = relationship("ContractModel", back_populates="parties")

    def __repr__(self) -> str:
        return f"<Party(id={self.id}, name='{self.name}', role={self.role})>"


class ClauseModel(Base):
    """Database model for contract clauses."""

    __tablename__ = "contract_clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"))
    template_id = Column(UUID(as_uuid=True), ForeignKey("contract_templates.id"))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    is_standard = Column(Boolean, default=False)
    is_mandatory = Column(Boolean, default=False)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)
    position = Column(Integer, default=0)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("contract_clauses.id"))
    variables = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contract = relationship("ContractModel", back_populates="clauses")
    template = relationship("TemplateModel", back_populates="clauses")
    children = relationship("ClauseModel", backref="parent", remote_side=[id])

    def __repr__(self) -> str:
        return f"<Clause(id={self.id}, title='{self.title}')>"


class TemplateModel(Base):
    """Database model for contract templates."""

    __tablename__ = "contract_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    contract_type = Column(SQLEnum(ContractType), nullable=False)
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    category = Column(String(100))
    jurisdiction = Column(String(100))
    language = Column(String(10), default="en")
    variables = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    clauses = relationship("ClauseModel", back_populates="template", cascade="all, delete-orphan")
    contracts = relationship("ContractModel", back_populates="template")

    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name='{self.name}')>"


class ObligationModel(Base):
    """Database model for contract obligations."""

    __tablename__ = "contract_obligations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    obligation_type = Column(SQLEnum(ObligationType), nullable=False)
    status = Column(SQLEnum(ObligationStatus), default=ObligationStatus.PENDING)
    responsible_party = Column(UUID(as_uuid=True), nullable=False)
    due_date = Column(DateTime, index=True)
    completed_date = Column(DateTime)
    amount = Column(Numeric(15, 2))
    currency = Column(SQLEnum(Currency))
    recurrence = Column(String(100))
    dependencies = Column(JSON, default=list)
    alerts_enabled = Column(Boolean, default=True)
    alert_days_before = Column(Integer, default=7)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contract = relationship("ContractModel", back_populates="obligations")

    def __repr__(self) -> str:
        return f"<Obligation(id={self.id}, title='{self.title}', status={self.status})>"


class MilestoneModel(Base):
    """Database model for contract milestones."""

    __tablename__ = "contract_milestones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(MilestoneStatus), default=MilestoneStatus.PENDING)
    due_date = Column(DateTime, index=True)
    completed_date = Column(DateTime)
    progress_percentage = Column(Integer, default=0)
    payment_trigger = Column(Boolean, default=False)
    payment_amount = Column(Numeric(15, 2))
    currency = Column(SQLEnum(Currency))
    deliverables = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contract = relationship("ContractModel", back_populates="milestones")

    def __repr__(self) -> str:
        return f"<Milestone(id={self.id}, title='{self.title}', status={self.status})>"


class AmendmentModel(Base):
    """Database model for contract amendments."""

    __tablename__ = "contract_amendments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    changes = Column(JSON, default=dict)
    reason = Column(Text)
    effective_date = Column(DateTime)
    approved_by = Column(UUID(as_uuid=True))
    approved_at = Column(DateTime)
    version = Column(String(20), default="1.0")
    metadata = Column(JSON, default=dict)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contract = relationship("ContractModel", back_populates="amendments")

    def __repr__(self) -> str:
        return f"<Amendment(id={self.id}, title='{self.title}')>"


class SignatureModel(Base):
    """Database model for contract signatures."""

    __tablename__ = "contract_signatures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    signer_id = Column(UUID(as_uuid=True), nullable=False)
    signer_name = Column(String(255), nullable=False)
    signer_email = Column(String(255), nullable=False)
    signer_role = Column(SQLEnum(PartyRole), nullable=False)
    status = Column(SQLEnum(SignatureStatus), default=SignatureStatus.PENDING)
    requested_at = Column(DateTime, default=datetime.utcnow)
    signed_at = Column(DateTime)
    signature_data = Column(Text)
    ip_address = Column(String(45))
    location = Column(String(255))
    device_info = Column(String(255))
    witness_name = Column(String(255))
    witness_email = Column(String(255))
    notarized = Column(Boolean, default=False)
    notary_info = Column(JSON)
    metadata = Column(JSON, default=dict)

    # Relationships
    contract = relationship("ContractModel", back_populates="signatures")

    def __repr__(self) -> str:
        return f"<Signature(id={self.id}, signer='{self.signer_name}', status={self.status})>"


class AuditLogModel(Base):
    """Database model for audit trail."""

    __tablename__ = "contract_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True))
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}')>"
