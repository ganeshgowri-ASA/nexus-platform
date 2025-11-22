"""
Backup and Restore Manager

Automated database backups, point-in-time recovery,
backup scheduling, and restore functionality.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import os
import gzip
import json
import logging
import shutil
from pathlib import Path


class BackupType(Enum):
    """Backup types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"


class BackupStatus(Enum):
    """Backup status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CompressionType(Enum):
    """Compression types"""
    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"


@dataclass
class BackupConfig:
    """Backup configuration"""
    backup_dir: str
    compression: CompressionType = CompressionType.GZIP
    max_backups: int = 10
    include_tables: Optional[List[str]] = None
    exclude_tables: Optional[List[str]] = None
    verify_backup: bool = True


@dataclass
class BackupInfo:
    """Backup information"""
    id: str
    name: str
    backup_type: BackupType
    created_at: datetime
    size_bytes: int
    filepath: str
    status: BackupStatus
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tables: List[str] = field(default_factory=list)
    duration_seconds: float = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "backup_type": self.backup_type.value,
            "created_at": self.created_at.isoformat(),
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_bytes / (1024 * 1024), 2),
            "filepath": self.filepath,
            "status": self.status.value,
            "error": self.error,
            "metadata": self.metadata,
            "tables": self.tables,
            "duration_seconds": self.duration_seconds
        }


class BackupManager:
    """
    Backup and Restore Manager

    Manages automated backups, point-in-time recovery,
    and backup scheduling.
    """

    def __init__(self, connection, config: Optional[BackupConfig] = None):
        """
        Initialize backup manager

        Args:
            connection: DatabaseConnection instance
            config: Backup configuration
        """
        self.connection = connection
        self.config = config or BackupConfig(backup_dir="./backups")
        self.backups: Dict[str, BackupInfo] = {}
        self.logger = logging.getLogger("database.backup")
        self.scheduled_backups: List[Dict[str, Any]] = []

        # Ensure backup directory exists
        Path(self.config.backup_dir).mkdir(parents=True, exist_ok=True)

        # Load existing backups
        self._load_backup_catalog()

    def create_backup(
        self,
        name: Optional[str] = None,
        backup_type: BackupType = BackupType.FULL,
        tables: Optional[List[str]] = None
    ) -> BackupInfo:
        """
        Create a database backup

        Args:
            name: Backup name (auto-generated if None)
            backup_type: Type of backup
            tables: Specific tables to backup (None = all)

        Returns:
            BackupInfo object
        """
        start_time = datetime.now()

        # Generate backup name
        if not name:
            name = f"backup_{start_time.strftime('%Y%m%d_%H%M%S')}"

        backup_id = f"{name}_{start_time.timestamp()}"

        # Create backup info
        backup_info = BackupInfo(
            id=backup_id,
            name=name,
            backup_type=backup_type,
            created_at=start_time,
            size_bytes=0,
            filepath="",
            status=BackupStatus.RUNNING
        )

        self.logger.info(f"Creating backup: {name}")

        try:
            # Determine tables to backup
            if tables is None:
                if self.config.include_tables:
                    tables = self.config.include_tables
                else:
                    tables = self.connection.get_tables()

                if self.config.exclude_tables:
                    tables = [t for t in tables if t not in self.config.exclude_tables]

            backup_info.tables = tables

            # Create backup file
            filepath = self._create_backup_file(backup_id, backup_type, tables)
            backup_info.filepath = filepath

            # Get file size
            backup_info.size_bytes = os.path.getsize(filepath)

            # Verify backup if configured
            if self.config.verify_backup:
                self._verify_backup(filepath)

            # Complete backup
            backup_info.status = BackupStatus.COMPLETED
            backup_info.duration_seconds = (datetime.now() - start_time).total_seconds()

            # Store backup info
            self.backups[backup_id] = backup_info
            self._save_backup_catalog()

            # Clean old backups
            self._cleanup_old_backups()

            self.logger.info(
                f"Backup completed: {name} "
                f"({backup_info.size_bytes / (1024 * 1024):.2f} MB in "
                f"{backup_info.duration_seconds:.2f}s)"
            )

            return backup_info

        except Exception as e:
            backup_info.status = BackupStatus.FAILED
            backup_info.error = str(e)
            self.logger.error(f"Backup failed: {e}")
            raise

    def _create_backup_file(
        self,
        backup_id: str,
        backup_type: BackupType,
        tables: List[str]
    ) -> str:
        """Create backup file"""
        # Generate filepath
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{backup_id}.sql"

        if self.config.compression == CompressionType.GZIP:
            filename += ".gz"

        filepath = os.path.join(self.config.backup_dir, filename)

        # Generate SQL dump
        sql_dump = []

        # Add header
        sql_dump.append("-- Database Backup")
        sql_dump.append(f"-- Created: {datetime.now().isoformat()}")
        sql_dump.append(f"-- Backup Type: {backup_type.value}")
        sql_dump.append(f"-- Tables: {', '.join(tables)}")
        sql_dump.append("")

        # Backup each table
        for table_name in tables:
            if backup_type in (BackupType.FULL, BackupType.SCHEMA_ONLY):
                # Add schema
                sql_dump.append(f"\n-- Schema for table: {table_name}")
                sql_dump.append(self._get_table_schema_sql(table_name))

            if backup_type in (BackupType.FULL, BackupType.DATA_ONLY):
                # Add data
                sql_dump.append(f"\n-- Data for table: {table_name}")
                sql_dump.append(self._get_table_data_sql(table_name))

        # Join SQL statements
        sql_content = "\n".join(sql_dump)

        # Write to file with optional compression
        if self.config.compression == CompressionType.GZIP:
            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                f.write(sql_content)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(sql_content)

        return filepath

    def _get_table_schema_sql(self, table_name: str) -> str:
        """Get CREATE TABLE statement"""
        # This is a simplified version
        # Real implementation would need database-specific logic
        schema = self.connection.get_table_schema(table_name)

        columns = []
        for col in schema:
            col_name = col.get('column_name') or col.get('name') or col.get('Field')
            col_type = col.get('data_type') or col.get('Type')
            nullable = col.get('is_nullable', 'YES')

            col_def = f"{col_name} {col_type}"
            if nullable == 'NO':
                col_def += " NOT NULL"

            columns.append(col_def)

        columns_sql = ",\n  ".join(columns)
        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n  {columns_sql}\n);\n"

    def _get_table_data_sql(self, table_name: str) -> str:
        """Get INSERT statements for table data"""
        # Get all data
        query = f"SELECT * FROM {table_name}"
        rows = self.connection.execute_query(query)

        if not rows:
            return f"-- No data in table {table_name}\n"

        insert_statements = []

        for row in rows:
            columns = list(row.keys())
            values = []

            for col in columns:
                value = row[col]
                if value is None:
                    values.append("NULL")
                elif isinstance(value, str):
                    values.append(f"'{value.replace('\'', '\'\'')}'")
                elif isinstance(value, (int, float)):
                    values.append(str(value))
                elif isinstance(value, bool):
                    values.append("TRUE" if value else "FALSE")
                elif isinstance(value, datetime):
                    values.append(f"'{value.isoformat()}'")
                else:
                    values.append(f"'{str(value)}'")

            columns_str = ", ".join(columns)
            values_str = ", ".join(values)
            insert_statements.append(
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
            )

        return "\n".join(insert_statements) + "\n"

    def restore_backup(
        self,
        backup_id: str,
        tables: Optional[List[str]] = None,
        drop_existing: bool = False
    ) -> None:
        """
        Restore from backup

        Args:
            backup_id: Backup ID to restore
            tables: Specific tables to restore (None = all)
            drop_existing: Drop existing tables before restore
        """
        if backup_id not in self.backups:
            raise ValueError(f"Backup '{backup_id}' not found")

        backup_info = self.backups[backup_id]
        self.logger.info(f"Restoring backup: {backup_info.name}")

        # Read backup file
        if backup_info.filepath.endswith('.gz'):
            with gzip.open(backup_info.filepath, 'rt', encoding='utf-8') as f:
                sql_content = f.read()
        else:
            with open(backup_info.filepath, 'r', encoding='utf-8') as f:
                sql_content = f.read()

        # Execute SQL statements
        statements = self._split_sql_statements(sql_content)

        for statement in statements:
            if not statement.strip() or statement.strip().startswith('--'):
                continue

            try:
                self.connection.execute_command(statement)
            except Exception as e:
                self.logger.error(f"Error executing statement: {e}")
                # Continue with next statement

        self.logger.info(f"Restore completed: {backup_info.name}")

    def list_backups(
        self,
        backup_type: Optional[BackupType] = None,
        limit: Optional[int] = None
    ) -> List[BackupInfo]:
        """
        List backups

        Args:
            backup_type: Filter by backup type
            limit: Limit number of results

        Returns:
            List of BackupInfo objects
        """
        backups = list(self.backups.values())

        # Filter by type
        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]

        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b.created_at, reverse=True)

        # Limit results
        if limit:
            backups = backups[:limit]

        return backups

    def get_backup_info(self, backup_id: str) -> BackupInfo:
        """Get backup information"""
        if backup_id not in self.backups:
            raise ValueError(f"Backup '{backup_id}' not found")
        return self.backups[backup_id]

    def delete_backup(self, backup_id: str) -> None:
        """Delete a backup"""
        if backup_id not in self.backups:
            raise ValueError(f"Backup '{backup_id}' not found")

        backup_info = self.backups[backup_id]

        # Delete file
        if os.path.exists(backup_info.filepath):
            os.remove(backup_info.filepath)

        # Remove from catalog
        del self.backups[backup_id]
        self._save_backup_catalog()

        self.logger.info(f"Deleted backup: {backup_info.name}")

    def schedule_backup(
        self,
        name: str,
        interval_hours: int,
        backup_type: BackupType = BackupType.FULL,
        tables: Optional[List[str]] = None
    ) -> str:
        """
        Schedule automatic backup

        Args:
            name: Backup name prefix
            interval_hours: Backup interval in hours
            backup_type: Type of backup
            tables: Tables to backup

        Returns:
            Schedule ID
        """
        schedule_id = f"schedule_{len(self.scheduled_backups) + 1}"

        schedule = {
            "id": schedule_id,
            "name": name,
            "interval_hours": interval_hours,
            "backup_type": backup_type,
            "tables": tables,
            "last_run": None,
            "next_run": datetime.now() + timedelta(hours=interval_hours),
            "enabled": True
        }

        self.scheduled_backups.append(schedule)
        self.logger.info(f"Scheduled backup: {name} every {interval_hours} hours")

        return schedule_id

    def run_scheduled_backups(self) -> List[BackupInfo]:
        """
        Run scheduled backups that are due

        Returns:
            List of created backups
        """
        created_backups = []
        now = datetime.now()

        for schedule in self.scheduled_backups:
            if not schedule["enabled"]:
                continue

            if schedule["next_run"] <= now:
                # Create backup
                backup_name = f"{schedule['name']}_{now.strftime('%Y%m%d_%H%M%S')}"

                try:
                    backup_info = self.create_backup(
                        name=backup_name,
                        backup_type=schedule["backup_type"],
                        tables=schedule["tables"]
                    )
                    created_backups.append(backup_info)

                    # Update schedule
                    schedule["last_run"] = now
                    schedule["next_run"] = now + timedelta(hours=schedule["interval_hours"])

                except Exception as e:
                    self.logger.error(f"Scheduled backup failed: {e}")

        return created_backups

    def export_backup_catalog(self, filepath: str) -> None:
        """Export backup catalog to JSON"""
        data = {
            "backups": [backup.to_dict() for backup in self.backups.values()],
            "exported_at": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def _verify_backup(self, filepath: str) -> bool:
        """Verify backup file integrity"""
        try:
            # Try to read the file
            if filepath.endswith('.gz'):
                with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                    _ = f.read(1024)  # Read first 1KB
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    _ = f.read(1024)

            return True
        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False

    def _cleanup_old_backups(self) -> None:
        """Clean up old backups based on max_backups setting"""
        if self.config.max_backups <= 0:
            return

        backups = sorted(
            self.backups.values(),
            key=lambda b: b.created_at,
            reverse=True
        )

        # Delete old backups
        for backup in backups[self.config.max_backups:]:
            try:
                self.delete_backup(backup.id)
            except Exception as e:
                self.logger.error(f"Failed to delete old backup: {e}")

    def _save_backup_catalog(self) -> None:
        """Save backup catalog to disk"""
        catalog_file = os.path.join(self.config.backup_dir, "backup_catalog.json")

        data = {
            "backups": [backup.to_dict() for backup in self.backups.values()],
            "updated_at": datetime.now().isoformat()
        }

        with open(catalog_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_backup_catalog(self) -> None:
        """Load backup catalog from disk"""
        catalog_file = os.path.join(self.config.backup_dir, "backup_catalog.json")

        if not os.path.exists(catalog_file):
            return

        try:
            with open(catalog_file, 'r') as f:
                data = json.load(f)

            for backup_data in data.get("backups", []):
                backup_info = BackupInfo(
                    id=backup_data["id"],
                    name=backup_data["name"],
                    backup_type=BackupType(backup_data["backup_type"]),
                    created_at=datetime.fromisoformat(backup_data["created_at"]),
                    size_bytes=backup_data["size_bytes"],
                    filepath=backup_data["filepath"],
                    status=BackupStatus(backup_data["status"]),
                    error=backup_data.get("error"),
                    metadata=backup_data.get("metadata", {}),
                    tables=backup_data.get("tables", []),
                    duration_seconds=backup_data.get("duration_seconds", 0)
                )

                # Only add if file still exists
                if os.path.exists(backup_info.filepath):
                    self.backups[backup_info.id] = backup_info

            self.logger.info(f"Loaded {len(self.backups)} backups from catalog")

        except Exception as e:
            self.logger.error(f"Failed to load backup catalog: {e}")

    def _split_sql_statements(self, sql: str) -> List[str]:
        """Split SQL into individual statements"""
        statements = []
        current = []

        for line in sql.split('\n'):
            # Skip comment-only lines
            if line.strip().startswith('--'):
                continue

            current.append(line)

            if ';' in line:
                statements.append('\n'.join(current))
                current = []

        if current:
            statements.append('\n'.join(current))

        return [s.strip() for s in statements if s.strip()]

    def estimate_backup_size(self, tables: Optional[List[str]] = None) -> int:
        """
        Estimate backup size

        Args:
            tables: Tables to include in estimate

        Returns:
            Estimated size in bytes
        """
        if tables is None:
            tables = self.connection.get_tables()

        total_size = 0

        for table_name in tables:
            # Get row count
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            result = self.connection.execute_query(count_query)
            row_count = result[0]['count'] if result else 0

            # Get schema
            schema = self.connection.get_table_schema(table_name)
            column_count = len(schema)

            # Estimate: ~100 bytes per column per row (rough estimate)
            table_size = row_count * column_count * 100

            total_size += table_size

        return total_size
