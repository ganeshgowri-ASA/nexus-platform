"""
FastAPI application for Testing & QA module
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from modules.testing.models.db_connection import get_db, init_db
from modules.testing.models.schemas import (
    TestCaseCreate, TestCaseResponse,
    TestSuiteCreate, TestSuiteResponse,
    TestRunCreate, TestRunResponse,
    TestExecutionResponse,
    DefectCreate, DefectUpdate, DefectResponse,
    CoverageReportResponse,
    TestAnalyticsResponse
)
from modules.testing.models.database import (
    TestCase, TestSuite, TestRun, TestExecution, Defect, CoverageReport
)
from modules.testing.services.test_execution_service import TestExecutionService

# Create FastAPI app
app = FastAPI(
    title="NEXUS Testing & QA API",
    description="Automated testing, test management, CI/CD integration, and quality assurance API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "NEXUS Testing & QA API",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Test Case Endpoints

@app.post("/test-cases", response_model=TestCaseResponse, status_code=201)
async def create_test_case(
    test_case: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """Create a new test case"""
    db_test_case = TestCase(**test_case.dict())
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case


@app.get("/test-cases", response_model=List[TestCaseResponse])
async def list_test_cases(
    test_type: Optional[str] = None,
    is_automated: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all test cases with optional filters"""
    query = db.query(TestCase).filter(TestCase.is_active == True)

    if test_type:
        query = query.filter(TestCase.test_type == test_type)
    if is_automated is not None:
        query = query.filter(TestCase.is_automated == is_automated)

    return query.offset(skip).limit(limit).all()


@app.get("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """Get test case by ID"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return test_case


@app.put("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def update_test_case(
    test_case_id: int,
    test_case_update: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """Update test case"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    for key, value in test_case_update.dict(exclude_unset=True).items():
        setattr(test_case, key, value)

    db.commit()
    db.refresh(test_case)
    return test_case


@app.delete("/test-cases/{test_case_id}", status_code=204)
async def delete_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """Delete test case (soft delete)"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    test_case.is_active = False
    db.commit()
    return None


# Test Suite Endpoints

@app.post("/test-suites", response_model=TestSuiteResponse, status_code=201)
async def create_test_suite(
    test_suite: TestSuiteCreate,
    db: Session = Depends(get_db)
):
    """Create a new test suite"""
    db_test_suite = TestSuite(**test_suite.dict())
    db.add(db_test_suite)
    db.commit()
    db.refresh(db_test_suite)
    return db_test_suite


@app.get("/test-suites", response_model=List[TestSuiteResponse])
async def list_test_suites(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all test suites"""
    return db.query(TestSuite).filter(TestSuite.is_active == True).offset(skip).limit(limit).all()


@app.get("/test-suites/{test_suite_id}", response_model=TestSuiteResponse)
async def get_test_suite(test_suite_id: int, db: Session = Depends(get_db)):
    """Get test suite by ID"""
    test_suite = db.query(TestSuite).filter(TestSuite.id == test_suite_id).first()
    if not test_suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return test_suite


# Test Run Endpoints

@app.post("/test-runs", response_model=TestRunResponse, status_code=201)
async def create_test_run(
    test_run: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create and execute a test run"""
    service = TestExecutionService(db)

    # Create test run
    db_test_run = service.create_test_run(
        test_suite_id=test_run.test_suite_id,
        name=test_run.name,
        environment=test_run.environment,
        build_number=test_run.build_number,
        branch=test_run.branch,
        commit_hash=test_run.commit_hash,
        config=test_run.config,
        triggered_by=test_run.triggered_by
    )

    # Execute in background
    background_tasks.add_task(service.execute_test_run, db_test_run.id)

    return db_test_run


@app.post("/test-runs/{test_run_id}/execute", response_model=TestRunResponse)
async def execute_test_run(
    test_run_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Execute an existing test run"""
    service = TestExecutionService(db)
    test_run = service.get_test_run(test_run_id)

    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    # Execute in background
    background_tasks.add_task(service.execute_test_run, test_run_id)

    return test_run


@app.get("/test-runs", response_model=List[TestRunResponse])
async def list_test_runs(
    test_suite_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all test runs"""
    service = TestExecutionService(db)
    return service.list_test_runs(test_suite_id=test_suite_id, skip=skip, limit=limit)


@app.get("/test-runs/{test_run_id}", response_model=TestRunResponse)
async def get_test_run(test_run_id: int, db: Session = Depends(get_db)):
    """Get test run by ID"""
    service = TestExecutionService(db)
    test_run = service.get_test_run(test_run_id)

    if not test_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    return test_run


@app.get("/test-runs/{test_run_id}/executions", response_model=List[TestExecutionResponse])
async def get_test_executions(
    test_run_id: int,
    db: Session = Depends(get_db)
):
    """Get all test executions for a test run"""
    executions = db.query(TestExecution).filter(
        TestExecution.test_run_id == test_run_id
    ).all()

    return executions


# Defect Endpoints

@app.post("/defects", response_model=DefectResponse, status_code=201)
async def create_defect(
    defect: DefectCreate,
    db: Session = Depends(get_db)
):
    """Create a new defect"""
    db_defect = Defect(**defect.dict())
    db.add(db_defect)
    db.commit()
    db.refresh(db_defect)
    return db_defect


@app.get("/defects", response_model=List[DefectResponse])
async def list_defects(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all defects with optional filters"""
    query = db.query(Defect)

    if status:
        query = query.filter(Defect.status == status)
    if severity:
        query = query.filter(Defect.severity == severity)

    return query.order_by(Defect.created_at.desc()).offset(skip).limit(limit).all()


@app.get("/defects/{defect_id}", response_model=DefectResponse)
async def get_defect(defect_id: int, db: Session = Depends(get_db)):
    """Get defect by ID"""
    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")
    return defect


@app.patch("/defects/{defect_id}", response_model=DefectResponse)
async def update_defect(
    defect_id: int,
    defect_update: DefectUpdate,
    db: Session = Depends(get_db)
):
    """Update defect"""
    defect = db.query(Defect).filter(Defect.id == defect_id).first()
    if not defect:
        raise HTTPException(status_code=404, detail="Defect not found")

    update_data = defect_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(defect, key, value)

    if defect_update.status == "resolved" and defect.resolved_at is None:
        defect.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(defect)
    return defect


# Analytics Endpoints

@app.get("/analytics", response_model=TestAnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Get testing analytics and statistics"""
    service = TestExecutionService(db)
    analytics = service.get_test_analytics()

    return TestAnalyticsResponse(
        total_test_cases=analytics["total_test_cases"],
        total_test_runs=analytics["total_test_runs"],
        total_defects=analytics["total_defects"],
        active_defects=analytics["active_defects"],
        test_pass_rate=analytics["test_pass_rate"],
        average_test_duration=analytics["average_test_duration"],
        tests_by_type=analytics["tests_by_type"],
        defects_by_severity=analytics["defects_by_severity"],
        recent_runs=[],  # Simplified for response
        top_failing_tests=analytics["top_failing_tests"]
    )


@app.get("/coverage/{test_run_id}", response_model=CoverageReportResponse)
async def get_coverage_report(
    test_run_id: int,
    db: Session = Depends(get_db)
):
    """Get coverage report for a test run"""
    report = db.query(CoverageReport).filter(
        CoverageReport.test_run_id == test_run_id
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Coverage report not found")

    return report


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
