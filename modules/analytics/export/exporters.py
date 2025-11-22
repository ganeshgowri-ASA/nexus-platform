"""
Data Exporters

Export functionality for CSV, JSON, Excel, and PDF formats.
"""

import csv
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from shared.constants import ExportFormat, MAX_EXPORT_ROWS, EXPORT_CHUNK_SIZE
from shared.utils import get_utc_now

logger = logging.getLogger(__name__)


class BaseExporter:
    """Base exporter class."""

    def __init__(self, max_rows: int = MAX_EXPORT_ROWS):
        """Initialize exporter."""
        self.max_rows = max_rows

    def export(
        self,
        data: List[Dict[str, Any]],
        file_path: str,
        **kwargs
    ) -> bool:
        """
        Export data to file.

        Args:
            data: Data to export
            file_path: Output file path
            **kwargs: Additional export options

        Returns:
            True if successful
        """
        raise NotImplementedError


class CSVExporter(BaseExporter):
    """CSV file exporter."""

    def export(
        self,
        data: List[Dict[str, Any]],
        file_path: str,
        **kwargs
    ) -> bool:
        """Export data to CSV file."""
        try:
            if not data:
                logger.warning("No data to export")
                return False

            # Limit rows
            data = data[:self.max_rows]

            # Get fieldnames from first row
            fieldnames = list(data[0].keys())

            # Write CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"Exported {len(data)} rows to CSV: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}", exc_info=True)
            return False


class JSONExporter(BaseExporter):
    """JSON file exporter."""

    def export(
        self,
        data: List[Dict[str, Any]],
        file_path: str,
        **kwargs
    ) -> bool:
        """Export data to JSON file."""
        try:
            if not data:
                logger.warning("No data to export")
                return False

            # Limit rows
            data = data[:self.max_rows]

            # Handle datetime serialization
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")

            # Write JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=json_serializer)

            logger.info(f"Exported {len(data)} rows to JSON: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}", exc_info=True)
            return False


class ExcelExporter(BaseExporter):
    """Excel file exporter."""

    def export(
        self,
        data: List[Dict[str, Any]],
        file_path: str,
        **kwargs
    ) -> bool:
        """Export data to Excel file."""
        try:
            if not data:
                logger.warning("No data to export")
                return False

            # Limit rows
            data = data[:self.max_rows]

            # Create DataFrame
            df = pd.DataFrame(data)

            # Write Excel
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')

                # Auto-adjust column widths
                worksheet = writer.sheets['Data']
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)

            logger.info(f"Exported {len(data)} rows to Excel: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}", exc_info=True)
            return False


class PDFExporter(BaseExporter):
    """PDF file exporter."""

    def export(
        self,
        data: List[Dict[str, Any]],
        file_path: str,
        title: str = "Analytics Report",
        **kwargs
    ) -> bool:
        """Export data to PDF file."""
        try:
            if not data:
                logger.warning("No data to export")
                return False

            # Limit rows for PDF
            data = data[:min(100, self.max_rows)]

            # Create PDF
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            elements = []

            # Styles
            styles = getSampleStyleSheet()

            # Title
            title_para = Paragraph(title, styles['Title'])
            elements.append(title_para)

            # Add timestamp
            timestamp = Paragraph(
                f"Generated: {get_utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
                styles['Normal']
            )
            elements.append(timestamp)
            elements.append(Paragraph("<br/><br/>", styles['Normal']))

            # Prepare table data
            if data:
                headers = list(data[0].keys())
                table_data = [headers]

                for row in data:
                    table_data.append([str(row.get(h, '')) for h in headers])

                # Create table
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                elements.append(table)

            # Build PDF
            doc.build(elements)

            logger.info(f"Exported {len(data)} rows to PDF: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}", exc_info=True)
            return False


class DataExporter:
    """Main data exporter."""

    def __init__(self, export_dir: str = "/tmp/nexus_exports"):
        """Initialize data exporter."""
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

        self.exporters = {
            ExportFormat.CSV: CSVExporter(),
            ExportFormat.JSON: JSONExporter(),
            ExportFormat.EXCEL: ExcelExporter(),
            ExportFormat.PDF: PDFExporter(),
        }

        logger.info(f"Data exporter initialized: {export_dir}")

    def export(
        self,
        data: List[Dict[str, Any]],
        format: ExportFormat,
        filename: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Export data in specified format.

        Args:
            data: Data to export
            format: Export format
            filename: Optional filename
            **kwargs: Additional export options

        Returns:
            File path if successful, None otherwise
        """
        try:
            # Get exporter
            exporter = self.exporters.get(format)
            if not exporter:
                logger.error(f"Unsupported export format: {format}")
                return None

            # Generate filename
            if not filename:
                timestamp = get_utc_now().strftime("%Y%m%d_%H%M%S")
                filename = f"export_{timestamp}.{format.value}"

            file_path = str(self.export_dir / filename)

            # Export
            success = exporter.export(data, file_path, **kwargs)

            if success:
                return file_path
            else:
                return None

        except Exception as e:
            logger.error(f"Error in export: {e}", exc_info=True)
            return None

    def cleanup_old_exports(self, days: int = 7) -> int:
        """
        Clean up export files older than specified days.

        Args:
            days: Age in days

        Returns:
            Number of files deleted
        """
        try:
            from datetime import timedelta

            cutoff_time = get_utc_now() - timedelta(days=days)
            deleted_count = 0

            for file_path in self.export_dir.glob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old export files")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up exports: {e}", exc_info=True)
            return 0
