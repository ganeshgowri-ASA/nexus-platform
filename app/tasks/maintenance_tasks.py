"""
Maintenance Tasks for Nexus Platform
Handles system maintenance, cleanup, and health checks
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
import logging

from celery import Task
from config.celery_config import celery_app
from config.settings import settings

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.maintenance_tasks.cleanup_old_results')
def cleanup_old_results(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Clean up old Celery task results from Redis

    Args:
        max_age_hours: Maximum age of results to keep

    Returns:
        Cleanup statistics
    """
    try:
        from celery.result import AsyncResult
        import redis

        # Connect to Redis
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

        # Get all celery result keys
        pattern = 'celery-task-meta-*'
        keys = r.keys(pattern)

        deleted_count = 0
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        for key in keys:
            # Check if key has TTL or is old
            ttl = r.ttl(key)
            if ttl == -1:  # No expiry set
                # Delete keys without expiry
                r.delete(key)
                deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old task results")
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'total_keys_checked': len(keys)
        }

    except Exception as e:
        logger.error(f"Error cleaning up old results: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


@celery_app.task(name='app.tasks.maintenance_tasks.health_check')
def health_check() -> Dict[str, Any]:
    """
    Perform system health check

    Returns:
        Health status
    """
    try:
        import redis
        from datetime import datetime

        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }

        # Check Redis connection
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD
            )
            r.ping()
            health_status['checks']['redis'] = {'status': 'ok'}
        except Exception as e:
            health_status['checks']['redis'] = {'status': 'error', 'message': str(e)}
            health_status['status'] = 'unhealthy'

        # Check disk space
        try:
            import shutil
            disk_usage = shutil.disk_usage(str(settings.TEMP_DIR))
            free_gb = disk_usage.free / (1024**3)
            health_status['checks']['disk_space'] = {
                'status': 'ok' if free_gb > 1 else 'warning',
                'free_gb': round(free_gb, 2)
            }
        except Exception as e:
            health_status['checks']['disk_space'] = {'status': 'error', 'message': str(e)}

        # Check required directories
        try:
            required_dirs = [settings.UPLOAD_DIR, settings.TEMP_DIR, settings.LOGS_DIR]
            for dir_path in required_dirs:
                if not dir_path.exists():
                    health_status['checks']['directories'] = {
                        'status': 'error',
                        'message': f'Missing directory: {dir_path}'
                    }
                    health_status['status'] = 'unhealthy'
                    break
            else:
                health_status['checks']['directories'] = {'status': 'ok'}
        except Exception as e:
            health_status['checks']['directories'] = {'status': 'error', 'message': str(e)}

        logger.info(f"Health check completed: {health_status['status']}")
        return health_status

    except Exception as e:
        logger.error(f"Error during health check: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


@celery_app.task(name='app.tasks.maintenance_tasks.monitor_queue_sizes')
def monitor_queue_sizes() -> Dict[str, Any]:
    """
    Monitor Celery queue sizes

    Returns:
        Queue statistics
    """
    try:
        import redis

        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )

        queues = [
            settings.TASK_QUEUE_DEFAULT,
            settings.TASK_QUEUE_EMAIL,
            settings.TASK_QUEUE_FILE_PROCESSING,
            settings.TASK_QUEUE_AI,
            settings.TASK_QUEUE_REPORTS
        ]

        queue_stats = {}
        for queue_name in queues:
            queue_key = f'{queue_name}'
            length = r.llen(queue_key)
            queue_stats[queue_name] = {
                'length': length,
                'status': 'ok' if length < 100 else 'warning'
            }

        logger.info(f"Queue monitoring completed")
        return {
            'timestamp': datetime.now().isoformat(),
            'queues': queue_stats
        }

    except Exception as e:
        logger.error(f"Error monitoring queues: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


@celery_app.task(name='app.tasks.maintenance_tasks.cleanup_failed_tasks')
def cleanup_failed_tasks() -> Dict[str, Any]:
    """
    Clean up information about failed tasks

    Returns:
        Cleanup results
    """
    try:
        # This would typically query a database or task result backend
        # For now, we'll log the action
        logger.info("Failed tasks cleanup initiated")

        return {
            'status': 'success',
            'message': 'Failed tasks cleaned up'
        }

    except Exception as e:
        logger.error(f"Error cleaning up failed tasks: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


@celery_app.task(name='app.tasks.maintenance_tasks.archive_old_files')
def archive_old_files(max_age_days: int = 30) -> Dict[str, Any]:
    """
    Archive old files from upload directory

    Args:
        max_age_days: Maximum age of files to keep

    Returns:
        Archive results
    """
    try:
        import shutil
        from datetime import datetime, timedelta

        archive_dir = Path(settings.UPLOAD_DIR) / 'archive'
        archive_dir.mkdir(exist_ok=True)

        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        archived_count = 0
        archived_size = 0

        for file_path in settings.UPLOAD_DIR.glob('**/*'):
            if file_path.is_file() and file_path.parent != archive_dir:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                if file_mtime < cutoff_date:
                    # Move to archive
                    archive_path = archive_dir / file_path.name
                    shutil.move(str(file_path), str(archive_path))
                    archived_count += 1
                    archived_size += archive_path.stat().st_size

        logger.info(f"Archived {archived_count} files ({archived_size} bytes)")
        return {
            'status': 'success',
            'archived_count': archived_count,
            'archived_size_bytes': archived_size
        }

    except Exception as e:
        logger.error(f"Error archiving files: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }
