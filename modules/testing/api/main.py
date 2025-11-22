"""
FastAPI application for Testing & QA module
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from ..models.database import (
    Base, TestSuite, TestCase, TestRun, TestExecution, Defect, CoverageReport,
    TestStatus, TestType, DefectSeverity, DefectStatus
)
from ..models.schemas import (
    TestSuiteCreate, TestSuiteResponse, TestCaseCreate, TestCaseResponse,
    TestRunCreate, TestRunResponse, TestExecutionResponse, DefectCreate,
    DefectResponse, CoverageReportResponse, TestAnalyticsResponse
)
from ..config.settings import settings
from ..services.test_executor import TestExecutor

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="NEXUS Testing & QA API - Automated testing, test management, CI/CD integration"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "service": "NEXUS Testing & QA API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}


# Test Suites
@app.post("/suites", response_model=TestSuiteResponse)
def create_test_suite(suite: TestSuiteCreate, db: Session = Depends(get_db)):
    """Create a new test suite"""
    try:
        db_suite = TestSuite(**suite.dict())
        db.add(db_suite)
        db.commit()
        db.refresh(db_suite)
        return TestSuiteResponse.from_orm(db_suite)
    except Exception as e:
        logger.error(f"Error creating test suite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/suites", response_model=List[TestSuiteResponse])
def get_test_suites(
    project_id: Optional[int] = None,
    test_type: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Get list of test suites"""
    try:
        query = db.query(TestSuite).filter(TestSuite.is_active == is_active)

        if project_id:
            query = query.filter(TestSuite.project_id == project_id)
        if test_type:
            query = query.filter(TestSuite.test_type == TestType[test_type.upper()])

        suites = query.order_by(TestSuite.created_at.desc()).all()
        return [TestSuiteResponse.from_orm(s) for s in suites]

    except Exception as e:
        logger.error(f"Error getting test suites: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/suites/{suite_id}", response_model=TestSuiteResponse)
def get_test_suite(suite_id: int, db: Session = Depends(get_db)):
    """Get test suite by ID"""
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return TestSuiteResponse.from_orm(suite)


# Test Cases
@app.post("/cases", response_model=TestCaseResponse)
def create_test_case(case: TestCaseCreate, db: Session = Depends(get_db)):
    """Create a new test case"""
    try:
        db_case = TestCase(**case.dict())
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        return TestCaseResponse.from_orm(db_case)
    except Exception as e:
        logger.error(f"Error creating test case: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cases", response_model=List[TestCaseResponse])
def get_test_cases(
    suite_id: Optional[int] = None,
    test_type: Optional[str] = None,
    status: Optional[str] = None,
    is_active: bool = True,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of test cases"""
    try:
        query = db.query(TestCase).filter(TestCase.is_active == is_active)

        if suite_id:
            query = query.filter(TestCase.suite_id == suite_id)
        if test_type:
            query = query.filter(TestCase.test_type == TestType[test_type.upper()])
        if status:
            query = query.filter(TestCase.last_status == TestStatus[status.upper()])

        cases = query.order_by(TestCase.created_at.desc()).limit(limit).all()
        return [TestCaseResponse.from_orm(c) for c in cases]

    except Exception as e:
        logger.error(f"Error getting test cases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cases/{case_id}", response_model=TestCaseResponse)
def get_test_case(case_id: int, db: Session = Depends(get_db)):
    """Get test case by ID"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return TestCaseResponse.from_orm(case)


# Test Runs
@app.post("/runs", response_model=TestRunResponse)
def create_test_run(
    run: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create and execute a test run"""
    try:
        # Create test run
        db_run = TestRun(**run.dict())
        db.add(db_run)
        db.commit()
        db.refresh(db_run)

        # Queue execution in background
        background_tasks.add_task(execute_test_run, db_run.id)

        return TestRunResponse.from_orm(db_run)

    except Exception as e:
        logger.error(f"Error creating test run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs", response_model=List[TestRunResponse])
def get_test_runs(
    suite_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get list of test runs"""
    try:
        query = db.query(TestRun)

        if suite_id:
            query = query.filter(TestRun.suite_id == suite_id)
        if status:
            query = query.filter(TestRun.status == TestStatus[status.upper()])

        runs = query.order_by(TestRun.created_at.desc()).limit(limit).all()
        return [TestRunResponse.from_orm(r) for r in runs]

    except Exception as e:
        logger.error(f"Error getting test runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs/{run_id}", response_model=TestRunResponse)
def get_test_run(run_id: int, db: Session = Depends(get_db)):
    """Get test run by ID"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return TestRunResponse.from_orm(run)


@app.get("/runs/{run_id}/executions", response_model=List[TestExecutionResponse])
def get_test_executions(run_id: int, db: Session = Depends(get_db)):
    """Get executions for a test run"""
    executions = db.query(TestExecution).filter(TestExecution.test_run_id == run_id).all()
    return [TestExecutionResponse.from_orm(e) for e in executions]


# Defects
@app.post("/defects", response_model=DefectResponse)
def create_defect(defect: DefectCreate, db: Session = Depends(get_db)):
    """Create a new defect"""
    try:
        db_defect = Defect(**defect.dict())
        db.add(db_defect)
        db.commit()
        db.refresh(db_defect)
        return DefectResponse.from_orm(db_defect)
    except Exception as e:
        logger.error(f"Error creating defect: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/defects", response_model=List[DefectResponse])
def get_defects(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of defects"""
    try:
        query = db.query(Defect)

        if severity:
            query = query.filter(Defect.severity == DefectSeverity[severity.upper()])
        if status:
            query = query.filter(Defect.status == DefectStatus[status.upper()])

        defects = query.order_by(Defect.created_at.desc()).limit(limit).all()
        return [DefectResponse.from_orm(d) for d in defects]

    except Exception as e:
        logger.error(f"Error getting defects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/defects/{defect_id}/status")
def update_defect_status(
    defect_id: int,
    status: str,
    resolution_notes: Optional[str] = None,
    resolved_by: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Update defect status"""
    try:
        defect = db.query(Defect).filter(Defect.id == defect_id).first()
        if not defect:
            raise HTTPException(status_code=404, detail="Defect not found")

        defect.status = DefectStatus[status.upper()]
        if resolution_notes:
            defect.resolution_notes = resolution_notes
        if status.upper() == "RESOLVED":
            defect.resolved_at = datetime.utcnow()
            defect.resolved_by = resolved_by

        db.commit()
        return {"message": "Defect status updated"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating defect status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics
@app.get("/analytics", response_model=TestAnalyticsResponse)
def get_analytics(
    days: int = 30,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get testing analytics"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # Total counts
        total_test_cases = db.query(func.count(TestCase.id)).filter(TestCase.is_active == True).scalar()
        total_test_runs = db.query(func.count(TestRun.id)).filter(TestRun.created_at >= start_date).scalar()
        total_defects = db.query(func.count(Defect.id)).filter(Defect.created_at >= start_date).scalar()

        # Test pass rate
        total_executions = db.query(func.count(TestExecution.id)).join(TestRun).filter(
            TestRun.created_at >= start_date
        ).scalar()

        passed_executions = db.query(func.count(TestExecution.id)).join(TestRun).filter(
            TestRun.created_at >= start_date,
            TestExecution.status == TestStatus.PASSED
        ).scalar()

        test_pass_rate = (passed_executions / total_executions * 100) if total_executions > 0 else 0

        # Average execution time
        avg_time = db.query(func.avg(TestExecution.duration_seconds)).join(TestRun).filter(
            TestRun.created_at >= start_date
        ).scalar()

        # Tests by type
        tests_by_type = {}
        for test_type in TestType:
            count = db.query(func.count(TestCase.id)).filter(
                TestCase.test_type == test_type,
                TestCase.is_active == True
            ).scalar()
            tests_by_type[test_type.value] = count

        # Tests by status
        tests_by_status = {}
        for status in TestStatus:
            count = db.query(func.count(TestCase.id)).filter(
                TestCase.last_status == status,
                TestCase.is_active == True
            ).scalar()
            tests_by_status[status.value] = count

        # Defects by severity
        defects_by_severity = {}
        for severity in DefectSeverity:
            count = db.query(func.count(Defect.id)).filter(
                Defect.severity == severity,
                Defect.created_at >= start_date
            ).scalar()
            defects_by_severity[severity.value] = count

        # Recent failures
        recent_failures = db.query(TestCase).filter(
            TestCase.last_status.in_([TestStatus.FAILED, TestStatus.ERROR])
        ).order_by(TestCase.last_run_at.desc()).limit(10).all()

        return TestAnalyticsResponse(
            total_test_cases=total_test_cases,
            total_test_runs=total_test_runs,
            total_defects=total_defects,
            test_pass_rate=test_pass_rate,
            average_execution_time=avg_time,
            tests_by_type=tests_by_type,
            tests_by_status=tests_by_status,
            defects_by_severity=defects_by_severity,
            recent_failures=[TestCaseResponse.from_orm(c) for c in recent_failures]
        )

    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions
def execute_test_run(run_id: int):
    """Execute test run in background"""
    db = SessionLocal()
    try:
        run = db.query(TestRun).filter(TestRun.id == run_id).first()
        if not run:
            return

        # Update status
        run.status = TestStatus.RUNNING
        run.started_at = datetime.utcnow()
        db.commit()

        # Get test cases for suite
        test_cases = db.query(TestCase).filter(
            TestCase.suite_id == run.suite_id,
            TestCase.is_active == True
        ).all()

        executor = TestExecutor()

        passed = 0
        failed = 0
        skipped = 0
        errors = 0

        # Execute each test case
        for test_case in test_cases:
            result = executor.execute_test_case({
                "id": test_case.id,
                "test_type": test_case.test_type.value,
                "file_path": test_case.file_path,
                "function_name": test_case.function_name,
                "code": test_case.code,
                "test_data": test_case.test_data
            })

            # Create execution record
            execution = TestExecution(
                test_run_id=run.id,
                test_case_id=test_case.id,
                status=TestStatus[result["status"].upper()],
                duration_seconds=result.get("duration_seconds"),
                output=result.get("output"),
                error_message=result.get("error_message"),
                stack_trace=result.get("stack_trace"),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(execution)

            # Update test case status
            test_case.last_status = TestStatus[result["status"].upper()]
            test_case.last_run_at = datetime.utcnow()

            # Count results
            if result["status"] == "passed":
                passed += 1
            elif result["status"] == "failed":
                failed += 1
            elif result["status"] == "skipped":
                skipped += 1
            else:
                errors += 1

        # Update run summary
        run.status = TestStatus.COMPLETED if failed == 0 and errors == 0 else TestStatus.FAILED
        run.total_tests = len(test_cases)
        run.passed_tests = passed
        run.failed_tests = failed
        run.skipped_tests = skipped
        run.error_tests = errors
        run.completed_at = datetime.utcnow()
        run.duration_seconds = (run.completed_at - run.started_at).total_seconds()

        db.commit()

    except Exception as e:
        logger.error(f"Error executing test run: {e}")
        if run:
            run.status = TestStatus.ERROR
            db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
