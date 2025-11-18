"""
Code Coverage Module

Provides CoverageAnalyzer, CodeCoverageTracker, and ReportGenerator for coverage analysis.
"""

import logging
import coverage as cov
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class CodeCoverageTracker:
    """
    Code coverage tracker.

    Tracks line and branch coverage during test execution.
    """

    def __init__(self, source_paths: List[str] = None):
        """
        Initialize coverage tracker.

        Args:
            source_paths: Paths to track coverage for
        """
        self.source_paths = source_paths or ["."]
        self.cov = cov.Coverage(
            source=self.source_paths,
            branch=True,
            omit=["*/tests/*", "*/test_*", "*/__pycache__/*"],
        )
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        """Start coverage tracking."""
        self.cov.start()
        self.logger.info("Coverage tracking started")

    def stop(self) -> None:
        """Stop coverage tracking."""
        self.cov.stop()
        self.logger.info("Coverage tracking stopped")

    def save(self, filename: str = ".coverage") -> None:
        """
        Save coverage data.

        Args:
            filename: Coverage data filename
        """
        self.cov.save()
        self.logger.info(f"Coverage data saved to {filename}")

    def get_data(self) -> Dict[str, Any]:
        """
        Get coverage data.

        Returns:
            Coverage data dictionary
        """
        self.cov.stop()
        self.cov.save()

        data = {}
        measured_files = self.cov.get_data().measured_files()

        for filepath in measured_files:
            analysis = self.cov.analysis2(filepath)

            if analysis:
                executed_lines = analysis[1]
                missing_lines = analysis[2]
                total_statements = len(executed_lines) + len(missing_lines)

                coverage_pct = (
                    (len(executed_lines) / total_statements * 100)
                    if total_statements > 0 else 0
                )

                data[filepath] = {
                    "total_statements": total_statements,
                    "executed_lines": len(executed_lines),
                    "missing_lines": len(missing_lines),
                    "coverage_percent": round(coverage_pct, 2),
                    "executed_line_numbers": list(executed_lines),
                    "missing_line_numbers": list(missing_lines),
                }

        return data


class ReportGenerator:
    """
    Coverage report generator.

    Generates coverage reports in multiple formats.
    """

    def __init__(self, coverage_data: Dict[str, Any] = None):
        """
        Initialize report generator.

        Args:
            coverage_data: Coverage data dictionary
        """
        self.coverage_data = coverage_data or {}
        self.logger = logging.getLogger(__name__)

    def generate_text_report(self) -> str:
        """
        Generate text coverage report.

        Returns:
            Text report
        """
        report = "Code Coverage Report\n"
        report += "=" * 80 + "\n\n"

        total_statements = 0
        total_executed = 0

        for filepath, data in self.coverage_data.items():
            total_statements += data["total_statements"]
            total_executed += data["executed_lines"]

            report += f"File: {filepath}\n"
            report += f"  Statements: {data['total_statements']}\n"
            report += f"  Executed: {data['executed_lines']}\n"
            report += f"  Missing: {data['missing_lines']}\n"
            report += f"  Coverage: {data['coverage_percent']:.2f}%\n\n"

        overall_coverage = (
            (total_executed / total_statements * 100)
            if total_statements > 0 else 0
        )

        report += "=" * 80 + "\n"
        report += f"TOTAL Coverage: {overall_coverage:.2f}%\n"
        report += f"Total Statements: {total_statements}\n"
        report += f"Executed: {total_executed}\n"
        report += f"Missing: {total_statements - total_executed}\n"

        return report

    def generate_html_report(self, output_dir: str = "htmlcov") -> str:
        """
        Generate HTML coverage report.

        Args:
            output_dir: Output directory for HTML report

        Returns:
            Output directory path
        """
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Code Coverage Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .high {{ color: green; font-weight: bold; }}
        .medium {{ color: orange; font-weight: bold; }}
        .low {{ color: red; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Code Coverage Report</h1>
    {summary}
    <table>
        <tr>
            <th>File</th>
            <th>Statements</th>
            <th>Executed</th>
            <th>Missing</th>
            <th>Coverage</th>
        </tr>
        {rows}
    </table>
</body>
</html>
"""

        total_statements = 0
        total_executed = 0
        rows = ""

        for filepath, data in self.coverage_data.items():
            total_statements += data["total_statements"]
            total_executed += data["executed_lines"]

            coverage_pct = data["coverage_percent"]
            css_class = "high" if coverage_pct >= 80 else "medium" if coverage_pct >= 60 else "low"

            rows += f"""
        <tr>
            <td>{filepath}</td>
            <td>{data['total_statements']}</td>
            <td>{data['executed_lines']}</td>
            <td>{data['missing_lines']}</td>
            <td class="{css_class}">{coverage_pct:.2f}%</td>
        </tr>
"""

        overall_coverage = (
            (total_executed / total_statements * 100)
            if total_statements > 0 else 0
        )

        summary = f"""
    <p><strong>Overall Coverage:</strong> {overall_coverage:.2f}%</p>
    <p><strong>Total Statements:</strong> {total_statements}</p>
    <p><strong>Executed:</strong> {total_executed}</p>
    <p><strong>Missing:</strong> {total_statements - total_executed}</p>
"""

        html_content = html_template.format(summary=summary, rows=rows)

        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir) / "index.html"

        with open(output_file, "w") as f:
            f.write(html_content)

        self.logger.info(f"HTML report generated: {output_file}")
        return str(output_file)

    def generate_json_report(self, output_file: str = "coverage.json") -> str:
        """
        Generate JSON coverage report.

        Args:
            output_file: Output file path

        Returns:
            Output file path
        """
        total_statements = 0
        total_executed = 0

        for data in self.coverage_data.values():
            total_statements += data["total_statements"]
            total_executed += data["executed_lines"]

        overall_coverage = (
            (total_executed / total_statements * 100)
            if total_statements > 0 else 0
        )

        report = {
            "summary": {
                "overall_coverage": round(overall_coverage, 2),
                "total_statements": total_statements,
                "executed_statements": total_executed,
                "missing_statements": total_statements - total_executed,
            },
            "files": self.coverage_data,
        }

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"JSON report generated: {output_file}")
        return output_file

    def generate_cobertura_report(self, output_file: str = "coverage.xml") -> str:
        """
        Generate Cobertura XML coverage report.

        Args:
            output_file: Output file path

        Returns:
            Output file path
        """
        total_statements = 0
        total_executed = 0

        for data in self.coverage_data.values():
            total_statements += data["total_statements"]
            total_executed += data["executed_lines"]

        line_rate = total_executed / total_statements if total_statements > 0 else 0

        xml_content = f"""<?xml version="1.0" ?>
<coverage line-rate="{line_rate:.4f}" branch-rate="0" version="1.0" timestamp="{int(__import__('time').time())}">
    <sources>
        <source>.</source>
    </sources>
    <packages>
"""

        for filepath, data in self.coverage_data.items():
            file_line_rate = data["executed_lines"] / data["total_statements"] if data["total_statements"] > 0 else 0

            xml_content += f"""
        <package name="{Path(filepath).parent}" line-rate="{file_line_rate:.4f}" branch-rate="0">
            <classes>
                <class name="{Path(filepath).stem}" filename="{filepath}" line-rate="{file_line_rate:.4f}">
                    <methods></methods>
                    <lines>
"""

            for line_num in data["executed_line_numbers"]:
                xml_content += f'                        <line number="{line_num}" hits="1"/>\n'

            for line_num in data["missing_line_numbers"]:
                xml_content += f'                        <line number="{line_num}" hits="0"/>\n'

            xml_content += """
                    </lines>
                </class>
            </classes>
        </package>
"""

        xml_content += """
    </packages>
</coverage>
"""

        with open(output_file, "w") as f:
            f.write(xml_content)

        self.logger.info(f"Cobertura XML report generated: {output_file}")
        return output_file


class CoverageAnalyzer:
    """
    Comprehensive coverage analyzer.

    Analyzes coverage data and provides insights.
    """

    def __init__(self, tracker: CodeCoverageTracker = None):
        """
        Initialize coverage analyzer.

        Args:
            tracker: Coverage tracker instance
        """
        self.tracker = tracker or CodeCoverageTracker()
        self.logger = logging.getLogger(__name__)

    def analyze(self, generate_reports: bool = True) -> Dict[str, Any]:
        """
        Analyze coverage and generate reports.

        Args:
            generate_reports: Whether to generate reports

        Returns:
            Analysis results
        """
        self.logger.info("Analyzing coverage data")

        coverage_data = self.tracker.get_data()

        # Calculate overall statistics
        total_statements = 0
        total_executed = 0
        files_analyzed = 0
        low_coverage_files = []

        for filepath, data in coverage_data.items():
            total_statements += data["total_statements"]
            total_executed += data["executed_lines"]
            files_analyzed += 1

            if data["coverage_percent"] < 80:
                low_coverage_files.append({
                    "file": filepath,
                    "coverage": data["coverage_percent"],
                })

        overall_coverage = (
            (total_executed / total_statements * 100)
            if total_statements > 0 else 0
        )

        analysis = {
            "overall_coverage": round(overall_coverage, 2),
            "total_statements": total_statements,
            "executed_statements": total_executed,
            "missing_statements": total_statements - total_executed,
            "files_analyzed": files_analyzed,
            "low_coverage_files": sorted(
                low_coverage_files,
                key=lambda x: x["coverage"],
            ),
            "coverage_data": coverage_data,
        }

        # Generate reports if requested
        if generate_reports:
            report_gen = ReportGenerator(coverage_data)
            analysis["reports"] = {
                "text": report_gen.generate_text_report(),
                "html": report_gen.generate_html_report(),
                "json": report_gen.generate_json_report(),
                "xml": report_gen.generate_cobertura_report(),
            }

        return analysis

    def get_uncovered_lines(self, filepath: str) -> List[int]:
        """
        Get uncovered lines for a specific file.

        Args:
            filepath: File path

        Returns:
            List of uncovered line numbers
        """
        coverage_data = self.tracker.get_data()

        if filepath in coverage_data:
            return coverage_data[filepath]["missing_line_numbers"]

        return []

    def get_coverage_percentage(self, filepath: str = None) -> float:
        """
        Get coverage percentage.

        Args:
            filepath: Optional file path (None for overall)

        Returns:
            Coverage percentage
        """
        coverage_data = self.tracker.get_data()

        if filepath:
            if filepath in coverage_data:
                return coverage_data[filepath]["coverage_percent"]
            return 0.0

        # Overall coverage
        total_statements = sum(d["total_statements"] for d in coverage_data.values())
        total_executed = sum(d["executed_lines"] for d in coverage_data.values())

        return (
            (total_executed / total_statements * 100)
            if total_statements > 0 else 0
        )
