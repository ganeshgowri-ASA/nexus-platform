"""
NEXUS Reports Builder - Data Sources Module
Support for DB (SQL/NoSQL), REST APIs, Files (CSV, Excel, JSON, XML), and custom data sources
"""

import json
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import io
import requests
from datetime import datetime


class DataSourceType(Enum):
    """Supported data source types"""
    SQL_DATABASE = "sql_database"
    NOSQL_DATABASE = "nosql_database"
    REST_API = "rest_api"
    CSV_FILE = "csv_file"
    EXCEL_FILE = "excel_file"
    JSON_FILE = "json_file"
    XML_FILE = "xml_file"
    CUSTOM_SQL = "custom_sql"
    GRAPHQL = "graphql"
    WEBSOCKET = "websocket"


@dataclass
class ConnectionConfig:
    """Configuration for database connections"""
    host: str
    port: int
    database: str
    username: str
    password: str
    driver: str = "postgresql"
    ssl: bool = False
    connection_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.connection_params is None:
            self.connection_params = {}


@dataclass
class APIConfig:
    """Configuration for REST API connections"""
    base_url: str
    auth_type: str = "none"  # none, basic, bearer, api_key, oauth2
    api_key: Optional[str] = None
    api_key_header: str = "X-API-Key"
    bearer_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    headers: Dict[str, str] = None
    timeout: int = 30

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


class DataSource(ABC):
    """Abstract base class for all data sources"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.last_connected = None
        self.is_connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the data source"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the data source"""
        pass

    @abstractmethod
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is valid"""
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get schema information"""
        pass

    def validate_query(self, query: str) -> bool:
        """Validate a query (can be overridden by subclasses)"""
        return True


class SQLDataSource(DataSource):
    """SQL Database data source"""

    def __init__(self, name: str, config: ConnectionConfig, description: str = ""):
        super().__init__(name, description)
        self.config = config
        self.connection = None
        self.supported_drivers = ["postgresql", "mysql", "mssql", "oracle", "sqlite"]

    def connect(self) -> bool:
        """Connect to SQL database"""
        try:
            # Placeholder for actual database connection
            # In production, use SQLAlchemy or specific database drivers
            self.is_connected = True
            self.last_connected = datetime.now()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from database"""
        try:
            if self.connection:
                # self.connection.close()
                self.is_connected = False
            return True
        except Exception as e:
            print(f"Disconnect failed: {e}")
            return False

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """Execute SQL query and return DataFrame"""
        if not self.is_connected:
            self.connect()

        try:
            # Placeholder implementation
            # In production: df = pd.read_sql(query, self.connection, params=parameters)
            df = pd.DataFrame()  # Simulated result
            return df
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            return self.connect()
        except Exception:
            return False

    def get_schema(self) -> Dict[str, Any]:
        """Get database schema"""
        if not self.is_connected:
            self.connect()

        try:
            # Placeholder - would query information_schema or equivalent
            schema = {
                "database": self.config.database,
                "tables": [],
                "views": []
            }
            return schema
        except Exception as e:
            raise Exception(f"Failed to get schema: {e}")

    def get_tables(self) -> List[str]:
        """Get list of tables"""
        schema = self.get_schema()
        return [t["name"] for t in schema.get("tables", [])]

    def get_columns(self, table: str) -> List[Dict[str, str]]:
        """Get columns for a table"""
        # Placeholder - would query table metadata
        return []

    def validate_query(self, query: str) -> bool:
        """Validate SQL query"""
        # Basic validation - check for dangerous operations
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER"]
        query_upper = query.upper()

        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False

        return True


class NoSQLDataSource(DataSource):
    """NoSQL Database data source (MongoDB, etc.)"""

    def __init__(self, name: str, connection_string: str, database: str, description: str = ""):
        super().__init__(name, description)
        self.connection_string = connection_string
        self.database = database
        self.client = None

    def connect(self) -> bool:
        """Connect to NoSQL database"""
        try:
            # Placeholder for MongoDB or other NoSQL connection
            self.is_connected = True
            self.last_connected = datetime.now()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from database"""
        try:
            if self.client:
                # self.client.close()
                self.is_connected = False
            return True
        except Exception:
            return False

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """Execute NoSQL query and return DataFrame"""
        if not self.is_connected:
            self.connect()

        try:
            # Placeholder - would execute MongoDB query
            df = pd.DataFrame()
            return df
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")

    def test_connection(self) -> bool:
        """Test connection"""
        return self.connect()

    def get_schema(self) -> Dict[str, Any]:
        """Get database schema"""
        return {
            "database": self.database,
            "collections": []
        }


class RESTAPIDataSource(DataSource):
    """REST API data source"""

    def __init__(self, name: str, config: APIConfig, description: str = ""):
        super().__init__(name, description)
        self.config = config
        self.session = None

    def connect(self) -> bool:
        """Initialize API session"""
        try:
            self.session = requests.Session()

            # Set up authentication
            if self.config.auth_type == "basic":
                self.session.auth = (self.config.username, self.config.password)
            elif self.config.auth_type == "bearer":
                self.session.headers["Authorization"] = f"Bearer {self.config.bearer_token}"
            elif self.config.auth_type == "api_key":
                self.session.headers[self.config.api_key_header] = self.config.api_key

            # Add custom headers
            self.session.headers.update(self.config.headers)

            self.is_connected = True
            self.last_connected = datetime.now()
            return True
        except Exception as e:
            print(f"API connection failed: {e}")
            return False

    def disconnect(self) -> bool:
        """Close API session"""
        if self.session:
            self.session.close()
            self.is_connected = False
        return True

    def execute_query(self, endpoint: str, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """Execute API request and return DataFrame"""
        if not self.is_connected:
            self.connect()

        try:
            url = f"{self.config.base_url}{endpoint}"
            response = self.session.get(url, params=parameters, timeout=self.config.timeout)
            response.raise_for_status()

            data = response.json()

            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Handle various response structures
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                elif 'results' in data:
                    df = pd.DataFrame(data['results'])
                else:
                    df = pd.DataFrame([data])
            else:
                df = pd.DataFrame()

            return df
        except Exception as e:
            raise Exception(f"API request failed: {e}")

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            self.connect()
            # Try a basic request
            response = self.session.get(self.config.base_url, timeout=5)
            return response.status_code < 500
        except Exception:
            return False

    def get_schema(self) -> Dict[str, Any]:
        """Get API schema (if available)"""
        return {
            "base_url": self.config.base_url,
            "endpoints": []
        }


class FileDataSource(DataSource):
    """File-based data source (CSV, Excel, JSON, XML)"""

    def __init__(self, name: str, file_path: str, file_type: str, description: str = ""):
        super().__init__(name, description)
        self.file_path = file_path
        self.file_type = file_type.lower()
        self.supported_types = ["csv", "excel", "json", "xml", "parquet"]

    def connect(self) -> bool:
        """Validate file exists"""
        try:
            # In production, check if file exists
            self.is_connected = True
            self.last_connected = datetime.now()
            return True
        except Exception:
            return False

    def disconnect(self) -> bool:
        """No action needed for files"""
        self.is_connected = False
        return True

    def execute_query(self, query: str = None, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """Read file and return DataFrame"""
        try:
            if self.file_type == "csv":
                df = pd.read_csv(self.file_path, **(parameters or {}))
            elif self.file_type in ["excel", "xlsx", "xls"]:
                df = pd.read_excel(self.file_path, **(parameters or {}))
            elif self.file_type == "json":
                df = pd.read_json(self.file_path, **(parameters or {}))
            elif self.file_type == "xml":
                df = pd.read_xml(self.file_path, **(parameters or {}))
            elif self.file_type == "parquet":
                df = pd.read_parquet(self.file_path, **(parameters or {}))
            else:
                raise ValueError(f"Unsupported file type: {self.file_type}")

            # Apply query filter if provided
            if query and isinstance(query, str):
                df = df.query(query)

            return df
        except Exception as e:
            raise Exception(f"Failed to read file: {e}")

    def test_connection(self) -> bool:
        """Test if file is readable"""
        return self.connect()

    def get_schema(self) -> Dict[str, Any]:
        """Get file schema"""
        try:
            df = self.execute_query()
            return {
                "file_path": self.file_path,
                "file_type": self.file_type,
                "columns": [
                    {
                        "name": col,
                        "dtype": str(df[col].dtype)
                    }
                    for col in df.columns
                ],
                "row_count": len(df)
            }
        except Exception:
            return {}


class CustomSQLDataSource(SQLDataSource):
    """Custom SQL queries with saved query templates"""

    def __init__(self, name: str, config: ConnectionConfig, custom_query: str, description: str = ""):
        super().__init__(name, config, description)
        self.custom_query = custom_query
        self.query_parameters: Dict[str, Any] = {}

    def set_parameter(self, name: str, value: Any):
        """Set a query parameter"""
        self.query_parameters[name] = value

    def get_parameterized_query(self) -> str:
        """Get query with parameters substituted"""
        query = self.custom_query
        for param, value in self.query_parameters.items():
            placeholder = f":{param}"
            query = query.replace(placeholder, str(value))
        return query

    def execute_query(self, query: str = None, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """Execute custom SQL query"""
        if query is None:
            query = self.get_parameterized_query()

        return super().execute_query(query, parameters)


class DataSourceManager:
    """Manages multiple data sources"""

    def __init__(self):
        self.data_sources: Dict[str, DataSource] = {}

    def add_data_source(self, data_source: DataSource) -> str:
        """Add a data source"""
        self.data_sources[data_source.name] = data_source
        return data_source.name

    def remove_data_source(self, name: str) -> bool:
        """Remove a data source"""
        if name in self.data_sources:
            self.data_sources[name].disconnect()
            del self.data_sources[name]
            return True
        return False

    def get_data_source(self, name: str) -> Optional[DataSource]:
        """Get a data source by name"""
        return self.data_sources.get(name)

    def list_data_sources(self) -> List[str]:
        """List all data source names"""
        return list(self.data_sources.keys())

    def test_all_connections(self) -> Dict[str, bool]:
        """Test all data source connections"""
        results = {}
        for name, ds in self.data_sources.items():
            results[name] = ds.test_connection()
        return results

    def execute_query(self, data_source_name: str, query: str, parameters: Dict[str, Any] = None) -> pd.DataFrame:
        """Execute query on a specific data source"""
        ds = self.get_data_source(data_source_name)
        if not ds:
            raise ValueError(f"Data source not found: {data_source_name}")

        return ds.execute_query(query, parameters)

    def merge_data_sources(self, sources: List[str], join_type: str = "inner", on: str = None) -> pd.DataFrame:
        """Merge data from multiple sources"""
        if len(sources) < 2:
            raise ValueError("At least 2 data sources required for merge")

        dataframes = []
        for source_name in sources:
            ds = self.get_data_source(source_name)
            if not ds:
                raise ValueError(f"Data source not found: {source_name}")
            dataframes.append(ds.execute_query(""))

        # Merge dataframes
        result = dataframes[0]
        for df in dataframes[1:]:
            result = pd.merge(result, df, how=join_type, on=on)

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary"""
        return {
            "data_sources": list(self.data_sources.keys()),
            "count": len(self.data_sources)
        }
