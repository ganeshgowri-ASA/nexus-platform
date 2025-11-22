"""
NEXUS Platform Database Package.

Re-exports database connection utilities from database.connection
for backwards compatibility.
"""

# Re-export everything from connection module
from database.connection import (
    Base,
    engine,
    SessionLocal,
    get_db,
    get_db_context,
    get_session,
    init_db,
    init_database,
    drop_database,
    get_table_names,
    crud,
    CRUDBase,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_context",
    "get_session",
    "init_db",
    "init_database",
    "drop_database",
    "get_table_names",
    "crud",
    "CRUDBase",
]

__version__ = "1.0.0"
