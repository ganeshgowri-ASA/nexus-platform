"""
Database models for Testing & QA module
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class TestStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(enum.Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"


class TestPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DefectSeverity(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    BLOCKER = "blocker"


class DefectStatus(enum.Enum):
    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class TestSuite(Base):
    """Test suite grouping"""
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    project_id = Column(Integer, nullable=True, index=True)

    # Configuration
    test_type = Column(Enum(TestType), nullable=False)
    tags = Column(JSON, nullable=True)  # List of tags
    environment = Column(String(100), nullable=True)

    # Metadata
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    is_active = Column(Boolean, default=True)

    # Relationships
    test_cases = relationship("TestCase", back_populates="suite", cascade="all, delete-orphan")
    test_runs = relationship("TestRun", back_populates="suite")


class TestCase(Base):
    """Individual test cases"""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)

    # Test details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(Enum(TestType), nullable=False)
    priority = Column(Enum(TestPriority), default=TestPriority.MEDIUM)

    # Test code
    file_path = Column(String(500), nullable=True)
    function_name = Column(String(255), nullable=True)
    code = Column(Text, nullable=True)

    # Configuration
    tags = Column(JSON, nullable=True)
    preconditions = Column(Text, nullable=True)
    expected_result = Column(Text, nullable=True)
    test_data = Column(JSON, nullable=True)

    # Execution settings
    timeout_seconds = Column(Integer, default=300)
    retry_count = Column(Integer, default=0)

    # Status
    last_status = Column(Enum(TestStatus), default=TestStatus.PENDING, index=True)
    last_run_at = Column(DateTime, nullable=True)

    # Metadata
    created_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    is_active = Column(Boolean, default=True)
    is_automated = Column(Boolean, default=True)

    # Relationships
    suite = relationship("TestSuite", back_populates="test_cases")
    executions = relationship("TestExecution", back_populates="test_case", cascade="all, delete-orphan")


class TestRun(Base):
    """Test run/execution batch"""
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)

    # Run details
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    run_type = Column(String(100), nullable=True)  # manual, automated, scheduled, ci/cd

    # Environment
    environment = Column(String(100), nullable=True)
    branch = Column(String(255), nullable=True)
    commit_sha = Column(String(255), nullable=True)
    build_number = Column(String(100), nullable=True)

    # Status
    status = Column(Enum(TestStatus), default=TestStatus.PENDING, index=True)

    # Results summary
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)

    # Timing
    duration_seconds = Column(Float, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # CI/CD Integration
    ci_pipeline_id = Column(String(255), nullable=True)
    ci_job_url = Column(String(500), nullable=True)

    # Metadata
    triggered_by = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    suite = relationship("TestSuite", back_populates="test_runs")
    executions = relationship("TestExecution", back_populates="test_run", cascade="all, delete-orphan")


class TestExecution(Base):
    """Individual test execution results"""
    __tablename__ = "test_executions"

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)

    # Execution details
    status = Column(Enum(TestStatus), nullable=False, index=True)
    duration_seconds = Column(Float, nullable=True)

    # Results
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    screenshots = Column(JSON, nullable=True)  # List of screenshot URLs

    # Assertions
    total_assertions = Column(Integer, default=0)
    passed_assertions = Column(Integer, default=0)
    failed_assertions = Column(Integer, default=0)

    # Performance metrics
    memory_usage_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)

    # Retry information
    attempt_number = Column(Integer, default=1)
    is_retry = Column(Boolean, default=False)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_run = relationship("TestRun", back_populates="executions")
    test_case = relationship("TestCase", back_populates="executions")


class Defect(Base):
    """Bug/defect tracking"""
    __tablename__ = "defects"

    id = Column(Integer, primary_key=True, index=True)

    # Defect details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(DefectSeverity), nullable=False, index=True)
    status = Column(Enum(DefectStatus), default=DefectStatus.NEW, index=True)
    priority = Column(Enum(TestPriority), default=TestPriority.MEDIUM)

    # Test information
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=True)
    test_execution_id = Column(Integer, ForeignKey("test_executions.id"), nullable=True)

    # Reproduction
    steps_to_reproduce = Column(Text, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)

    # Environment
    environment = Column(String(100), nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)

    # Attachments
    screenshots = Column(JSON, nullable=True)
    logs = Column(JSON, nullable=True)

    # Assignment
    assigned_to = Column(Integer, nullable=True)
    reported_by = Column(Integer, nullable=False)

    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_case = relationship("TestCase")
    test_execution = relationship("TestExecution")


class CoverageReport(Base):
    """Code coverage reports"""
    __tablename__ = "coverage_reports"

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)

    # Coverage metrics
    line_coverage_percent = Column(Float, nullable=True)
    branch_coverage_percent = Column(Float, nullable=True)
    function_coverage_percent = Column(Float, nullable=True)

    # Details
    total_lines = Column(Integer, nullable=True)
    covered_lines = Column(Integer, nullable=True)
    total_branches = Column(Integer, nullable=True)
    covered_branches = Column(Integer, nullable=True)

    # Report files
    report_url = Column(String(500), nullable=True)
    report_data = Column(JSON, nullable=True)  # Detailed coverage data

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_run = relationship("TestRun")


class PerformanceMetric(Base):
    """Performance test metrics"""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    test_execution_id = Column(Integer, ForeignKey("test_executions.id"), nullable=False)

    # Performance metrics
    response_time_ms = Column(Float, nullable=True)
    throughput_rps = Column(Float, nullable=True)  # Requests per second
    error_rate_percent = Column(Float, nullable=True)

    # Resource usage
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    disk_io_mbps = Column(Float, nullable=True)
    network_io_mbps = Column(Float, nullable=True)

    # Load testing
    concurrent_users = Column(Integer, nullable=True)
    total_requests = Column(Integer, nullable=True)
    successful_requests = Column(Integer, nullable=True)
    failed_requests = Column(Integer, nullable=True)

    # Timestamps
    measured_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_execution = relationship("TestExecution")
