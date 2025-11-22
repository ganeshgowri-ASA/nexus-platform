<<<<<<< HEAD
<<<<<<< HEAD
#!/usr/bin/env python
"""
Database initialization script for NEXUS Platform.

This script performs the following operations:
1. Creates database tables if they don't exist
2. Runs pending Alembic migrations
3. Creates default admin user if specified
4. Sets up initial system configuration

Usage:
    python scripts/init_db.py [OPTIONS]

Options:
    --drop          Drop all tables before creating (WARNING: destructive)
    --migrate-only  Only run migrations, don't create tables
    --create-admin  Create default admin user
    --admin-email   Admin email (default: admin@nexus.local)
    --admin-password Admin password (default: Admin@123)
    --skip-migrations Skip Alembic migrations
    --help          Show this help message
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.security import get_password_hash
from backend.database import Base, engine, get_db_session, import_models
from backend.models.user import User

logger = get_logger(__name__)
settings = get_settings()


def run_migrations(alembic_cfg: Config) -> None:
    """
    Run Alembic migrations to bring database to latest version.

    Args:
        alembic_cfg: Alembic configuration
    """
    logger.info("Running Alembic migrations...")
    try:
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def create_tables(drop_first: bool = False) -> None:
    """
    Create all database tables.

    Args:
        drop_first: If True, drop all tables before creating
    """
    # Import all models to ensure they're registered
    import_models()

    if drop_first:
        logger.warning("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("Tables dropped")

    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully")


def create_admin_user(email: str, password: str, username: str = "admin") -> User:
    """
    Create default admin user.

    Args:
        email: Admin email
        password: Admin password
        username: Admin username

    Returns:
        User: Created admin user
    """
    db = get_db_session()
    try:
        # Check if admin user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()

        if existing_user:
            logger.warning(f"Admin user already exists: {existing_user.email}")
            return existing_user

        # Create admin user
        logger.info(f"Creating admin user: {email}")
        admin_user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name="System Administrator",
            is_active=True,
            is_admin=True,
            is_superuser=True,
            is_verified=True,
            password_changed_at=datetime.utcnow(),
            storage_quota=107374182400,  # 100GB for admin
            storage_used=0,
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        logger.info(f"Admin user created successfully: {admin_user.email}")
        return admin_user

    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def verify_database_connection() -> bool:
    """
    Verify database connection.

    Returns:
        bool: True if connection successful
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.info("Database connection verified")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


def get_database_version() -> str:
    """
    Get database version information.

    Returns:
        str: Database version
    """
    try:
        with engine.connect() as conn:
            if "postgresql" in settings.DATABASE_URL:
                result = conn.execute(text("SELECT version()"))
                return result.fetchone()[0]
            elif "sqlite" in settings.DATABASE_URL:
                result = conn.execute(text("SELECT sqlite_version()"))
                return f"SQLite {result.fetchone()[0]}"
            else:
                return "Unknown"
    except Exception as e:
        logger.error(f"Failed to get database version: {e}")
        return "Unknown"


def main() -> int:
    """
    Main function to initialize database.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Initialize NEXUS Platform database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all tables before creating (WARNING: destructive)",
    )
    parser.add_argument(
        "--migrate-only",
        action="store_true",
        help="Only run migrations, don't create tables",
    )
    parser.add_argument(
        "--create-admin",
        action="store_true",
        help="Create default admin user",
    )
    parser.add_argument(
        "--admin-email",
        default="admin@nexus.local",
        help="Admin email address",
    )
    parser.add_argument(
        "--admin-password",
        default="Admin@123",
        help="Admin password",
    )
    parser.add_argument(
        "--admin-username",
        default="admin",
        help="Admin username",
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip Alembic migrations",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("NEXUS Platform - Database Initialization")
    print("=" * 70)
    print()

    # Verify database connection
    print("Verifying database connection...")
    if not verify_database_connection():
        print("ERROR: Database connection failed!")
        print(f"Database URL: {settings.DATABASE_URL}")
        return 1

    db_version = get_database_version()
    print(f"Database: {db_version}")
    print()

    try:
        # Create/drop tables
        if not args.migrate_only:
            if args.drop:
                print("WARNING: About to drop all tables!")
                response = input("Are you sure? Type 'yes' to continue: ")
                if response.lower() != "yes":
                    print("Aborted.")
                    return 0

            create_tables(drop_first=args.drop)
            print("✓ Database tables created")
            print()

        # Run migrations
        if not args.skip_migrations:
            alembic_ini = project_root / "alembic.ini"
            if alembic_ini.exists():
                print("Running database migrations...")
                alembic_cfg = Config(str(alembic_ini))
                alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
                run_migrations(alembic_cfg)
                print("✓ Migrations completed")
                print()
            else:
                print("⚠ alembic.ini not found, skipping migrations")
                print()

        # Create admin user
        if args.create_admin:
            print("Creating admin user...")
            admin_user = create_admin_user(
                email=args.admin_email,
                password=args.admin_password,
                username=args.admin_username,
            )
            print(f"✓ Admin user: {admin_user.email}")
            print(f"  Username: {admin_user.username}")
            print(f"  Password: {args.admin_password}")
            print()

        print("=" * 70)
        print("Database initialization completed successfully!")
        print("=" * 70)
        return 0

    except Exception as e:
        logger.exception("Database initialization failed")
        print(f"\nERROR: {e}")
        print("\nDatabase initialization failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
=======
"""
Database initialization script
"""
=======
"""
Database initialization script.
"""

>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
import sys
import os

# Add parent directory to path
<<<<<<< HEAD
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config.database import init_db, engine
from src.database.models import Base
from src.utils.logger import get_logger

=======
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import init_db, drop_db, engine
from config.settings import settings
from core.utils import setup_logging, get_logger

setup_logging()
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
logger = get_logger(__name__)


def main():
<<<<<<< HEAD
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
=======
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
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp


if __name__ == "__main__":
    main()
<<<<<<< HEAD
>>>>>>> origin/claude/build-rpa-module-011gc98wDCMg5EmJGgT8DFqE
=======
>>>>>>> origin/claude/build-nexus-pipeline-module-01QTVSb9CH4TjcrrT8nhjeJp
