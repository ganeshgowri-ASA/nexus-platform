"""
Integration monitoring and metrics tracking.

Tracks performance metrics, error rates, sync status, and provides
comprehensive monitoring for all integrations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from .models import (
    IntegrationMetric, Connection, SyncJob, SyncStatus,
    Webhook, WebhookDelivery, IntegrationStatus
)

logger = logging.getLogger(__name__)


class IntegrationMetrics:
    """
    Collects and analyzes integration metrics.

    Provides comprehensive metrics for monitoring integration health,
    performance, and usage patterns.
    """

    def __init__(self, db: Session):
        """
        Initialize metrics collector.

        Args:
            db: Database session
        """
        self.db = db

    def record_metric(
        self,
        connection_id: int,
        metric_type: str,
        metric_name: str,
        value: float,
        dimensions: Optional[Dict[str, Any]] = None
    ) -> IntegrationMetric:
        """
        Record a metric.

        Args:
            connection_id: Connection ID
            metric_type: Type of metric (e.g., 'api_call', 'sync', 'error')
            metric_name: Name of the metric
            value: Metric value
            dimensions: Additional metric dimensions

        Returns:
            Created metric record
        """
        metric = IntegrationMetric(
            connection_id=connection_id,
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            dimensions=dimensions or {}
        )

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)

        return metric

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get overall dashboard metrics.

        Returns:
            Dashboard metrics dictionary
        """
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Connection metrics
        total_connections = self.db.query(Connection).count()
        active_connections = self.db.query(Connection).filter(
            Connection.status == IntegrationStatus.ACTIVE,
            Connection.is_active == True
        ).count()
        failed_connections = self.db.query(Connection).filter(
            Connection.status == IntegrationStatus.ERROR
        ).count()

        # Sync metrics for today
        syncs_today = self.db.query(SyncJob).filter(
            SyncJob.created_at >= today
        ).all()

        total_syncs = len(syncs_today)
        successful_syncs = sum(1 for s in syncs_today if s.status == SyncStatus.COMPLETED)
        failed_syncs = sum(1 for s in syncs_today if s.status == SyncStatus.FAILED)
        total_records = sum(s.successful_records for s in syncs_today)
        total_api_calls = sum(s.api_calls_made for s in syncs_today)

        # Average sync duration
        completed_syncs = [s for s in syncs_today if s.status == SyncStatus.COMPLETED and s.duration_seconds]
        avg_duration = sum(s.duration_seconds for s in completed_syncs) / len(completed_syncs) if completed_syncs else 0

        # Webhook metrics
        webhooks_today = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.created_at >= today
        ).count()

        # Uptime calculation
        total_possible_uptime = total_connections * 24 * 60  # minutes
        downtime_minutes = failed_connections * 24 * 60
        uptime_percentage = ((total_possible_uptime - downtime_minutes) / total_possible_uptime * 100) if total_possible_uptime > 0 else 100

        return {
            'total_connections': total_connections,
            'active_connections': active_connections,
            'failed_connections': failed_connections,
            'total_syncs_today': total_syncs,
            'successful_syncs_today': successful_syncs,
            'failed_syncs_today': failed_syncs,
            'total_records_synced_today': total_records,
            'average_sync_duration': avg_duration,
            'total_api_calls_today': total_api_calls,
            'total_webhooks_delivered_today': webhooks_today,
            'uptime_percentage': uptime_percentage
        }

    def get_connection_metrics(
        self,
        connection_id: int,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific connection.

        Args:
            connection_id: Connection ID
            period_days: Period in days to analyze

        Returns:
            Connection metrics dictionary
        """
        since = datetime.now() - timedelta(days=period_days)

        # Sync metrics
        syncs = self.db.query(SyncJob).filter(
            and_(
                SyncJob.connection_id == connection_id,
                SyncJob.created_at >= since
            )
        ).all()

        total_syncs = len(syncs)
        successful_syncs = sum(1 for s in syncs if s.status == SyncStatus.COMPLETED)
        failed_syncs = sum(1 for s in syncs if s.status == SyncStatus.FAILED)
        total_records = sum(s.successful_records for s in syncs)
        total_api_calls = sum(s.api_calls_made for s in syncs)

        avg_records_per_sync = total_records / total_syncs if total_syncs > 0 else 0

        # Average duration
        completed = [s for s in syncs if s.status == SyncStatus.COMPLETED and s.duration_seconds]
        avg_duration = sum(s.duration_seconds for s in completed) / len(completed) if completed else 0

        # Last sync duration
        last_sync = syncs[-1] if syncs else None
        last_duration = last_sync.duration_seconds if last_sync and last_sync.duration_seconds else 0

        # Success rate
        success_rate = (successful_syncs / total_syncs * 100) if total_syncs > 0 else 0

        # Uptime calculation
        connection = self.db.query(Connection).filter(Connection.id == connection_id).first()
        is_healthy = connection.status == IntegrationStatus.ACTIVE if connection else False
        uptime_percentage = 95.0 if is_healthy else 50.0  # Simplified calculation

        return {
            'connection_id': connection_id,
            'total_syncs': total_syncs,
            'successful_syncs': successful_syncs,
            'failed_syncs': failed_syncs,
            'total_records_synced': total_records,
            'average_records_per_sync': avg_records_per_sync,
            'average_sync_duration': avg_duration,
            'total_api_calls': total_api_calls,
            'last_sync_duration': last_duration,
            'success_rate': success_rate,
            'uptime_percentage': uptime_percentage
        }

    def get_error_tracking(
        self,
        connection_id: Optional[int] = None,
        period_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get error tracking information.

        Args:
            connection_id: Optional connection ID filter
            period_hours: Period in hours to analyze

        Returns:
            List of error records
        """
        since = datetime.now() - timedelta(hours=period_hours)

        query = self.db.query(SyncJob).filter(
            and_(
                SyncJob.status == SyncStatus.FAILED,
                SyncJob.created_at >= since
            )
        )

        if connection_id:
            query = query.filter(SyncJob.connection_id == connection_id)

        failed_jobs = query.all()

        errors = []
        for job in failed_jobs:
            errors.append({
                'job_id': job.id,
                'connection_id': job.connection_id,
                'entity_type': job.entity_type,
                'error_message': job.error_message,
                'failed_at': job.completed_at,
                'failed_records': job.failed_records,
                'retry_count': job.retry_count
            })

        return errors

    def get_performance_metrics(
        self,
        connection_id: int,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get performance metrics for a connection.

        Args:
            connection_id: Connection ID
            period_days: Period in days

        Returns:
            Performance metrics
        """
        since = datetime.now() - timedelta(days=period_days)

        # Query metrics
        metrics = self.db.query(IntegrationMetric).filter(
            and_(
                IntegrationMetric.connection_id == connection_id,
                IntegrationMetric.timestamp >= since
            )
        ).all()

        # Aggregate by type
        by_type: Dict[str, List[float]] = {}
        for metric in metrics:
            if metric.metric_type not in by_type:
                by_type[metric.metric_type] = []
            by_type[metric.metric_type].append(metric.value)

        # Calculate statistics
        result = {}
        for metric_type, values in by_type.items():
            result[metric_type] = {
                'count': len(values),
                'avg': sum(values) / len(values) if values else 0,
                'min': min(values) if values else 0,
                'max': max(values) if values else 0,
                'total': sum(values)
            }

        return result


class SyncStatusMonitor:
    """
    Monitors synchronization status and health.

    Provides real-time sync status monitoring and alerting.
    """

    def __init__(self, db: Session):
        """
        Initialize sync status monitor.

        Args:
            db: Database session
        """
        self.db = db

    def get_sync_status(self, job_id: int) -> Dict[str, Any]:
        """
        Get current status of a sync job.

        Args:
            job_id: Sync job ID

        Returns:
            Status dictionary
        """
        job = self.db.query(SyncJob).filter(SyncJob.id == job_id).first()

        if not job:
            return {'error': 'Job not found'}

        progress = 0.0
        if job.total_records > 0:
            progress = (job.processed_records / job.total_records) * 100

        estimated_completion = None
        if job.status == SyncStatus.RUNNING and job.records_per_second and job.total_records > 0:
            remaining = job.total_records - job.processed_records
            seconds_remaining = remaining / job.records_per_second
            estimated_completion = datetime.now() + timedelta(seconds=seconds_remaining)

        return {
            'job_id': job.id,
            'status': job.status.value,
            'progress_percentage': progress,
            'processed_records': job.processed_records,
            'total_records': job.total_records,
            'successful_records': job.successful_records,
            'failed_records': job.failed_records,
            'current_operation': f"Processing {job.entity_type}",
            'estimated_completion': estimated_completion,
            'started_at': job.started_at,
            'duration_seconds': job.duration_seconds
        }

    def check_connection_health(self, connection_id: int) -> Dict[str, Any]:
        """
        Check health of a connection.

        Args:
            connection_id: Connection ID

        Returns:
            Health status
        """
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if not connection:
            return {'error': 'Connection not found'}

        is_healthy = connection.status == IntegrationStatus.ACTIVE
        last_check = connection.last_success_at or connection.created_at

        return {
            'connection_id': connection_id,
            'is_healthy': is_healthy,
            'status': connection.status.value,
            'last_check': last_check,
            'consecutive_failures': connection.consecutive_failures,
            'last_error': connection.last_error_message,
            'uptime_percentage': 95.0 if is_healthy else 50.0  # Simplified
        }


class ErrorTracker:
    """
    Tracks and analyzes integration errors.

    Provides error analytics and pattern detection.
    """

    def __init__(self, db: Session):
        """
        Initialize error tracker.

        Args:
            db: Database session
        """
        self.db = db

    def track_error(
        self,
        connection_id: int,
        error_type: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track an error occurrence.

        Args:
            connection_id: Connection ID
            error_type: Type of error
            error_message: Error message
            details: Additional error details
        """
        # Update connection error info
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if connection:
            connection.last_error_at = datetime.now()
            connection.last_error_message = error_message
            connection.consecutive_failures += 1
            self.db.commit()

        logger.error(f"Error tracked for connection {connection_id}: {error_message}")

    def get_error_patterns(
        self,
        period_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Analyze error patterns.

        Args:
            period_days: Period in days to analyze

        Returns:
            List of error patterns
        """
        since = datetime.now() - timedelta(days=period_days)

        # Get failed jobs
        failed_jobs = self.db.query(SyncJob).filter(
            and_(
                SyncJob.status == SyncStatus.FAILED,
                SyncJob.created_at >= since
            )
        ).all()

        # Group by error message
        error_counts: Dict[str, int] = {}
        for job in failed_jobs:
            msg = job.error_message or 'Unknown error'
            error_counts[msg] = error_counts.get(msg, 0) + 1

        # Sort by frequency
        patterns = [
            {'error': msg, 'count': count}
            for msg, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        return patterns[:10]  # Top 10 patterns
