"""
Celery tasks for asynchronous integration operations.

Handles background processing of sync jobs, webhook deliveries,
token refreshes, and scheduled synchronizations.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from celery import Celery, Task
from sqlalchemy.orm import Session

from .models import SyncJob, Connection, Webhook, SyncStatus, IntegrationStatus
from .sync import DataSync
from .webhooks import WebhookSender
from .oauth import OAuthFlowManager
from .registry import ConnectorFactory
from .monitoring import IntegrationMetrics
from .queue import get_queue, get_event_bus

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'integration_hub',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000
)


def get_db_session():
    """Get database session."""
    # This should be replaced with actual NEXUS database session
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine("sqlite:///integration_hub.db")
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@celery_app.task(bind=True, max_retries=3)
def run_sync_job(self: Task, job_id: int) -> Dict[str, Any]:
    """
    Execute a synchronization job.

    Args:
        job_id: Sync job ID

    Returns:
        Job result dictionary
    """
    db = get_db_session()
    try:
        # Get job
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
        if not job:
            raise ValueError(f"Sync job {job_id} not found")

        # Update job with Celery task ID
        job.celery_task_id = self.request.id
        db.commit()

        # Create connector
        factory = ConnectorFactory(db, encryption_key=b"dummy_key_replace_with_actual")
        connector = factory.create_connector(job.connection_id)

        # Run sync
        sync = DataSync(db, connector, job)
        result_job = asyncio.run(sync.execute())

        # Publish event
        event_bus = get_event_bus()
        asyncio.run(event_bus.publish(
            'sync.completed' if result_job.status == SyncStatus.COMPLETED else 'sync.failed',
            {
                'job_id': job_id,
                'connection_id': job.connection_id,
                'status': result_job.status.value,
                'processed_records': result_job.processed_records,
                'duration': result_job.duration_seconds
            }
        ))

        return {
            'job_id': job_id,
            'status': result_job.status.value,
            'processed_records': result_job.processed_records,
            'successful_records': result_job.successful_records,
            'failed_records': result_job.failed_records
        }

    except Exception as e:
        logger.error(f"Sync job {job_id} failed: {str(e)}")

        # Update job status
        if job:
            job.status = SyncStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            db.commit()

        # Retry if not at max
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        raise

    finally:
        db.close()


@celery_app.task
def refresh_oauth_token(connection_id: int) -> Dict[str, Any]:
    """
    Refresh OAuth token for a connection.

    Args:
        connection_id: Connection ID

    Returns:
        Refresh result
    """
    db = get_db_session()
    try:
        oauth_manager = OAuthFlowManager(db, encryption_key=b"dummy_key_replace_with_actual")
        token_data = asyncio.run(oauth_manager.refresh_token(connection_id))

        return {
            'connection_id': connection_id,
            'success': True,
            'expires_at': token_data.get('expires_in')
        }

    except Exception as e:
        logger.error(f"Token refresh failed for connection {connection_id}: {str(e)}")
        return {
            'connection_id': connection_id,
            'success': False,
            'error': str(e)
        }

    finally:
        db.close()


@celery_app.task
def send_webhook(webhook_id: int, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a webhook event.

    Args:
        webhook_id: Webhook ID
        event_type: Event type
        payload: Event payload

    Returns:
        Delivery result
    """
    db = get_db_session()
    try:
        sender = WebhookSender(db)
        delivery = asyncio.run(sender.send_webhook(webhook_id, event_type, payload))

        return {
            'webhook_id': webhook_id,
            'delivery_id': delivery.id,
            'status': delivery.status.value
        }

    except Exception as e:
        logger.error(f"Webhook send failed: {str(e)}")
        return {
            'webhook_id': webhook_id,
            'success': False,
            'error': str(e)
        }

    finally:
        db.close()


@celery_app.task
def retry_failed_webhooks() -> Dict[str, Any]:
    """
    Retry failed webhook deliveries.

    Returns:
        Retry summary
    """
    db = get_db_session()
    try:
        sender = WebhookSender(db)
        retried = asyncio.run(sender.retry_failed_deliveries(max_retries=100))

        return {
            'retried_count': retried,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Webhook retry failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

    finally:
        db.close()


@celery_app.task
def check_connection_health(connection_id: int) -> Dict[str, Any]:
    """
    Check and update connection health status.

    Args:
        connection_id: Connection ID

    Returns:
        Health check result
    """
    db = get_db_session()
    try:
        connection = db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            return {'error': 'Connection not found'}

        # Create connector and test
        factory = ConnectorFactory(db, encryption_key=b"dummy_key_replace_with_actual")
        connector = factory.create_connector(connection_id)
        result = asyncio.run(connector.test_connection())

        # Update connection status
        if result.get('success'):
            connection.status = IntegrationStatus.ACTIVE
            connection.last_success_at = datetime.now()
            connection.consecutive_failures = 0
        else:
            connection.status = IntegrationStatus.ERROR
            connection.last_error_at = datetime.now()
            connection.last_error_message = result.get('message', 'Health check failed')
            connection.consecutive_failures += 1

        db.commit()

        return {
            'connection_id': connection_id,
            'healthy': result.get('success', False),
            'message': result.get('message', '')
        }

    except Exception as e:
        logger.error(f"Health check failed for connection {connection_id}: {str(e)}")

        if connection:
            connection.status = IntegrationStatus.ERROR
            connection.last_error_at = datetime.now()
            connection.last_error_message = str(e)
            connection.consecutive_failures += 1
            db.commit()

        return {
            'connection_id': connection_id,
            'healthy': False,
            'error': str(e)
        }

    finally:
        db.close()


@celery_app.task
def cleanup_old_jobs(days: int = 30) -> Dict[str, Any]:
    """
    Clean up old completed sync jobs.

    Args:
        days: Days to keep

    Returns:
        Cleanup summary
    """
    db = get_db_session()
    try:
        cutoff = datetime.now() - timedelta(days=days)

        # Delete old completed jobs
        deleted = db.query(SyncJob).filter(
            SyncJob.status == SyncStatus.COMPLETED,
            SyncJob.completed_at < cutoff
        ).delete()

        db.commit()

        logger.info(f"Cleaned up {deleted} old sync jobs")

        return {
            'deleted_count': deleted,
            'cutoff_date': cutoff.isoformat()
        }

    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

    finally:
        db.close()


@celery_app.task
def record_metrics(connection_id: int, metric_type: str, metric_name: str, value: float) -> None:
    """
    Record integration metric.

    Args:
        connection_id: Connection ID
        metric_type: Type of metric
        metric_name: Name of metric
        value: Metric value
    """
    db = get_db_session()
    try:
        metrics = IntegrationMetrics(db)
        metrics.record_metric(connection_id, metric_type, metric_name, value)

    except Exception as e:
        logger.error(f"Metric recording failed: {str(e)}")

    finally:
        db.close()


# Periodic tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic Celery tasks."""

    # Health checks every 5 minutes
    sender.add_periodic_task(
        300.0,  # 5 minutes
        check_all_connections_health.s(),
        name='check-all-connections'
    )

    # Retry failed webhooks every 10 minutes
    sender.add_periodic_task(
        600.0,  # 10 minutes
        retry_failed_webhooks.s(),
        name='retry-webhooks'
    )

    # Cleanup old jobs daily
    sender.add_periodic_task(
        86400.0,  # 24 hours
        cleanup_old_jobs.s(days=30),
        name='cleanup-jobs'
    )


@celery_app.task
def check_all_connections_health() -> Dict[str, Any]:
    """Check health of all active connections."""
    db = get_db_session()
    try:
        connections = db.query(Connection).filter(
            Connection.is_active == True
        ).all()

        results = []
        for connection in connections:
            check_connection_health.delay(connection.id)
            results.append(connection.id)

        return {
            'checked': len(results),
            'connection_ids': results
        }

    finally:
        db.close()


# Import asyncio for async operations
import asyncio
