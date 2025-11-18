"""
Pydantic schemas for Testing & QA module
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TestStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestTypeEnum(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"


class TestPriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DefectSeverityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    BLOCKER = "blocker"


class DefectStatusEnum(str, Enum):
    NEW = "new"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


# Request Schemas
class TestSuiteCreate(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: Optional[int] = None
    test_type: TestTypeEnum
    tags: Optional[List[str]] = None
    environment: Optional[str] = None
    created_by: int


class TestCaseCreate(BaseModel):
    suite_id: int
    name: str
    description: Optional[str] = None
    test_type: TestTypeEnum
    priority: TestPriorityEnum = TestPriorityEnum.MEDIUM
    file_path: Optional[str] = None
    function_name: Optional[str] = None
    code: Optional[str] = None
    tags: Optional[List[str]] = None
    preconditions: Optional[str] = None
    expected_result: Optional[str] = None
    test_data: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 300
    created_by: int


class TestRunCreate(BaseModel):
    suite_id: int
    name: str
    description: Optional[str] = None
    run_type: Optional[str] = "manual"
    environment: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    build_number: Optional[str] = None
    triggered_by: int


class DefectCreate(BaseModel):
    title: str
    description: str
    severity: DefectSeverityEnum
    priority: TestPriorityEnum = TestPriorityEnum.MEDIUM
    test_case_id: Optional[int] = None
    test_execution_id: Optional[int] = None
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    environment: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    reported_by: int


# Response Schemas
class TestSuiteResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    test_type: str
    tags: Optional[List[str]] = None
    environment: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class TestCaseResponse(BaseModel):
    id: int
    suite_id: int
    name: str
    description: Optional[str] = None
    test_type: str
    priority: str
    last_status: str
    last_run_at: Optional[datetime] = None
    created_at: datetime
    is_active: bool
    is_automated: bool

    class Config:
        from_attributes = True


class TestExecutionResponse(BaseModel):
    id: int
    test_case_id: int
    status: str
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    total_assertions: int
    passed_assertions: int
    failed_assertions: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestRunResponse(BaseModel):
    id: int
    suite_id: int
    name: str
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DefectResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    status: str
    priority: str
    test_case_id: Optional[int] = None
    environment: Optional[str] = None
    assigned_to: Optional[int] = None
    reported_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoverageReportResponse(BaseModel):
    id: int
    test_run_id: int
    line_coverage_percent: Optional[float] = None
    branch_coverage_percent: Optional[float] = None
    function_coverage_percent: Optional[float] = None
    total_lines: Optional[int] = None
    covered_lines: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TestAnalyticsResponse(BaseModel):
    total_test_cases: int
    total_test_runs: int
    total_defects: int
    test_pass_rate: float
    average_execution_time: Optional[float] = None
    tests_by_type: Dict[str, int]
    tests_by_status: Dict[str, int]
    defects_by_severity: Dict[str, int]
    recent_failures: List[TestCaseResponse]

    class Config:
        from_attributes = True
