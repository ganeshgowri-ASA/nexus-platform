#!/usr/bin/env python3
"""
NEXUS Platform - Main Application Entry Point

Launches the NEXUS platform with all integrated modules.
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
import click
from typing import Optional

from shared.config import get_settings
from shared.logger import setup_logging, get_logger

settings = get_settings()
logger = get_logger(__name__)


@click.group()
def cli() -> None:
    """NEXUS Platform CLI"""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8501, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def streamlit(host: str, port: int, reload: bool) -> None:
    """Launch Streamlit dashboard"""
    import subprocess

    setup_logging(
        log_level=settings.log_level,
        json_format=settings.is_production,
    )

    logger.info(f"Starting Streamlit dashboard on {host}:{port}")

    cmd = [
        "streamlit",
        "run",
        "modules/analytics/ui/app.py",
        f"--server.address={host}",
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]

    subprocess.run(cmd)


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.option("--workers", default=4, help="Number of workers")
def api(host: str, port: int, reload: bool, workers: int) -> None:
    """Launch FastAPI REST API"""
    import subprocess

    setup_logging(
        log_level=settings.log_level,
        json_format=settings.is_production,
    )

    logger.info(f"Starting FastAPI server on {host}:{port} with {workers} workers")

    cmd = [
        "uvicorn",
        "modules.analytics.api.main:app",
        f"--host={host}",
        f"--port={port}",
        f"--workers={workers}",
    ]

    if reload:
        cmd.append("--reload")

    subprocess.run(cmd)


@cli.command()
@click.option("--loglevel", default="info", help="Log level")
def celery_worker(loglevel: str) -> None:
    """Launch Celery worker for async task processing"""
    import subprocess

    setup_logging(
        log_level=settings.log_level,
        json_format=settings.is_production,
    )

    logger.info("Starting Celery worker")

    cmd = [
        "celery",
        "-A",
        "modules.analytics.processing.celery_app",
        "worker",
        f"--loglevel={loglevel}",
        "--pool=prefork",
        "--concurrency=4",
    ]

    subprocess.run(cmd)


@cli.command()
@click.option("--loglevel", default="info", help="Log level")
def celery_beat(loglevel: str) -> None:
    """Launch Celery beat scheduler"""
    import subprocess

    setup_logging(
        log_level=settings.log_level,
        json_format=settings.is_production,
    )

    logger.info("Starting Celery beat scheduler")

    cmd = [
        "celery",
        "-A",
        "modules.analytics.processing.celery_app",
        "beat",
        f"--loglevel={loglevel}",
    ]

    subprocess.run(cmd)


@cli.command()
def flower() -> None:
    """Launch Flower (Celery monitoring tool)"""
    import subprocess

    setup_logging(
        log_level=settings.log_level,
        json_format=settings.is_production,
    )

    logger.info("Starting Flower monitoring on port 5555")

    cmd = [
        "celery",
        "-A",
        "modules.analytics.processing.celery_app",
        "flower",
        "--port=5555",
    ]

    subprocess.run(cmd)


@cli.command()
def init_db() -> None:
    """Initialize database with schema"""
    import subprocess

    setup_logging(log_level=settings.log_level)

    logger.info("Initializing database...")

    # Run Alembic migrations
    cmd = ["alembic", "upgrade", "head"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        logger.info("✓ Database initialized successfully")
    else:
        logger.error(f"✗ Database initialization failed: {result.stderr}")
        sys.exit(1)


@cli.command()
def create_migration() -> None:
    """Create a new database migration"""
    import subprocess

    message = click.prompt("Migration message")

    logger.info(f"Creating migration: {message}")

    cmd = ["alembic", "revision", "--autogenerate", "-m", message]
    subprocess.run(cmd)


@cli.command()
def test() -> None:
    """Run test suite"""
    import subprocess

    logger.info("Running test suite...")

    cmd = [
        "pytest",
        "modules/analytics/tests/",
        "-v",
        "--cov=modules/analytics",
        "--cov-report=html",
        "--cov-report=term-missing",
    ]

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@cli.command()
def lint() -> None:
    """Run code linting"""
    import subprocess

    logger.info("Running linters...")

    # Ruff
    logger.info("Running ruff...")
    subprocess.run(["ruff", "check", "."])

    # MyPy
    logger.info("Running mypy...")
    subprocess.run(["mypy", "modules/", "shared/"])

    logger.info("✓ Linting complete")


@cli.command()
def format_code() -> None:
    """Format code with black and isort"""
    import subprocess

    logger.info("Formatting code...")

    subprocess.run(["black", "."])
    subprocess.run(["isort", "."])

    logger.info("✓ Code formatted")


@cli.command()
def health_check() -> None:
    """Check health of all services"""
    import asyncio
    from modules.analytics.storage.database import check_database_health
    from modules.analytics.storage.cache import check_cache_health

    async def check() -> None:
        setup_logging(log_level=settings.log_level)

        logger.info("Checking service health...")

        # Check database
        db_healthy = await check_database_health()
        status = "✓" if db_healthy else "✗"
        logger.info(f"{status} Database: {'Healthy' if db_healthy else 'Unhealthy'}")

        # Check cache
        cache_healthy = await check_cache_health()
        status = "✓" if cache_healthy else "✗"
        logger.info(f"{status} Redis: {'Healthy' if cache_healthy else 'Unhealthy'}")

        if db_healthy and cache_healthy:
            logger.info("✓ All services healthy")
        else:
            logger.error("✗ Some services are unhealthy")
            sys.exit(1)

    asyncio.run(check())


@cli.command()
def version() -> None:
    """Show version information"""
    from modules.analytics import __version__

    click.echo(f"NEXUS Platform v{__version__}")
    click.echo(f"Analytics Module v{__version__}")
    click.echo(f"Environment: {settings.environment}")


if __name__ == "__main__":
    cli()
