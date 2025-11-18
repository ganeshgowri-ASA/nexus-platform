#!/usr/bin/env python
"""
Celery worker startup script for NEXUS Platform.

This script starts the Celery worker for processing asynchronous tasks such as:
- Document processing (OCR, conversion, thumbnail generation)
- AI operations (summarization, classification, entity extraction)
- Bulk operations
- Email notifications
- Scheduled maintenance tasks

Usage:
    python scripts/celery_worker.py [OPTIONS]

Options:
    --loglevel LEVEL    Set log level (default: info)
    --concurrency N     Number of worker processes (default: 4)
    --queues QUEUES     Comma-separated list of queues (default: all)
    --pool TYPE         Pool type: prefork, eventlet, gevent (default: prefork)
    --beat              Also start Celery beat scheduler
    --flower            Also start Flower monitoring (port 5555)
    --help              Show this help message
"""

import argparse
import multiprocessing
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def get_celery_app():
    """Get or create Celery application."""
    from celery import Celery

    # Create Celery app
    app = Celery(
        "nexus",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    # Configure Celery
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max
        task_soft_time_limit=3000,  # 50 minutes soft limit
        worker_prefetch_multiplier=4,
        worker_max_tasks_per_child=1000,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_routes={
            "nexus.tasks.document.*": {"queue": "document"},
            "nexus.tasks.ai.*": {"queue": "ai"},
            "nexus.tasks.email.*": {"queue": "email"},
            "nexus.tasks.maintenance.*": {"queue": "maintenance"},
        },
        beat_schedule={
            "cleanup-temp-files": {
                "task": "nexus.tasks.maintenance.cleanup_temp_files",
                "schedule": 3600.0,  # Every hour
            },
            "process-retention-policies": {
                "task": "nexus.tasks.maintenance.process_retention_policies",
                "schedule": 86400.0,  # Every day
            },
            "update-search-index": {
                "task": "nexus.tasks.maintenance.update_search_index",
                "schedule": 1800.0,  # Every 30 minutes
            },
        },
    )

    # Auto-discover tasks
    app.autodiscover_tasks(
        [
            "modules.documents",
            "backend.tasks",
        ],
        force=True,
    )

    return app


def start_worker(
    loglevel: str = "info",
    concurrency: int = None,
    queues: str = None,
    pool: str = "prefork",
) -> None:
    """
    Start Celery worker.

    Args:
        loglevel: Log level
        concurrency: Number of worker processes
        queues: Comma-separated queue names
        pool: Pool type
    """
    app = get_celery_app()

    if concurrency is None:
        concurrency = multiprocessing.cpu_count()

    # Build worker arguments
    worker_args = [
        "--loglevel", loglevel,
        "--concurrency", str(concurrency),
        "--pool", pool,
    ]

    if queues:
        worker_args.extend(["--queues", queues])

    logger.info(f"Starting Celery worker with {concurrency} processes...")
    logger.info(f"Broker: {settings.CELERY_BROKER_URL}")
    logger.info(f"Backend: {settings.CELERY_RESULT_BACKEND}")

    if queues:
        logger.info(f"Queues: {queues}")
    else:
        logger.info("Queues: all")

    # Start worker
    app.worker_main(worker_args)


def start_beat() -> None:
    """Start Celery beat scheduler."""
    app = get_celery_app()

    logger.info("Starting Celery beat scheduler...")

    app.start(["celery", "beat", "--loglevel=info"])


def start_flower(port: int = 5555) -> None:
    """
    Start Flower monitoring tool.

    Args:
        port: Port to run Flower on
    """
    logger.info(f"Starting Flower on port {port}...")

    os.system(
        f"celery -A scripts.celery_worker:get_celery_app flower "
        f"--port={port} --broker={settings.CELERY_BROKER_URL}"
    )


def main() -> int:
    """Main function to start Celery services."""
    parser = argparse.ArgumentParser(
        description="Start Celery worker for NEXUS Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--loglevel",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Number of worker processes (default: CPU count)",
    )
    parser.add_argument(
        "--queues",
        default=None,
        help="Comma-separated list of queues to process",
    )
    parser.add_argument(
        "--pool",
        default="prefork",
        choices=["prefork", "eventlet", "gevent", "solo"],
        help="Pool type (default: prefork)",
    )
    parser.add_argument(
        "--beat",
        action="store_true",
        help="Also start Celery beat scheduler",
    )
    parser.add_argument(
        "--flower",
        action="store_true",
        help="Also start Flower monitoring",
    )
    parser.add_argument(
        "--flower-port",
        type=int,
        default=5555,
        help="Flower port (default: 5555)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("NEXUS Platform - Celery Worker")
    print("=" * 70)
    print()

    try:
        # Start Flower in background if requested
        if args.flower:
            import subprocess
            subprocess.Popen([
                sys.executable,
                "-m", "flower",
                "--broker", settings.CELERY_BROKER_URL,
                "--port", str(args.flower_port),
            ])
            print(f"✓ Flower started on http://localhost:{args.flower_port}")

        # Start beat in background if requested
        if args.beat:
            import subprocess
            subprocess.Popen([
                sys.executable,
                "-m", "celery",
                "-A", "scripts.celery_worker:get_celery_app",
                "beat",
                "--loglevel", args.loglevel,
            ])
            print("✓ Celery beat started")

        print()
        print("Starting Celery worker...")
        print(f"  Log level: {args.loglevel}")
        print(f"  Concurrency: {args.concurrency or multiprocessing.cpu_count()}")
        print(f"  Pool: {args.pool}")
        print(f"  Queues: {args.queues or 'all'}")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 70)
        print()

        # Start worker (blocking)
        start_worker(
            loglevel=args.loglevel,
            concurrency=args.concurrency,
            queues=args.queues,
            pool=args.pool,
        )

        return 0

    except KeyboardInterrupt:
        print("\n\nShutting down Celery worker...")
        return 0
    except Exception as e:
        logger.exception("Failed to start Celery worker")
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
