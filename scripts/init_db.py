"""
Database initialization script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config.database import init_db, engine
from src.database.models import Base
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Initialize the database"""
    logger.info("Initializing database...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        logger.info("✅ Database initialized successfully!")
        logger.info("Tables created:")

        # List all tables
        for table in Base.metadata.sorted_tables:
            logger.info(f"  - {table.name}")

    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {str(e)}")
        raise


if __name__ == "__main__":
    main()
