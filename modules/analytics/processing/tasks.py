"""
Async Tasks

Celery tasks for analytics processing.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from modules.analytics.core.aggregator import DataAggregator
from modules.analytics.core.processor import EventProcessor
from modules.analytics.processing.celery_app import get_celery
from modules.analytics.storage.database import get_database
from shared.constants import AggregationPeriod
from shared.utils import get_utc_now

logger = logging.getLogger(__name__)

app = get_celery()


@app.task(name="modules.analytics.processing.tasks.process_events_task")
def process_events_task(batch_size: int = 1000) -> dict:
    """
    Process unprocessed events.

    Args:
        batch_size: Number of events to process

    Returns:
        Task result dictionary
    """
    try:
        db = get_database()
        processor = EventProcessor(db)

        count = processor.process_events(batch_size)

        logger.info(f"Processed {count} events")
        return {"status": "success", "events_processed": count}

    except Exception as e:
        logger.error(f"Error in process_events_task: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@app.task(name="modules.analytics.processing.tasks.aggregate_metrics_task")
def aggregate_metrics_task(hours: int = 1) -> dict:
    """
    Aggregate metrics for time period.

    Args:
        hours: Number of hours to aggregate

    Returns:
        Task result dictionary
    """
    try:
        db = get_database()
        aggregator = DataAggregator(db)

        end_date = get_utc_now()
        start_date = end_date - timedelta(hours=hours)

        with db.session() as session:
            # Aggregate events
            event_metrics = aggregator.aggregate_events(
                session,
                start_date,
                end_date,
                period=AggregationPeriod.HOUR
            )

            # Calculate session metrics
            session_metrics = aggregator.calculate_session_metrics(
                session,
                start_date,
                end_date
            )

            session.commit()

        logger.info(f"Aggregated metrics for {hours} hours")
        return {
            "status": "success",
            "event_metrics": len(event_metrics),
            "session_metrics": session_metrics
        }

    except Exception as e:
        logger.error(f"Error in aggregate_metrics_task: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@app.task(name="modules.analytics.processing.tasks.cleanup_exports_task")
def cleanup_exports_task() -> dict:
    """
    Clean up expired export files.

    Returns:
        Task result dictionary
    """
    try:
        db = get_database()
        from modules.analytics.storage.repositories import ExportJobRepository

        repo = ExportJobRepository()

        with db.session() as session:
            expired = repo.get_expired(session)

            # Delete expired exports
            for export in expired:
                # Delete file if exists
                if export.file_path:
                    import os
                    if os.path.exists(export.file_path):
                        os.remove(export.file_path)

                # Delete record
                repo.delete(session, export.id)

            session.commit()

        logger.info(f"Cleaned up {len(expired)} expired exports")
        return {"status": "success", "cleaned": len(expired)}

    except Exception as e:
        logger.error(f"Error in cleanup_exports_task: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
