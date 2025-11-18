"""
NEXUS Database Manager & Query Builder Module

A comprehensive database management tool with visual query building,
schema design, data exploration, and performance monitoring.

Supports: PostgreSQL, MySQL, MongoDB, SQLite, SQL Server
"""

from typing import Dict, Any

__version__ = "1.0.0"
__author__ = "NEXUS Platform"

# Module components
__all__ = [
    "DatabaseManager",
    "QueryBuilder",
    "SchemaDesigner",
    "DataExplorer",
    "MigrationManager",
    "BackupManager",
    "PerformanceMonitor",
    "AdminManager",
]

# Re-export main classes
from .manager import DatabaseManager
from .query_builder import QueryBuilder
from .schema_designer import SchemaDesigner
from .data_explorer import DataExplorer
from .migration import MigrationManager
from .backup import BackupManager
from .performance import PerformanceMonitor
from .admin import AdminManager
