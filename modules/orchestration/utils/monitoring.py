"""Monitoring and metrics collection using Prometheus."""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
from typing import Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Create metrics registry
registry = CollectorRegistry()

# Workflow metrics
workflow_executions_total = Counter(
    "workflow_executions_total",
    "Total number of workflow executions",
    ["workflow_id", "status"],
    registry=registry,
)

workflow_execution_duration = Histogram(
    "workflow_execution_duration_seconds",
    "Workflow execution duration in seconds",
    ["workflow_id"],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600],
    registry=registry,
)

active_workflows = Gauge(
    "active_workflows",
    "Number of currently running workflows",
    registry=registry,
)

# Task metrics
task_executions_total = Counter(
    "task_executions_total",
    "Total number of task executions",
    ["task_type", "status"],
    registry=registry,
)

task_execution_duration = Histogram(
    "task_execution_duration_seconds",
    "Task execution duration in seconds",
    ["task_type"],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 300, 600],
    registry=registry,
)

task_retries_total = Counter(
    "task_retries_total",
    "Total number of task retries",
    ["task_type"],
    registry=registry,
)

# System metrics
celery_queue_length = Gauge(
    "celery_queue_length",
    "Number of tasks in Celery queue",
    ["queue"],
    registry=registry,
)

redis_connections = Gauge(
    "redis_connections",
    "Number of Redis connections",
    registry=registry,
)


class MetricsCollector:
    """Metrics collector for workflow orchestration."""

    @staticmethod
    def record_workflow_execution(
        workflow_id: int, status: str, duration: Optional[float] = None
    ):
        """Record workflow execution metrics."""
        workflow_executions_total.labels(
            workflow_id=str(workflow_id), status=status
        ).inc()

        if duration:
            workflow_execution_duration.labels(
                workflow_id=str(workflow_id)
            ).observe(duration)

    @staticmethod
    def record_task_execution(
        task_type: str, status: str, duration: Optional[float] = None
    ):
        """Record task execution metrics."""
        task_executions_total.labels(task_type=task_type, status=status).inc()

        if duration:
            task_execution_duration.labels(task_type=task_type).observe(duration)

    @staticmethod
    def record_task_retry(task_type: str):
        """Record task retry."""
        task_retries_total.labels(task_type=task_type).inc()

    @staticmethod
    def set_active_workflows(count: int):
        """Set number of active workflows."""
        active_workflows.set(count)

    @staticmethod
    def set_queue_length(queue: str, length: int):
        """Set Celery queue length."""
        celery_queue_length.labels(queue=queue).set(length)

    @staticmethod
    def set_redis_connections(count: int):
        """Set Redis connections count."""
        redis_connections.set(count)


def track_execution_time(metric_name: str = None):
    """Decorator to track execution time."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                if metric_name:
                    logger.info(f"{metric_name} took {duration:.2f} seconds")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{metric_name or func.__name__} failed after {duration:.2f} seconds: {e}"
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if metric_name:
                    logger.info(f"{metric_name} took {duration:.2f} seconds")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{metric_name or func.__name__} failed after {duration:.2f} seconds: {e}"
                )
                raise

        # Check if function is async
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Metrics collector instance
metrics = MetricsCollector()
