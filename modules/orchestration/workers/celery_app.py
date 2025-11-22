"""Celery application for distributed task execution."""

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from kombu import Exchange, Queue
import logging

from ..config.settings import settings

# Create Celery app
celery_app = Celery(
    "nexus_orchestration",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue="nexus_default",
    task_default_exchange="nexus",
    task_default_routing_key="nexus.default",
)

# Define queues
celery_app.conf.task_queues = (
    Queue("nexus_default", Exchange("nexus"), routing_key="nexus.default"),
    Queue("nexus_high_priority", Exchange("nexus"), routing_key="nexus.high"),
    Queue("nexus_low_priority", Exchange("nexus"), routing_key="nexus.low"),
)

# Configure task routes
celery_app.conf.task_routes = {
    "nexus_orchestration.workers.tasks.*": {"queue": "nexus_default"},
}

logger = logging.getLogger(__name__)


@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """Handler for task prerun signal."""
    logger.info(f"Task {task.name} [{task_id}] started")


@task_postrun.connect
def task_postrun_handler(task_id, task, *args, **kwargs):
    """Handler for task postrun signal."""
    logger.info(f"Task {task.name} [{task_id}] completed")


@task_failure.connect
def task_failure_handler(task_id, exception, *args, **kwargs):
    """Handler for task failure signal."""
    logger.error(f"Task [{task_id}] failed: {exception}")
