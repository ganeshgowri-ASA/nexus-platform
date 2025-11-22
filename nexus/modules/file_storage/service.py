"""
File Storage Service

Manages file upload, download, and storage across multiple providers.
"""

import os
from pathlib import Path
from typing import Optional, BinaryIO
from datetime import datetime
import hashlib
from config.settings import settings
from config.logging import get_logger
from nexus.core.exceptions import FileStorageError

logger = get_logger(__name__)


class FileStorageService:
    """
    File storage service with multiple backend support.

    Supported backends:
    - local: Local filesystem
    - s3: AWS S3
    - minio: MinIO
    - azure: Azure Blob Storage
    - gcs: Google Cloud Storage
    """

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize file storage service.

        Args:
            provider: Storage provider (local, s3, minio, azure, gcs)
        """
        self.provider = provider or settings.STORAGE_PROVIDER
        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialize the selected storage provider."""
        if self.provider == "local":
            self._init_local()
        elif self.provider == "s3":
            self._init_s3()
        elif self.provider == "minio":
            self._init_minio()
        elif self.provider == "azure":
            self._init_azure()
        elif self.provider == "gcs":
            self._init_gcs()
        else:
            raise FileStorageError(f"Unsupported storage provider: {self.provider}")

        logger.info(f"File storage initialized with provider: {self.provider}")

    def _init_local(self) -> None:
        """Initialize local filesystem storage."""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _init_s3(self) -> None:
        """Initialize AWS S3 storage."""
        try:
            import boto3
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
            )
            self.bucket_name = settings.S3_BUCKET_NAME
        except Exception as e:
            raise FileStorageError(f"Failed to initialize S3: {e}")

    def _init_minio(self) -> None:
        """Initialize MinIO storage."""
        try:
            from minio import Minio
            self.minio_client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            self.bucket_name = settings.MINIO_BUCKET

            # Create bucket if it doesn't exist
            if not self.minio_client.bucket_exists(self.bucket_name):
                self.minio_client.make_bucket(self.bucket_name)
        except Exception as e:
            raise FileStorageError(f"Failed to initialize MinIO: {e}")

    def _init_azure(self) -> None:
        """Initialize Azure Blob Storage."""
        try:
            from azure.storage.blob import BlobServiceClient
            self.blob_service_client = BlobServiceClient.from_connection_string(
                settings.AZURE_STORAGE_CONNECTION_STRING
            )
            self.container_name = settings.AZURE_STORAGE_CONTAINER
        except Exception as e:
            raise FileStorageError(f"Failed to initialize Azure: {e}")

    def _init_gcs(self) -> None:
        """Initialize Google Cloud Storage."""
        try:
            from google.cloud import storage
            self.gcs_client = storage.Client.from_service_account_json(
                settings.GCS_CREDENTIALS_PATH
            )
            self.bucket_name = settings.GCS_BUCKET_NAME
        except Exception as e:
            raise FileStorageError(f"Failed to initialize GCS: {e}")

    def save_file(
        self,
        file: BinaryIO,
        filename: str,
        folder: Optional[str] = None,
    ) -> str:
        """
        Save a file to storage.

        Args:
            file: File object to save
            filename: Name of the file
            folder: Optional folder/prefix

        Returns:
            File path/key in storage

        Raises:
            FileStorageError: If save fails
        """
        # Generate unique filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        unique_filename = f"{timestamp}_{file_hash}_{filename}"

        if folder:
            file_path = f"{folder}/{unique_filename}"
        else:
            file_path = unique_filename

        try:
            if self.provider == "local":
                return self._save_local(file, file_path)
            elif self.provider == "s3":
                return self._save_s3(file, file_path)
            elif self.provider == "minio":
                return self._save_minio(file, file_path)
            elif self.provider == "azure":
                return self._save_azure(file, file_path)
            elif self.provider == "gcs":
                return self._save_gcs(file, file_path)
            else:
                raise FileStorageError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"File save failed: {e}")
            raise FileStorageError(f"Failed to save file: {str(e)}")

    def _save_local(self, file: BinaryIO, file_path: str) -> str:
        """Save file to local filesystem."""
        full_path = self.upload_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(file.read())

        logger.debug(f"File saved locally: {file_path}")
        return str(file_path)

    def _save_s3(self, file: BinaryIO, file_path: str) -> str:
        """Save file to AWS S3."""
        self.s3_client.upload_fileobj(file, self.bucket_name, file_path)
        logger.debug(f"File saved to S3: {file_path}")
        return file_path

    def _save_minio(self, file: BinaryIO, file_path: str) -> str:
        """Save file to MinIO."""
        # Get file size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        self.minio_client.put_object(
            self.bucket_name,
            file_path,
            file,
            file_size,
        )
        logger.debug(f"File saved to MinIO: {file_path}")
        return file_path

    def _save_azure(self, file: BinaryIO, file_path: str) -> str:
        """Save file to Azure Blob Storage."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path,
        )
        blob_client.upload_blob(file)
        logger.debug(f"File saved to Azure: {file_path}")
        return file_path

    def _save_gcs(self, file: BinaryIO, file_path: str) -> str:
        """Save file to Google Cloud Storage."""
        bucket = self.gcs_client.bucket(self.bucket_name)
        blob = bucket.blob(file_path)
        blob.upload_from_file(file)
        logger.debug(f"File saved to GCS: {file_path}")
        return file_path

    def get_file(self, file_path: str) -> bytes:
        """
        Retrieve a file from storage.

        Args:
            file_path: Path/key of the file

        Returns:
            File contents as bytes

        Raises:
            FileStorageError: If retrieval fails
        """
        try:
            if self.provider == "local":
                return self._get_local(file_path)
            elif self.provider == "s3":
                return self._get_s3(file_path)
            elif self.provider == "minio":
                return self._get_minio(file_path)
            elif self.provider == "azure":
                return self._get_azure(file_path)
            elif self.provider == "gcs":
                return self._get_gcs(file_path)
            else:
                raise FileStorageError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"File retrieval failed: {e}")
            raise FileStorageError(f"Failed to retrieve file: {str(e)}")

    def _get_local(self, file_path: str) -> bytes:
        """Get file from local filesystem."""
        full_path = self.upload_dir / file_path
        with open(full_path, "rb") as f:
            return f.read()

    def _get_s3(self, file_path: str) -> bytes:
        """Get file from AWS S3."""
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_path)
        return response["Body"].read()

    def _get_minio(self, file_path: str) -> bytes:
        """Get file from MinIO."""
        response = self.minio_client.get_object(self.bucket_name, file_path)
        return response.read()

    def _get_azure(self, file_path: str) -> bytes:
        """Get file from Azure Blob Storage."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=file_path,
        )
        return blob_client.download_blob().readall()

    def _get_gcs(self, file_path: str) -> bytes:
        """Get file from Google Cloud Storage."""
        bucket = self.gcs_client.bucket(self.bucket_name)
        blob = bucket.blob(file_path)
        return blob.download_as_bytes()

    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path/key of the file

        Returns:
            True if deletion was successful

        Raises:
            FileStorageError: If deletion fails
        """
        try:
            if self.provider == "local":
                full_path = self.upload_dir / file_path
                if full_path.exists():
                    full_path.unlink()
                    return True
            elif self.provider == "s3":
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
                return True
            elif self.provider == "minio":
                self.minio_client.remove_object(self.bucket_name, file_path)
                return True
            elif self.provider == "azure":
                blob_client = self.blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=file_path,
                )
                blob_client.delete_blob()
                return True
            elif self.provider == "gcs":
                bucket = self.gcs_client.bucket(self.bucket_name)
                blob = bucket.blob(file_path)
                blob.delete()
                return True

            return False

        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            raise FileStorageError(f"Failed to delete file: {str(e)}")

    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            file_path: Path/key of the file

        Returns:
            True if file exists
        """
        try:
            if self.provider == "local":
                return (self.upload_dir / file_path).exists()
            elif self.provider == "s3":
                try:
                    self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
                    return True
                except:
                    return False
            elif self.provider == "minio":
                try:
                    self.minio_client.stat_object(self.bucket_name, file_path)
                    return True
                except:
                    return False
            # Add other providers as needed
            return False

        except Exception as e:
            logger.error(f"File existence check failed: {e}")
            return False
