"""
Task Statistics Utilities
Helper functions for gathering Celery task statistics
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_task_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get Celery task statistics for a given period

    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)

    Returns:
        Task statistics dictionary
    """
    try:
        from config.celery_config import celery_app
        from celery.result import AsyncResult

        # Get inspect instance
        inspect = celery_app.control.inspect()

        stats = {
            'active_tasks': 0,
            'scheduled_tasks': 0,
            'registered_tasks': 0,
            'active_workers': 0,
            'workers': {}
        }

        # Get active tasks
        active = inspect.active()
        if active:
            stats['active_tasks'] = sum(len(tasks) for tasks in active.values())
            stats['active_workers'] = len(active)
            stats['workers'] = active

        # Get scheduled tasks
        scheduled = inspect.scheduled()
        if scheduled:
            stats['scheduled_tasks'] = sum(len(tasks) for tasks in scheduled.values())

        # Get registered tasks
        registered = inspect.registered()
        if registered:
            all_tasks = set()
            for worker_tasks in registered.values():
                all_tasks.update(worker_tasks)
            stats['registered_tasks'] = len(all_tasks)
            stats['task_list'] = sorted(list(all_tasks))

        # Get reserved tasks
        reserved = inspect.reserved()
        if reserved:
            stats['reserved_tasks'] = sum(len(tasks) for tasks in reserved.values())

        return stats

    except Exception as e:
        logger.error(f"Error getting task statistics: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


def get_worker_stats() -> Dict[str, Any]:
    """
    Get Celery worker statistics

    Returns:
        Worker statistics dictionary
    """
    try:
        from config.celery_config import celery_app

        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if not stats:
            return {
                'status': 'no_workers',
                'message': 'No active workers found'
            }

        return {
            'status': 'ok',
            'worker_count': len(stats),
            'workers': stats
        }

    except Exception as e:
        logger.error(f"Error getting worker stats: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


def get_queue_lengths() -> Dict[str, int]:
    """
    Get lengths of all task queues

    Returns:
        Dictionary mapping queue names to lengths
    """
    try:
        import redis
        from config.settings import settings

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

        queue_lengths = {}
        for queue_name in queues:
            length = r.llen(queue_name)
            queue_lengths[queue_name] = length

        return queue_lengths

    except Exception as e:
        logger.error(f"Error getting queue lengths: {str(e)}")
        return {}
