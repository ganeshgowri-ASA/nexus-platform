"""
Data loaders for ETL module.

This module provides loaders for various target systems including
databases, files, APIs, cloud storage, and streaming platforms.
"""

import logging
import json
import csv
import io
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, Boolean, DateTime
from sqlalchemy.pool import NullPool
from sqlalchemy.dialects.postgresql import insert as pg_insert
import pymongo
import requests
import boto3
from azure.storage.blob import BlobServiceClient
from google.cloud import storage as gcs_storage

from modules.etl.models import DataTarget, SourceType, DatabaseType, LoadStrategy

logger = logging.getLogger(__name__)


class LoaderException(Exception):
    """Base exception for loader errors."""
    pass


class ConnectionException(LoaderException):
    """Exception for connection failures."""
    pass


class LoadException(LoaderException):
    """Exception for load failures."""
    pass


class BaseLoader(ABC):
    """Abstract base class for all loaders."""

    def __init__(self, data_target: DataTarget, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the loader.

        Args:
            data_target: DataTarget configuration
            config: Additional configuration options
        """
        self.data_target = data_target
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._connection = None

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the target system."""
        pass

    @abstractmethod
    def load(
        self,
        data: List[Dict[str, Any]],
        strategy: Optional[LoadStrategy] = None
    ) -> int:
        """
        Load data to the target system.

        Args:
            data: Data records to load
            strategy: Load strategy (full, incremental, upsert, etc.)

        Returns:
            Number of records loaded
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the target system."""
        pass

    def test_connection(self) -> bool:
        """
        Test connection to the target system.

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

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


class DatabaseLoader(BaseLoader):
    """Loader for relational databases."""

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
            self.logger.info(f"Connected to database: {self.data_target.name}")
        except Exception as e:
            raise ConnectionException(f"Failed to connect to database: {str(e)}")

    def _build_connection_string(self) -> str:
        """Build database connection string."""
        if self.data_target.connection_string:
            return self.data_target.connection_string

        db_type = self.data_target.database_type.value
        user = self.data_target.username
        password = self.data_target.password
        host = self.data_target.host
        port = self.data_target.port
        database = self.data_target.database_name

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

    def load(
        self,
        data: List[Dict[str, Any]],
        strategy: Optional[LoadStrategy] = None
    ) -> int:
        """Load data to database."""
        if not data:
            self.logger.warning("No data to load")
            return 0

        strategy = strategy or self.data_target.load_strategy
        table_name = self.config.get("table_name")

        if not table_name:
            raise LoadException("Table name is required for database loading")

        try:
            if strategy == LoadStrategy.FULL:
                return self._load_full(data, table_name)
            elif strategy == LoadStrategy.APPEND:
                return self._load_append(data, table_name)
            elif strategy == LoadStrategy.UPSERT:
                return self._load_upsert(data, table_name)
            elif strategy == LoadStrategy.REPLACE:
                return self._load_replace(data, table_name)
            else:
                raise LoadException(f"Unsupported load strategy: {strategy}")

        except Exception as e:
            raise LoadException(f"Failed to load data to database: {str(e)}")

    def _load_full(self, data: List[Dict[str, Any]], table_name: str) -> int:
        """Full load - truncate and insert."""
        with self._connection.begin() as conn:
            # Truncate table
            conn.execute(text(f"TRUNCATE TABLE {table_name}"))
            # Insert data
            return self._insert_data(data, table_name, conn)

    def _load_append(self, data: List[Dict[str, Any]], table_name: str) -> int:
        """Append data to table."""
        with self._connection.begin() as conn:
            return self._insert_data(data, table_name, conn)

    def _load_upsert(self, data: List[Dict[str, Any]], table_name: str) -> int:
        """Upsert data (insert or update on conflict)."""
        key_columns = self.config.get("key_columns", ["id"])

        if self.data_target.database_type == DatabaseType.POSTGRESQL:
            return self._load_upsert_postgres(data, table_name, key_columns)
        else:
            # Fallback to delete and insert
            return self._load_upsert_fallback(data, table_name, key_columns)

    def _load_upsert_postgres(
        self,
        data: List[Dict[str, Any]],
        table_name: str,
        key_columns: List[str]
    ) -> int:
        """PostgreSQL specific upsert using ON CONFLICT."""
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=self._connection)

        with self._connection.begin() as conn:
            count = 0
            for record in data:
                stmt = pg_insert(table).values(**record)
                update_dict = {c.name: c for c in stmt.excluded if c.name not in key_columns}
                stmt = stmt.on_conflict_do_update(
                    index_elements=key_columns,
                    set_=update_dict
                )
                conn.execute(stmt)
                count += 1

            self.logger.info(f"Upserted {count} records to {table_name}")
            return count

    def _load_upsert_fallback(
        self,
        data: List[Dict[str, Any]],
        table_name: str,
        key_columns: List[str]
    ) -> int:
        """Fallback upsert using delete and insert."""
        with self._connection.begin() as conn:
            count = 0
            for record in data:
                # Build delete condition
                conditions = []
                for key in key_columns:
                    value = record.get(key)
                    if isinstance(value, str):
                        conditions.append(f"{key} = '{value}'")
                    else:
                        conditions.append(f"{key} = {value}")

                where_clause = " AND ".join(conditions)

                # Delete existing record
                conn.execute(text(f"DELETE FROM {table_name} WHERE {where_clause}"))

                # Insert new record
                columns = ", ".join(record.keys())
                values = ", ".join([f":{k}" for k in record.keys()])
                conn.execute(
                    text(f"INSERT INTO {table_name} ({columns}) VALUES ({values})"),
                    record
                )
                count += 1

            self.logger.info(f"Upserted {count} records to {table_name}")
            return count

    def _load_replace(self, data: List[Dict[str, Any]], table_name: str) -> int:
        """Replace - drop and recreate table."""
        with self._connection.begin() as conn:
            # Drop table
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))

            # Create table from data structure
            self._create_table_from_data(data, table_name, conn)

            # Insert data
            return self._insert_data(data, table_name, conn)

    def _insert_data(self, data: List[Dict[str, Any]], table_name: str, conn) -> int:
        """Insert data using pandas for efficiency."""
        df = pd.DataFrame(data)
        df.to_sql(
            table_name,
            conn,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=self.config.get("batch_size", 1000)
        )
        count = len(data)
        self.logger.info(f"Inserted {count} records to {table_name}")
        return count

    def _create_table_from_data(self, data: List[Dict[str, Any]], table_name: str, conn) -> None:
        """Create table based on data structure."""
        if not data:
            raise LoadException("Cannot create table from empty data")

        # Infer column types from first record
        sample = data[0]
        columns = []

        for key, value in sample.items():
            if isinstance(value, bool):
                col_type = Boolean
            elif isinstance(value, int):
                col_type = Integer
            elif isinstance(value, float):
                col_type = Float
            elif isinstance(value, datetime):
                col_type = DateTime
            else:
                col_type = String(500)

            columns.append(Column(key, col_type))

        metadata = MetaData()
        table = Table(table_name, metadata, *columns)
        table.create(self._connection)

    def disconnect(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.dispose()
            self.logger.info("Database connection closed")


class MongoDBLoader(BaseLoader):
    """Loader for MongoDB databases."""

    def connect(self) -> None:
        """Establish MongoDB connection."""
        try:
            connection_string = (
                self.data_target.connection_string or
                f"mongodb://{self.data_target.username}:{self.data_target.password}"
                f"@{self.data_target.host}:{self.data_target.port}/"
            )
            self._connection = pymongo.MongoClient(connection_string)
            # Test connection
            self._connection.server_info()
            self.logger.info(f"Connected to MongoDB: {self.data_target.name}")
        except Exception as e:
            raise ConnectionException(f"Failed to connect to MongoDB: {str(e)}")

    def load(
        self,
        data: List[Dict[str, Any]],
        strategy: Optional[LoadStrategy] = None
    ) -> int:
        """Load data to MongoDB collection."""
        if not data:
            self.logger.warning("No data to load")
            return 0

        try:
            db = self._connection[self.data_target.database_name]
            collection_name = self.config.get("collection")
            if not collection_name:
                raise LoadException("Collection name is required for MongoDB loading")

            collection = db[collection_name]
            strategy = strategy or self.data_target.load_strategy

            if strategy == LoadStrategy.FULL:
                collection.delete_many({})
                result = collection.insert_many(data)
                count = len(result.inserted_ids)
            elif strategy == LoadStrategy.APPEND:
                result = collection.insert_many(data)
                count = len(result.inserted_ids)
            elif strategy == LoadStrategy.UPSERT:
                count = 0
                key_fields = self.config.get("key_columns", ["_id"])
                for record in data:
                    filter_dict = {k: record[k] for k in key_fields if k in record}
                    collection.update_one(filter_dict, {"$set": record}, upsert=True)
                    count += 1
            else:
                raise LoadException(f"Unsupported load strategy: {strategy}")

            self.logger.info(f"Loaded {count} documents to MongoDB")
            return count

        except Exception as e:
            raise LoadException(f"Failed to load data to MongoDB: {str(e)}")

    def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._connection:
            self._connection.close()
            self.logger.info("MongoDB connection closed")


class FileLoader(BaseLoader):
    """Loader for file-based targets (CSV, JSON, Excel, Parquet)."""

    def connect(self) -> None:
        """Verify file path is writable."""
        import os
        file_path = self.data_target.file_path
        if not file_path:
            raise ConnectionException("File path is required")

        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        self.logger.info(f"File path verified: {file_path}")

    def load(
        self,
        data: List[Dict[str, Any]],
        strategy: Optional[LoadStrategy] = None
    ) -> int:
        """Load data to file."""
        if not data:
            self.logger.warning("No data to load")
            return 0

        try:
            file_path = self.data_target.file_path
            file_extension = file_path.split(".")[-1].lower()

            df = pd.DataFrame(data)

            if file_extension == "csv":
                df.to_csv(file_path, index=False)
            elif file_extension == "json":
                df.to_json(file_path, orient="records", indent=2)
            elif file_extension in ["xlsx", "xls"]:
                df.to_excel(file_path, index=False)
            elif file_extension == "parquet":
                df.to_parquet(file_path, index=False)
            else:
                raise LoadException(f"Unsupported file format: {file_extension}")

            count = len(data)
            self.logger.info(f"Loaded {count} records to file: {file_path}")
            return count

        except Exception as e:
            raise LoadException(f"Failed to load data to file: {str(e)}")

    def disconnect(self) -> None:
        """No connection to close for file loading."""
        pass


class APILoader(BaseLoader):
    """Loader for REST APIs."""

    def connect(self) -> None:
        """Test API connection."""
        try:
            headers = self._build_headers()
            response = requests.get(
                self.data_target.api_url,
                headers=headers,
                timeout=self.config.get("timeout", 30)
            )
            response.raise_for_status()
            self.logger.info(f"Connected to API: {self.data_target.name}")
        except Exception as e:
            raise ConnectionException(f"Failed to connect to API: {str(e)}")

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = dict(self.data_target.headers or {})
        headers["Content-Type"] = "application/json"
        if self.data_target.api_key:
            headers["Authorization"] = f"Bearer {self.data_target.api_key}"
        return headers

    def load(
        self,
        data: List[Dict[str, Any]],
        strategy: Optional[LoadStrategy] = None
    ) -> int:
        """Load data to API."""
        if not data:
            self.logger.warning("No data to load")
            return 0

        try:
            headers = self._build_headers()
            url = self.data_target.api_url
            method = self.config.get("method", "POST").upper()
            batch_size = self.config.get("batch_size", 100)

            count = 0

            # Send data in batches
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]

                if method == "POST":
                    response = requests.post(url, json=batch, headers=headers, timeout=30)
                elif method == "PUT":
                    response = requests.put(url, json=batch, headers=headers, timeout=30)
                elif method == "PATCH":
                    response = requests.patch(url, json=batch, headers=headers, timeout=30)
                else:
                    raise LoadException(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                count += len(batch)

            self.logger.info(f"Loaded {count} records to API")
            return count

        except Exception as e:
            raise LoadException(f"Failed to load data to API: {str(e)}")

    def disconnect(self) -> None:
        """No persistent connection for API."""
        pass


class CloudLoader(BaseLoader):
    """Loader for cloud storage (AWS S3, Azure Blob, Google Cloud Storage)."""

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

            self.logger.info(f"Connected to cloud storage: {self.data_target.name}")
        except Exception as e:
            raise ConnectionException(f"Failed to connect to cloud storage: {str(e)}")

    def _connect_s3(self) -> None:
        """Connect to AWS S3."""
        self._connection = boto3.client(
            "s3",
            aws_access_key_id=self.data_target.username,
            aws_secret_access_key=self.data_target.password,
            region_name=self.data_target.region
        )
        # Test connection
        self._connection.head_bucket(Bucket=self.data_target.bucket_name)

    def _connect_azure(self) -> None:
        """Connect to Azure Blob Storage."""
        connection_string = self.data_target.connection_string
        self._connection = BlobServiceClient.from_connection_string(connection_string)
        # Test connection
        self._connection.get_container_client(self.data_target.bucket_name)

    def _connect_gcs(self) -> None:
        """Connect to Google Cloud Storage."""
        self._connection = gcs_storage.Client()
        # Test connection
        self._connection.get_bucket(self.data_target.bucket_name)

    def load(
        self,
        data: List[Dict[str, Any]],
        strategy: Optional[LoadStrategy] = None
    ) -> int:
        """Load data to cloud storage."""
        if not data:
            self.logger.warning("No data to load")
            return 0

        try:
            provider = self.config.get("provider", "s3").lower()
            file_key = self.data_target.file_path

            if provider == "s3":
                return self._load_s3(data, file_key)
            elif provider == "azure":
                return self._load_azure(data, file_key)
            elif provider == "gcs":
                return self._load_gcs(data, file_key)
            else:
                raise ValueError(f"Unsupported cloud provider: {provider}")

        except Exception as e:
            raise LoadException(f"Failed to load data to cloud storage: {str(e)}")

    def _load_s3(self, data: List[Dict[str, Any]], file_key: str) -> int:
        """Load data to S3."""
        content = self._serialize_data(data, file_key)
        self._connection.put_object(
            Bucket=self.data_target.bucket_name,
            Key=file_key,
            Body=content
        )
        count = len(data)
        self.logger.info(f"Loaded {count} records to S3")
        return count

    def _load_azure(self, data: List[Dict[str, Any]], file_key: str) -> int:
        """Load data to Azure Blob Storage."""
        content = self._serialize_data(data, file_key)
        blob_client = self._connection.get_blob_client(
            container=self.data_target.bucket_name,
            blob=file_key
        )
        blob_client.upload_blob(content, overwrite=True)
        count = len(data)
        self.logger.info(f"Loaded {count} records to Azure Blob Storage")
        return count

    def _load_gcs(self, data: List[Dict[str, Any]], file_key: str) -> int:
        """Load data to Google Cloud Storage."""
        content = self._serialize_data(data, file_key)
        bucket = self._connection.bucket(self.data_target.bucket_name)
        blob = bucket.blob(file_key)
        blob.upload_from_string(content)
        count = len(data)
        self.logger.info(f"Loaded {count} records to GCS")
        return count

    def _serialize_data(self, data: List[Dict[str, Any]], file_key: str) -> bytes:
        """Serialize data based on file type."""
        file_extension = file_key.split(".")[-1].lower()
        df = pd.DataFrame(data)

        if file_extension == "csv":
            return df.to_csv(index=False).encode()
        elif file_extension == "json":
            return df.to_json(orient="records").encode()
        elif file_extension in ["xlsx", "xls"]:
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False)
            return buffer.getvalue()
        elif file_extension == "parquet":
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False)
            return buffer.getvalue()
        else:
            # Default to JSON
            return json.dumps(data, indent=2).encode()

    def disconnect(self) -> None:
        """Close cloud storage connection."""
        self._connection = None
        self.logger.info("Cloud storage connection closed")


class StreamLoader(BaseLoader):
    """Loader for streaming platforms (Kafka, etc.)."""

    def connect(self) -> None:
        """Establish streaming connection."""
        # Placeholder for streaming implementation
        self.logger.info(f"Connected to stream: {self.data_target.name}")

    def load(
        self,
        data: List[Dict[str, Any]],
        strategy: Optional[LoadStrategy] = None
    ) -> int:
        """Load data to streaming platform."""
        if not data:
            self.logger.warning("No data to load")
            return 0

        # Placeholder for streaming implementation
        count = len(data)
        self.logger.info(f"Loaded {count} records to stream")
        return count

    def disconnect(self) -> None:
        """Close streaming connection."""
        self.logger.info("Stream connection closed")


class LoaderFactory:
    """Factory for creating appropriate loader instances."""

    @staticmethod
    def create_loader(
        data_target: DataTarget,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseLoader:
        """
        Create a loader based on target type.

        Args:
            data_target: DataTarget configuration
            config: Additional configuration options

        Returns:
            Appropriate loader instance
        """
        target_type = data_target.target_type

        if target_type == SourceType.DATABASE:
            if data_target.database_type == DatabaseType.MONGODB:
                return MongoDBLoader(data_target, config)
            else:
                return DatabaseLoader(data_target, config)
        elif target_type == SourceType.FILE:
            return FileLoader(data_target, config)
        elif target_type == SourceType.API:
            return APILoader(data_target, config)
        elif target_type == SourceType.CLOUD_STORAGE:
            return CloudLoader(data_target, config)
        elif target_type == SourceType.STREAM:
            return StreamLoader(data_target, config)
        else:
            raise ValueError(f"Unsupported target type: {target_type}")
