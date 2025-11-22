"""
Database module for NEXUS Platform.

Provides database connection, session management, and models for authentication.
"""
from .models import (
    Base,
    User,
    Role,
    Permission,
    UserSession,
    LoginHistory,
    UserRole
)
from .connection import (
    get_db,
    init_db,
    create_tables,
    SessionLocal,
    engine
)

# Also re-export the advanced database management tools
try:
    from .manager import DatabaseManager
    from .query_builder import QueryBuilder
    from .schema_designer import SchemaDesigner
    from .data_explorer import DataExplorer
    from .migration import MigrationManager
    from .backup import BackupManager
    from .performance import PerformanceMonitor
    from .admin import AdminManager

    __all__ = [
        # Core database components
        'Base',
        'User',
        'Role',
        'Permission',
        'UserSession',
        'LoginHistory',
        'UserRole',
        'get_db',
        'init_db',
        'create_tables',
        'SessionLocal',
        'engine',
        # Advanced tools
        'DatabaseManager',
        'QueryBuilder',
        'SchemaDesigner',
        'DataExplorer',
        'MigrationManager',
        'BackupManager',
        'PerformanceMonitor',
        'AdminManager',
    ]
except ImportError:
    # Advanced tools may not be available in all deployments
    __all__ = [
        'Base',
        'User',
        'Role',
        'Permission',
        'UserSession',
        'LoginHistory',
        'UserRole',
        'get_db',
        'init_db',
        'create_tables',
        'SessionLocal',
        'engine',
    ]
