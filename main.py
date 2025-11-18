"""
Main entry point for NEXUS Content Calendar.

Run this script to start all services.
"""
import subprocess
import sys
import argparse
from pathlib import Path


def run_api():
    """Start FastAPI server."""
    print("Starting FastAPI server...")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "api:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])


def run_streamlit():
    """Start Streamlit UI."""
    print("Starting Streamlit UI...")
    subprocess.run([
        sys.executable, "-m", "streamlit",
        "run",
        "modules/content_calendar/streamlit_ui.py",
        "--server.port", "8501"
    ])


def run_celery_worker():
    """Start Celery worker."""
    print("Starting Celery worker...")
    subprocess.run([
        "celery", "-A", "celery_app",
        "worker",
        "--loglevel=info"
    ])


def run_celery_beat():
    """Start Celery beat scheduler."""
    print("Starting Celery beat...")
    subprocess.run([
        "celery", "-A", "celery_app",
        "beat",
        "--loglevel=info"
    ])


def init_database():
    """Initialize database."""
    print("Initializing database...")
    from database import init_db
    init_db()
    print("Database initialized successfully!")


def run_tests():
    """Run test suite."""
    print("Running tests...")
    subprocess.run([
        sys.executable, "-m", "pytest",
        "-v",
        "--cov=modules",
        "--cov-report=html"
    ])


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="NEXUS Content Calendar - Management Tool"
    )

    parser.add_argument(
        "command",
        choices=[
            "api",
            "streamlit",
            "celery-worker",
            "celery-beat",
            "init-db",
            "test",
            "all"
        ],
        help="Command to run"
    )

    args = parser.parse_args()

    if args.command == "api":
        run_api()
    elif args.command == "streamlit":
        run_streamlit()
    elif args.command == "celery-worker":
        run_celery_worker()
    elif args.command == "celery-beat":
        run_celery_beat()
    elif args.command == "init-db":
        init_database()
    elif args.command == "test":
        run_tests()
    elif args.command == "all":
        print("Starting all services...")
        print("Note: Use docker-compose for production deployment")
        print("Run each service in a separate terminal:")
        print("  python main.py api")
        print("  python main.py streamlit")
        print("  python main.py celery-worker")
        print("  python main.py celery-beat")


if __name__ == "__main__":
    main()
