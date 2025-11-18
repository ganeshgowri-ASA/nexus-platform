"""
NEXUS Reports Builder - Export Module
Comprehensive export functionality for PDF, Excel, CSV, JSON, and HTML formats
"""

import pandas as pd
import io
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import base64


class ExportFormat(Enum):
    """Supported export formats"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    XML = "xml"
    POWERPOINT = "powerpoint"
    WORD = "word"


class PageOrientation(Enum):
    """Page orientation for exports"""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


@dataclass
class ExportConfig:
    """Configuration for export"""
    format: ExportFormat
    filename: str
    include_charts: bool = True
    include_tables: bool = True
    include_filters: bool = True
    include_parameters: bool = True
    page_orientation: PageOrientation = PageOrientation.PORTRAIT
    page_size: str = "A4"
    compress: bool = False
    password_protect: bool = False
    password: str = ""
    watermark: str = ""
    header_text: str = ""
    footer_text: str = ""
    include_timestamp: bool = True
    author: str = ""
    title: str = ""
    subject: str = ""
    keywords: List[str] = None

    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


class PDFExporter:
    """Export reports to PDF format"""

    def __init__(self, config: ExportConfig):
        self.config = config

    def export(self, report_data: Dict[str, Any]) -> bytes:
        """Export report to PDF"""
        try:
            # In production, use libraries like reportlab or weasyprint
            # This is a placeholder implementation

            pdf_content = self._generate_pdf(report_data)
            return pdf_content

        except Exception as e:
            raise Exception(f"PDF export failed: {e}")

    def _generate_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """Generate PDF content"""
        # Placeholder - would use reportlab or similar
        # For now, return a simple bytes object
        content = f"""
        PDF Report
        Title: {self.config.title}
        Generated: {datetime.now().isoformat()}

        Report Data:
        {json.dumps(report_data, indent=2)}
        """.encode('utf-8')

        return content

    def add_header_footer(self, pdf, page_number: int, total_pages: int):
        """Add header and footer to PDF page"""
        if self.config.header_text:
            # Add header
            pass

        if self.config.footer_text:
            # Add footer
            footer = self.config.footer_text
            if "{page}" in footer:
                footer = footer.replace("{page}", str(page_number))
            if "{total_pages}" in footer:
                footer = footer.replace("{total_pages}", str(total_pages))

        if self.config.include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add_watermark(self, pdf):
        """Add watermark to PDF"""
        if self.config.watermark:
            # Add watermark
            pass


class ExcelExporter:
    """Export reports to Excel format"""

    def __init__(self, config: ExportConfig):
        self.config = config

    def export(self, report_data: Dict[str, Any]) -> bytes:
        """Export report to Excel"""
        try:
            output = io.BytesIO()

            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Write summary sheet
                self._write_summary_sheet(writer, report_data)

                # Write data sheets
                if 'tables' in report_data:
                    for i, table in enumerate(report_data['tables']):
                        sheet_name = table.get('name', f'Sheet{i+1}')
                        df = pd.DataFrame(table['data'])
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                        # Apply formatting
                        worksheet = writer.sheets[sheet_name]
                        self._apply_excel_formatting(worksheet, df)

                # Write charts if included
                if self.config.include_charts and 'charts' in report_data:
                    self._write_charts_sheet(writer, report_data['charts'])

            output.seek(0)
            return output.read()

        except Exception as e:
            raise Exception(f"Excel export failed: {e}")

    def _write_summary_sheet(self, writer, report_data: Dict[str, Any]):
        """Write summary sheet with report metadata"""
        summary_data = {
            'Report Title': [self.config.title],
            'Generated': [datetime.now().isoformat()],
            'Author': [self.config.author]
        }

        if self.config.include_parameters and 'parameters' in report_data:
            for param, value in report_data['parameters'].items():
                summary_data[f'Parameter: {param}'] = [value]

        df = pd.DataFrame(summary_data)
        df.to_excel(writer, sheet_name='Summary', index=False)

    def _write_charts_sheet(self, writer, charts: List[Dict[str, Any]]):
        """Write charts information"""
        chart_info = []
        for i, chart in enumerate(charts):
            chart_info.append({
                'Chart': i + 1,
                'Type': chart.get('type', 'unknown'),
                'Title': chart.get('title', '')
            })

        df = pd.DataFrame(chart_info)
        df.to_excel(writer, sheet_name='Charts', index=False)

    def _apply_excel_formatting(self, worksheet, df: pd.DataFrame):
        """Apply formatting to Excel worksheet"""
        try:
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

            # Header formatting
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF")

            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass

                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        except ImportError:
            # openpyxl not available, skip formatting
            pass


class CSVExporter:
    """Export reports to CSV format"""

    def __init__(self, config: ExportConfig):
        self.config = config

    def export(self, data: Union[pd.DataFrame, List[Dict[str, Any]]]) -> bytes:
        """Export data to CSV"""
        try:
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = data

            output = io.StringIO()
            df.to_csv(output, index=False)
            return output.getvalue().encode('utf-8')

        except Exception as e:
            raise Exception(f"CSV export failed: {e}")


class JSONExporter:
    """Export reports to JSON format"""

    def __init__(self, config: ExportConfig):
        self.config = config

    def export(self, data: Any) -> bytes:
        """Export data to JSON"""
        try:
            json_str = json.dumps(data, indent=2, default=str)
            return json_str.encode('utf-8')

        except Exception as e:
            raise Exception(f"JSON export failed: {e}")


class HTMLExporter:
    """Export reports to HTML format"""

    def __init__(self, config: ExportConfig):
        self.config = config

    def export(self, report_data: Dict[str, Any]) -> bytes:
        """Export report to HTML"""
        try:
            html = self._generate_html(report_data)
            return html.encode('utf-8')

        except Exception as e:
            raise Exception(f"HTML export failed: {e}")

    def _generate_html(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML content"""
        html_parts = []

        # HTML header
        html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .report-container {{
            background-color: white;
            padding: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .report-header {{
            border-bottom: 2px solid #366092;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .report-title {{
            color: #366092;
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }}
        .report-metadata {{
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }}
        .section {{
            margin: 20px 0;
        }}
        .section-title {{
            color: #366092;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        th {{
            background-color: #366092;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1 class="report-title">{title}</h1>
            <div class="report-metadata">
                Generated: {timestamp} | Author: {author}
            </div>
        </div>
        """.format(
            title=self.config.title,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            author=self.config.author
        ))

        # Parameters section
        if self.config.include_parameters and 'parameters' in report_data:
            html_parts.append('<div class="section">')
            html_parts.append('<h2 class="section-title">Parameters</h2>')
            html_parts.append('<table>')
            html_parts.append('<tr><th>Parameter</th><th>Value</th></tr>')

            for param, value in report_data['parameters'].items():
                html_parts.append(f'<tr><td>{param}</td><td>{value}</td></tr>')

            html_parts.append('</table>')
            html_parts.append('</div>')

        # Tables section
        if self.config.include_tables and 'tables' in report_data:
            for table in report_data['tables']:
                html_parts.append('<div class="section">')
                html_parts.append(f'<h2 class="section-title">{table.get("name", "Data Table")}</h2>')

                df = pd.DataFrame(table['data'])
                html_parts.append(df.to_html(index=False, classes='data-table'))

                html_parts.append('</div>')

        # Charts section
        if self.config.include_charts and 'charts' in report_data:
            html_parts.append('<div class="section">')
            html_parts.append('<h2 class="section-title">Charts</h2>')

            for i, chart in enumerate(report_data['charts']):
                html_parts.append(f'<div class="chart-container">')
                html_parts.append(f'<h3>{chart.get("title", f"Chart {i+1}")}</h3>')

                # Embed chart (would use actual chart HTML)
                if 'html' in chart:
                    html_parts.append(chart['html'])
                elif 'image' in chart:
                    html_parts.append(f'<img src="data:image/png;base64,{chart["image"]}" />')

                html_parts.append('</div>')

            html_parts.append('</div>')

        # Footer
        html_parts.append(f"""
        <div class="footer">
            {self.config.footer_text or "Generated by NEXUS Reports Builder"}
        </div>
    </div>
</body>
</html>
        """)

        return ''.join(html_parts)


class ReportExporter:
    """Main exporter class that handles all export formats"""

    def __init__(self):
        self.exporters = {}

    def export(self, report_data: Dict[str, Any], config: ExportConfig) -> bytes:
        """Export report in specified format"""
        format_type = config.format

        if format_type == ExportFormat.PDF:
            exporter = PDFExporter(config)
            return exporter.export(report_data)

        elif format_type == ExportFormat.EXCEL:
            exporter = ExcelExporter(config)
            return exporter.export(report_data)

        elif format_type == ExportFormat.CSV:
            exporter = CSVExporter(config)
            # Extract first table for CSV export
            if 'tables' in report_data and report_data['tables']:
                data = report_data['tables'][0]['data']
            else:
                data = []
            return exporter.export(data)

        elif format_type == ExportFormat.JSON:
            exporter = JSONExporter(config)
            return exporter.export(report_data)

        elif format_type == ExportFormat.HTML:
            exporter = HTMLExporter(config)
            return exporter.export(report_data)

        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def export_to_file(self, report_data: Dict[str, Any], config: ExportConfig, file_path: str):
        """Export report to file"""
        content = self.export(report_data, config)

        with open(file_path, 'wb') as f:
            f.write(content)

    def export_to_base64(self, report_data: Dict[str, Any], config: ExportConfig) -> str:
        """Export report as base64 encoded string"""
        content = self.export(report_data, config)
        return base64.b64encode(content).decode('utf-8')

    def get_mime_type(self, format_type: ExportFormat) -> str:
        """Get MIME type for format"""
        mime_types = {
            ExportFormat.PDF: "application/pdf",
            ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.CSV: "text/csv",
            ExportFormat.JSON: "application/json",
            ExportFormat.HTML: "text/html"
        }
        return mime_types.get(format_type, "application/octet-stream")


class BatchExporter:
    """Export multiple reports in batch"""

    def __init__(self):
        self.exporter = ReportExporter()
        self.exports: List[Dict[str, Any]] = []

    def add_export(self, report_data: Dict[str, Any], config: ExportConfig):
        """Add a report to batch export"""
        self.exports.append({
            'report_data': report_data,
            'config': config
        })

    def export_all(self, output_dir: str) -> List[str]:
        """Export all reports to directory"""
        exported_files = []

        for export_item in self.exports:
            report_data = export_item['report_data']
            config = export_item['config']

            file_path = f"{output_dir}/{config.filename}"
            self.exporter.export_to_file(report_data, config, file_path)
            exported_files.append(file_path)

        return exported_files

    def export_to_zip(self, zip_path: str):
        """Export all reports to a ZIP file"""
        import zipfile

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for export_item in self.exports:
                report_data = export_item['report_data']
                config = export_item['config']

                content = self.exporter.export(report_data, config)
                zipf.writestr(config.filename, content)

    def clear(self):
        """Clear all pending exports"""
        self.exports.clear()
