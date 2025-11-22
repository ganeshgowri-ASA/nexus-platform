"""
Core Test Framework Module

Provides TestRunner, TestSuiteManager, and TestExecutor for running tests.
"""

import asyncio
import logging
import time
import traceback
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import pytest
import sys
import os
from pathlib import Path

from modules.testing_qa.models import TestStatus, TestType
from modules.testing_qa.schemas import (
    TestExecutionRequest,
    TestRunResponse,
    TestExecutionResponse,
)

logger = logging.getLogger(__name__)


class TestExecutor:
    """
    Test executor for running individual tests.

    Handles test execution, timeout management, retries, and result collection.
    """

    def __init__(
        self,
        timeout_seconds: int = 300,
        max_retries: int = 0,
        capture_output: bool = True,
    ):
        """
        Initialize test executor.

        Args:
            timeout_seconds: Maximum execution time per test
            max_retries: Maximum number of retries for failed tests
            capture_output: Whether to capture stdout/stderr
        """
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.capture_output = capture_output
        self.logger = logging.getLogger(__name__)

    async def execute_test(
        self,
        test_function: Callable,
        test_params: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single test function.

        Args:
            test_function: The test function to execute
            test_params: Parameters to pass to the test function

        Returns:
            Execution result dictionary
        """
        start_time = time.time()
        result = {
            "status": TestStatus.PENDING,
            "execution_time_ms": 0.0,
            "error_message": None,
            "stack_trace": None,
            "stdout": None,
            "stderr": None,
            "assertions": [],
        }

        try:
            self.logger.info(f"Executing test: {test_function.__name__}")

            # Execute test with timeout
            if asyncio.iscoroutinefunction(test_function):
                await asyncio.wait_for(
                    test_function(**(test_params or {})),
                    timeout=self.timeout_seconds,
                )
            else:
                test_function(**(test_params or {}))

            result["status"] = TestStatus.PASSED
            self.logger.info(f"Test passed: {test_function.__name__}")

        except AssertionError as e:
            result["status"] = TestStatus.FAILED
            result["error_message"] = str(e)
            result["stack_trace"] = traceback.format_exc()
            self.logger.warning(f"Test failed: {test_function.__name__} - {e}")

        except asyncio.TimeoutError:
            result["status"] = TestStatus.ERROR
            result["error_message"] = f"Test timed out after {self.timeout_seconds}s"
            result["stack_trace"] = traceback.format_exc()
            self.logger.error(f"Test timed out: {test_function.__name__}")

        except Exception as e:
            result["status"] = TestStatus.ERROR
            result["error_message"] = str(e)
            result["stack_trace"] = traceback.format_exc()
            self.logger.error(f"Test error: {test_function.__name__} - {e}")

        finally:
            execution_time = (time.time() - start_time) * 1000
            result["execution_time_ms"] = execution_time

        return result

    async def execute_with_retry(
        self,
        test_function: Callable,
        test_params: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Execute test with retry logic.

        Args:
            test_function: The test function to execute
            test_params: Parameters to pass to the test function

        Returns:
            Execution result dictionary
        """
        result = None
        attempts = []

        for attempt in range(self.max_retries + 1):
            self.logger.info(
                f"Test attempt {attempt + 1}/{self.max_retries + 1}: {test_function.__name__}"
            )

            result = await self.execute_test(test_function, test_params)
            attempts.append(result.copy())

            if result["status"] == TestStatus.PASSED:
                break

            if attempt < self.max_retries:
                self.logger.info(f"Retrying test: {test_function.__name__}")
                await asyncio.sleep(1)  # Brief delay between retries

        # Check for flakiness
        if len(attempts) > 1:
            statuses = [a["status"] for a in attempts]
            if TestStatus.PASSED in statuses and TestStatus.FAILED in statuses:
                result["is_flaky"] = True
                self.logger.warning(f"Flaky test detected: {test_function.__name__}")

        result["retry_count"] = len(attempts) - 1
        return result


class TestSuiteManager:
    """
    Test suite manager for organizing and managing test collections.

    Handles test discovery, suite creation, and test organization.
    """

    def __init__(self, base_path: str = None):
        """
        Initialize test suite manager.

        Args:
            base_path: Base directory for test discovery
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.logger = logging.getLogger(__name__)
        self.suites: Dict[str, Dict[str, Any]] = {}

    def discover_tests(
        self,
        pattern: str = "test_*.py",
        test_type: TestType = TestType.UNIT,
    ) -> List[Dict[str, Any]]:
        """
        Discover tests in the base path.

        Args:
            pattern: File pattern for test discovery
            test_type: Type of tests to discover

        Returns:
            List of discovered test files
        """
        self.logger.info(f"Discovering tests with pattern: {pattern}")

        discovered_tests = []

        try:
            for test_file in self.base_path.rglob(pattern):
                if test_file.is_file():
                    discovered_tests.append(
                        {
                            "file_path": str(test_file),
                            "name": test_file.stem,
                            "test_type": test_type,
                            "relative_path": str(test_file.relative_to(self.base_path)),
                        }
                    )

            self.logger.info(f"Discovered {len(discovered_tests)} test files")

        except Exception as e:
            self.logger.error(f"Error discovering tests: {e}")

        return discovered_tests

    def create_suite(
        self,
        name: str,
        test_files: List[str],
        test_type: TestType,
        configuration: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Create a test suite.

        Args:
            name: Suite name
            test_files: List of test file paths
            test_type: Type of tests in suite
            configuration: Suite configuration

        Returns:
            Created suite information
        """
        suite = {
            "name": name,
            "test_files": test_files,
            "test_type": test_type,
            "configuration": configuration or {},
            "created_at": datetime.utcnow(),
        }

        self.suites[name] = suite
        self.logger.info(f"Created test suite: {name} with {len(test_files)} files")

        return suite

    def get_suite(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a test suite by name.

        Args:
            name: Suite name

        Returns:
            Suite information or None
        """
        return self.suites.get(name)

    def list_suites(self) -> List[Dict[str, Any]]:
        """
        List all test suites.

        Returns:
            List of all suites
        """
        return list(self.suites.values())


class TestRunner:
    """
    Main test runner for executing test suites.

    Supports parallel execution, retry logic, and comprehensive result tracking.
    """

    def __init__(
        self,
        parallel: bool = False,
        max_workers: int = 4,
        timeout_seconds: int = 300,
        max_retries: int = 0,
    ):
        """
        Initialize test runner.

        Args:
            parallel: Enable parallel test execution
            max_workers: Maximum parallel workers
            timeout_seconds: Test execution timeout
            max_retries: Maximum retries for failed tests
        """
        self.parallel = parallel
        self.max_workers = max_workers
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        self.executor = TestExecutor(timeout_seconds, max_retries)

    async def run_pytest_suite(
        self,
        test_paths: List[str],
        pytest_args: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Run tests using pytest.

        Args:
            test_paths: List of test paths to execute
            pytest_args: Additional pytest arguments

        Returns:
            Test execution results
        """
        self.logger.info(f"Running pytest suite with {len(test_paths)} paths")

        start_time = time.time()
        args = pytest_args or []

        # Add default arguments
        args.extend(
            [
                "-v",  # Verbose
                "--tb=short",  # Short traceback
                f"--timeout={self.timeout_seconds}",  # Timeout
                "--junit-xml=test-results.xml",  # JUnit XML report
            ]
        )

        # Add test paths
        args.extend(test_paths)

        try:
            # Run pytest
            exit_code = pytest.main(args)

            execution_time = (time.time() - start_time) * 1000

            result = {
                "status": (
                    TestStatus.PASSED if exit_code == 0 else TestStatus.FAILED
                ),
                "exit_code": exit_code,
                "execution_time_ms": execution_time,
                "test_paths": test_paths,
                "pytest_args": args,
            }

            self.logger.info(
                f"Pytest suite completed with exit code {exit_code} in {execution_time:.2f}ms"
            )

            return result

        except Exception as e:
            self.logger.error(f"Error running pytest suite: {e}")
            return {
                "status": TestStatus.ERROR,
                "error_message": str(e),
                "stack_trace": traceback.format_exc(),
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

    async def run_test_suite(
        self,
        suite_name: str,
        test_suite_manager: TestSuiteManager,
        configuration: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Run a complete test suite.

        Args:
            suite_name: Name of the suite to run
            test_suite_manager: Test suite manager instance
            configuration: Suite execution configuration

        Returns:
            Comprehensive test results
        """
        self.logger.info(f"Running test suite: {suite_name}")

        suite = test_suite_manager.get_suite(suite_name)
        if not suite:
            raise ValueError(f"Test suite not found: {suite_name}")

        start_time = time.time()
        config = configuration or suite.get("configuration", {})

        # Get test files
        test_files = suite.get("test_files", [])

        # Run tests
        result = await self.run_pytest_suite(
            test_files, config.get("pytest_args", [])
        )

        # Add suite metadata
        result["suite_name"] = suite_name
        result["test_type"] = suite.get("test_type")
        result["total_files"] = len(test_files)
        result["started_at"] = datetime.utcnow()

        execution_time = (time.time() - start_time) * 1000
        result["total_execution_time_ms"] = execution_time

        self.logger.info(
            f"Test suite '{suite_name}' completed in {execution_time:.2f}ms"
        )

        return result

    async def run_parallel_tests(
        self,
        test_paths: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Run tests in parallel.

        Args:
            test_paths: List of test paths

        Returns:
            List of test results
        """
        self.logger.info(f"Running {len(test_paths)} tests in parallel")

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(self._run_single_test, path): path for path in test_paths
            }

            for future in as_completed(futures):
                path = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error running test {path}: {e}")
                    results.append(
                        {
                            "test_path": path,
                            "status": TestStatus.ERROR,
                            "error_message": str(e),
                        }
                    )

        self.logger.info(f"Completed {len(results)} parallel tests")
        return results

    def _run_single_test(self, test_path: str) -> Dict[str, Any]:
        """
        Run a single test file.

        Args:
            test_path: Path to test file

        Returns:
            Test result
        """
        start_time = time.time()

        try:
            exit_code = pytest.main(["-v", test_path])

            return {
                "test_path": test_path,
                "status": (
                    TestStatus.PASSED if exit_code == 0 else TestStatus.FAILED
                ),
                "exit_code": exit_code,
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

        except Exception as e:
            return {
                "test_path": test_path,
                "status": TestStatus.ERROR,
                "error_message": str(e),
                "execution_time_ms": (time.time() - start_time) * 1000,
            }

    def generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics from test results.

        Args:
            results: List of test results

        Returns:
            Summary statistics
        """
        total = len(results)
        passed = sum(1 for r in results if r.get("status") == TestStatus.PASSED)
        failed = sum(1 for r in results if r.get("status") == TestStatus.FAILED)
        error = sum(1 for r in results if r.get("status") == TestStatus.ERROR)
        skipped = sum(1 for r in results if r.get("status") == TestStatus.SKIPPED)

        total_time = sum(r.get("execution_time_ms", 0) for r in results)
        avg_time = total_time / total if total > 0 else 0

        summary = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "error": error,
            "skipped": skipped,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "total_execution_time_ms": total_time,
            "average_execution_time_ms": avg_time,
        }

        return summary
