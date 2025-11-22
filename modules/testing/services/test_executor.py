"""
Test execution service for running different types of tests
"""
import subprocess
import json
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import pytest
import sys
from io import StringIO

logger = logging.getLogger(__name__)


class TestExecutor:
    """Base test executor"""

    def __init__(self, test_results_dir: str = "./test_results"):
        self.test_results_dir = Path(test_results_dir)
        self.test_results_dir.mkdir(parents=True, exist_ok=True)

    def execute_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test case"""
        start_time = time.time()

        try:
            result = {
                "test_case_id": test_case["id"],
                "status": "passed",
                "duration_seconds": 0,
                "output": "",
                "error_message": None,
                "stack_trace": None
            }

            test_type = test_case.get("test_type", "unit")

            if test_type == "unit":
                result = self._execute_unit_test(test_case)
            elif test_type == "integration":
                result = self._execute_integration_test(test_case)
            elif test_type == "e2e":
                result = self._execute_e2e_test(test_case)
            elif test_type == "performance":
                result = self._execute_performance_test(test_case)
            elif test_type == "security":
                result = self._execute_security_test(test_case)

            result["duration_seconds"] = time.time() - start_time

            return result

        except Exception as e:
            logger.error(f"Error executing test case: {e}")
            return {
                "test_case_id": test_case["id"],
                "status": "error",
                "duration_seconds": time.time() - start_time,
                "error_message": str(e),
                "stack_trace": None
            }

    def _execute_unit_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute unit test using pytest"""
        try:
            if test_case.get("file_path"):
                # Run pytest on specific file
                test_file = test_case["file_path"]
                function_name = test_case.get("function_name")

                test_path = f"{test_file}::{function_name}" if function_name else test_file

                # Capture output
                old_stdout = sys.stdout
                sys.stdout = captured_output = StringIO()

                # Run pytest
                result_code = pytest.main([
                    test_path,
                    "-v",
                    "--tb=short",
                    f"--json-report",
                    f"--json-report-file={self.test_results_dir}/result.json"
                ])

                sys.stdout = old_stdout
                output = captured_output.getvalue()

                # Parse result
                if result_code == 0:
                    return {
                        "status": "passed",
                        "output": output,
                        "error_message": None
                    }
                else:
                    return {
                        "status": "failed",
                        "output": output,
                        "error_message": "Test failed"
                    }

            elif test_case.get("code"):
                # Execute inline code
                return self._execute_inline_code(test_case["code"])

            else:
                return {
                    "status": "error",
                    "error_message": "No test file or code provided"
                }

        except Exception as e:
            logger.error(f"Unit test execution error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def _execute_integration_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute integration test"""
        # Similar to unit test but may involve API calls, database operations, etc.
        return self._execute_unit_test(test_case)

    def _execute_e2e_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute E2E test using Selenium"""
        try:
            from .selenium_runner import SeleniumRunner

            runner = SeleniumRunner()
            result = runner.run_test(test_case)
            return result

        except Exception as e:
            logger.error(f"E2E test execution error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def _execute_performance_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute performance test"""
        try:
            from .performance_tester import PerformanceTester

            tester = PerformanceTester()
            result = tester.run_test(test_case)
            return result

        except Exception as e:
            logger.error(f"Performance test execution error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def _execute_security_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute security test"""
        try:
            from .security_scanner import SecurityScanner

            scanner = SecurityScanner()
            result = scanner.run_scan(test_case)
            return result

        except Exception as e:
            logger.error(f"Security test execution error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def _execute_inline_code(self, code: str) -> Dict[str, Any]:
        """Execute inline test code"""
        try:
            # Create a temporary test file
            test_file = self.test_results_dir / "temp_test.py"

            with open(test_file, "w") as f:
                f.write(code)

            # Run pytest
            result_code = pytest.main([
                str(test_file),
                "-v",
                "--tb=short"
            ])

            # Clean up
            test_file.unlink()

            if result_code == 0:
                return {
                    "status": "passed",
                    "output": "Test passed"
                }
            else:
                return {
                    "status": "failed",
                    "output": "Test failed"
                }

        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }

    def run_test_suite(self, test_suite_path: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run entire test suite"""
        try:
            args = [
                test_suite_path,
                "-v",
                "--tb=short",
                f"--json-report",
                f"--json-report-file={self.test_results_dir}/suite_result.json",
                f"--html={self.test_results_dir}/report.html",
                "--self-contained-html"
            ]

            # Add filters
            if filters:
                if filters.get("markers"):
                    args.extend(["-m", filters["markers"]])
                if filters.get("keywords"):
                    args.extend(["-k", filters["keywords"]])

            # Run pytest
            result_code = pytest.main(args)

            # Read JSON report
            report_file = self.test_results_dir / "suite_result.json"
            if report_file.exists():
                with open(report_file) as f:
                    report_data = json.load(f)

                return {
                    "status": "completed" if result_code == 0 else "failed",
                    "summary": report_data.get("summary", {}),
                    "report_path": str(self.test_results_dir / "report.html")
                }

            return {
                "status": "completed" if result_code == 0 else "failed",
                "report_path": str(self.test_results_dir / "report.html")
            }

        except Exception as e:
            logger.error(f"Test suite execution error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def generate_coverage_report(self, source_dir: str) -> Dict[str, Any]:
        """Generate code coverage report"""
        try:
            # Run pytest with coverage
            result = subprocess.run([
                "pytest",
                "--cov=" + source_dir,
                "--cov-report=html",
                "--cov-report=json",
                f"--cov-report=term"
            ], capture_output=True, text=True)

            # Parse coverage.json
            coverage_file = Path("coverage.json")
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)

                return {
                    "line_coverage": coverage_data.get("totals", {}).get("percent_covered"),
                    "total_lines": coverage_data.get("totals", {}).get("num_statements"),
                    "covered_lines": coverage_data.get("totals", {}).get("covered_lines"),
                    "report_path": "htmlcov/index.html"
                }

            return {
                "error": "Coverage report not generated"
            }

        except Exception as e:
            logger.error(f"Coverage report generation error: {e}")
            return {
                "error": str(e)
            }
