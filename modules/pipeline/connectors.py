"""Data connectors for Pipeline module."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Iterator
import json
import csv
from datetime import datetime
from io import StringIO
from core.utils import get_logger

logger = get_logger(__name__)


class BaseConnector(ABC):
    """Base class for all data connectors."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize connector.

        Args:
            config: Connector configuration
        """
        self.config = config
        self.is_connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection.

        Returns:
            True if disconnection successful
        """
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection.

        Returns:
            Connection test results
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class SourceConnector(BaseConnector):
    """Base class for source connectors."""

    @abstractmethod
    def read(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        Read data from source.

        Yields:
            Data records
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Get data schema.

        Returns:
            Schema information
        """
        pass


class DestinationConnector(BaseConnector):
    """Base class for destination connectors."""

    @abstractmethod
    def write(self, data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Write data to destination.

        Args:
            data: Data records to write

        Returns:
            Write operation results
        """
        pass


# ============================================================================
# Database Connectors
# ============================================================================

class PostgreSQLConnector(SourceConnector, DestinationConnector):
    """PostgreSQL database connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            import psycopg2
            self.connection = psycopg2.connect(
                host=self.config.get("host"),
                port=self.config.get("port", 5432),
                database=self.config.get("database"),
                user=self.config.get("user"),
                password=self.config.get("password")
            )
            self.cursor = self.connection.cursor()
            self.is_connected = True
            logger.info(f"Connected to PostgreSQL: {self.config.get('database')}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from PostgreSQL."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            self.is_connected = False
            logger.info("Disconnected from PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from PostgreSQL: {e}")
            return False

    def test_connection(self) -> Dict[str, Any]:
        """Test PostgreSQL connection."""
        try:
            with self:
                self.cursor.execute("SELECT version();")
                version = self.cursor.fetchone()[0]
                return {
                    "status": "success",
                    "message": "Connection successful",
                    "version": version
                }
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e)
            }

    def read(self, query: str = None, table: str = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """Read data from PostgreSQL."""
        try:
            if query:
                self.cursor.execute(query)
            elif table:
                self.cursor.execute(f"SELECT * FROM {table}")
            else:
                raise ValueError("Either query or table must be specified")

            columns = [desc[0] for desc in self.cursor.description]

            while True:
                rows = self.cursor.fetchmany(kwargs.get("batch_size", 1000))
                if not rows:
                    break

                for row in rows:
                    yield dict(zip(columns, row))

        except Exception as e:
            logger.error(f"Failed to read from PostgreSQL: {e}")
            raise

    def write(self, data: List[Dict[str, Any]], table: str, mode: str = "append", **kwargs) -> Dict[str, Any]:
        """Write data to PostgreSQL."""
        try:
            if not data:
                return {"records_written": 0}

            # Get columns from first record
            columns = list(data[0].keys())
            placeholders = ", ".join(["%s"] * len(columns))

            if mode == "replace":
                self.cursor.execute(f"TRUNCATE TABLE {table}")

            insert_query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

            records_written = 0
            for record in data:
                values = [record.get(col) for col in columns]
                self.cursor.execute(insert_query, values)
                records_written += 1

            self.connection.commit()

            return {
                "records_written": records_written,
                "status": "success"
            }

        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to write to PostgreSQL: {e}")
            raise

    def get_schema(self) -> Dict[str, Any]:
        """Get database schema."""
        try:
            self.cursor.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)

            schema = {}
            for table_name, column_name, data_type in self.cursor.fetchall():
                if table_name not in schema:
                    schema[table_name] = []
                schema[table_name].append({
                    "name": column_name,
                    "type": data_type
                })

            return schema

        except Exception as e:
            logger.error(f"Failed to get schema: {e}")
            raise


# ============================================================================
# File Connectors
# ============================================================================

class CSVConnector(SourceConnector, DestinationConnector):
    """CSV file connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.file_handle = None

    def connect(self) -> bool:
        """No connection needed for CSV."""
        self.is_connected = True
        return True

    def disconnect(self) -> bool:
        """Close file handle if open."""
        if self.file_handle:
            self.file_handle.close()
        self.is_connected = False
        return True

    def test_connection(self) -> Dict[str, Any]:
        """Test CSV file access."""
        try:
            file_path = self.config.get("file_path")
            with open(file_path, 'r') as f:
                f.readline()
            return {
                "status": "success",
                "message": "File accessible"
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e)
            }

    def read(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """Read data from CSV file."""
        file_path = self.config.get("file_path")
        delimiter = self.config.get("delimiter", ",")
        encoding = self.config.get("encoding", "utf-8")

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    yield row
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            raise

    def write(self, data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Write data to CSV file."""
        file_path = self.config.get("file_path")
        delimiter = self.config.get("delimiter", ",")
        encoding = self.config.get("encoding", "utf-8")
        mode = kwargs.get("mode", "w")

        try:
            if not data:
                return {"records_written": 0}

            with open(file_path, mode, encoding=encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=delimiter)

                if mode == 'w':
                    writer.writeheader()

                writer.writerows(data)

            return {
                "records_written": len(data),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Failed to write CSV: {e}")
            raise

    def get_schema(self) -> Dict[str, Any]:
        """Get CSV schema."""
        file_path = self.config.get("file_path")
        delimiter = self.config.get("delimiter", ",")

        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                # Read first row to get columns
                first_row = next(reader)

                return {
                    "columns": [
                        {"name": col, "type": "string"}
                        for col in first_row.keys()
                    ]
                }

        except Exception as e:
            logger.error(f"Failed to get CSV schema: {e}")
            raise


class JSONConnector(SourceConnector, DestinationConnector):
    """JSON file connector."""

    def connect(self) -> bool:
        """No connection needed for JSON."""
        self.is_connected = True
        return True

    def disconnect(self) -> bool:
        """No disconnection needed for JSON."""
        self.is_connected = False
        return True

    def test_connection(self) -> Dict[str, Any]:
        """Test JSON file access."""
        try:
            file_path = self.config.get("file_path")
            with open(file_path, 'r') as f:
                json.load(f)
            return {
                "status": "success",
                "message": "File accessible and valid JSON"
            }
        except Exception as e:
            return {
                "status": "failed",
                "message": str(e)
            }

    def read(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """Read data from JSON file."""
        file_path = self.config.get("file_path")
        encoding = self.config.get("encoding", "utf-8")

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                data = json.load(f)

                # Handle both array of objects and single object
                if isinstance(data, list):
                    for record in data:
                        yield record
                else:
                    yield data

        except Exception as e:
            logger.error(f"Failed to read JSON: {e}")
            raise

    def write(self, data: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Write data to JSON file."""
        file_path = self.config.get("file_path")
        encoding = self.config.get("encoding", "utf-8")
        indent = self.config.get("indent", 2)

        try:
            with open(file_path, 'w', encoding=encoding) as f:
                json.dump(data, f, indent=indent, default=str)

            return {
                "records_written": len(data),
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Failed to write JSON: {e}")
            raise

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema."""
        return {
            "type": "json",
            "message": "Dynamic schema based on content"
        }


# ============================================================================
# API Connectors
# ============================================================================

class RESTAPIConnector(SourceConnector, DestinationConnector):
    """REST API connector."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.session = None

    def connect(self) -> bool:
        """Initialize HTTP session."""
        try:
            import requests
            self.session = requests.Session()

            # Set headers
            headers = self.config.get("headers", {})
            self.session.headers.update(headers)

            # Set authentication
            auth_type = self.config.get("auth_type")
            if auth_type == "basic":
                from requests.auth import HTTPBasicAuth
                self.session.auth = HTTPBasicAuth(
                    self.config.get("username"),
                    self.config.get("password")
                )
            elif auth_type == "bearer":
                token = self.config.get("token")
                self.session.headers["Authorization"] = f"Bearer {token}"

            self.is_connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize API session: {e}")
            return False

    def disconnect(self) -> bool:
        """Close HTTP session."""
        if self.session:
            self.session.close()
        self.is_connected = False
        return True

    def test_connection(self) -> Dict[str, Any]:
        """Test API connection."""
        try:
            with self:
                base_url = self.config.get("base_url")
                test_endpoint = self.config.get("test_endpoint", "/")
                response = self.session.get(f"{base_url}{test_endpoint}")
                response.raise_for_status()

                return {
                    "status": "success",
                    "message": "API accessible",
                    "status_code": response.status_code
                }

        except Exception as e:
            return {
                "status": "failed",
                "message": str(e)
            }

    def read(self, endpoint: str = None, params: Dict = None, **kwargs) -> Iterator[Dict[str, Any]]:
        """Read data from REST API."""
        try:
            base_url = self.config.get("base_url")
            endpoint = endpoint or self.config.get("endpoint")
            url = f"{base_url}{endpoint}"

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Handle different response formats
            if isinstance(data, list):
                for record in data:
                    yield record
            elif isinstance(data, dict):
                # Check for common pagination patterns
                if "data" in data:
                    for record in data["data"]:
                        yield record
                elif "results" in data:
                    for record in data["results"]:
                        yield record
                else:
                    yield data

        except Exception as e:
            logger.error(f"Failed to read from API: {e}")
            raise

    def write(self, data: List[Dict[str, Any]], endpoint: str = None, **kwargs) -> Dict[str, Any]:
        """Write data to REST API."""
        try:
            base_url = self.config.get("base_url")
            endpoint = endpoint or self.config.get("endpoint")
            url = f"{base_url}{endpoint}"

            method = kwargs.get("method", "POST")

            records_written = 0
            for record in data:
                if method == "POST":
                    response = self.session.post(url, json=record)
                elif method == "PUT":
                    response = self.session.put(url, json=record)
                elif method == "PATCH":
                    response = self.session.patch(url, json=record)

                response.raise_for_status()
                records_written += 1

            return {
                "records_written": records_written,
                "status": "success"
            }

        except Exception as e:
            logger.error(f"Failed to write to API: {e}")
            raise

    def get_schema(self) -> Dict[str, Any]:
        """Get API schema (if available via OpenAPI/Swagger)."""
        return {
            "type": "api",
            "message": "Schema depends on API specification"
        }


# ============================================================================
# Connector Factory
# ============================================================================

class ConnectorFactory:
    """Factory for creating connectors."""

    _connectors = {
        "postgresql": PostgreSQLConnector,
        "csv": CSVConnector,
        "json": JSONConnector,
        "rest_api": RESTAPIConnector,
    }

    @classmethod
    def create(cls, connector_type: str, config: Dict[str, Any]) -> BaseConnector:
        """
        Create a connector instance.

        Args:
            connector_type: Type of connector
            config: Connector configuration

        Returns:
            Connector instance
        """
        connector_class = cls._connectors.get(connector_type)

        if not connector_class:
            raise ValueError(f"Unknown connector type: {connector_type}")

        return connector_class(config)

    @classmethod
    def register(cls, connector_type: str, connector_class: type):
        """
        Register a new connector type.

        Args:
            connector_type: Type identifier
            connector_class: Connector class
        """
        cls._connectors[connector_type] = connector_class

    @classmethod
    def get_available_connectors(cls) -> List[str]:
        """
        Get list of available connector types.

        Returns:
            List of connector type names
        """
        return list(cls._connectors.keys())
