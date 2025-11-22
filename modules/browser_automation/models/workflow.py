"""Workflow database models"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from .database import Base


class WorkflowStatus(str, enum.Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, enum.Enum):
    """Types of workflow steps"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    EXTRACT = "extract"
    SCREENSHOT = "screenshot"
    PDF = "pdf"
    WAIT = "wait"
    SCROLL = "scroll"
    SELECT = "select"
    SUBMIT = "submit"
    CUSTOM_JS = "custom_js"


class Workflow(Base):
    """Workflow model for browser automation"""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    headless = Column(Boolean, default=True)
    browser_type = Column(String(50), default="chromium")  # chromium, firefox, webkit
    timeout = Column(Integer, default=30000)
    user_id = Column(String(255), nullable=True, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStep(Base):
    """Individual steps in a workflow"""
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    step_type = Column(SQLEnum(StepType), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Step configuration
    selector = Column(String(500), nullable=True)  # CSS/XPath selector
    selector_type = Column(String(50), default="css")  # css, xpath, id, name
    value = Column(Text, nullable=True)  # Input value or URL
    wait_before = Column(Integer, default=0)  # Wait before step (ms)
    wait_after = Column(Integer, default=0)  # Wait after step (ms)

    # Advanced options
    options = Column(JSON, nullable=True)  # Additional step options
    error_handling = Column(String(50), default="stop")  # stop, continue, retry
    max_retries = Column(Integer, default=3)

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")


class WorkflowExecution(Base):
    """Workflow execution history"""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)

    # Execution details
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Results
    result_data = Column(JSON, nullable=True)  # Extracted data
    screenshots = Column(JSON, nullable=True)  # List of screenshot paths
    pdfs = Column(JSON, nullable=True)  # List of PDF paths
    error_message = Column(Text, nullable=True)
    error_step = Column(Integer, nullable=True)

    # Metadata
    triggered_by = Column(String(50), default="manual")  # manual, scheduled, api
    user_id = Column(String(255), nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
