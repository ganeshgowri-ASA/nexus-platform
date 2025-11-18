"""
Monitoring, metrics, and alerting for ETL module.

This module provides comprehensive monitoring capabilities including
metrics collection, alerting, and performance tracking.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from modules.etl.models import ETLJob, JobRun, JobStatus

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """Alert data structure."""
    severity: str  # 'info', 'warning', 'error', 'critical'
    title: str
    message: str
    job_id: Optional[int] = None
    job_run_id: Optional[int] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class ETLMetrics:
    """Collects and reports ETL metrics."""

    def __init__(self, db_session: Any):
        """
        Initialize ETL metrics collector.

        Args:
            db_session: Database session
        """
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)

    def get_overall_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get overall ETL metrics.

        Args:
            days: Number of days to include

        Returns:
            Overall metrics dictionary
        """
        since = datetime.utcnow() - timedelta(days=days)

        # Total jobs
        total_jobs = self.db_session.query(ETLJob).count()
        active_jobs = self.db_session.query(ETLJob).filter(ETLJob.is_active == True).count()
        scheduled_jobs = self.db_session.query(ETLJob).filter(
            ETLJob.is_active == True,
            ETLJob.is_scheduled == True
        ).count()

        # Job runs
        total_runs = self.db_session.query(JobRun).filter(
            JobRun.created_at >= since
        ).count()

        successful_runs = self.db_session.query(JobRun).filter(
            JobRun.created_at >= since,
            JobRun.status == JobStatus.COMPLETED
        ).count()

        failed_runs = self.db_session.query(JobRun).filter(
            JobRun.created_at >= since,
            JobRun.status == JobStatus.FAILED
        ).count()

        running_jobs = self.db_session.query(JobRun).filter(
            JobRun.status == JobStatus.RUNNING
        ).count()

        # Calculate success rate
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0

        # Average execution time
        completed_runs = self.db_session.query(JobRun).filter(
            JobRun.created_at >= since,
            JobRun.status == JobStatus.COMPLETED,
            JobRun.duration_seconds.isnot(None)
        ).all()

        avg_execution_time = (
            sum(r.duration_seconds for r in completed_runs) / len(completed_runs)
            if completed_runs else 0
        )

        # Total records processed
        total_records = sum(r.records_loaded or 0 for r in completed_runs)

        # Average data quality score
        runs_with_quality = [r for r in completed_runs if r.data_quality_score is not None]
        avg_quality = (
            sum(r.data_quality_score for r in runs_with_quality) / len(runs_with_quality)
            if runs_with_quality else None
        )

        return {
            "period_days": days,
            "total_jobs": total_jobs,
            "active_jobs": active_jobs,
            "scheduled_jobs": scheduled_jobs,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "running_jobs": running_jobs,
            "success_rate": round(success_rate, 2),
            "avg_execution_time_seconds": round(avg_execution_time, 2),
            "total_records_processed": total_records,
            "data_quality_avg_score": round(avg_quality, 2) if avg_quality else None
        }

    def get_job_performance(self, job_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get performance metrics for a specific job.

        Args:
            job_id: Job ID
            days: Number of days to include

        Returns:
            Job performance metrics
        """
        since = datetime.utcnow() - timedelta(days=days)

        runs = self.db_session.query(JobRun).filter(
            JobRun.job_id == job_id,
            JobRun.created_at >= since
        ).order_by(JobRun.created_at).all()

        if not runs:
            return {"job_id": job_id, "no_data": True}

        # Calculate trends
        timeline = []
        for run in runs:
            timeline.append({
                "timestamp": run.created_at.isoformat(),
                "status": run.status.value,
                "duration": run.duration_seconds,
                "records": run.records_loaded,
                "quality_score": run.data_quality_score
            })

        # Performance statistics
        completed_runs = [r for r in runs if r.status == JobStatus.COMPLETED]

        return {
            "job_id": job_id,
            "period_days": days,
            "total_runs": len(runs),
            "successful_runs": len(completed_runs),
            "failed_runs": len([r for r in runs if r.status == JobStatus.FAILED]),
            "avg_duration": (
                sum(r.duration_seconds for r in completed_runs if r.duration_seconds) / len(completed_runs)
                if completed_runs else 0
            ),
            "min_duration": min((r.duration_seconds for r in completed_runs if r.duration_seconds), default=0),
            "max_duration": max((r.duration_seconds for r in completed_runs if r.duration_seconds), default=0),
            "total_records": sum(r.records_loaded or 0 for r in completed_runs),
            "timeline": timeline
        }

    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health status.

        Returns:
            Health status dictionary
        """
        # Check for failed jobs in last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_failures = self.db_session.query(JobRun).filter(
            JobRun.created_at >= one_hour_ago,
            JobRun.status == JobStatus.FAILED
        ).count()

        # Check for long-running jobs (>2 hours)
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
        long_running = self.db_session.query(JobRun).filter(
            JobRun.status == JobStatus.RUNNING,
            JobRun.started_at < two_hours_ago
        ).count()

        # Determine overall health
        if recent_failures > 5 or long_running > 0:
            health = "unhealthy"
        elif recent_failures > 0:
            health = "degraded"
        else:
            health = "healthy"

        return {
            "status": health,
            "recent_failures": recent_failures,
            "long_running_jobs": long_running,
            "timestamp": datetime.utcnow().isoformat()
        }


class JobMetrics:
    """Collects metrics for individual jobs."""

    def __init__(self, job_run: JobRun):
        """
        Initialize job metrics collector.

        Args:
            job_run: Job run instance
        """
        self.job_run = job_run
        self.start_time = datetime.utcnow()
        self.stage_times: Dict[str, float] = {}

    def record_stage_time(self, stage: str, duration: float) -> None:
        """Record execution time for a stage."""
        self.stage_times[stage] = duration

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return {
            "job_run_id": self.job_run.id,
            "stage_times": self.stage_times,
            "total_duration": (datetime.utcnow() - self.start_time).total_seconds()
        }


class DataMetrics:
    """Collects data-level metrics."""

    @staticmethod
    def calculate_metrics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate metrics for a dataset.

        Args:
            data: Data records

        Returns:
            Data metrics
        """
        if not data:
            return {"record_count": 0}

        import pandas as pd
        df = pd.DataFrame(data)

        return {
            "record_count": len(df),
            "field_count": len(df.columns),
            "null_counts": df.isnull().sum().to_dict(),
            "memory_usage_bytes": int(df.memory_usage(deep=True).sum())
        }


class Alerting:
    """Handles alerting for ETL events."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize alerting system.

        Args:
            config: Alerting configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Email configuration
        self.smtp_host = self.config.get("smtp_host", "localhost")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.smtp_username = self.config.get("smtp_username")
        self.smtp_password = self.config.get("smtp_password")
        self.from_email = self.config.get("from_email", "etl@example.com")

        # Slack configuration
        self.slack_webhook_url = self.config.get("slack_webhook_url")

    def send_alert(self, alert: Alert, channels: Optional[List[str]] = None) -> None:
        """
        Send an alert to configured channels.

        Args:
            alert: Alert to send
            channels: List of channels ('email', 'slack')
        """
        channels = channels or ["email"]

        try:
            if "email" in channels:
                self._send_email_alert(alert)

            if "slack" in channels:
                self._send_slack_alert(alert)

        except Exception as e:
            self.logger.error(f"Failed to send alert: {str(e)}")

    def _send_email_alert(self, alert: Alert) -> None:
        """Send alert via email."""
        if not self.config.get("email_enabled", False):
            return

        recipients = self.config.get("alert_emails", [])
        if not recipients:
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = f"[{alert.severity.upper()}] {alert.title}"

            # Email body
            body = f"""
            Severity: {alert.severity.upper()}
            Title: {alert.title}
            Message: {alert.message}
            Timestamp: {alert.timestamp.isoformat()}

            Job ID: {alert.job_id}
            Job Run ID: {alert.job_run_id}
            """

            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_username and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)

                server.send_message(msg)

            self.logger.info(f"Email alert sent to {len(recipients)} recipients")

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {str(e)}")

    def _send_slack_alert(self, alert: Alert) -> None:
        """Send alert to Slack."""
        webhook_url = self.slack_webhook_url

        if not webhook_url:
            return

        try:
            # Slack color based on severity
            color_map = {
                "info": "#36a64f",
                "warning": "#ff9800",
                "error": "#f44336",
                "critical": "#9c27b0"
            }

            payload = {
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "#808080"),
                        "title": alert.title,
                        "text": alert.message,
                        "fields": [
                            {"title": "Severity", "value": alert.severity.upper(), "short": True},
                            {"title": "Job ID", "value": str(alert.job_id), "short": True},
                            {"title": "Timestamp", "value": alert.timestamp.isoformat(), "short": False}
                        ],
                        "footer": "NEXUS ETL",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            self.logger.info("Slack alert sent successfully")

        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {str(e)}")

    def alert_job_failure(
        self,
        job: ETLJob,
        job_run: JobRun,
        error_message: str
    ) -> None:
        """
        Send alert for job failure.

        Args:
            job: ETL job
            job_run: Failed job run
            error_message: Error message
        """
        if not job.notify_on_failure:
            return

        alert = Alert(
            severity="error",
            title=f"ETL Job Failed: {job.name}",
            message=f"Job '{job.name}' failed with error: {error_message}",
            job_id=job.id,
            job_run_id=job_run.id
        )

        channels = []
        if job.notification_emails:
            channels.append("email")
        if job.notification_slack_webhook:
            channels.append("slack")

        self.send_alert(alert, channels)

    def alert_job_success(
        self,
        job: ETLJob,
        job_run: JobRun
    ) -> None:
        """
        Send alert for job success.

        Args:
            job: ETL job
            job_run: Successful job run
        """
        if not job.notify_on_success:
            return

        alert = Alert(
            severity="info",
            title=f"ETL Job Completed: {job.name}",
            message=f"Job '{job.name}' completed successfully. Processed {job_run.records_loaded} records.",
            job_id=job.id,
            job_run_id=job_run.id
        )

        channels = []
        if job.notification_emails:
            channels.append("email")
        if job.notification_slack_webhook:
            channels.append("slack")

        self.send_alert(alert, channels)

    def alert_data_quality_issue(
        self,
        job: ETLJob,
        job_run: JobRun,
        quality_score: float
    ) -> None:
        """
        Send alert for data quality issues.

        Args:
            job: ETL job
            job_run: Job run
            quality_score: Data quality score
        """
        threshold = self.config.get("quality_threshold", 80.0)

        if quality_score >= threshold:
            return

        alert = Alert(
            severity="warning",
            title=f"Data Quality Alert: {job.name}",
            message=f"Data quality score ({quality_score:.2f}%) is below threshold ({threshold}%)",
            job_id=job.id,
            job_run_id=job_run.id
        )

        self.send_alert(alert, ["email", "slack"])


class PerformanceMonitor:
    """Monitors ETL performance and identifies bottlenecks."""

    def __init__(self, db_session: Any):
        """
        Initialize performance monitor.

        Args:
            db_session: Database session
        """
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)

    def identify_slow_jobs(self, threshold_minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Identify jobs that are running slower than threshold.

        Args:
            threshold_minutes: Duration threshold in minutes

        Returns:
            List of slow jobs
        """
        threshold_seconds = threshold_minutes * 60

        slow_runs = self.db_session.query(JobRun).filter(
            JobRun.status == JobStatus.COMPLETED,
            JobRun.duration_seconds > threshold_seconds
        ).order_by(JobRun.duration_seconds.desc()).limit(10).all()

        results = []
        for run in slow_runs:
            results.append({
                "job_id": run.job_id,
                "job_name": run.job.name if run.job else None,
                "run_id": run.id,
                "duration_minutes": run.duration_seconds / 60,
                "records_processed": run.records_loaded,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None
            })

        return results

    def analyze_failure_patterns(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze failure patterns.

        Args:
            days: Number of days to analyze

        Returns:
            Failure pattern analysis
        """
        since = datetime.utcnow() - timedelta(days=days)

        failed_runs = self.db_session.query(JobRun).filter(
            JobRun.created_at >= since,
            JobRun.status == JobStatus.FAILED
        ).all()

        # Group by job
        job_failures: Dict[int, int] = {}
        error_types: Dict[str, int] = {}

        for run in failed_runs:
            job_failures[run.job_id] = job_failures.get(run.job_id, 0) + 1

            # Categorize errors
            if run.error_message:
                if "connection" in run.error_message.lower():
                    error_types["connection"] = error_types.get("connection", 0) + 1
                elif "timeout" in run.error_message.lower():
                    error_types["timeout"] = error_types.get("timeout", 0) + 1
                elif "validation" in run.error_message.lower():
                    error_types["validation"] = error_types.get("validation", 0) + 1
                else:
                    error_types["other"] = error_types.get("other", 0) + 1

        # Find jobs with most failures
        top_failing_jobs = sorted(
            job_failures.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "period_days": days,
            "total_failures": len(failed_runs),
            "error_types": error_types,
            "top_failing_jobs": [
                {"job_id": job_id, "failure_count": count}
                for job_id, count in top_failing_jobs
            ]
        }
