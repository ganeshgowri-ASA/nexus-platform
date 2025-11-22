"""
Tests for Database Manager
"""

import pytest
from unittest.mock import Mock, patch
from ..manager import (
    DatabaseManager, ConnectionConfig, DatabaseType,
    SQLiteConnection, PostgreSQLConnection
)


class TestDatabaseManager:
    """Test DatabaseManager class"""

    def test_init(self):
        """Test initialization"""
        manager = DatabaseManager()
        assert len(manager.connections) == 0
        assert len(manager.configs) == 0

    def test_add_sqlite_connection(self):
        """Test adding SQLite connection"""
        manager = DatabaseManager()
        config = ConnectionConfig(
            name="test_db",
            db_type=DatabaseType.SQLITE,
            database=":memory:"
        )

        with patch.object(SQLiteConnection, 'connect'):
            manager.add_connection(config)

        assert "test_db" in manager.connections
        assert isinstance(manager.connections["test_db"], SQLiteConnection)

    def test_add_duplicate_connection_raises_error(self):
        """Test that adding duplicate connection raises error"""
        manager = DatabaseManager()
        config = ConnectionConfig(
            name="test_db",
            db_type=DatabaseType.SQLITE,
            database=":memory:"
        )

        with patch.object(SQLiteConnection, 'connect'):
            manager.add_connection(config)

            with pytest.raises(ValueError, match="already exists"):
                manager.add_connection(config)

    def test_remove_connection(self):
        """Test removing connection"""
        manager = DatabaseManager()
        config = ConnectionConfig(
            name="test_db",
            db_type=DatabaseType.SQLITE,
            database=":memory:"
        )

        with patch.object(SQLiteConnection, 'connect'):
            with patch.object(SQLiteConnection, 'disconnect'):
                manager.add_connection(config)
                manager.remove_connection("test_db")

        assert "test_db" not in manager.connections

    def test_get_connection(self):
        """Test getting connection"""
        manager = DatabaseManager()
        config = ConnectionConfig(
            name="test_db",
            db_type=DatabaseType.SQLITE,
            database=":memory:"
        )

        with patch.object(SQLiteConnection, 'connect'):
            manager.add_connection(config)
            conn = manager.get_connection("test_db")

        assert isinstance(conn, SQLiteConnection)

    def test_get_nonexistent_connection_raises_error(self):
        """Test getting nonexistent connection raises error"""
        manager = DatabaseManager()

        with pytest.raises(ValueError, match="not found"):
            manager.get_connection("nonexistent")

    def test_list_connections(self):
        """Test listing connections"""
        manager = DatabaseManager()

        with patch.object(SQLiteConnection, 'connect'):
            manager.add_connection(ConnectionConfig(
                name="db1",
                db_type=DatabaseType.SQLITE,
                database=":memory:"
            ))
            manager.add_connection(ConnectionConfig(
                name="db2",
                db_type=DatabaseType.SQLITE,
                database=":memory:"
            ))

        connections = manager.list_connections()
        assert len(connections) == 2
        assert "db1" in connections
        assert "db2" in connections


class TestConnectionConfig:
    """Test ConnectionConfig class"""

    def test_to_dict(self):
        """Test converting to dictionary"""
        config = ConnectionConfig(
            name="test",
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="secret"
        )

        config_dict = config.to_dict()

        assert config_dict["name"] == "test"
        assert config_dict["db_type"] == "postgresql"
        assert "password" not in config_dict  # Password should be excluded
