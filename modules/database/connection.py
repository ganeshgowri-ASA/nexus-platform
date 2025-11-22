"""
Database connection and session management.
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .models import Base, Role, Permission

# Get database URL from environment or use SQLite as default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./nexus_platform.db"
)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
else:
    # PostgreSQL/MySQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def init_db() -> None:
    """
    Initialize database with default data.
    Creates default roles and permissions.
    """
    create_tables()

    db = SessionLocal()
    try:
        # Check if roles already exist
        existing_roles = db.query(Role).count()
        if existing_roles > 0:
            print("ℹ️  Database already initialized")
            return

        # Create default permissions
        permissions = [
            # User management
            Permission(name="user.create", description="Create new users", module="user"),
            Permission(name="user.read", description="View user information", module="user"),
            Permission(name="user.update", description="Update user information", module="user"),
            Permission(name="user.delete", description="Delete users", module="user"),

            # Role management
            Permission(name="role.create", description="Create new roles", module="role"),
            Permission(name="role.read", description="View roles", module="role"),
            Permission(name="role.update", description="Update roles", module="role"),
            Permission(name="role.delete", description="Delete roles", module="role"),

            # System settings
            Permission(name="settings.read", description="View system settings", module="settings"),
            Permission(name="settings.update", description="Update system settings", module="settings"),

            # Dashboard access
            Permission(name="dashboard.view", description="Access dashboard", module="dashboard"),
            Permission(name="dashboard.admin", description="Access admin dashboard", module="dashboard"),

            # Reports
            Permission(name="reports.view", description="View reports", module="reports"),
            Permission(name="reports.create", description="Create reports", module="reports"),
            Permission(name="reports.export", description="Export reports", module="reports"),
        ]

        db.add_all(permissions)
        db.flush()  # Flush to get permission IDs

        # Create default roles with permissions
        admin_role = Role(
            name="admin",
            description="Administrator with full access"
        )
        admin_role.permissions = permissions  # Admin gets all permissions

        manager_role = Role(
            name="manager",
            description="Manager with elevated privileges"
        )
        # Manager gets most permissions except role/user management
        manager_permissions = [p for p in permissions if not p.name.startswith(("role.", "user.delete"))]
        manager_role.permissions = manager_permissions

        user_role = Role(
            name="user",
            description="Standard user with basic access"
        )
        # User gets read-only access
        user_permissions = [
            p for p in permissions
            if p.name in ["user.read", "dashboard.view", "reports.view"]
        ]
        user_role.permissions = user_permissions

        guest_role = Role(
            name="guest",
            description="Guest with minimal access"
        )
        # Guest gets very limited access
        guest_permissions = [p for p in permissions if p.name == "dashboard.view"]
        guest_role.permissions = guest_permissions

        db.add_all([admin_role, manager_role, user_role, guest_role])
        db.commit()

        print("✅ Database initialized with default roles and permissions")
        print(f"   - Created {len(permissions)} permissions")
        print("   - Created 4 roles: admin, manager, user, guest")

    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing database: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
