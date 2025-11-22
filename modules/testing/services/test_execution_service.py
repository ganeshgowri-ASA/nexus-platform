"""
Test execution service - orchestrates test execution
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from modules.testing.models.database import (
    TestCase, TestSuite, TestRun, TestExecution,
    TestStatus, TestType, Defect, CoverageReport, PerformanceMetric
)
from modules.testing.runners.pytest_runner import PytestRunner
from modules.testing.runners.selenium_runner import SeleniumRunner


class TestExecutionService:
    """Service for orchestrating test execution"""

    def __init__(self, db: Session):
        self.db = db
        self.pytest_runner = PytestRunner()
        self.selenium_runner = SeleniumRunner()

    def create_test_run(
        self,
        test_suite_id: int,
        name: Optional[str] = None,
        environment: Optional[str] = None,
        build_number: Optional[str] = None,
        branch: Optional[str] = None,
        commit_hash: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        triggered_by: Optional[str] = None
    ) -> TestRun:
        """Create a new test run"""
        test_suite = self.db.query(TestSuite).filter(TestSuite.id == test_suite_id).first()

        if not test_suite:
            raise ValueError(f"Test suite {test_suite_id} not found")

        test_run = TestRun(
            test_suite_id=test_suite_id,
            name=name or f"Test Run {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            environment=environment or test_suite.environment,
            build_number=build_number,
            branch=branch,
            commit_hash=commit_hash,
            config=config,
            triggered_by=triggered_by,
            status=TestStatus.PENDING
        )

        self.db.add(test_run)
        self.db.commit()
        self.db.refresh(test_run)

        return test_run

    def execute_test_run(self, test_run_id: int) -> TestRun:
        """Execute a test run"""
        test_run = self.db.query(TestRun).filter(TestRun.id == test_run_id).first()

        if not test_run:
            raise ValueError(f"Test run {test_run_id} not found")

        try:
            # Update status
            test_run.status = TestStatus.RUNNING
            test_run.start_time = datetime.utcnow()
            self.db.commit()

            # Get test suite and test cases
            test_suite = self.db.query(TestSuite).filter(TestSuite.id == test_run.test_suite_id).first()
            test_case_ids = test_suite.test_case_ids or []

            test_cases = self.db.query(TestCase).filter(
                TestCase.id.in_(test_case_ids),
                TestCase.is_active == True
            ).all()

            test_run.total_tests = len(test_cases)
            self.db.commit()

            # Execute tests
            for test_case in test_cases:
                self._execute_test_case(test_run.id, test_case)

            # Update test run with results
            executions = self.db.query(TestExecution).filter(
                TestExecution.test_run_id == test_run_id
            ).all()

            test_run.passed_tests = sum(1 for e in executions if e.status == TestStatus.PASSED)
            test_run.failed_tests = sum(1 for e in executions if e.status == TestStatus.FAILED)
            test_run.skipped_tests = sum(1 for e in executions if e.status == TestStatus.SKIPPED)
            test_run.error_tests = sum(1 for e in executions if e.status == TestStatus.ERROR)

            test_run.status = TestStatus.PASSED if test_run.failed_tests == 0 and test_run.error_tests == 0 else TestStatus.FAILED
            test_run.end_time = datetime.utcnow()
            test_run.duration = (test_run.end_time - test_run.start_time).total_seconds()

            self.db.commit()
            self.db.refresh(test_run)

        except Exception as e:
            test_run.status = TestStatus.ERROR
            test_run.end_time = datetime.utcnow()
            if test_run.start_time:
                test_run.duration = (test_run.end_time - test_run.start_time).total_seconds()
            self.db.commit()
            raise

        return test_run

    def _execute_test_case(self, test_run_id: int, test_case: TestCase) -> TestExecution:
        """Execute a single test case"""
        execution = TestExecution(
            test_run_id=test_run_id,
            test_case_id=test_case.id,
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow()
        )

        self.db.add(execution)
        self.db.commit()

        try:
            if test_case.test_type == TestType.E2E:
                # Execute E2E test with Selenium
                result = self._execute_e2e_test(test_case)
            else:
                # Execute unit/integration test with pytest
                result = self._execute_pytest_test(test_case)

            # Update execution with results
            execution.status = TestStatus(result["status"])
            execution.end_time = datetime.utcnow()
            execution.duration = result.get("duration", 0)
            execution.actual_result = result.get("actual_result")
            execution.error_message = result.get("error_message")
            execution.stack_trace = result.get("stack_trace")
            execution.logs = result.get("logs")
            execution.screenshots = result.get("screenshots", [])

            self.db.commit()
            self.db.refresh(execution)

        except Exception as e:
            execution.status = TestStatus.ERROR
            execution.error_message = str(e)
            execution.end_time = datetime.utcnow()
            self.db.commit()

        return execution

    def _execute_pytest_test(self, test_case: TestCase) -> Dict[str, Any]:
        """Execute pytest test"""
        try:
            result = self.pytest_runner.run_single_test(
                test_file=test_case.test_file,
                test_function=test_case.test_function,
                test_class=test_case.test_class
            )

            if result["status"] == "passed":
                return {
                    "status": "passed",
                    "duration": result.get("duration", 0),
                    "actual_result": "Test passed successfully"
                }
            else:
                test_results = result.get("test_results", {})
                tests = test_results.get("tests", [])
                error_msg = tests[0].get("error") if tests else "Test failed"

                return {
                    "status": "failed",
                    "duration": result.get("duration", 0),
                    "error_message": error_msg,
                    "stack_trace": error_msg
                }

        except Exception as e:
            return {
                "status": "error",
                "duration": 0,
                "error_message": str(e)
            }

    def _execute_e2e_test(self, test_case: TestCase) -> Dict[str, Any]:
        """Execute E2E test with Selenium"""
        try:
            steps = test_case.steps or []

            if not steps:
                return {
                    "status": "skipped",
                    "duration": 0,
                    "actual_result": "No test steps defined"
                }

            result = self.selenium_runner.run_test_scenario(
                test_name=test_case.name,
                steps=steps
            )

            return {
                "status": result["status"],
                "duration": result.get("duration", 0),
                "actual_result": f"Completed {len(result['steps'])} steps",
                "error_message": result.get("error"),
                "screenshots": result.get("screenshots", []),
                "logs": str(result.get("steps", []))
            }

        except Exception as e:
            return {
                "status": "error",
                "duration": 0,
                "error_message": str(e)
            }

    def get_test_run(self, test_run_id: int) -> Optional[TestRun]:
        """Get test run by ID"""
        return self.db.query(TestRun).filter(TestRun.id == test_run_id).first()

    def list_test_runs(
        self,
        test_suite_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TestRun]:
        """List test runs"""
        query = self.db.query(TestRun)

        if test_suite_id:
            query = query.filter(TestRun.test_suite_id == test_suite_id)

        return query.order_by(TestRun.created_at.desc()).offset(skip).limit(limit).all()

    def get_test_analytics(self) -> Dict[str, Any]:
        """Get test analytics"""
        total_test_cases = self.db.query(func.count(TestCase.id)).scalar()
        total_test_runs = self.db.query(func.count(TestRun.id)).scalar()
        total_defects = self.db.query(func.count(Defect.id)).scalar()
        active_defects = self.db.query(func.count(Defect.id)).filter(
            Defect.status.in_(["open", "in_progress"])
        ).scalar()

        # Test pass rate
        completed_runs = self.db.query(TestRun).filter(
            TestRun.status.in_([TestStatus.PASSED, TestStatus.FAILED])
        ).all()

        total_tests = sum(run.total_tests for run in completed_runs)
        passed_tests = sum(run.passed_tests for run in completed_runs)
        test_pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Average test duration
        avg_duration = self.db.query(func.avg(TestRun.duration)).filter(
            TestRun.duration.isnot(None)
        ).scalar() or 0

        # Tests by type
        tests_by_type = dict(
            self.db.query(
                TestCase.test_type,
                func.count(TestCase.id)
            ).group_by(TestCase.test_type).all()
        )

        # Defects by severity
        defects_by_severity = dict(
            self.db.query(
                Defect.severity,
                func.count(Defect.id)
            ).group_by(Defect.severity).all()
        )

        # Recent runs
        recent_runs = self.db.query(TestRun).order_by(
            TestRun.created_at.desc()
        ).limit(10).all()

        # Top failing tests
        top_failing = self.db.query(
            TestExecution.test_case_id,
            func.count(TestExecution.id).label('fail_count')
        ).filter(
            TestExecution.status == TestStatus.FAILED
        ).group_by(TestExecution.test_case_id).order_by(
            func.count(TestExecution.id).desc()
        ).limit(10).all()

        top_failing_tests = []
        for test_case_id, fail_count in top_failing:
            test_case = self.db.query(TestCase).filter(TestCase.id == test_case_id).first()
            if test_case:
                top_failing_tests.append({
                    "test_id": test_case.id,
                    "test_name": test_case.name,
                    "fail_count": fail_count
                })

        return {
            "total_test_cases": total_test_cases,
            "total_test_runs": total_test_runs,
            "total_defects": total_defects,
            "active_defects": active_defects,
            "test_pass_rate": test_pass_rate,
            "average_test_duration": float(avg_duration),
            "tests_by_type": {str(k): v for k, v in tests_by_type.items()},
            "defects_by_severity": {str(k): v for k, v in defects_by_severity.items()},
            "recent_runs": recent_runs,
            "top_failing_tests": top_failing_tests
        }

    def create_defect_from_failure(
        self,
        test_execution_id: int,
        title: Optional[str] = None,
        severity: str = "medium",
        priority: str = "medium"
    ) -> Defect:
        """Create a defect from a failed test execution"""
        execution = self.db.query(TestExecution).filter(
            TestExecution.id == test_execution_id
        ).first()

        if not execution:
            raise ValueError(f"Test execution {test_execution_id} not found")

        test_case = execution.test_case

        defect = Defect(
            title=title or f"Test Failure: {test_case.name}",
            description=f"Test case '{test_case.name}' failed.\n\nError: {execution.error_message}",
            severity=severity,
            priority=priority,
            test_execution_id=test_execution_id,
            steps_to_reproduce=test_case.preconditions or "",
            expected_behavior=test_case.expected_result or "",
            actual_behavior=execution.actual_result or execution.error_message,
            screenshots=execution.screenshots,
            logs=execution.logs
        )

        self.db.add(defect)
        self.db.commit()
        self.db.refresh(defect)

        return defect
