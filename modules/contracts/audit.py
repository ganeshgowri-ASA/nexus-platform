"""Audit trail and logging."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class AuditEntry(BaseModel):
    """Audit trail entry."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    user_id: UUID
    user_name: str
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    old_value: Optional[Dict] = None
    new_value: Optional[Dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditTrail:
    """Manages complete audit trail."""

    def __init__(self):
        """Initialize audit trail."""
        self.entries: Dict[UUID, List[AuditEntry]] = {}

    def log(
        self,
        contract_id: UUID,
        user_id: UUID,
        user_name: str,
        action: str,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
        **kwargs
    ) -> AuditEntry:
        """Log an audit entry."""
        logger.info("Logging audit entry", contract_id=contract_id, action=action)

        entry = AuditEntry(
            contract_id=contract_id,
            user_id=user_id,
            user_name=user_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            **kwargs
        )

        if contract_id not in self.entries:
            self.entries[contract_id] = []
        self.entries[contract_id].append(entry)

        return entry

    def get_trail(
        self,
        contract_id: UUID,
        action: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> List[AuditEntry]:
        """Get audit trail for contract."""
        entries = self.entries.get(contract_id, [])

        if action:
            entries = [e for e in entries if e.action == action]
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]

        return sorted(entries, key=lambda e: e.timestamp, reverse=True)
