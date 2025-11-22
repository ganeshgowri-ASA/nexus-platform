"""
Database models for NEXUS Platform
"""
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from src.config.database import Base


class AutomationStatus(str, Enum):
    """Automation status enumeration"""

    ACTIVE = "active"
    PAUSED = "paused"
    DRAFT = "draft"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """Execution status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TriggerType(str, Enum):
    """Trigger type enumeration"""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    EVENT = "event"


class Bot(Base):
    """Bot/Agent configuration"""

    __tablename__ = "bots"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    bot_type = Column(String, default="standard")  # standard, ui_automation, api, etc.
    capabilities = Column(JSON, default=list)  # List of bot capabilities
    configuration = Column(JSON, default=dict)  # Bot-specific configuration
    status = Column(SQLEnum(AutomationStatus), default=AutomationStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    automations = relationship("Automation", back_populates="bot")


class Automation(Base):
    """Automation/Process definition"""

    __tablename__ = "automations"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    bot_id = Column(String, ForeignKey("bots.id"), nullable=True)
    trigger_type = Column(SQLEnum(TriggerType), default=TriggerType.MANUAL)
    workflow = Column(JSON, nullable=False)  # Workflow definition (nodes, edges, etc.)
    inputs = Column(JSON, default=dict)  # Input parameters schema
    outputs = Column(JSON, default=dict)  # Output parameters schema
    variables = Column(JSON, default=dict)  # Global variables
    error_handling = Column(JSON, default=dict)  # Error handling configuration
    retry_config = Column(JSON, default=dict)  # Retry configuration
    timeout = Column(Integer, default=3600)  # Execution timeout in seconds
    status = Column(SQLEnum(AutomationStatus), default=AutomationStatus.DRAFT)
    version = Column(Integer, default=1)
    is_template = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    last_executed_at = Column(DateTime, nullable=True)

    # Relationships
    bot = relationship("Bot", back_populates="automations")
    executions = relationship(
        "AutomationExecution", back_populates="automation", cascade="all, delete-orphan"
    )
    schedules = relationship(
        "Schedule", back_populates="automation", cascade="all, delete-orphan"
    )


class AutomationExecution(Base):
    """Automation execution history"""

    __tablename__ = "automation_executions"

    id = Column(String, primary_key=True)
    automation_id = Column(String, ForeignKey("automations.id"), nullable=False)
    trigger_type = Column(SQLEnum(TriggerType))
    status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING)
    input_data = Column(JSON, default=dict)  # Input data for this execution
    output_data = Column(JSON, default=dict)  # Output data from this execution
    variables = Column(JSON, default=dict)  # Runtime variables
    logs = Column(JSON, default=list)  # Execution logs
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    retry_count = Column(Integer, default=0)
    parent_execution_id = Column(String, nullable=True)  # For sub-workflows
    triggered_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    automation = relationship("Automation", back_populates="executions")
    audit_logs = relationship(
        "AuditLog", back_populates="execution", cascade="all, delete-orphan"
    )


class Schedule(Base):
    """Automation scheduling configuration"""

    __tablename__ = "schedules"

    id = Column(String, primary_key=True)
    automation_id = Column(String, ForeignKey("automations.id"), nullable=False)
    name = Column(String, nullable=False)
    cron_expression = Column(String, nullable=False)  # Cron expression for scheduling
    timezone = Column(String, default="UTC")
    is_active = Column(Boolean, default=True)
    input_data = Column(JSON, default=dict)  # Default input data for scheduled runs
    next_run_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)

    # Relationships
    automation = relationship("Automation", back_populates="schedules")


class AuditLog(Base):
    """Audit log for all RPA actions"""

    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    execution_id = Column(
        String, ForeignKey("automation_executions.id"), nullable=True
    )
    automation_id = Column(String, nullable=True)
    action = Column(String, nullable=False)  # action performed
    entity_type = Column(String)  # automation, bot, schedule, etc.
    entity_id = Column(String)
    details = Column(JSON, default=dict)
    user_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    execution = relationship("AutomationExecution", back_populates="audit_logs")


class UIElement(Base):
    """UI Element definitions for automation"""

    __tablename__ = "ui_elements"

    id = Column(String, primary_key=True)
    automation_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    element_type = Column(String)  # button, input, dropdown, etc.
    selector = Column(JSON, default=dict)  # Selector strategy (xpath, css, id, etc.)
    screenshot_path = Column(String, nullable=True)
    properties = Column(JSON, default=dict)  # Element properties
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
