"""
Migration Manager

Database migration system with version control, rollback support,
and schema evolution tracking.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib
import logging


class MigrationStatus(Enum):
    """Migration status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Database migration"""
    version: str
    name: str
    description: str
    up_sql: str
    down_sql: str
    checksum: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    applied_at: Optional[datetime] = None
    status: MigrationStatus = MigrationStatus.PENDING
    error: Optional[str] = None

    def __post_init__(self):
        """Calculate checksum"""
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate migration checksum"""
        content = f"{self.version}{self.up_sql}{self.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "up_sql": self.up_sql,
            "down_sql": self.down_sql,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat(),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "status": self.status.value,
            "error": self.error
        }


class MigrationManager:
    """
    Migration Manager

    Manages database migrations with version control, rollback support,
    and automatic schema evolution tracking.
    """

    def __init__(self, connection):
        """
        Initialize migration manager

        Args:
            connection: DatabaseConnection instance
        """
        self.connection = connection
        self.migrations: Dict[str, Migration] = {}
        self.logger = logging.getLogger("database.migration")
        self._ensure_migration_table()

    def _ensure_migration_table(self) -> None:
        """Ensure migration tracking table exists"""
        create_table_sql = """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                checksum VARCHAR(64) NOT NULL,
                up_sql TEXT NOT NULL,
                down_sql TEXT NOT NULL,
                applied_at TIMESTAMP NOT NULL,
                status VARCHAR(50) NOT NULL,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """

        try:
            self.connection.execute_command(create_table_sql)
            self.logger.info("Migration table initialized")
        except Exception as e:
            self.logger.warning(f"Migration table already exists or error: {e}")

    def add_migration(
        self,
        version: str,
        name: str,
        up_sql: str,
        down_sql: str,
        description: str = ""
    ) -> Migration:
        """
        Add a new migration

        Args:
            version: Migration version (e.g., "001", "2024_01_15_001")
            name: Migration name
            up_sql: SQL to apply migration
            down_sql: SQL to rollback migration
            description: Migration description

        Returns:
            Created migration
        """
        if version in self.migrations:
            raise ValueError(f"Migration version '{version}' already exists")

        migration = Migration(
            version=version,
            name=name,
            description=description,
            up_sql=up_sql,
            down_sql=down_sql
        )

        self.migrations[version] = migration
        self.logger.info(f"Added migration: {version} - {name}")
        return migration

    def apply_migration(self, version: str) -> None:
        """
        Apply a migration

        Args:
            version: Migration version to apply
        """
        if version not in self.migrations:
            raise ValueError(f"Migration '{version}' not found")

        migration = self.migrations[version]

        if migration.status == MigrationStatus.COMPLETED:
            self.logger.warning(f"Migration {version} already applied")
            return

        self.logger.info(f"Applying migration: {version} - {migration.name}")
        migration.status = MigrationStatus.RUNNING

        try:
            # Execute migration SQL
            for statement in self._split_sql_statements(migration.up_sql):
                if statement.strip():
                    self.connection.execute_command(statement)

            # Update status
            migration.status = MigrationStatus.COMPLETED
            migration.applied_at = datetime.now()

            # Record in database
            self._record_migration(migration)

            self.logger.info(f"Migration {version} applied successfully")

        except Exception as e:
            migration.status = MigrationStatus.FAILED
            migration.error = str(e)
            self.logger.error(f"Migration {version} failed: {e}")
            raise

    def rollback_migration(self, version: str) -> None:
        """
        Rollback a migration

        Args:
            version: Migration version to rollback
        """
        if version not in self.migrations:
            raise ValueError(f"Migration '{version}' not found")

        migration = self.migrations[version]

        if migration.status != MigrationStatus.COMPLETED:
            raise ValueError(f"Migration {version} is not applied")

        self.logger.info(f"Rolling back migration: {version} - {migration.name}")

        try:
            # Execute rollback SQL
            for statement in self._split_sql_statements(migration.down_sql):
                if statement.strip():
                    self.connection.execute_command(statement)

            # Update status
            migration.status = MigrationStatus.ROLLED_BACK
            migration.applied_at = None

            # Update database record
            self._update_migration_status(migration)

            self.logger.info(f"Migration {version} rolled back successfully")

        except Exception as e:
            migration.error = str(e)
            self.logger.error(f"Rollback of migration {version} failed: {e}")
            raise

    def apply_all_pending(self) -> List[str]:
        """
        Apply all pending migrations in order

        Returns:
            List of applied migration versions
        """
        applied = []

        # Sort migrations by version
        sorted_versions = sorted(self.migrations.keys())

        for version in sorted_versions:
            migration = self.migrations[version]
            if migration.status == MigrationStatus.PENDING:
                self.apply_migration(version)
                applied.append(version)

        return applied

    def rollback_to(self, target_version: str) -> List[str]:
        """
        Rollback to a specific version

        Args:
            target_version: Version to rollback to

        Returns:
            List of rolled back migration versions
        """
        rolled_back = []

        # Get versions in reverse order
        sorted_versions = sorted(self.migrations.keys(), reverse=True)

        for version in sorted_versions:
            if version <= target_version:
                break

            migration = self.migrations[version]
            if migration.status == MigrationStatus.COMPLETED:
                self.rollback_migration(version)
                rolled_back.append(version)

        return rolled_back

    def get_migration_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all migrations

        Returns:
            List of migration status dictionaries
        """
        statuses = []

        for version in sorted(self.migrations.keys()):
            migration = self.migrations[version]
            statuses.append({
                "version": migration.version,
                "name": migration.name,
                "description": migration.description,
                "status": migration.status.value,
                "applied_at": migration.applied_at.isoformat() if migration.applied_at else None,
                "error": migration.error
            })

        return statuses

    def get_current_version(self) -> Optional[str]:
        """
        Get current database version

        Returns:
            Latest applied migration version
        """
        applied_migrations = [
            v for v, m in self.migrations.items()
            if m.status == MigrationStatus.COMPLETED
        ]

        return max(applied_migrations) if applied_migrations else None

    def verify_migrations(self) -> Dict[str, Any]:
        """
        Verify migration integrity

        Returns:
            Verification results
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # Load applied migrations from database
        applied_migrations = self._load_applied_migrations()

        # Check for checksum mismatches
        for version, db_migration in applied_migrations.items():
            if version in self.migrations:
                local_migration = self.migrations[version]

                if local_migration.checksum != db_migration['checksum']:
                    results["valid"] = False
                    results["errors"].append(
                        f"Migration {version}: Checksum mismatch "
                        f"(local: {local_migration.checksum}, db: {db_migration['checksum']})"
                    )

        # Check for missing migrations
        for version in applied_migrations:
            if version not in self.migrations:
                results["warnings"].append(
                    f"Migration {version} is applied in database but not found locally"
                )

        return results

    def generate_migration(
        self,
        name: str,
        description: str = ""
    ) -> Migration:
        """
        Generate a new migration file

        Args:
            name: Migration name
            description: Migration description

        Returns:
            Generated migration
        """
        # Generate version from timestamp
        version = datetime.now().strftime("%Y%m%d%H%M%S")

        # Create migration with empty SQL
        migration = self.add_migration(
            version=version,
            name=name,
            up_sql="-- Add your migration SQL here\n",
            down_sql="-- Add your rollback SQL here\n",
            description=description
        )

        return migration

    def export_migrations(self, filepath: str) -> None:
        """
        Export migrations to JSON file

        Args:
            filepath: Output file path
        """
        data = {
            "migrations": [
                migration.to_dict()
                for migration in self.migrations.values()
            ],
            "exported_at": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Exported {len(self.migrations)} migrations to {filepath}")

    def import_migrations(self, filepath: str) -> int:
        """
        Import migrations from JSON file

        Args:
            filepath: Input file path

        Returns:
            Number of imported migrations
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        count = 0
        for migration_data in data.get("migrations", []):
            version = migration_data["version"]

            if version not in self.migrations:
                migration = Migration(
                    version=version,
                    name=migration_data["name"],
                    description=migration_data["description"],
                    up_sql=migration_data["up_sql"],
                    down_sql=migration_data["down_sql"],
                    checksum=migration_data.get("checksum"),
                    created_at=datetime.fromisoformat(migration_data["created_at"]),
                    status=MigrationStatus(migration_data.get("status", "pending"))
                )

                if migration_data.get("applied_at"):
                    migration.applied_at = datetime.fromisoformat(migration_data["applied_at"])

                self.migrations[version] = migration
                count += 1

        self.logger.info(f"Imported {count} migrations from {filepath}")
        return count

    def create_schema_snapshot(self, name: str) -> Dict[str, Any]:
        """
        Create a snapshot of current database schema

        Args:
            name: Snapshot name

        Returns:
            Schema snapshot data
        """
        snapshot = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "version": self.get_current_version(),
            "tables": {}
        }

        # Get all tables
        tables = self.connection.get_tables()

        for table_name in tables:
            schema = self.connection.get_table_schema(table_name)
            snapshot["tables"][table_name] = schema

        return snapshot

    def _split_sql_statements(self, sql: str) -> List[str]:
        """
        Split SQL into individual statements

        Args:
            sql: SQL string

        Returns:
            List of SQL statements
        """
        # Simple split by semicolon (doesn't handle all edge cases)
        statements = []
        current = []

        for line in sql.split('\n'):
            # Skip comments
            if line.strip().startswith('--'):
                continue

            current.append(line)

            if ';' in line:
                statements.append('\n'.join(current))
                current = []

        if current:
            statements.append('\n'.join(current))

        return [s.strip() for s in statements if s.strip()]

    def _record_migration(self, migration: Migration) -> None:
        """Record migration in database"""
        insert_sql = """
            INSERT INTO schema_migrations
            (version, name, description, checksum, up_sql, down_sql, applied_at, status)
            VALUES (:version, :name, :description, :checksum, :up_sql, :down_sql, :applied_at, :status)
        """

        params = {
            "version": migration.version,
            "name": migration.name,
            "description": migration.description,
            "checksum": migration.checksum,
            "up_sql": migration.up_sql,
            "down_sql": migration.down_sql,
            "applied_at": migration.applied_at,
            "status": migration.status.value
        }

        self.connection.execute_command(insert_sql, params)

    def _update_migration_status(self, migration: Migration) -> None:
        """Update migration status in database"""
        update_sql = """
            UPDATE schema_migrations
            SET status = :status, error = :error, applied_at = :applied_at
            WHERE version = :version
        """

        params = {
            "status": migration.status.value,
            "error": migration.error,
            "applied_at": migration.applied_at,
            "version": migration.version
        }

        self.connection.execute_command(update_sql, params)

    def _load_applied_migrations(self) -> Dict[str, Dict[str, Any]]:
        """Load applied migrations from database"""
        try:
            query = "SELECT * FROM schema_migrations ORDER BY version"
            results = self.connection.execute_query(query)

            return {
                row['version']: row
                for row in results
            }
        except Exception as e:
            self.logger.warning(f"Could not load applied migrations: {e}")
            return {}

    def compare_schemas(
        self,
        source_connection,
        target_connection
    ) -> Dict[str, Any]:
        """
        Compare two database schemas

        Args:
            source_connection: Source database connection
            target_connection: Target database connection

        Returns:
            Schema differences
        """
        differences = {
            "missing_tables": [],
            "extra_tables": [],
            "table_differences": {}
        }

        # Get tables from both databases
        source_tables = set(source_connection.get_tables())
        target_tables = set(target_connection.get_tables())

        # Find missing and extra tables
        differences["missing_tables"] = list(source_tables - target_tables)
        differences["extra_tables"] = list(target_tables - source_tables)

        # Compare common tables
        common_tables = source_tables & target_tables

        for table_name in common_tables:
            source_schema = source_connection.get_table_schema(table_name)
            target_schema = target_connection.get_table_schema(table_name)

            # Convert to comparable format
            source_cols = {col.get('column_name') or col.get('name'): col for col in source_schema}
            target_cols = {col.get('column_name') or col.get('name'): col for col in target_schema}

            table_diff = {
                "missing_columns": list(set(source_cols.keys()) - set(target_cols.keys())),
                "extra_columns": list(set(target_cols.keys()) - set(source_cols.keys()))
            }

            if table_diff["missing_columns"] or table_diff["extra_columns"]:
                differences["table_differences"][table_name] = table_diff

        return differences

    def generate_migration_from_diff(
        self,
        name: str,
        differences: Dict[str, Any]
    ) -> Migration:
        """
        Generate migration from schema differences

        Args:
            name: Migration name
            differences: Schema differences from compare_schemas

        Returns:
            Generated migration
        """
        up_sql_parts = []
        down_sql_parts = []

        # Add missing tables
        for table_name in differences.get("missing_tables", []):
            up_sql_parts.append(f"-- Create table {table_name}")
            up_sql_parts.append(f"CREATE TABLE {table_name} (...);")
            down_sql_parts.append(f"DROP TABLE {table_name};")

        # Remove extra tables
        for table_name in differences.get("extra_tables", []):
            up_sql_parts.append(f"DROP TABLE {table_name};")
            down_sql_parts.append(f"-- Recreate table {table_name}")

        # Handle column differences
        for table_name, table_diff in differences.get("table_differences", {}).items():
            for col in table_diff.get("missing_columns", []):
                up_sql_parts.append(f"ALTER TABLE {table_name} ADD COLUMN {col} ...;")
                down_sql_parts.append(f"ALTER TABLE {table_name} DROP COLUMN {col};")

            for col in table_diff.get("extra_columns", []):
                up_sql_parts.append(f"ALTER TABLE {table_name} DROP COLUMN {col};")
                down_sql_parts.append(f"ALTER TABLE {table_name} ADD COLUMN {col} ...;")

        up_sql = "\n".join(up_sql_parts)
        down_sql = "\n".join(down_sql_parts)

        return self.generate_migration(name, "Auto-generated from schema diff")
