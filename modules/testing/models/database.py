"""
Database models for Testing & QA module
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Text, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class TestStatus(str, enum.Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(str, enum.Enum):
    """Test type enumeration"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"


class Priority(str, enum.Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DefectSeverity(str, enum.Enum):
    """Defect severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    BLOCKER = "blocker"


class DefectStatus(str, enum.Enum):
    """Defect status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class TestCase(Base):
    """Test case definitions"""
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Test metadata
    test_type = Column(Enum(TestType), nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    tags = Column(JSON)  # List of tags for categorization

    # Test details
    test_file = Column(String(500))  # Path to test file
    test_function = Column(String(200))  # Function/method name
    test_class = Column(String(200), nullable=True)  # Class name if applicable

    # Pre/Post conditions
    preconditions = Column(Text, nullable=True)
    postconditions = Column(Text, nullable=True)

    # Expected results
    expected_result = Column(Text, nullable=True)

    # Test steps (for manual/E2E tests)
    steps = Column(JSON, nullable=True)  # List of test steps

    # Automation
    is_automated = Column(Boolean, default=False)
    automation_script = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)

    # Relationships
    executions = relationship("TestExecution", back_populates="test_case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestCase(id={self.id}, name={self.name}, type={self.test_type})>"


class TestSuite(Base):
    """Test suite - collection of test cases"""
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Suite metadata
    tags = Column(JSON)
    test_case_ids = Column(JSON)  # List of test case IDs

    # Configuration
    environment = Column(String(100), nullable=True)  # dev, staging, prod
    parallel_execution = Column(Boolean, default=False)
    max_parallel_tests = Column(Integer, default=1)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    runs = relationship("TestRun", back_populates="test_suite", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestSuite(id={self.id}, name={self.name})>"


class TestRun(Base):
    """Test run - execution of a test suite"""
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    test_suite_id = Column(Integer, ForeignKey("test_suites.id"), nullable=False)
    name = Column(String(200), nullable=True)

    # Run metadata
    environment = Column(String(100), nullable=True)
    build_number = Column(String(100), nullable=True)
    branch = Column(String(200), nullable=True)
    commit_hash = Column(String(64), nullable=True)

    # Execution details
    status = Column(Enum(TestStatus), default=TestStatus.PENDING)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds

    # Results summary
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)

    # Coverage
    coverage_percentage = Column(Float, nullable=True)
    coverage_report_path = Column(String(500), nullable=True)

    # Configuration
    config = Column(JSON, nullable=True)

    # Triggered by
    triggered_by = Column(String(100), nullable=True)  # user, CI/CD, schedule

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_suite = relationship("TestSuite", back_populates="runs")
    executions = relationship("TestExecution", back_populates="test_run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestRun(id={self.id}, status={self.status}, tests={self.passed_tests}/{self.total_tests})>"


class TestExecution(Base):
    """Individual test execution within a test run"""
    __tablename__ = "test_executions"

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)

    # Execution details
    status = Column(Enum(TestStatus), nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds

    # Results
    actual_result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)

    # Logs and artifacts
    logs = Column(Text, nullable=True)
    screenshots = Column(JSON, nullable=True)  # List of screenshot paths
    artifacts = Column(JSON, nullable=True)  # List of artifact paths

    # Retry information
    retry_count = Column(Integer, default=0)
    is_retry = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_run = relationship("TestRun", back_populates="executions")
    test_case = relationship("TestCase", back_populates="executions")
    defects = relationship("Defect", back_populates="test_execution")

    def __repr__(self):
        return f"<TestExecution(id={self.id}, test={self.test_case_id}, status={self.status})>"


class Defect(Base):
    """Defect/Bug tracking"""
    __tablename__ = "defects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Defect metadata
    severity = Column(Enum(DefectSeverity), nullable=False)
    priority = Column(Enum(Priority), nullable=False)
    status = Column(Enum(DefectStatus), default=DefectStatus.OPEN)

    # Categorization
    component = Column(String(200), nullable=True)
    tags = Column(JSON)

    # Related test
    test_execution_id = Column(Integer, ForeignKey("test_executions.id"), nullable=True)

    # Environment
    environment = Column(String(100), nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)

    # Reproduction
    steps_to_reproduce = Column(Text, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)

    # Artifacts
    screenshots = Column(JSON, nullable=True)
    logs = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)

    # Assignment
    assigned_to = Column(String(100), nullable=True)
    reported_by = Column(String(100), nullable=True)

    # Resolution
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_execution = relationship("TestExecution", back_populates="defects")

    def __repr__(self):
        return f"<Defect(id={self.id}, title={self.title}, severity={self.severity})>"


class CoverageReport(Base):
    """Code coverage reports"""
    __tablename__ = "coverage_reports"

    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=True)

    # Coverage metrics
    line_coverage = Column(Float, nullable=True)
    branch_coverage = Column(Float, nullable=True)
    function_coverage = Column(Float, nullable=True)
    overall_coverage = Column(Float, nullable=True)

    # Detailed metrics
    total_lines = Column(Integer, nullable=True)
    covered_lines = Column(Integer, nullable=True)
    missed_lines = Column(Integer, nullable=True)

    # File-level coverage
    file_coverage = Column(JSON, nullable=True)  # {file_path: coverage_percentage}

    # Report files
    html_report_path = Column(String(500), nullable=True)
    xml_report_path = Column(String(500), nullable=True)
    json_report_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CoverageReport(id={self.id}, coverage={self.overall_coverage:.2f}%)>"


class PerformanceMetric(Base):
    """Performance test metrics"""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    test_execution_id = Column(Integer, ForeignKey("test_executions.id"), nullable=False)

    # Performance metrics
    response_time = Column(Float, nullable=True)  # Average response time in ms
    throughput = Column(Float, nullable=True)  # Requests per second
    error_rate = Column(Float, nullable=True)  # Percentage

    # Resource usage
    cpu_usage = Column(Float, nullable=True)  # Percentage
    memory_usage = Column(Float, nullable=True)  # MB
    disk_io = Column(Float, nullable=True)  # MB/s

    # Load testing
    concurrent_users = Column(Integer, nullable=True)
    total_requests = Column(Integer, nullable=True)
    successful_requests = Column(Integer, nullable=True)
    failed_requests = Column(Integer, nullable=True)

    # Latency percentiles
    p50_latency = Column(Float, nullable=True)
    p95_latency = Column(Float, nullable=True)
    p99_latency = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PerformanceMetric(id={self.id}, response_time={self.response_time}ms)>"
