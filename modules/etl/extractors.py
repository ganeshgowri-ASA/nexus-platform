"""
Data extractors for ETL module.

This module provides extractors for various data sources including
databases, files, APIs, web scraping, and cloud storage.
"""

import logging
import json
import csv
import io
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator, Generator
from datetime import datetime
import hashlib

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import pymongo
import requests
from bs4 import BeautifulSoup
import boto3
from azure.storage.blob import BlobServiceClient
from google.cloud import storage as gcs_storage

from modules.etl.models import DataSource, SourceType, DatabaseType

logger = logging.getLogger(__name__)


class ExtractorException(Exception):
    """Base exception for extractor errors."""
    pass


class ConnectionException(ExtractorException):
    """Exception for connection failures."""
    pass


class ExtractionException(ExtractorException):
    """Exception for extraction failures."""
    pass


class BaseExtractor(ABC):
    """Abstract base class for all extractors."""

    def __init__(self, data_source: DataSource, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the extractor.

        Args:
            data_source: DataSource configuration
            config: Additional configuration options
        """
        self.data_source = data_source
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._connection = None

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the data source."""
        pass

    @abstractmethod
    def extract(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract data from the source.

        Args:
            query: Query or filter expression
            filters: Additional filters
            limit: Maximum number of records to extract
            offset: Number of records to skip

        Returns:
            List of extracted records as dictionaries
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the data source."""
        pass

    def extract_incremental(
        self,
        watermark_column: str,
        last_watermark_value: Optional[Any] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract data incrementally using watermark column.

        Args:
            watermark_column: Column to use for incremental extraction
            last_watermark_value: Last extracted watermark value
            query: Base query to modify

        Returns:
            List of new/updated records
        """
        filters = {}
        if last_watermark_value:
            filters[watermark_column] = {"operator": ">", "value": last_watermark_value}

        return self.extract(query=query, filters=filters)

    def test_connection(self) -> bool:
        """
        Test connection to the data source.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connect()
            self.disconnect()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

    def get_schema(self) -> Dict[str, Any]:
        """
        Get schema information from the data source.

        Returns:
            Dictionary containing schema information
        """
        return {}

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class DatabaseExtractor(BaseExtractor):
    """Extractor for relational databases."""

    def connect(self) -> None:
        """Establish database connection."""
        try:
            connection_string = self._build_connection_string()
            self._connection = create_engine(
                connection_string,
                poolclass=NullPool,
                echo=self.config.get("echo_sql", False)
            )
            # Test connection
            with self._connection.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.logger.info(f"Connected to database: {self.data_source.name}")
        except Exception as e:
            raise ConnectionException(f"Failed to connect to database: {str(e)}")

    def _build_connection_string(self) -> str:
        """Build database connection string."""
        if self.data_source.connection_string:
            return self.data_source.connection_string

        db_type = self.data_source.database_type.value
        user = self.data_source.username
        password = self.data_source.password
        host = self.data_source.host
        port = self.data_source.port
        database = self.data_source.database_name

        if db_type == DatabaseType.POSTGRESQL.value:
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        elif db_type == DatabaseType.MYSQL.value:
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        elif db_type == DatabaseType.MSSQL.value:
            return f"mssql+pyodbc://{user}:{password}@{host}:{port}/{database}"
        elif db_type == DatabaseType.ORACLE.value:
            return f"oracle+cx_oracle://{user}:{password}@{host}:{port}/{database}"
        elif db_type == DatabaseType.SQLITE.value:
            return f"sqlite:///{database}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def extract(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extract data from database."""
        try:
            if not query:
                raise ExtractionException("Query is required for database extraction")

            # Add limit and offset to query
            modified_query = query
            if limit:
                modified_query += f" LIMIT {limit}"
            if offset:
                modified_query += f" OFFSET {offset}"

            with self._connection.connect() as conn:
                result = conn.execute(text(modified_query))
                columns = result.keys()
                rows = result.fetchall()

                data = [dict(zip(columns, row)) for row in rows]
                self.logger.info(f"Extracted {len(data)} records from database")
                return data

        except Exception as e:
            raise ExtractionException(f"Failed to extract data from database: {str(e)}")

    def extract_table(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extract data from a specific table."""
        select_clause = ", ".join(columns) if columns else "*"
        query = f"SELECT {select_clause} FROM {table_name}"

        if filters:
            where_clauses = []
            for field, condition in filters.items():
                operator = condition.get("operator", "=")
                value = condition.get("value")
                if isinstance(value, str):
                    where_clauses.append(f"{field} {operator} '{value}'")
                else:
                    where_clauses.append(f"{field} {operator} {value}")
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

        return self.extract(query=query, limit=limit)

    def get_schema(self) -> Dict[str, Any]:
        """Get database schema information."""
        try:
            inspector = sqlalchemy.inspect(self._connection)
            tables = inspector.get_table_names()
            schema = {}

            for table in tables:
                columns = inspector.get_columns(table)
                schema[table] = [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True)
                    }
                    for col in columns
                ]

            return schema
        except Exception as e:
            self.logger.error(f"Failed to get database schema: {str(e)}")
            return {}

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.dispose()
            self.logger.info("Database connection closed")


class MongoDBExtractor(BaseExtractor):
    """Extractor for MongoDB databases."""

    def connect(self) -> None:
        """Establish MongoDB connection."""
        try:
            connection_string = (
                self.data_source.connection_string or
                f"mongodb://{self.data_source.username}:{self.data_source.password}"
                f"@{self.data_source.host}:{self.data_source.port}/"
            )
            self._connection = pymongo.MongoClient(connection_string)
            # Test connection
            self._connection.server_info()
            self.logger.info(f"Connected to MongoDB: {self.data_source.name}")
        except Exception as e:
            raise ConnectionException(f"Failed to connect to MongoDB: {str(e)}")

    def extract(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extract data from MongoDB collection."""
        try:
            db = self._connection[self.data_source.database_name]
            collection_name = self.config.get("collection")
            if not collection_name:
                raise ExtractionException("Collection name is required for MongoDB extraction")

            collection = db[collection_name]

            # Build query filter
            query_filter = json.loads(query) if query else {}
            if filters:
                query_filter.update(filters)

            # Execute query
            cursor = collection.find(query_filter)
            if offset:
                cursor = cursor.skip(offset)
            if limit:
                cursor = cursor.limit(limit)

            data = list(cursor)

            # Convert ObjectId to string
            for doc in data:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            self.logger.info(f"Extracted {len(data)} documents from MongoDB")
            return data

        except Exception as e:
            raise ExtractionException(f"Failed to extract data from MongoDB: {str(e)}")

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._connection:
            self._connection.close()
            self.logger.info("MongoDB connection closed")


class FileExtractor(BaseExtractor):
    """Extractor for file-based data sources (CSV, JSON, Excel, Parquet)."""

    def connect(self) -> None:
        """Verify file exists."""
        import os
        file_path = self.data_source.file_path
        if not file_path or not os.path.exists(file_path):
            raise ConnectionException(f"File not found: {file_path}")
        self.logger.info(f"File verified: {file_path}")

    def extract(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extract data from file."""
        try:
            file_path = self.data_source.file_path
            file_extension = file_path.split(".")[-1].lower()

            if file_extension == "csv":
                df = pd.read_csv(file_path)
            elif file_extension == "json":
                df = pd.read_json(file_path)
            elif file_extension in ["xlsx", "xls"]:
                df = pd.read_excel(file_path)
            elif file_extension == "parquet":
                df = pd.read_parquet(file_path)
            else:
                raise ExtractionException(f"Unsupported file format: {file_extension}")

            # Apply filters if provided
            if filters:
                for field, condition in filters.items():
                    operator = condition.get("operator", "==")
                    value = condition.get("value")
                    if operator == "==":
                        df = df[df[field] == value]
                    elif operator == ">":
                        df = df[df[field] > value]
                    elif operator == "<":
                        df = df[df[field] < value]

            # Apply offset and limit
            if offset:
                df = df.iloc[offset:]
            if limit:
                df = df.head(limit)

            data = df.to_dict(orient="records")
            self.logger.info(f"Extracted {len(data)} records from file")
            return data

        except Exception as e:
            raise ExtractionException(f"Failed to extract data from file: {str(e)}")

    def disconnect(self) -> None:
        """No connection to close for file extraction."""
        pass


class APIExtractor(BaseExtractor):
    """Extractor for REST APIs."""

    def connect(self) -> None:
        """Test API connection."""
        try:
            headers = self._build_headers()
            response = requests.get(
                self.data_source.api_url,
                headers=headers,
                timeout=self.config.get("timeout", 30)
            )
            response.raise_for_status()
            self.logger.info(f"Connected to API: {self.data_source.name}")
        except Exception as e:
            raise ConnectionException(f"Failed to connect to API: {str(e)}")

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = dict(self.data_source.headers or {})
        if self.data_source.api_key:
            headers["Authorization"] = f"Bearer {self.data_source.api_key}"
        return headers

    def extract(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extract data from API."""
        try:
            headers = self._build_headers()
            params = filters or {}

            if limit:
                params["limit"] = limit
            if offset:
                params["offset"] = offset

            url = query if query else self.data_source.api_url
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self.config.get("timeout", 30)
            )
            response.raise_for_status()

            data = response.json()

            # Handle different response formats
            if isinstance(data, list):
                result = data
            elif isinstance(data, dict):
                # Try to find data in common response keys
                result = (
                    data.get("data") or
                    data.get("results") or
                    data.get("items") or
                    [data]
                )
            else:
                result = [data]

            self.logger.info(f"Extracted {len(result)} records from API")
            return result

        except Exception as e:
            raise ExtractionException(f"Failed to extract data from API: {str(e)}")

    def disconnect(self) -> None:
        """No persistent connection for API."""
        pass


class WebExtractor(BaseExtractor):
    """Extractor for web scraping."""

    def connect(self) -> None:
        """Test web page accessibility."""
        try:
            response = requests.get(
                self.data_source.api_url,
                timeout=self.config.get("timeout", 30)
            )
            response.raise_for_status()
            self.logger.info(f"Connected to web page: {self.data_source.name}")
        except Exception as e:
            raise ConnectionException(f"Failed to access web page: {str(e)}")

    def extract(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extract data from web page using BeautifulSoup."""
        try:
            url = query if query else self.data_source.api_url
            response = requests.get(url, timeout=self.config.get("timeout", 30))
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Extract based on CSS selectors
            selector = self.config.get("selector", "table")
            elements = soup.select(selector)

            data = []
            for element in elements[:limit] if limit else elements:
                # Extract text content
                row_data = {
                    "text": element.get_text(strip=True),
                    "html": str(element)
                }

                # Extract attributes if specified
                if "attributes" in self.config:
                    for attr in self.config["attributes"]:
                        row_data[attr] = element.get(attr)

                data.append(row_data)

            self.logger.info(f"Extracted {len(data)} elements from web page")
            return data

        except Exception as e:
            raise ExtractionException(f"Failed to extract data from web page: {str(e)}")

    def disconnect(self) -> None:
        """No persistent connection for web scraping."""
        pass


class CloudStorageExtractor(BaseExtractor):
    """Extractor for cloud storage (AWS S3, Azure Blob, Google Cloud Storage)."""

    def connect(self) -> None:
        """Test cloud storage connection."""
        try:
            provider = self.config.get("provider", "s3").lower()
            if provider == "s3":
                self._connect_s3()
            elif provider == "azure":
                self._connect_azure()
            elif provider == "gcs":
                self._connect_gcs()
            else:
                raise ValueError(f"Unsupported cloud provider: {provider}")

            self.logger.info(f"Connected to cloud storage: {self.data_source.name}")
        except Exception as e:
            raise ConnectionException(f"Failed to connect to cloud storage: {str(e)}")

    def _connect_s3(self) -> None:
        """Connect to AWS S3."""
        self._connection = boto3.client(
            "s3",
            aws_access_key_id=self.data_source.username,
            aws_secret_access_key=self.data_source.password,
            region_name=self.data_source.region
        )
        # Test connection
        self._connection.head_bucket(Bucket=self.data_source.bucket_name)

    def _connect_azure(self) -> None:
        """Connect to Azure Blob Storage."""
        connection_string = self.data_source.connection_string
        self._connection = BlobServiceClient.from_connection_string(connection_string)
        # Test connection
        self._connection.get_container_client(self.data_source.bucket_name)

    def _connect_gcs(self) -> None:
        """Connect to Google Cloud Storage."""
        self._connection = gcs_storage.Client()
        # Test connection
        self._connection.get_bucket(self.data_source.bucket_name)

    def extract(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Extract data from cloud storage."""
        try:
            provider = self.config.get("provider", "s3").lower()
            file_key = query or self.data_source.file_path

            if provider == "s3":
                return self._extract_s3(file_key, limit, offset)
            elif provider == "azure":
                return self._extract_azure(file_key, limit, offset)
            elif provider == "gcs":
                return self._extract_gcs(file_key, limit, offset)
            else:
                raise ValueError(f"Unsupported cloud provider: {provider}")

        except Exception as e:
            raise ExtractionException(f"Failed to extract data from cloud storage: {str(e)}")

    def _extract_s3(self, file_key: str, limit: Optional[int], offset: Optional[int]) -> List[Dict[str, Any]]:
        """Extract data from S3."""
        obj = self._connection.get_object(Bucket=self.data_source.bucket_name, Key=file_key)
        content = obj["Body"].read()

        return self._parse_content(content, file_key, limit, offset)

    def _extract_azure(self, file_key: str, limit: Optional[int], offset: Optional[int]) -> List[Dict[str, Any]]:
        """Extract data from Azure Blob Storage."""
        blob_client = self._connection.get_blob_client(
            container=self.data_source.bucket_name,
            blob=file_key
        )
        content = blob_client.download_blob().readall()

        return self._parse_content(content, file_key, limit, offset)

    def _extract_gcs(self, file_key: str, limit: Optional[int], offset: Optional[int]) -> List[Dict[str, Any]]:
        """Extract data from Google Cloud Storage."""
        bucket = self._connection.bucket(self.data_source.bucket_name)
        blob = bucket.blob(file_key)
        content = blob.download_as_bytes()

        return self._parse_content(content, file_key, limit, offset)

    def _parse_content(self, content: bytes, file_key: str, limit: Optional[int], offset: Optional[int]) -> List[Dict[str, Any]]:
        """Parse file content based on file type."""
        file_extension = file_key.split(".")[-1].lower()

        if file_extension == "csv":
            df = pd.read_csv(io.BytesIO(content))
        elif file_extension == "json":
            df = pd.read_json(io.BytesIO(content))
        elif file_extension in ["xlsx", "xls"]:
            df = pd.read_excel(io.BytesIO(content))
        elif file_extension == "parquet":
            df = pd.read_parquet(io.BytesIO(content))
        else:
            raise ExtractionException(f"Unsupported file format: {file_extension}")

        # Apply offset and limit
        if offset:
            df = df.iloc[offset:]
        if limit:
            df = df.head(limit)

        data = df.to_dict(orient="records")
        self.logger.info(f"Extracted {len(data)} records from cloud storage")
        return data

    def disconnect(self) -> None:
        """Close cloud storage connection."""
        self._connection = None
        self.logger.info("Cloud storage connection closed")


class ExtractorFactory:
    """Factory for creating appropriate extractor instances."""

    @staticmethod
    def create_extractor(
        data_source: DataSource,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseExtractor:
        """
        Create an extractor based on source type.

        Args:
            data_source: DataSource configuration
            config: Additional configuration options

        Returns:
            Appropriate extractor instance
        """
        source_type = data_source.source_type

        if source_type == SourceType.DATABASE:
            if data_source.database_type == DatabaseType.MONGODB:
                return MongoDBExtractor(data_source, config)
            else:
                return DatabaseExtractor(data_source, config)
        elif source_type == SourceType.FILE:
            return FileExtractor(data_source, config)
        elif source_type == SourceType.API:
            return APIExtractor(data_source, config)
        elif source_type == SourceType.WEB:
            return WebExtractor(data_source, config)
        elif source_type == SourceType.CLOUD_STORAGE:
            return CloudStorageExtractor(data_source, config)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
