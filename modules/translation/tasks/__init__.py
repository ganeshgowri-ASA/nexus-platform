"""
Celery tasks for translation module
"""

from .celery_tasks import app, process_batch_translation

__all__ = ["app", "process_batch_translation"]
