"""
Pydantic schemas for Testing & QA module API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Test Case schemas
class TestCaseCreate(BaseModel):
    """Create test case request"""
    name: str
    description: Optional[str] = None
    test_type: str = Field(..., description="unit, integration, e2e, performance, security, regression")
    priority: str = Field("medium", description="low, medium, high, critical")
    tags: Optional[List[str]] = None
    test_file: Optional[str] = None
    test_function: Optional[str] = None
    test_class: Optional[str] = None
    preconditions: Optional[str] = None
    postconditions: Optional[str] = None
    expected_result: Optional[str] = None
    steps: Optional[List[Dict[str, str]]] = None
    is_automated: bool = False
    automation_script: Optional[str] = None


class TestCaseResponse(BaseModel):
    """Test case response"""
    id: int
    name: str
    description: Optional[str] = None
    test_type: str
    priority: str
    tags: Optional[List[str]] = None
    is_automated: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Test Suite schemas
class TestSuiteCreate(BaseModel):
    """Create test suite request"""
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    test_case_ids: List[int]
    environment: Optional[str] = None
    parallel_execution: bool = False
    max_parallel_tests: int = 1


class TestSuiteResponse(BaseModel):
    """Test suite response"""
    id: int
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    test_case_ids: List[int]
    environment: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Test Run schemas
class TestRunCreate(BaseModel):
    """Create test run request"""
    test_suite_id: int
    name: Optional[str] = None
    environment: Optional[str] = None
    build_number: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    triggered_by: Optional[str] = None


class TestRunResponse(BaseModel):
    """Test run response"""
    id: int
    test_suite_id: int
    name: Optional[str] = None
    environment: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    coverage_percentage: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Test Execution schemas
class TestExecutionResponse(BaseModel):
    """Test execution response"""
    id: int
    test_run_id: int
    test_case_id: int
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    retry_count: int

    class Config:
        from_attributes = True


# Defect schemas
class DefectCreate(BaseModel):
    """Create defect request"""
    title: str
    description: str
    severity: str = Field(..., description="low, medium, high, critical, blocker")
    priority: str = Field(..., description="low, medium, high, critical")
    component: Optional[str] = None
    tags: Optional[List[str]] = None
    test_execution_id: Optional[int] = None
    environment: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    assigned_to: Optional[str] = None
    reported_by: Optional[str] = None


class DefectUpdate(BaseModel):
    """Update defect request"""
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None


class DefectResponse(BaseModel):
    """Defect response"""
    id: int
    title: str
    description: str
    severity: str
    priority: str
    status: str
    component: Optional[str] = None
    tags: Optional[List[str]] = None
    test_execution_id: Optional[int] = None
    assigned_to: Optional[str] = None
    reported_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Coverage schemas
class CoverageReportResponse(BaseModel):
    """Coverage report response"""
    id: int
    test_run_id: Optional[int] = None
    line_coverage: Optional[float] = None
    branch_coverage: Optional[float] = None
    function_coverage: Optional[float] = None
    overall_coverage: Optional[float] = None
    total_lines: Optional[int] = None
    covered_lines: Optional[int] = None
    missed_lines: Optional[int] = None
    html_report_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics schemas
class TestAnalyticsResponse(BaseModel):
    """Test analytics response"""
    total_test_cases: int
    total_test_runs: int
    total_defects: int
    active_defects: int
    test_pass_rate: float
    average_test_duration: float
    tests_by_type: Dict[str, int]
    defects_by_severity: Dict[str, int]
    recent_runs: List[TestRunResponse]
    top_failing_tests: List[Dict[str, Any]]


# Performance metrics schemas
class PerformanceMetricResponse(BaseModel):
    """Performance metric response"""
    id: int
    test_execution_id: int
    response_time: Optional[float] = None
    throughput: Optional[float] = None
    error_rate: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    concurrent_users: Optional[int] = None
    p50_latency: Optional[float] = None
    p95_latency: Optional[float] = None
    p99_latency: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
