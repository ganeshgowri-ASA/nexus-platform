"""
Report Generation Tasks for Nexus Platform
Handles generating various types of reports (analytics, summaries, exports)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json

from celery import Task, chain
from config.celery_config import celery_app
from config.settings import settings

logger = logging.getLogger(__name__)


class ReportTask(Task):
    """Base class for report generation tasks"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 2, 'countdown': 30}


@celery_app.task(base=ReportTask, bind=True, name='app.tasks.report_tasks.generate_analytics_report')
def generate_analytics_report(
    self,
    data: Dict[str, Any],
    report_type: str = 'summary',
    format: str = 'html'
) -> Dict[str, Any]:
    """
    Generate analytics report from data

    Args:
        data: Analytics data to report on
        report_type: Type of report (summary, detailed, trends)
        format: Output format (html, pdf, excel)

    Returns:
        Report generation result with file path
    """
    try:
        import pandas as pd
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_name = f"analytics_report_{report_type}_{timestamp}"

        # Process data into DataFrame
        df = pd.DataFrame(data.get('records', []))

        results = {
            'report_name': report_name,
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'format': format,
            'outputs': {}
        }

        if format == 'html':
            # Generate HTML report with charts
            html_content = generate_html_report(df, report_type, report_name)
            output_path = settings.TEMP_DIR / f"{report_name}.html"
            output_path.write_text(html_content)
            results['outputs']['html_file'] = str(output_path)

        elif format == 'excel':
            # Generate Excel report
            output_path = settings.TEMP_DIR / f"{report_name}.xlsx"
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Data', index=False)

                # Add summary sheet if data available
                if not df.empty:
                    summary_df = df.describe()
                    summary_df.to_excel(writer, sheet_name='Summary')

            results['outputs']['excel_file'] = str(output_path)

        elif format == 'json':
            # Generate JSON report
            output_path = settings.TEMP_DIR / f"{report_name}.json"
            report_data = {
                'metadata': {
                    'report_name': report_name,
                    'report_type': report_type,
                    'generated_at': results['generated_at'],
                    'record_count': len(df)
                },
                'data': df.to_dict(orient='records'),
                'summary': df.describe().to_dict() if not df.empty else {}
            }
            output_path.write_text(json.dumps(report_data, indent=2))
            results['outputs']['json_file'] = str(output_path)

        logger.info(f"Generated {report_type} report in {format} format")
        return results

    except Exception as e:
        logger.error(f"Error generating analytics report: {str(e)}")
        raise self.retry(exc=e)


def generate_html_report(df, report_type: str, title: str) -> str:
    """Generate HTML report with embedded charts"""
    import plotly.express as px
    from jinja2 import Template

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ title }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            .metadata { background: #f5f5f5; padding: 10px; margin: 10px 0; }
            .chart { margin: 20px 0; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #4CAF50; color: white; }
        </style>
    </head>
    <body>
        <h1>{{ title }}</h1>
        <div class="metadata">
            <p><strong>Report Type:</strong> {{ report_type }}</p>
            <p><strong>Generated:</strong> {{ timestamp }}</p>
            <p><strong>Records:</strong> {{ record_count }}</p>
        </div>

        {% if summary_html %}
        <h2>Summary Statistics</h2>
        {{ summary_html | safe }}
        {% endif %}

        {% if charts %}
        <h2>Visualizations</h2>
        {% for chart in charts %}
        <div class="chart">{{ chart | safe }}</div>
        {% endfor %}
        {% endif %}

        <h2>Data Table</h2>
        {{ data_html | safe }}
    </body>
    </html>
    """

    # Generate summary
    summary_html = df.describe().to_html() if not df.empty else ""

    # Generate sample charts if numeric columns exist
    charts = []
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols and len(df) > 0:
        # Bar chart of first numeric column
        fig = px.bar(df.head(10), y=numeric_cols[0], title=f"{numeric_cols[0]} - Top 10")
        charts.append(fig.to_html(include_plotlyjs='cdn'))

    template = Template(html_template)
    return template.render(
        title=title,
        report_type=report_type,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        record_count=len(df),
        summary_html=summary_html,
        charts=charts,
        data_html=df.to_html(classes='data-table', index=False)
    )


@celery_app.task(base=ReportTask, bind=True, name='app.tasks.report_tasks.generate_summary_report')
def generate_summary_report(
    self,
    title: str,
    sections: List[Dict[str, Any]],
    include_ai_summary: bool = False
) -> Dict[str, Any]:
    """
    Generate a summary report with multiple sections

    Args:
        title: Report title
        sections: List of sections with title and content
        include_ai_summary: Whether to generate AI-powered executive summary

    Returns:
        Report generation result
    """
    try:
        from jinja2 import Template

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_name = f"summary_report_{timestamp}"

        # If AI summary requested, generate it
        ai_summary = None
        if include_ai_summary:
            from app.tasks.ai_tasks import claude_completion

            # Combine all section content
            content = '\n\n'.join([
                f"{s.get('title', 'Section')}: {s.get('content', '')}"
                for s in sections
            ])

            ai_result = claude_completion(
                prompt=f"Provide an executive summary of the following report:\n\n{content}",
                max_tokens=500
            )
            ai_summary = ai_result.get('content', '')

        # Generate HTML report
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; max-width: 900px; }
                h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
                h2 { color: #34495e; margin-top: 30px; }
                .metadata { background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }
                .executive-summary { background: #e8f4f8; padding: 20px; margin: 20px 0; border-left: 4px solid #3498db; }
                .section { margin: 30px 0; }
                .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #ccc; color: #7f8c8d; }
            </style>
        </head>
        <body>
            <h1>{{ title }}</h1>

            <div class="metadata">
                <p><strong>Generated:</strong> {{ timestamp }}</p>
                <p><strong>Sections:</strong> {{ section_count }}</p>
            </div>

            {% if ai_summary %}
            <div class="executive-summary">
                <h2>Executive Summary</h2>
                <p>{{ ai_summary }}</p>
            </div>
            {% endif %}

            {% for section in sections %}
            <div class="section">
                <h2>{{ section.title }}</h2>
                <div>{{ section.content }}</div>
            </div>
            {% endfor %}

            <div class="footer">
                <p>Report generated by Nexus Platform</p>
            </div>
        </body>
        </html>
        """

        template = Template(html_template)
        html_content = template.render(
            title=title,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            section_count=len(sections),
            ai_summary=ai_summary,
            sections=sections
        )

        output_path = settings.TEMP_DIR / f"{report_name}.html"
        output_path.write_text(html_content)

        logger.info(f"Generated summary report: {report_name}")
        return {
            'status': 'success',
            'report_name': report_name,
            'output_file': str(output_path),
            'sections_count': len(sections),
            'ai_summary_included': include_ai_summary
        }

    except Exception as e:
        logger.error(f"Error generating summary report: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(base=ReportTask, bind=True, name='app.tasks.report_tasks.export_data')
def export_data(
    self,
    data: List[Dict[str, Any]],
    format: str = 'csv',
    filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Export data to various formats

    Args:
        data: List of data records
        format: Export format (csv, excel, json, xml)
        filename: Optional custom filename

    Returns:
        Export result with file path
    """
    try:
        import pandas as pd

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = filename or f"export_{timestamp}"

        df = pd.DataFrame(data)

        if format == 'csv':
            output_path = settings.TEMP_DIR / f"{filename}.csv"
            df.to_csv(output_path, index=False)

        elif format == 'excel':
            output_path = settings.TEMP_DIR / f"{filename}.xlsx"
            df.to_excel(output_path, index=False, engine='openpyxl')

        elif format == 'json':
            output_path = settings.TEMP_DIR / f"{filename}.json"
            output_path.write_text(json.dumps(data, indent=2))

        elif format == 'xml':
            output_path = settings.TEMP_DIR / f"{filename}.xml"
            xml_content = df.to_xml()
            output_path.write_text(xml_content)

        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Exported {len(data)} records to {format} format")
        return {
            'status': 'success',
            'format': format,
            'output_file': str(output_path),
            'record_count': len(data),
            'file_size_bytes': output_path.stat().st_size
        }

    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(base=ReportTask, bind=True, name='app.tasks.report_tasks.generate_task_performance_report')
def generate_task_performance_report(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate report on Celery task performance

    Args:
        start_date: Start date for report (ISO format)
        end_date: End date for report (ISO format)

    Returns:
        Performance report
    """
    try:
        from celery.result import AsyncResult
        from app.utils.task_stats import get_task_statistics

        # Get task statistics (implementation in utils)
        stats = get_task_statistics(start_date, end_date)

        # Generate report
        report_data = {
            'period': {
                'start': start_date or 'N/A',
                'end': end_date or 'N/A'
            },
            'statistics': stats
        }

        # Create HTML report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_name = f"task_performance_{timestamp}"

        return generate_summary_report(
            title="Task Performance Report",
            sections=[
                {
                    'title': 'Overview',
                    'content': f"Report Period: {report_data['period']['start']} to {report_data['period']['end']}"
                },
                {
                    'title': 'Task Statistics',
                    'content': json.dumps(stats, indent=2)
                }
            ]
        )

    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(name='app.tasks.report_tasks.schedule_recurring_report')
def schedule_recurring_report(
    report_config: Dict[str, Any],
    schedule_frequency: str = 'daily'
) -> Dict[str, Any]:
    """
    Schedule a recurring report

    Args:
        report_config: Report configuration (type, parameters, recipients)
        schedule_frequency: Frequency (daily, weekly, monthly)

    Returns:
        Scheduling result
    """
    # This would integrate with Celery Beat for recurring tasks
    logger.info(f"Scheduled {schedule_frequency} report: {report_config.get('title', 'Untitled')}")

    return {
        'status': 'scheduled',
        'frequency': schedule_frequency,
        'config': report_config
    }
