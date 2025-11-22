"""
Core Database Module

Re-exports database functionality from config.database for convenience.
"""

from config.database import (
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    get_async_db,
    init_db,
    drop_db,
    check_db_connection,
)

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_session",
    "get_async_db",
    "init_db",
    "drop_db",
    "check_db_connection",
]
