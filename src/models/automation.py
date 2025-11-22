"""
Automation workflow models for marketing automation.

This module contains models for automation workflows, triggers, actions, and execution logs.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import Base
from config.constants import AutomationStatus, TriggerType, ActionType


class Automation(Base):
    """
    Automation workflow model.

    Attributes:
        id: Automation ID
        workspace_id: Associated workspace ID
        name: Automation name
        description: Automation description
        status: Automation status (active, paused, archived)
        trigger_type: Trigger type
        trigger_config: Trigger configuration (JSON)
        actions: List of actions (JSON array)
        conditions: Execution conditions (JSON)
        execution_count: Total execution count
        last_executed_at: Last execution timestamp
        created_by: Creator user ID
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "automations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(AutomationStatus), nullable=False, default=AutomationStatus.PAUSED)
    trigger_type = Column(SQLEnum(TriggerType), nullable=False)
    trigger_config = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=False)  # Array of action configurations
    conditions = Column(JSON, default={})
    execution_count = Column(Integer, default=0)
    last_executed_at = Column(DateTime)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="automations")
    executions = relationship("AutomationExecution", back_populates="automation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Automation(id={self.id}, name={self.name}, status={self.status})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "name": self.name,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "trigger_type": self.trigger_type.value if self.trigger_type else None,
            "trigger_config": self.trigger_config,
            "actions": self.actions,
            "conditions": self.conditions,
            "execution_count": self.execution_count,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AutomationExecution(Base):
    """
    Automation execution log.

    Attributes:
        id: Execution ID
        automation_id: Associated automation ID
        contact_id: Contact ID (if applicable)
        status: Execution status (success, failed, partial)
        trigger_data: Trigger event data (JSON)
        actions_executed: Actions executed (JSON array)
        error_message: Error message if failed
        started_at: Execution start timestamp
        completed_at: Execution completion timestamp
        created_at: Creation timestamp
    """

    __tablename__ = "automation_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    automation_id = Column(UUID(as_uuid=True), ForeignKey("automations.id"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), index=True)
    status = Column(String(50), nullable=False)  # success, failed, partial
    trigger_data = Column(JSON, default={})
    actions_executed = Column(JSON, default=[])
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    automation = relationship("Automation", back_populates="executions")

    def __repr__(self) -> str:
        return f"<AutomationExecution(id={self.id}, status={self.status})>"


class DripCampaign(Base):
    """
    Drip campaign model for nurture sequences.

    Attributes:
        id: Drip campaign ID
        workspace_id: Associated workspace ID
        name: Campaign name
        description: Campaign description
        status: Campaign status
        entry_trigger: Entry trigger configuration (JSON)
        steps: Campaign steps (JSON array)
        total_enrolled: Total enrolled contacts
        total_completed: Total completed contacts
        created_by: Creator user ID
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "drip_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), nullable=False, default="draft")
    entry_trigger = Column(JSON, nullable=False)
    steps = Column(JSON, nullable=False)  # Array of step configurations
    total_enrolled = Column(Integer, default=0)
    total_completed = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    enrollments = relationship("DripEnrollment", back_populates="drip_campaign", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DripCampaign(id={self.id}, name={self.name})>"


class DripEnrollment(Base):
    """
    Drip campaign enrollment tracking.

    Attributes:
        id: Enrollment ID
        drip_campaign_id: Associated drip campaign ID
        contact_id: Enrolled contact ID
        status: Enrollment status
        current_step: Current step index
        enrolled_at: Enrollment timestamp
        completed_at: Completion timestamp
        paused_at: Pause timestamp
        metadata: Additional metadata (JSON)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "drip_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    drip_campaign_id = Column(UUID(as_uuid=True), ForeignKey("drip_campaigns.id"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="active")
    current_step = Column(Integer, default=0)
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    paused_at = Column(DateTime)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drip_campaign = relationship("DripCampaign", back_populates="enrollments")

    def __repr__(self) -> str:
        return f"<DripEnrollment(id={self.id}, status={self.status})>"


class WorkflowNode(Base):
    """
    Visual workflow builder node.

    Attributes:
        id: Node ID
        automation_id: Associated automation ID
        node_type: Node type (trigger, action, condition, delay)
        node_config: Node configuration (JSON)
        position_x: X position in visual editor
        position_y: Y position in visual editor
        next_node_id: Next node ID for sequential flow
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "workflow_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    automation_id = Column(UUID(as_uuid=True), ForeignKey("automations.id"), nullable=False, index=True)
    node_type = Column(String(50), nullable=False)
    node_config = Column(JSON, nullable=False)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    next_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<WorkflowNode(id={self.id}, type={self.node_type})>"
