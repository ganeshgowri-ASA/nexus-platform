"""
Database initialization script.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import init_db, drop_db, engine
from config.settings import settings
from core.utils import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """Initialize database."""
    logger.info("Initializing NEXUS database...")

    # Confirm if production
    if settings.ENVIRONMENT == "production":
        response = input("You are about to initialize production database. Continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Database initialization cancelled")
            return

    try:
        # Create tables
        init_db()
        logger.info("Database initialized successfully!")

        # Print created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        logger.info(f"Created {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table}")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
