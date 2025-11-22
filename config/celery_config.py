"""
Celery Configuration for Nexus Platform
"""
from celery import Celery
from config.settings import settings

# Initialize Celery app
celery_app = Celery(
    "nexus_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.email_tasks',
        'app.tasks.file_tasks',
        'app.tasks.ai_tasks',
        'app.tasks.report_tasks',
    ]
)

# Celery Configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task execution settings
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,

    # Task routing - Different queues for different task types
    task_routes={
        'app.tasks.email_tasks.*': {'queue': settings.TASK_QUEUE_EMAIL},
        'app.tasks.file_tasks.*': {'queue': settings.TASK_QUEUE_FILE_PROCESSING},
        'app.tasks.ai_tasks.*': {'queue': settings.TASK_QUEUE_AI},
        'app.tasks.report_tasks.*': {'queue': settings.TASK_QUEUE_REPORTS},
    },

    # Task priority settings
    task_default_priority=5,

    # Beat scheduler settings (for periodic tasks)
    beat_schedule={
        'cleanup-temp-files': {
            'task': 'app.tasks.file_tasks.cleanup_temp_files',
            'schedule': 3600.0,  # Every hour
        },
        'cleanup-old-results': {
            'task': 'app.tasks.maintenance_tasks.cleanup_old_results',
            'schedule': 86400.0,  # Every day
        },
    },
)

# Optional: Task annotations for specific task configurations
celery_app.conf.task_annotations = {
    'app.tasks.ai_tasks.*': {
        'rate_limit': '10/m',  # 10 AI tasks per minute
        'time_limit': 600,  # 10 minutes for AI tasks
    },
    'app.tasks.file_tasks.process_large_file': {
        'time_limit': 1800,  # 30 minutes for large files
    },
}
