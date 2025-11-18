"""Database initialization script for NEXUS Platform."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import engine, SessionLocal
from database.models import Base
from loguru import logger


def init_database():
    """Initialize database tables."""
    logger.info("Initializing database...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")

        # Verify connection
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            logger.info("✅ Database connection verified!")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Error initializing database: {str(e)}")
        raise


def drop_all_tables():
    """Drop all database tables (use with caution!)."""
    logger.warning("Dropping all database tables...")

    response = input("Are you sure you want to drop all tables? (yes/no): ")
    if response.lower() != "yes":
        logger.info("Operation cancelled")
        return

    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ All tables dropped successfully!")
    except Exception as e:
        logger.error(f"❌ Error dropping tables: {str(e)}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all tables before creating"
    )

    args = parser.parse_args()

    if args.drop:
        drop_all_tables()

    init_database()
    logger.info("🎉 Database initialization complete!")
