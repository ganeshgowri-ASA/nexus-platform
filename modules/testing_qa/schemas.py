"""
Pydantic Schemas for Testing & QA Module

Request/response schemas for API validation and serialization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from modules.testing_qa.models import TestStatus, TestType, BugSeverity


# Base configuration for all schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# ============================================================================
# Test Suite Schemas
# ============================================================================


class TestSuiteBase(BaseSchema):
    """Base test suite schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    test_type: TestType
    module_name: Optional[str] = Field(None, max_length=255)
    tags: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    parallel_execution: bool = False
    timeout_seconds: int = Field(default=300, ge=0, le=3600)


class TestSuiteCreate(TestSuiteBase):
    """Schema for creating a test suite."""

    created_by: Optional[str] = None


class TestSuiteUpdate(BaseSchema):
    """Schema for updating a test suite."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    test_type: Optional[TestType] = None
    module_name: Optional[str] = None
    tags: Optional[List[str]] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    parallel_execution: Optional[bool] = None
    timeout_seconds: Optional[int] = Field(None, ge=0, le=3600)


class TestSuiteResponse(TestSuiteBase):
    """Schema for test suite response."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None


# ============================================================================
# Test Case Schemas
# ============================================================================


class TestCaseBase(BaseSchema):
    """Base test case schema."""

    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    test_function: str = Field(..., min_length=1, max_length=500)
    file_path: Optional[str] = None
    line_number: Optional[int] = Field(None, ge=0)
    priority: int = Field(default=5, ge=1, le=10)
    tags: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_result: Optional[str] = None


class TestCaseCreate(TestCaseBase):
    """Schema for creating a test case."""

    test_suite_id: int


class TestCaseUpdate(BaseSchema):
    """Schema for updating a test case."""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    test_function: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = Field(None, ge=0)
    status: Optional[TestStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    tags: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    expected_result: Optional[str] = None


class TestCaseResponse(TestCaseBase):
    """Schema for test case response."""

    id: int
    test_suite_id: int
    status: TestStatus
    actual_result: Optional[str] = None
    execution_time_ms: Optional[float] = None
    retry_count: int
    is_flaky: bool
    flakiness_score: float
    last_executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ============================================================================
# Test Run Schemas
# ============================================================================


class TestRunBase(BaseSchema):
    """Base test run schema."""

    run_name: Optional[str] = None
    environment: str = Field(default="development", max_length=100)
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    ci_build_id: Optional[str] = None
    triggered_by: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestRunCreate(TestRunBase):
    """Schema for creating a test run."""

    test_suite_id: int


class TestRunUpdate(BaseSchema):
    """Schema for updating a test run."""

    status: Optional[TestStatus] = None
    total_tests: Optional[int] = Field(None, ge=0)
    passed_tests: Optional[int] = Field(None, ge=0)
    failed_tests: Optional[int] = Field(None, ge=0)
    skipped_tests: Optional[int] = Field(None, ge=0)
    error_tests: Optional[int] = Field(None, ge=0)
    execution_time_ms: Optional[float] = Field(None, ge=0)
    coverage_percentage: Optional[float] = Field(None, ge=0, le=100)
    completed_at: Optional[datetime] = None


class TestRunResponse(TestRunBase):
    """Schema for test run response."""

    id: int
    test_suite_id: int
    status: TestStatus
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    execution_time_ms: Optional[float] = None
    coverage_percentage: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


# ============================================================================
# Test Execution Schemas
# ============================================================================


class TestExecutionBase(BaseSchema):
    """Base test execution schema."""

    status: TestStatus
    execution_time_ms: Optional[float] = Field(None, ge=0)
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    assertions: List[Dict[str, Any]] = Field(default_factory=list)
    retry_attempt: int = Field(default=0, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestExecutionCreate(TestExecutionBase):
    """Schema for creating a test execution."""

    test_run_id: int
    test_case_id: int


class TestExecutionResponse(TestExecutionBase):
    """Schema for test execution response."""

    id: int
    test_run_id: int
    test_case_id: int
    executed_at: datetime


# ============================================================================
# Bug Report Schemas
# ============================================================================


class BugReportBase(BaseSchema):
    """Base bug report schema."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    severity: BugSeverity = BugSeverity.MEDIUM
    bug_type: Optional[str] = None
    module_name: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    reproduction_steps: Optional[str] = None
    environment: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    screenshots: List[str] = Field(default_factory=list)
    related_tests: List[int] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BugReportCreate(BugReportBase):
    """Schema for creating a bug report."""

    test_run_id: Optional[int] = None


class BugReportUpdate(BaseSchema):
    """Schema for updating a bug report."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    severity: Optional[BugSeverity] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    fix_commit_hash: Optional[str] = None
    resolved_at: Optional[datetime] = None


class BugReportResponse(BugReportBase):
    """Schema for bug report response."""

    id: int
    test_run_id: Optional[int] = None
    status: str
    fix_commit_hash: Optional[str] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None


# ============================================================================
# Coverage Report Schemas
# ============================================================================


class CoverageReportBase(BaseSchema):
    """Base coverage report schema."""

    module_name: Optional[str] = None
    file_path: Optional[str] = None
    total_statements: int = Field(default=0, ge=0)
    covered_statements: int = Field(default=0, ge=0)
    missing_statements: int = Field(default=0, ge=0)
    total_branches: int = Field(default=0, ge=0)
    covered_branches: int = Field(default=0, ge=0)
    missing_branches: int = Field(default=0, ge=0)
    line_coverage_percent: float = Field(default=0.0, ge=0, le=100)
    branch_coverage_percent: float = Field(default=0.0, ge=0, le=100)
    overall_coverage_percent: float = Field(default=0.0, ge=0, le=100)
    uncovered_lines: List[int] = Field(default_factory=list)
    uncovered_branches: List[Dict[str, int]] = Field(default_factory=list)
    complexity_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CoverageReportCreate(CoverageReportBase):
    """Schema for creating a coverage report."""

    test_run_id: int


class CoverageReportResponse(CoverageReportBase):
    """Schema for coverage report response."""

    id: int
    test_run_id: int
    generated_at: datetime


# ============================================================================
# Test Metrics Schemas
# ============================================================================


class TestMetricsBase(BaseSchema):
    """Base test metrics schema."""

    date: datetime
    module_name: Optional[str] = None
    total_tests: int = Field(default=0, ge=0)
    passed_tests: int = Field(default=0, ge=0)
    failed_tests: int = Field(default=0, ge=0)
    skipped_tests: int = Field(default=0, ge=0)
    flaky_tests: int = Field(default=0, ge=0)
    avg_execution_time_ms: Optional[float] = Field(None, ge=0)
    total_execution_time_ms: Optional[float] = Field(None, ge=0)
    coverage_percentage: Optional[float] = Field(None, ge=0, le=100)
    bugs_found: int = Field(default=0, ge=0)
    bugs_fixed: int = Field(default=0, ge=0)
    test_stability_score: Optional[float] = Field(None, ge=0, le=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestMetricsCreate(TestMetricsBase):
    """Schema for creating test metrics."""

    pass


class TestMetricsResponse(TestMetricsBase):
    """Schema for test metrics response."""

    id: int
    created_at: datetime


# ============================================================================
# Request/Response Schemas
# ============================================================================


class TestExecutionRequest(BaseSchema):
    """Request schema for executing tests."""

    test_suite_id: Optional[int] = None
    test_case_ids: Optional[List[int]] = None
    environment: str = "development"
    configuration: Dict[str, Any] = Field(default_factory=dict)
    parallel: bool = False
    max_retries: int = Field(default=0, ge=0, le=5)


class TestGenerationRequest(BaseSchema):
    """Request schema for AI test generation."""

    module_name: str
    file_path: Optional[str] = None
    test_type: TestType = TestType.UNIT
    coverage_target: float = Field(default=80.0, ge=0, le=100)
    include_edge_cases: bool = True
    use_ai: bool = True


class TestAnalyticsRequest(BaseSchema):
    """Request schema for test analytics."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    module_name: Optional[str] = None
    test_type: Optional[TestType] = None
    group_by: str = Field(default="date", pattern="^(date|module|type)$")


class TestAnalyticsResponse(BaseSchema):
    """Response schema for test analytics."""

    total_runs: int
    total_tests: int
    pass_rate: float
    fail_rate: float
    average_execution_time: float
    coverage_trend: List[Dict[str, Any]]
    flakiness_trend: List[Dict[str, Any]]
    top_failures: List[Dict[str, Any]]
    metrics_by_period: List[Dict[str, Any]]


# ============================================================================
# Utility Schemas
# ============================================================================


class PaginationParams(BaseSchema):
    """Pagination parameters."""

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=1000)


class FilterParams(BaseSchema):
    """Filter parameters."""

    test_type: Optional[TestType] = None
    status: Optional[TestStatus] = None
    module_name: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class BulkOperationResponse(BaseSchema):
    """Response for bulk operations."""

    success: bool
    processed: int
    failed: int
    errors: List[str] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list)
