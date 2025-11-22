"""
Report Generator

Custom report generation with templates.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from jinja2 import Template

from modules.analytics.core.aggregator import DataAggregator
from modules.analytics.export.exporters import DataExporter
from modules.analytics.storage.database import Database
from shared.constants import ExportFormat
from shared.utils import format_number, get_time_range, get_utc_now

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Custom report generator."""

    def __init__(self, db: Database, exporter: DataExporter):
        """Initialize report generator."""
        self.db = db
        self.exporter = exporter
        self.aggregator = DataAggregator(db)

        logger.info("Report generator initialized")

    def generate_overview_report(
        self,
        period: str = "last_30_days",
        format: ExportFormat = ExportFormat.PDF
    ) -> Optional[str]:
        """
        Generate analytics overview report.

        Args:
            period: Time period
            format: Export format

        Returns:
            File path if successful
        """
        try:
            start_date, end_date = get_time_range(period)

            with self.db.session() as session:
                # Get metrics
                session_metrics = self.aggregator.calculate_session_metrics(
                    session,
                    start_date,
                    end_date
                )

                # Prepare report data
                report_data = [{
                    "Metric": "Total Sessions",
                    "Value": format_number(session_metrics.get("total_sessions", 0))
                }, {
                    "Metric": "Unique Users",
                    "Value": format_number(session_metrics.get("unique_users", 0))
                }, {
                    "Metric": "Avg Session Duration",
                    "Value": f"{session_metrics.get('avg_duration_seconds', 0):.1f}s"
                }, {
                    "Metric": "Avg Page Views",
                    "Value": f"{session_metrics.get('avg_page_views', 0):.1f}"
                }, {
                    "Metric": "Bounce Rate",
                    "Value": f"{session_metrics.get('bounce_rate', 0):.1f}%"
                }, {
                    "Metric": "Conversion Rate",
                    "Value": f"{session_metrics.get('conversion_rate', 0):.1f}%"
                }]

                # Export
                return self.exporter.export(
                    report_data,
                    format,
                    title=f"Analytics Overview - {period}"
                )

        except Exception as e:
            logger.error(f"Error generating overview report: {e}", exc_info=True)
            return None

    def generate_custom_report(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        format: ExportFormat = ExportFormat.PDF
    ) -> Optional[str]:
        """
        Generate custom report with multiple sections.

        Args:
            title: Report title
            sections: List of report sections
            format: Export format

        Returns:
            File path if successful
        """
        try:
            report_data = []

            for section in sections:
                section_title = section.get("title", "Section")
                section_data = section.get("data", [])

                # Add section header
                report_data.append({
                    "Section": section_title,
                    "Data": ""
                })

                # Add section data
                for item in section_data:
                    report_data.append(item)

            # Export
            return self.exporter.export(
                report_data,
                format,
                title=title
            )

        except Exception as e:
            logger.error(f"Error generating custom report: {e}", exc_info=True)
            return None
