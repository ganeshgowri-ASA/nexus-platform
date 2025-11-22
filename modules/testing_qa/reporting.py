"""
Test Reporting Module

Provides TestReporter, HTMLReporter, JUnitReporter, and AllureReporter for test reporting.
"""

import logging
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class JUnitReporter:
    """
    JUnit XML test reporter.

    Generates JUnit-compatible XML reports for CI/CD integration.
    """

    def __init__(self):
        """Initialize JUnit reporter."""
        self.logger = logging.getLogger(__name__)

    def generate_report(
        self,
        test_results: List[Dict[str, Any]],
        output_file: str = "junit-report.xml",
    ) -> str:
        """
        Generate JUnit XML report.

        Args:
            test_results: List of test results
            output_file: Output file path

        Returns:
            Output file path
        """
        # Create root testsuite element
        total_tests = len(test_results)
        failures = sum(1 for r in test_results if r.get("status") == "failed")
        errors = sum(1 for r in test_results if r.get("status") == "error")
        skipped = sum(1 for r in test_results if r.get("status") == "skipped")
        time_total = sum(r.get("execution_time_ms", 0) for r in test_results) / 1000

        testsuite = ET.Element("testsuite", {
            "name": "TestSuite",
            "tests": str(total_tests),
            "failures": str(failures),
            "errors": str(errors),
            "skipped": str(skipped),
            "time": f"{time_total:.3f}",
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Add testcase elements
        for result in test_results:
            testcase = ET.SubElement(testsuite, "testcase", {
                "name": result.get("name", "unknown"),
                "classname": result.get("class", "TestClass"),
                "time": f"{result.get('execution_time_ms', 0) / 1000:.3f}",
            })

            status = result.get("status")

            if status == "failed":
                failure = ET.SubElement(testcase, "failure", {
                    "message": result.get("error_message", "Test failed"),
                })
                failure.text = result.get("stack_trace", "")

            elif status == "error":
                error = ET.SubElement(testcase, "error", {
                    "message": result.get("error_message", "Test error"),
                })
                error.text = result.get("stack_trace", "")

            elif status == "skipped":
                ET.SubElement(testcase, "skipped")

            # Add stdout/stderr if available
            if result.get("stdout"):
                stdout = ET.SubElement(testcase, "system-out")
                stdout.text = result["stdout"]

            if result.get("stderr"):
                stderr = ET.SubElement(testcase, "system-err")
                stderr.text = result["stderr"]

        # Write to file
        tree = ET.ElementTree(testsuite)
        ET.indent(tree, space="  ")
        tree.write(output_file, encoding="utf-8", xml_declaration=True)

        self.logger.info(f"JUnit report generated: {output_file}")
        return output_file


class HTMLReporter:
    """
    HTML test reporter.

    Generates human-readable HTML test reports.
    """

    def __init__(self):
        """Initialize HTML reporter."""
        self.logger = logging.getLogger(__name__)

    def generate_report(
        self,
        test_results: List[Dict[str, Any]],
        output_file: str = "test-report.html",
    ) -> str:
        """
        Generate HTML test report.

        Args:
            test_results: List of test results
            output_file: Output file path

        Returns:
            Output file path
        """
        total_tests = len(test_results)
        passed = sum(1 for r in test_results if r.get("status") == "passed")
        failed = sum(1 for r in test_results if r.get("status") == "failed")
        errors = sum(1 for r in test_results if r.get("status") == "error")
        skipped = sum(1 for r in test_results if r.get("status") == "skipped")

        pass_rate = (passed / total_tests * 100) if total_tests > 0 else 0

        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; margin-top: 0; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; color: white; }}
        .summary-card.passed {{ background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%); }}
        .summary-card.failed {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .summary-card h3 {{ margin: 0; font-size: 14px; opacity: 0.9; }}
        .summary-card .value {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 30px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: 600; color: #333; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .status.passed {{ background-color: #d4edda; color: #155724; }}
        .status.failed {{ background-color: #f8d7da; color: #721c24; }}
        .status.error {{ background-color: #fff3cd; color: #856404; }}
        .status.skipped {{ background-color: #d1ecf1; color: #0c5460; }}
        .error-details {{ background-color: #f8f9fa; padding: 10px; margin-top: 10px; border-left: 3px solid #dc3545; font-family: monospace; font-size: 12px; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Test Report</h1>
        <p>Generated: {timestamp}</p>

        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{total}</div>
            </div>
            <div class="summary-card passed">
                <h3>Passed</h3>
                <div class="value">{passed}</div>
            </div>
            <div class="summary-card failed">
                <h3>Failed</h3>
                <div class="value">{failed}</div>
            </div>
            <div class="summary-card">
                <h3>Pass Rate</h3>
                <div class="value">{pass_rate:.1f}%</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration (ms)</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

        rows = ""
        for result in test_results:
            status = result.get("status", "unknown")
            status_class = status.lower()

            error_html = ""
            if result.get("error_message"):
                error_html = f'<div class="error-details">{result["error_message"]}</div>'

            rows += f"""
                <tr>
                    <td>{result.get("name", "unknown")}</td>
                    <td><span class="status {status_class}">{status}</span></td>
                    <td>{result.get("execution_time_ms", 0):.2f}</td>
                    <td>{error_html}</td>
                </tr>
"""

        html_content = html_template.format(
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            total=total_tests,
            passed=passed,
            failed=failed,
            pass_rate=pass_rate,
            rows=rows,
        )

        with open(output_file, "w") as f:
            f.write(html_content)

        self.logger.info(f"HTML report generated: {output_file}")
        return output_file


class AllureReporter:
    """
    Allure test reporter.

    Generates Allure-compatible JSON reports.
    """

    def __init__(self):
        """Initialize Allure reporter."""
        self.logger = logging.getLogger(__name__)

    def generate_report(
        self,
        test_results: List[Dict[str, Any]],
        output_dir: str = "allure-results",
    ) -> str:
        """
        Generate Allure JSON reports.

        Args:
            test_results: List of test results
            output_dir: Output directory path

        Returns:
            Output directory path
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for i, result in enumerate(test_results):
            # Map status to Allure format
            status_map = {
                "passed": "passed",
                "failed": "failed",
                "error": "broken",
                "skipped": "skipped",
            }

            allure_result = {
                "uuid": result.get("id", f"test-{i}"),
                "name": result.get("name", "unknown"),
                "fullName": result.get("full_name", result.get("name", "unknown")),
                "status": status_map.get(result.get("status"), "unknown"),
                "stage": "finished",
                "start": int(datetime.utcnow().timestamp() * 1000),
                "stop": int(datetime.utcnow().timestamp() * 1000) + int(result.get("execution_time_ms", 0)),
                "labels": [
                    {"name": "suite", "value": result.get("suite", "TestSuite")},
                    {"name": "framework", "value": "pytest"},
                ],
                "parameters": [],
                "attachments": [],
            }

            # Add error details if failed
            if result.get("error_message"):
                allure_result["statusDetails"] = {
                    "message": result["error_message"],
                    "trace": result.get("stack_trace", ""),
                }

            # Write result file
            result_file = Path(output_dir) / f"{allure_result['uuid']}-result.json"
            with open(result_file, "w") as f:
                json.dump(allure_result, f, indent=2)

        self.logger.info(f"Allure reports generated in: {output_dir}")
        return output_dir


class TestReporter:
    """
    Main test reporter.

    Orchestrates multiple report formats and provides unified interface.
    """

    def __init__(self):
        """Initialize test reporter."""
        self.junit_reporter = JUnitReporter()
        self.html_reporter = HTMLReporter()
        self.allure_reporter = AllureReporter()
        self.logger = logging.getLogger(__name__)

    def generate_reports(
        self,
        test_results: List[Dict[str, Any]],
        formats: List[str] = None,
        output_dir: str = "test-reports",
    ) -> Dict[str, str]:
        """
        Generate test reports in multiple formats.

        Args:
            test_results: List of test results
            formats: Report formats to generate (junit, html, allure, json)
            output_dir: Output directory

        Returns:
            Dictionary mapping format to output file path
        """
        formats = formats or ["html", "junit", "json"]
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        report_files = {}

        try:
            if "junit" in formats:
                output_file = str(Path(output_dir) / "junit-report.xml")
                report_files["junit"] = self.junit_reporter.generate_report(
                    test_results, output_file
                )

            if "html" in formats:
                output_file = str(Path(output_dir) / "test-report.html")
                report_files["html"] = self.html_reporter.generate_report(
                    test_results, output_file
                )

            if "allure" in formats:
                allure_dir = str(Path(output_dir) / "allure-results")
                report_files["allure"] = self.allure_reporter.generate_report(
                    test_results, allure_dir
                )

            if "json" in formats:
                output_file = str(Path(output_dir) / "test-results.json")
                with open(output_file, "w") as f:
                    json.dump({
                        "timestamp": datetime.utcnow().isoformat(),
                        "total_tests": len(test_results),
                        "results": test_results,
                    }, f, indent=2, default=str)
                report_files["json"] = output_file

            self.logger.info(f"Generated {len(report_files)} report formats")

        except Exception as e:
            self.logger.error(f"Error generating reports: {e}")

        return report_files

    def generate_summary(
        self,
        test_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate test execution summary.

        Args:
            test_results: List of test results

        Returns:
            Summary statistics
        """
        total = len(test_results)
        passed = sum(1 for r in test_results if r.get("status") == "passed")
        failed = sum(1 for r in test_results if r.get("status") == "failed")
        errors = sum(1 for r in test_results if r.get("status") == "error")
        skipped = sum(1 for r in test_results if r.get("status") == "skipped")

        total_time = sum(r.get("execution_time_ms", 0) for r in test_results)
        avg_time = total_time / total if total > 0 else 0

        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "total_execution_time_ms": total_time,
            "average_execution_time_ms": avg_time,
            "timestamp": datetime.utcnow().isoformat(),
        }
