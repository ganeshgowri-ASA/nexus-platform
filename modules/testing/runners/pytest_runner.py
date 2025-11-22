"""
Pytest test runner for unit and integration tests
"""
import pytest
import subprocess
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import coverage


class PytestRunner:
    """Runner for executing pytest tests"""

    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.coverage_enabled = True

    def run_tests(
        self,
        test_paths: Optional[List[str]] = None,
        markers: Optional[List[str]] = None,
        parallel: bool = False,
        max_workers: int = 4,
        coverage_enabled: bool = True,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Run pytest tests

        Args:
            test_paths: List of test file paths or directories
            markers: List of pytest markers to filter tests
            parallel: Whether to run tests in parallel
            max_workers: Number of parallel workers
            coverage_enabled: Whether to collect coverage
            verbose: Verbose output

        Returns:
            Dict with test results
        """
        start_time = datetime.utcnow()

        # Build pytest arguments
        args = []

        # Add test paths
        if test_paths:
            args.extend(test_paths)

        # Add markers
        if markers:
            for marker in markers:
                args.extend(["-m", marker])

        # Parallel execution
        if parallel:
            args.extend(["-n", str(max_workers)])

        # Verbosity
        if verbose:
            args.append("-v")

        # JSON report
        json_report_path = "/tmp/pytest_report.json"
        args.extend(["--json-report", f"--json-report-file={json_report_path}"])

        # Coverage
        if coverage_enabled:
            args.extend([
                "--cov=" + self.project_root,
                "--cov-report=html",
                "--cov-report=xml",
                "--cov-report=json",
                "--cov-report=term"
            ])

        # Run pytest
        result = pytest.main(args)

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Parse results
        test_results = self._parse_pytest_results(json_report_path)

        # Parse coverage
        coverage_data = None
        if coverage_enabled and os.path.exists("coverage.json"):
            coverage_data = self._parse_coverage_report("coverage.json")

        return {
            "status": "passed" if result == 0 else "failed",
            "exit_code": result,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": duration,
            "test_results": test_results,
            "coverage": coverage_data
        }

    def run_single_test(
        self,
        test_file: str,
        test_function: Optional[str] = None,
        test_class: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run a single test

        Args:
            test_file: Path to test file
            test_function: Test function name
            test_class: Test class name

        Returns:
            Dict with test result
        """
        test_path = test_file

        if test_class and test_function:
            test_path = f"{test_file}::{test_class}::{test_function}"
        elif test_function:
            test_path = f"{test_file}::{test_function}"

        return self.run_tests(test_paths=[test_path])

    def _parse_pytest_results(self, json_report_path: str) -> Dict[str, Any]:
        """Parse pytest JSON report"""
        if not os.path.exists(json_report_path):
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "error": 0,
                "tests": []
            }

        try:
            with open(json_report_path, "r") as f:
                data = json.load(f)

            summary = data.get("summary", {})
            tests = data.get("tests", [])

            return {
                "total": summary.get("total", 0),
                "passed": summary.get("passed", 0),
                "failed": summary.get("failed", 0),
                "skipped": summary.get("skipped", 0),
                "error": summary.get("error", 0),
                "tests": [
                    {
                        "name": test.get("nodeid", ""),
                        "outcome": test.get("outcome", ""),
                        "duration": test.get("duration", 0),
                        "error": test.get("call", {}).get("longrepr", "") if test.get("outcome") == "failed" else None
                    }
                    for test in tests
                ]
            }
        except Exception as e:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "error": 0,
                "tests": [],
                "parse_error": str(e)
            }

    def _parse_coverage_report(self, coverage_json_path: str) -> Dict[str, Any]:
        """Parse coverage JSON report"""
        try:
            with open(coverage_json_path, "r") as f:
                data = json.load(f)

            totals = data.get("totals", {})

            return {
                "line_coverage": totals.get("percent_covered", 0),
                "total_lines": totals.get("num_statements", 0),
                "covered_lines": totals.get("covered_lines", 0),
                "missed_lines": totals.get("missing_lines", 0),
                "files": {
                    file_path: {
                        "coverage": file_data["summary"]["percent_covered"],
                        "lines": file_data["summary"]["num_statements"],
                        "covered": file_data["summary"]["covered_lines"],
                        "missed": file_data["summary"]["missing_lines"]
                    }
                    for file_path, file_data in data.get("files", {}).items()
                }
            }
        except Exception as e:
            return {
                "error": str(e)
            }

    def discover_tests(self, test_dir: str = "tests") -> List[Dict[str, Any]]:
        """
        Discover all tests in a directory

        Args:
            test_dir: Directory to search for tests

        Returns:
            List of discovered tests
        """
        # Run pytest in collect-only mode
        result = subprocess.run(
            ["pytest", test_dir, "--collect-only", "-q"],
            capture_output=True,
            text=True
        )

        tests = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if "::" in line and line.startswith("<"):
                # Parse test identification
                parts = line.split("::")
                if len(parts) >= 2:
                    file_part = parts[0].replace("<", "").replace(">", "").strip()
                    test_name = parts[-1]

                    tests.append({
                        "file": file_part,
                        "name": test_name,
                        "full_path": line
                    })

        return tests
