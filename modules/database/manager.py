"""
Database Connection Manager

Handles connections to multiple database types with connection pooling,
health monitoring, and transaction management.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from enum import Enum
from contextlib import contextmanager
import threading
from abc import ABC, abstractmethod


class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    SQLITE = "sqlite"
    SQLSERVER = "sqlserver"
    MARIADB = "mariadb"


@dataclass
class ConnectionConfig:
    """Database connection configuration"""
    name: str
    db_type: DatabaseType
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = ""
    username: Optional[str] = None
    password: Optional[str] = None
    ssl: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    timeout: int = 30
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding password)"""
        return {
            "name": self.name,
            "db_type": self.db_type.value,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "ssl": self.ssl,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "timeout": self.timeout,
            "extra_params": self.extra_params,
        }


@dataclass
class ConnectionStatus:
    """Connection health status"""
    connected: bool
    last_check: datetime
    response_time: float  # milliseconds
    error: Optional[str] = None
    active_connections: int = 0
    pool_size: int = 0


class DatabaseConnection(ABC):
    """Abstract base class for database connections"""

    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connection = None
        self.pool = None
        self._lock = threading.RLock()
        self.logger = logging.getLogger(f"db.{config.name}")

    @abstractmethod
    def connect(self) -> None:
        """Establish connection"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection"""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query"""
        pass

    @abstractmethod
    def execute_command(self, command: str, params: Optional[Dict] = None) -> int:
        """Execute INSERT/UPDATE/DELETE"""
        pass

    @abstractmethod
    def get_tables(self) -> List[str]:
        """Get list of tables"""
        pass

    @abstractmethod
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema"""
        pass

    @abstractmethod
    def check_health(self) -> ConnectionStatus:
        """Check connection health"""
        pass

    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        raise NotImplementedError("Subclass must implement transaction()")


class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL database connection"""

    def connect(self) -> None:
        """Establish PostgreSQL connection"""
        try:
            import psycopg2
            from psycopg2 import pool

            self.pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.pool_size,
                host=self.config.host,
                port=self.config.port or 5432,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                sslmode='require' if self.config.ssl else 'prefer',
                connect_timeout=self.config.timeout,
                **self.config.extra_params
            )
            self.logger.info(f"Connected to PostgreSQL: {self.config.name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def disconnect(self) -> None:
        """Close PostgreSQL connection"""
        if self.pool:
            self.pool.closeall()
            self.pool = None
            self.logger.info(f"Disconnected from PostgreSQL: {self.config.name}")

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query"""
        import psycopg2.extras

        conn = self.pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                results = cursor.fetchall()
                return [dict(row) for row in results]
        finally:
            self.pool.putconn(conn)

    def execute_command(self, command: str, params: Optional[Dict] = None) -> int:
        """Execute INSERT/UPDATE/DELETE"""
        conn = self.pool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(command, params or {})
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)

    def get_tables(self) -> List[str]:
        """Get list of tables"""
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """
        results = self.execute_query(query)
        return [row['table_name'] for row in results]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema"""
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %(table)s
            ORDER BY ordinal_position
        """
        return self.execute_query(query, {"table": table_name})

    def check_health(self) -> ConnectionStatus:
        """Check connection health"""
        start = datetime.now()
        try:
            self.execute_query("SELECT 1")
            response_time = (datetime.now() - start).total_seconds() * 1000
            return ConnectionStatus(
                connected=True,
                last_check=datetime.now(),
                response_time=response_time,
                active_connections=self.pool._used if self.pool else 0,
                pool_size=self.config.pool_size
            )
        except Exception as e:
            return ConnectionStatus(
                connected=False,
                last_check=datetime.now(),
                response_time=0,
                error=str(e)
            )

    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)


class MySQLConnection(DatabaseConnection):
    """MySQL database connection"""

    def connect(self) -> None:
        """Establish MySQL connection"""
        try:
            import pymysql
            from dbutils.pooled_db import PooledDB

            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=self.config.pool_size,
                host=self.config.host,
                port=self.config.port or 3306,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                **self.config.extra_params
            )
            self.logger.info(f"Connected to MySQL: {self.config.name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to MySQL: {e}")
            raise

    def disconnect(self) -> None:
        """Close MySQL connection"""
        if self.pool:
            self.pool.close()
            self.pool = None
            self.logger.info(f"Disconnected from MySQL: {self.config.name}")

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query"""
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or {})
                return cursor.fetchall()
        finally:
            conn.close()

    def execute_command(self, command: str, params: Optional[Dict] = None) -> int:
        """Execute INSERT/UPDATE/DELETE"""
        conn = self.pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(command, params or {})
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_tables(self) -> List[str]:
        """Get list of tables"""
        query = "SHOW TABLES"
        results = self.execute_query(query)
        if results:
            key = list(results[0].keys())[0]
            return [row[key] for row in results]
        return []

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema"""
        query = f"DESCRIBE `{table_name}`"
        return self.execute_query(query)

    def check_health(self) -> ConnectionStatus:
        """Check connection health"""
        start = datetime.now()
        try:
            self.execute_query("SELECT 1")
            response_time = (datetime.now() - start).total_seconds() * 1000
            return ConnectionStatus(
                connected=True,
                last_check=datetime.now(),
                response_time=response_time
            )
        except Exception as e:
            return ConnectionStatus(
                connected=False,
                last_check=datetime.now(),
                response_time=0,
                error=str(e)
            )

    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        conn = self.pool.connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class SQLiteConnection(DatabaseConnection):
    """SQLite database connection"""

    def connect(self) -> None:
        """Establish SQLite connection"""
        try:
            import sqlite3

            self.connection = sqlite3.connect(
                self.config.database,
                check_same_thread=False,
                timeout=self.config.timeout
            )
            self.connection.row_factory = sqlite3.Row
            self.logger.info(f"Connected to SQLite: {self.config.name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to SQLite: {e}")
            raise

    def disconnect(self) -> None:
        """Close SQLite connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info(f"Disconnected from SQLite: {self.config.name}")

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query"""
        with self._lock:
            cursor = self.connection.execute(query, params or {})
            results = cursor.fetchall()
            return [dict(row) for row in results]

    def execute_command(self, command: str, params: Optional[Dict] = None) -> int:
        """Execute INSERT/UPDATE/DELETE"""
        with self._lock:
            try:
                cursor = self.connection.execute(command, params or {})
                self.connection.commit()
                return cursor.rowcount
            except Exception as e:
                self.connection.rollback()
                raise

    def get_tables(self) -> List[str]:
        """Get list of tables"""
        query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        results = self.execute_query(query)
        return [row['name'] for row in results]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema"""
        query = f"PRAGMA table_info('{table_name}')"
        return self.execute_query(query)

    def check_health(self) -> ConnectionStatus:
        """Check connection health"""
        start = datetime.now()
        try:
            self.execute_query("SELECT 1")
            response_time = (datetime.now() - start).total_seconds() * 1000
            return ConnectionStatus(
                connected=True,
                last_check=datetime.now(),
                response_time=response_time
            )
        except Exception as e:
            return ConnectionStatus(
                connected=False,
                last_check=datetime.now(),
                response_time=0,
                error=str(e)
            )

    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        with self._lock:
            try:
                yield self.connection
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise


class MongoDBConnection(DatabaseConnection):
    """MongoDB database connection"""

    def connect(self) -> None:
        """Establish MongoDB connection"""
        try:
            from pymongo import MongoClient

            connection_string = self._build_connection_string()
            self.connection = MongoClient(
                connection_string,
                maxPoolSize=self.config.pool_size,
                serverSelectionTimeoutMS=self.config.timeout * 1000
            )
            self.database = self.connection[self.config.database]
            self.logger.info(f"Connected to MongoDB: {self.config.name}")
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _build_connection_string(self) -> str:
        """Build MongoDB connection string"""
        if self.config.username and self.config.password:
            auth = f"{self.config.username}:{self.config.password}@"
        else:
            auth = ""

        ssl_param = "ssl=true&" if self.config.ssl else ""
        return f"mongodb://{auth}{self.config.host}:{self.config.port or 27017}/{ssl_param}"

    def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info(f"Disconnected from MongoDB: {self.config.name}")

    def execute_query(self, collection: str, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute find query"""
        coll = self.database[collection]
        results = coll.find(filter_dict or {})
        return [self._convert_objectid(doc) for doc in results]

    def _convert_objectid(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ObjectId to string"""
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc

    def execute_command(self, collection: str, operation: str, data: Dict[str, Any]) -> int:
        """Execute insert/update/delete"""
        coll = self.database[collection]

        if operation == "insert_one":
            result = coll.insert_one(data)
            return 1 if result.inserted_id else 0
        elif operation == "update_one":
            result = coll.update_one(data.get('filter', {}), data.get('update', {}))
            return result.modified_count
        elif operation == "delete_one":
            result = coll.delete_one(data)
            return result.deleted_count
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def get_tables(self) -> List[str]:
        """Get list of collections"""
        return sorted(self.database.list_collection_names())

    def get_table_schema(self, collection_name: str) -> List[Dict[str, Any]]:
        """Get collection schema (sample first document)"""
        coll = self.database[collection_name]
        sample = coll.find_one()
        if sample:
            return [{"field": key, "type": type(value).__name__} for key, value in sample.items()]
        return []

    def check_health(self) -> ConnectionStatus:
        """Check connection health"""
        start = datetime.now()
        try:
            self.connection.admin.command('ping')
            response_time = (datetime.now() - start).total_seconds() * 1000
            return ConnectionStatus(
                connected=True,
                last_check=datetime.now(),
                response_time=response_time
            )
        except Exception as e:
            return ConnectionStatus(
                connected=False,
                last_check=datetime.now(),
                response_time=0,
                error=str(e)
            )

    @contextmanager
    def transaction(self):
        """Transaction context manager (MongoDB 4.0+)"""
        with self.connection.start_session() as session:
            with session.start_transaction():
                yield session


class DatabaseManager:
    """
    Database Connection Manager

    Manages multiple database connections with pooling, health monitoring,
    and transaction support.
    """

    def __init__(self):
        self.connections: Dict[str, DatabaseConnection] = {}
        self.configs: Dict[str, ConnectionConfig] = {}
        self.logger = logging.getLogger("database.manager")
        self._lock = threading.RLock()

    def add_connection(self, config: ConnectionConfig) -> None:
        """Add a new database connection"""
        with self._lock:
            if config.name in self.connections:
                raise ValueError(f"Connection '{config.name}' already exists")

            # Create appropriate connection type
            connection_class = self._get_connection_class(config.db_type)
            connection = connection_class(config)

            # Store config and connection
            self.configs[config.name] = config
            self.connections[config.name] = connection

            # Connect
            connection.connect()
            self.logger.info(f"Added connection: {config.name}")

    def _get_connection_class(self, db_type: DatabaseType) -> type:
        """Get connection class for database type"""
        mapping = {
            DatabaseType.POSTGRESQL: PostgreSQLConnection,
            DatabaseType.MYSQL: MySQLConnection,
            DatabaseType.MONGODB: MongoDBConnection,
            DatabaseType.SQLITE: SQLiteConnection,
            DatabaseType.MARIADB: MySQLConnection,  # Use MySQL driver
        }

        if db_type not in mapping:
            raise ValueError(f"Unsupported database type: {db_type}")

        return mapping[db_type]

    def remove_connection(self, name: str) -> None:
        """Remove a database connection"""
        with self._lock:
            if name not in self.connections:
                raise ValueError(f"Connection '{name}' not found")

            # Disconnect and remove
            self.connections[name].disconnect()
            del self.connections[name]
            del self.configs[name]
            self.logger.info(f"Removed connection: {name}")

    def get_connection(self, name: str) -> DatabaseConnection:
        """Get a database connection"""
        if name not in self.connections:
            raise ValueError(f"Connection '{name}' not found")
        return self.connections[name]

    def list_connections(self) -> List[str]:
        """List all connection names"""
        return list(self.connections.keys())

    def get_connection_info(self, name: str) -> Dict[str, Any]:
        """Get connection information"""
        if name not in self.configs:
            raise ValueError(f"Connection '{name}' not found")

        config = self.configs[name]
        status = self.connections[name].check_health()

        return {
            "config": config.to_dict(),
            "status": {
                "connected": status.connected,
                "last_check": status.last_check.isoformat(),
                "response_time_ms": status.response_time,
                "error": status.error,
                "active_connections": status.active_connections,
                "pool_size": status.pool_size,
            }
        }

    def test_connection(self, config: ConnectionConfig) -> Tuple[bool, Optional[str]]:
        """Test a connection without saving it"""
        try:
            connection_class = self._get_connection_class(config.db_type)
            connection = connection_class(config)
            connection.connect()
            status = connection.check_health()
            connection.disconnect()

            if status.connected:
                return True, None
            else:
                return False, status.error
        except Exception as e:
            return False, str(e)

    def save_connections(self, filepath: str) -> None:
        """Save connections to JSON file (excluding passwords)"""
        data = {
            name: config.to_dict()
            for name, config in self.configs.items()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Saved {len(data)} connections to {filepath}")

    def load_connections(self, filepath: str, password_callback=None) -> None:
        """Load connections from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        for name, config_dict in data.items():
            # Convert db_type string to enum
            config_dict['db_type'] = DatabaseType(config_dict['db_type'])

            # Get password from callback if provided
            if password_callback and config_dict.get('username'):
                config_dict['password'] = password_callback(name, config_dict['username'])

            config = ConnectionConfig(**config_dict)
            self.add_connection(config)

        self.logger.info(f"Loaded {len(data)} connections from {filepath}")

    def close_all(self) -> None:
        """Close all connections"""
        with self._lock:
            for connection in self.connections.values():
                try:
                    connection.disconnect()
                except Exception as e:
                    self.logger.error(f"Error disconnecting: {e}")

            self.connections.clear()
            self.configs.clear()
            self.logger.info("Closed all connections")
