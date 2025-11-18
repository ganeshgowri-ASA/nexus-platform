"""
NEXUS Reports Builder - Scheduler Module
Automated report scheduling with email delivery, recurring schedules, and job management
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


class ScheduleFrequency(Enum):
    """Schedule frequency options"""
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM_CRON = "custom_cron"


class ScheduleStatus(Enum):
    """Status of scheduled jobs"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(Enum):
    """Export format options"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


@dataclass
class EmailConfig:
    """Email configuration for report delivery"""
    smtp_host: str
    smtp_port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    from_email: str = ""
    from_name: str = "NEXUS Reports"


@dataclass
class EmailRecipient:
    """Email recipient configuration"""
    email: str
    name: str = ""
    cc: bool = False
    bcc: bool = False


@dataclass
class ScheduleConfig:
    """Configuration for report schedule"""
    frequency: ScheduleFrequency
    start_date: datetime
    end_date: Optional[datetime] = None
    time_of_day: str = "09:00"  # HH:MM format
    day_of_week: int = 0  # 0=Monday, 6=Sunday
    day_of_month: int = 1  # 1-31
    cron_expression: str = ""
    timezone: str = "UTC"


@dataclass
class JobExecution:
    """Record of a job execution"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    error_message: str = ""
    output_file: str = ""
    records_processed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'execution_id': self.execution_id,
            'job_id': self.job_id,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status.value,
            'error_message': self.error_message,
            'output_file': self.output_file,
            'records_processed': self.records_processed
        }


@dataclass
class ScheduledJob:
    """Represents a scheduled report job"""
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    report_id: str = ""
    schedule: ScheduleConfig = None
    export_format: ExportFormat = ExportFormat.PDF
    email_recipients: List[EmailRecipient] = field(default_factory=list)
    email_subject: str = "Scheduled Report: {report_name}"
    email_body: str = "Please find the attached report."
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    created_by: str = "admin"
    created_at: datetime = field(default_factory=datetime.now)
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_history: List[JobExecution] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    max_history: int = 100

    def __post_init__(self):
        if self.schedule:
            self.calculate_next_execution()

    def calculate_next_execution(self):
        """Calculate the next execution time"""
        if not self.schedule or self.status != ScheduleStatus.ACTIVE:
            self.next_execution = None
            return

        now = datetime.now()
        start = self.schedule.start_date

        if start > now:
            self.next_execution = start
            return

        if self.schedule.end_date and now > self.schedule.end_date:
            self.status = ScheduleStatus.COMPLETED
            self.next_execution = None
            return

        freq = self.schedule.frequency

        if freq == ScheduleFrequency.ONCE:
            if self.last_execution:
                self.status = ScheduleStatus.COMPLETED
                self.next_execution = None
            else:
                self.next_execution = start

        elif freq == ScheduleFrequency.HOURLY:
            base = self.last_execution or start
            self.next_execution = base + timedelta(hours=1)

        elif freq == ScheduleFrequency.DAILY:
            base = self.last_execution or start
            next_day = base + timedelta(days=1)
            # Set to specific time of day
            time_parts = self.schedule.time_of_day.split(':')
            self.next_execution = next_day.replace(
                hour=int(time_parts[0]),
                minute=int(time_parts[1]),
                second=0,
                microsecond=0
            )

        elif freq == ScheduleFrequency.WEEKLY:
            base = self.last_execution or start
            days_ahead = self.schedule.day_of_week - base.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date = base + timedelta(days=days_ahead)
            time_parts = self.schedule.time_of_day.split(':')
            self.next_execution = next_date.replace(
                hour=int(time_parts[0]),
                minute=int(time_parts[1]),
                second=0,
                microsecond=0
            )

        elif freq == ScheduleFrequency.MONTHLY:
            base = self.last_execution or start
            # Move to next month
            if base.month == 12:
                next_month = base.replace(year=base.year + 1, month=1)
            else:
                next_month = base.replace(month=base.month + 1)

            # Set to specific day of month
            try:
                time_parts = self.schedule.time_of_day.split(':')
                self.next_execution = next_month.replace(
                    day=min(self.schedule.day_of_month, 28),
                    hour=int(time_parts[0]),
                    minute=int(time_parts[1]),
                    second=0,
                    microsecond=0
                )
            except ValueError:
                # Handle invalid day for month
                self.next_execution = next_month

        elif freq == ScheduleFrequency.QUARTERLY:
            base = self.last_execution or start
            # Add 3 months
            new_month = base.month + 3
            new_year = base.year
            if new_month > 12:
                new_month -= 12
                new_year += 1

            try:
                time_parts = self.schedule.time_of_day.split(':')
                self.next_execution = base.replace(
                    year=new_year,
                    month=new_month,
                    day=self.schedule.day_of_month,
                    hour=int(time_parts[0]),
                    minute=int(time_parts[1]),
                    second=0,
                    microsecond=0
                )
            except ValueError:
                self.next_execution = base.replace(year=new_year, month=new_month)

        elif freq == ScheduleFrequency.YEARLY:
            base = self.last_execution or start
            next_year = base.replace(year=base.year + 1)
            time_parts = self.schedule.time_of_day.split(':')
            self.next_execution = next_year.replace(
                hour=int(time_parts[0]),
                minute=int(time_parts[1]),
                second=0,
                microsecond=0
            )

    def is_due(self) -> bool:
        """Check if job is due for execution"""
        if self.status != ScheduleStatus.ACTIVE:
            return False

        if not self.next_execution:
            return False

        return datetime.now() >= self.next_execution

    def add_execution(self, execution: JobExecution):
        """Add execution record"""
        self.execution_history.append(execution)

        # Limit history size
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history:]

        self.last_execution = execution.completed_at or datetime.now()
        self.calculate_next_execution()

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0.0
            }

        successful = sum(1 for e in self.execution_history if e.status == ScheduleStatus.COMPLETED)
        failed = sum(1 for e in self.execution_history if e.status == ScheduleStatus.FAILED)

        return {
            'total_executions': len(self.execution_history),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(self.execution_history) * 100
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'job_id': self.job_id,
            'name': self.name,
            'description': self.description,
            'report_id': self.report_id,
            'schedule': {
                'frequency': self.schedule.frequency.value,
                'start_date': self.schedule.start_date.isoformat(),
                'end_date': self.schedule.end_date.isoformat() if self.schedule.end_date else None,
                'time_of_day': self.schedule.time_of_day,
                'day_of_week': self.schedule.day_of_week,
                'day_of_month': self.schedule.day_of_month
            } if self.schedule else None,
            'export_format': self.export_format.value,
            'email_recipients': [
                {'email': r.email, 'name': r.name, 'cc': r.cc, 'bcc': r.bcc}
                for r in self.email_recipients
            ],
            'status': self.status.value,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'execution_stats': self.get_execution_stats()
        }


class ReportScheduler:
    """Main scheduler for managing report jobs"""

    def __init__(self, email_config: Optional[EmailConfig] = None):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.email_config = email_config
        self.is_running = False

    def add_job(self, job: ScheduledJob) -> str:
        """Add a scheduled job"""
        self.jobs[job.job_id] = job
        return job.job_id

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        """Get a job by ID"""
        return self.jobs.get(job_id)

    def list_jobs(self, status: Optional[ScheduleStatus] = None) -> List[ScheduledJob]:
        """List all jobs, optionally filtered by status"""
        if status:
            return [job for job in self.jobs.values() if job.status == status]
        return list(self.jobs.values())

    def pause_job(self, job_id: str) -> bool:
        """Pause a job"""
        job = self.get_job(job_id)
        if job:
            job.status = ScheduleStatus.PAUSED
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        job = self.get_job(job_id)
        if job and job.status == ScheduleStatus.PAUSED:
            job.status = ScheduleStatus.ACTIVE
            job.calculate_next_execution()
            return True
        return False

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        job = self.get_job(job_id)
        if job:
            job.status = ScheduleStatus.CANCELLED
            return True
        return False

    def get_due_jobs(self) -> List[ScheduledJob]:
        """Get all jobs that are due for execution"""
        return [job for job in self.jobs.values() if job.is_due()]

    def execute_job(self, job_id: str, report_generator: Callable = None) -> JobExecution:
        """Execute a job"""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        execution = JobExecution(
            job_id=job_id,
            started_at=datetime.now()
        )

        try:
            # Generate report (would call actual report generator)
            if report_generator:
                output_file = report_generator(job.report_id, job.parameters)
                execution.output_file = output_file

            # Send email if configured
            if job.email_recipients and self.email_config:
                self.send_report_email(job, execution.output_file)

            execution.status = ScheduleStatus.COMPLETED
            execution.completed_at = datetime.now()

        except Exception as e:
            execution.status = ScheduleStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now()

        job.add_execution(execution)
        return execution

    def send_report_email(self, job: ScheduledJob, attachment_path: str):
        """Send report via email"""
        if not self.email_config:
            raise ValueError("Email configuration not set")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{self.email_config.from_name} <{self.email_config.from_email}>"
        msg['Subject'] = job.email_subject.replace('{report_name}', job.name)

        # Add recipients
        to_emails = [r.email for r in job.email_recipients if not r.cc and not r.bcc]
        cc_emails = [r.email for r in job.email_recipients if r.cc]
        bcc_emails = [r.email for r in job.email_recipients if r.bcc]

        msg['To'] = ', '.join(to_emails)
        if cc_emails:
            msg['Cc'] = ', '.join(cc_emails)

        # Add body
        msg.attach(MIMEText(job.email_body, 'plain'))

        # Add attachment
        if attachment_path:
            try:
                with open(attachment_path, 'rb') as f:
                    attachment = MIMEApplication(f.read())
                    attachment.add_header('Content-Disposition', 'attachment',
                                        filename=attachment_path.split('/')[-1])
                    msg.attach(attachment)
            except Exception as e:
                print(f"Failed to attach file: {e}")

        # Send email
        try:
            if self.email_config.use_ssl:
                server = smtplib.SMTP_SSL(self.email_config.smtp_host, self.email_config.smtp_port)
            else:
                server = smtplib.SMTP(self.email_config.smtp_host, self.email_config.smtp_port)
                if self.email_config.use_tls:
                    server.starttls()

            if self.email_config.username and self.email_config.password:
                server.login(self.email_config.username, self.email_config.password)

            all_recipients = to_emails + cc_emails + bcc_emails
            server.send_message(msg, to_addrs=all_recipients)
            server.quit()

        except Exception as e:
            raise Exception(f"Failed to send email: {e}")

    def run_pending_jobs(self, report_generator: Callable = None):
        """Run all pending jobs"""
        due_jobs = self.get_due_jobs()

        results = []
        for job in due_jobs:
            try:
                execution = self.execute_job(job.job_id, report_generator)
                results.append(execution)
            except Exception as e:
                print(f"Failed to execute job {job.job_id}: {e}")

        return results

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        total_jobs = len(self.jobs)
        active_jobs = len(self.list_jobs(ScheduleStatus.ACTIVE))
        paused_jobs = len(self.list_jobs(ScheduleStatus.PAUSED))
        completed_jobs = len(self.list_jobs(ScheduleStatus.COMPLETED))
        failed_jobs = len(self.list_jobs(ScheduleStatus.FAILED))

        total_executions = sum(len(job.execution_history) for job in self.jobs.values())
        successful_executions = sum(
            sum(1 for e in job.execution_history if e.status == ScheduleStatus.COMPLETED)
            for job in self.jobs.values()
        )

        return {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'paused_jobs': paused_jobs,
            'completed_jobs': completed_jobs,
            'failed_jobs': failed_jobs,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert scheduler state to dictionary"""
        return {
            'jobs': [job.to_dict() for job in self.jobs.values()],
            'stats': self.get_scheduler_stats()
        }
