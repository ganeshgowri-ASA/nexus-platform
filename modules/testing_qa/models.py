"""
SQLAlchemy Models for Testing & QA Module

Database models for test suites, test cases, test runs, bug reports,
and coverage tracking.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class TestStatus(str, enum.Enum):
    """Test execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    FLAKY = "flaky"


class TestType(str, enum.Enum):
    """Test type classification."""

    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    API = "api"
    LOAD = "load"
    SECURITY = "security"
    VISUAL = "visual"
    ACCESSIBILITY = "accessibility"
    MUTATION = "mutation"
    CONTRACT = "contract"


class BugSeverity(str, enum.Enum):
    """Bug severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TestSuite(Base):
    """Test suite model."""

    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    test_type = Column(SQLEnum(TestType), nullable=False, index=True)
    module_name = Column(String(255), nullable=True, index=True)
    tags = Column(JSON, default=list)
    configuration = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, index=True)
    parallel_execution = Column(Boolean, default=False)
    timeout_seconds = Column(Integer, default=300)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    # Relationships
    test_cases = relationship("TestCase", back_populates="test_suite", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="test_suite", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TestSuite(id={self.id}, name='{self.name}', type='{self.test_type}')>"


class TestCase(Base):
    """Test case model."""

    __tablename__ = "test_cases"
    __table_args__ = (Index("idx_suite_status", "test_suite_id", "status"),)

    id = Column(Integer, primary_key=True, index=True)
    test_suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    test_function = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=True)
    line_number = Column(Integer, nullable=True)
    status = Column(SQLEnum(TestStatus), default=TestStatus.PENDING, index=True)
    priority = Column(Integer, default=5)
    tags = Column(JSON, default=list)
    parameters = Column(JSON, default=dict)
    expected_result = Column(Text, nullable=True)
    actual_result = Column(Text, nullable=True)
    execution_time_ms = Column(Float, nullable=True)
    retry_count = Column(Integer, default=0)
    is_flaky = Column(Boolean, default=False, index=True)
    flakiness_score = Column(Float, default=0.0)
    last_executed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    test_suite = relationship("TestSuite", back_populates="test_cases")
    executions = relationship("TestExecution", back_populates="test_case", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TestCase(id={self.id}, name='{self.name}', status='{self.status}')>"


class TestRun(Base):
    """Test run/execution session model."""

    __tablename__ = "test_runs"
    __table_args__ = (Index("idx_suite_started", "test_suite_id", "started_at"),)

    id = Column(Integer, primary_key=True, index=True)
    test_suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    run_name = Column(String(500), nullable=True)
    status = Column(SQLEnum(TestStatus), default=TestStatus.PENDING, index=True)
    environment = Column(String(100), default="development")
    branch = Column(String(255), nullable=True)
    commit_hash = Column(String(255), nullable=True)
    ci_build_id = Column(String(255), nullable=True, index=True)
    triggered_by = Column(String(255), nullable=True)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)
    execution_time_ms = Column(Float, nullable=True)
    coverage_percentage = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    configuration = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)

    # Relationships
    test_suite = relationship("TestSuite", back_populates="test_runs")
    executions = relationship("TestExecution", back_populates="test_run", cascade="all, delete-orphan")
    bug_reports = relationship("BugReport", back_populates="test_run", cascade="all, delete-orphan")
    coverage_reports = relationship("CoverageReport", back_populates="test_run", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TestRun(id={self.id}, suite_id={self.test_suite_id}, status='{self.status}')>"


class TestExecution(Base):
    """Individual test execution record."""

    __tablename__ = "test_executions"
    __table_args__ = (Index("idx_run_case", "test_run_id", "test_case_id"),)

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    status = Column(SQLEnum(TestStatus), nullable=False, index=True)
    execution_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    screenshots = Column(JSON, default=list)
    logs = Column(JSON, default=list)
    assertions = Column(JSON, default=list)
    retry_attempt = Column(Integer, default=0)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSON, default=dict)

    # Relationships
    test_run = relationship("TestRun", back_populates="executions")
    test_case = relationship("TestCase", back_populates="executions")

    def __repr__(self) -> str:
        return f"<TestExecution(id={self.id}, case_id={self.test_case_id}, status='{self.status}')>"


class BugReport(Base):
    """Bug report model."""

    __tablename__ = "bug_reports"
    __table_args__ = (Index("idx_severity_status", "severity", "status"),)

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(SQLEnum(BugSeverity), default=BugSeverity.MEDIUM, index=True)
    status = Column(String(50), default="open", index=True)
    bug_type = Column(String(100), nullable=True)
    module_name = Column(String(255), nullable=True, index=True)
    file_path = Column(String(1000), nullable=True)
    line_number = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    reproduction_steps = Column(Text, nullable=True)
    environment = Column(String(100), nullable=True)
    assigned_to = Column(String(255), nullable=True)
    tags = Column(JSON, default=list)
    screenshots = Column(JSON, default=list)
    related_tests = Column(JSON, default=list)
    fix_commit_hash = Column(String(255), nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSON, default=dict)

    # Relationships
    test_run = relationship("TestRun", back_populates="bug_reports")

    def __repr__(self) -> str:
        return f"<BugReport(id={self.id}, title='{self.title}', severity='{self.severity}')>"


class CoverageReport(Base):
    """Code coverage report model."""

    __tablename__ = "coverage_reports"
    __table_args__ = (Index("idx_run_module", "test_run_id", "module_name"),)

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    module_name = Column(String(255), nullable=True, index=True)
    file_path = Column(String(1000), nullable=True)
    total_statements = Column(Integer, default=0)
    covered_statements = Column(Integer, default=0)
    missing_statements = Column(Integer, default=0)
    total_branches = Column(Integer, default=0)
    covered_branches = Column(Integer, default=0)
    missing_branches = Column(Integer, default=0)
    line_coverage_percent = Column(Float, default=0.0)
    branch_coverage_percent = Column(Float, default=0.0)
    overall_coverage_percent = Column(Float, default=0.0)
    uncovered_lines = Column(JSON, default=list)
    uncovered_branches = Column(JSON, default=list)
    complexity_score = Column(Float, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSON, default=dict)

    # Relationships
    test_run = relationship("TestRun", back_populates="coverage_reports")

    def __repr__(self) -> str:
        return f"<CoverageReport(id={self.id}, module='{self.module_name}', coverage={self.overall_coverage_percent}%)>"


class TestMetrics(Base):
    """Test metrics and analytics model."""

    __tablename__ = "test_metrics"
    __table_args__ = (Index("idx_date_module", "date", "module_name"),)

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    module_name = Column(String(255), nullable=True, index=True)
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    flaky_tests = Column(Integer, default=0)
    avg_execution_time_ms = Column(Float, nullable=True)
    total_execution_time_ms = Column(Float, nullable=True)
    coverage_percentage = Column(Float, nullable=True)
    bugs_found = Column(Integer, default=0)
    bugs_fixed = Column(Integer, default=0)
    test_stability_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSON, default=dict)

    def __repr__(self) -> str:
        return f"<TestMetrics(id={self.id}, date={self.date}, module='{self.module_name}')>"


class FlakynessRecord(Base):
    """Test flakiness tracking model."""

    __tablename__ = "flakiness_records"
    __table_args__ = (Index("idx_test_date", "test_case_id", "detected_at"),)

    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    execution_count = Column(Integer, default=0)
    pass_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    flakiness_percentage = Column(Float, default=0.0)
    last_pass_at = Column(DateTime(timezone=True), nullable=True)
    last_fail_at = Column(DateTime(timezone=True), nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    failure_patterns = Column(JSON, default=list)
    recommended_action = Column(String(500), nullable=True)
    metadata = Column(JSON, default=dict)

    def __repr__(self) -> str:
        return f"<FlakynessRecord(id={self.id}, test_case_id={self.test_case_id}, flakiness={self.flakiness_percentage}%)>"
