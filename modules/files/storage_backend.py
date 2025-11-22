"""Storage backend module for NEXUS Platform.

This module handles file storage operations with support for local storage
and cloud storage providers (AWS S3, Azure Blob, Google Cloud Storage).
"""
import os
import shutil
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, BinaryIO, Tuple
from io import BytesIO


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_file(self,
                 file_content: BinaryIO,
                 filename: str,
                 user_id: int,
                 metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """Save a file to storage.

        Args:
            file_content: File content as a file-like object
            filename: Original filename
            user_id: ID of the user uploading the file
            metadata: Optional metadata dictionary

        Returns:
            Tuple of (file_path, file_id)
        """
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> BinaryIO:
        """Retrieve a file from storage.

        Args:
            file_path: Path to the file

        Returns:
            File content as a file-like object
        """
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage.

        Args:
            file_path: Path to the file

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in storage.

        Args:
            file_path: Path to the file

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def get_file_size(self, file_path: str) -> int:
        """Get the size of a file.

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes
        """
        pass

    @abstractmethod
    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy a file within storage.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move a file within storage.

        Args:
            source_path: Source file path
            dest_path: Destination file path

        Returns:
            True if successful, False otherwise
        """
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, base_path: str = "data/uploads"):
        """Initialize local storage backend.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_file(self,
                 file_content: BinaryIO,
                 filename: str,
                 user_id: int,
                 metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """Save a file to local storage.

        Files are organized by: base_path/user_id/year/month/unique_id_filename

        Args:
            file_content: File content as a file-like object
            filename: Original filename
            user_id: ID of the user uploading the file
            metadata: Optional metadata dictionary

        Returns:
            Tuple of (file_path, file_id)
        """
        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Create organized directory structure
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")

        # Build directory path: base_path/user_id/year/month/
        dir_path = self.base_path / str(user_id) / year / month
        dir_path.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)

        # Create unique filename: file_id + original extension
        file_ext = Path(safe_filename).suffix
        unique_filename = f"{file_id}{file_ext}"

        # Full file path
        file_path = dir_path / unique_filename

        # Save file
        with open(file_path, 'wb') as f:
            # Read and write in chunks for large files
            chunk_size = 8192
            while True:
                chunk = file_content.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)

        # Return relative path from base_path
        relative_path = str(file_path.relative_to(self.base_path))
        return relative_path, file_id

    def get_file(self, file_path: str) -> BinaryIO:
        """Retrieve a file from local storage.

        Args:
            file_path: Relative path to the file

        Returns:
            File content as a file-like object
        """
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Return file handle (caller must close it)
        return open(full_path, 'rb')

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from local storage.

        Args:
            file_path: Relative path to the file

        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.base_path / file_path

            if not full_path.exists():
                return False

            full_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in local storage.

        Args:
            file_path: Relative path to the file

        Returns:
            True if file exists, False otherwise
        """
        full_path = self.base_path / file_path
        return full_path.exists() and full_path.is_file()

    def get_file_size(self, file_path: str) -> int:
        """Get the size of a file in local storage.

        Args:
            file_path: Relative path to the file

        Returns:
            File size in bytes
        """
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        return full_path.stat().st_size

    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy a file within local storage.

        Args:
            source_path: Source file relative path
            dest_path: Destination file relative path

        Returns:
            True if successful, False otherwise
        """
        try:
            source_full = self.base_path / source_path
            dest_full = self.base_path / dest_path

            # Create destination directory if needed
            dest_full.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_full, dest_full)
            return True
        except Exception as e:
            print(f"Error copying file: {e}")
            return False

    def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move a file within local storage.

        Args:
            source_path: Source file relative path
            dest_path: Destination file relative path

        Returns:
            True if successful, False otherwise
        """
        try:
            source_full = self.base_path / source_path
            dest_full = self.base_path / dest_path

            # Create destination directory if needed
            dest_full.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(source_full), str(dest_full))
            return True
        except Exception as e:
            print(f"Error moving file: {e}")
            return False

    def get_absolute_path(self, file_path: str) -> str:
        """Get absolute filesystem path for a relative path.

        Args:
            file_path: Relative path to the file

        Returns:
            Absolute path string
        """
        return str(self.base_path / file_path)

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize a filename for safe storage.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove any path components
        filename = os.path.basename(filename)

        # Replace unsafe characters
        unsafe_chars = ['/', '\\', '..', '\x00', '\n', '\r', '\t']
        for char in unsafe_chars:
            filename = filename.replace(char, '_')

        # Limit filename length (keep extension)
        name, ext = os.path.splitext(filename)
        if len(name) > 200:
            name = name[:200]

        return name + ext


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend (stub for future implementation)."""

    def __init__(self,
                 bucket_name: str,
                 aws_access_key: Optional[str] = None,
                 aws_secret_key: Optional[str] = None,
                 region: str = 'us-east-1'):
        """Initialize S3 storage backend.

        Args:
            bucket_name: S3 bucket name
            aws_access_key: AWS access key (or use environment variable)
            aws_secret_key: AWS secret key (or use environment variable)
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.region = region

        # In production, initialize boto3 client here
        # import boto3
        # self.s3_client = boto3.client(
        #     's3',
        #     aws_access_key_id=aws_access_key,
        #     aws_secret_access_key=aws_secret_key,
        #     region_name=region
        # )

    def save_file(self,
                 file_content: BinaryIO,
                 filename: str,
                 user_id: int,
                 metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """Save a file to S3.

        Args:
            file_content: File content
            filename: Original filename
            user_id: User ID
            metadata: Optional metadata

        Returns:
            Tuple of (s3_key, file_id)
        """
        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Create S3 key
        now = datetime.utcnow()
        s3_key = f"uploads/{user_id}/{now.year}/{now.month:02d}/{file_id}_{filename}"

        # Upload to S3
        # self.s3_client.upload_fileobj(
        #     file_content,
        #     self.bucket_name,
        #     s3_key,
        #     ExtraArgs={'Metadata': metadata or {}}
        # )

        raise NotImplementedError("S3 storage backend not yet implemented")

    def get_file(self, file_path: str) -> BinaryIO:
        """Retrieve a file from S3."""
        # buffer = BytesIO()
        # self.s3_client.download_fileobj(self.bucket_name, file_path, buffer)
        # buffer.seek(0)
        # return buffer
        raise NotImplementedError("S3 storage backend not yet implemented")

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from S3."""
        # self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
        # return True
        raise NotImplementedError("S3 storage backend not yet implemented")

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in S3."""
        # try:
        #     self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
        #     return True
        # except:
        #     return False
        raise NotImplementedError("S3 storage backend not yet implemented")

    def get_file_size(self, file_path: str) -> int:
        """Get file size from S3."""
        # response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
        # return response['ContentLength']
        raise NotImplementedError("S3 storage backend not yet implemented")

    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy a file within S3."""
        # copy_source = {'Bucket': self.bucket_name, 'Key': source_path}
        # self.s3_client.copy_object(CopySource=copy_source, Bucket=self.bucket_name, Key=dest_path)
        # return True
        raise NotImplementedError("S3 storage backend not yet implemented")

    def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move a file within S3."""
        # self.copy_file(source_path, dest_path)
        # self.delete_file(source_path)
        # return True
        raise NotImplementedError("S3 storage backend not yet implemented")


class AzureBlobStorageBackend(StorageBackend):
    """Azure Blob Storage backend (stub for future implementation)."""

    def __init__(self,
                 container_name: str,
                 connection_string: Optional[str] = None):
        """Initialize Azure Blob Storage backend.

        Args:
            container_name: Azure container name
            connection_string: Azure connection string
        """
        self.container_name = container_name

        # In production, initialize Azure client here
        # from azure.storage.blob import BlobServiceClient
        # self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        # self.container_client = self.blob_service_client.get_container_client(container_name)

    def save_file(self,
                 file_content: BinaryIO,
                 filename: str,
                 user_id: int,
                 metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """Save a file to Azure Blob Storage."""
        raise NotImplementedError("Azure Blob Storage backend not yet implemented")

    def get_file(self, file_path: str) -> BinaryIO:
        """Retrieve a file from Azure Blob Storage."""
        raise NotImplementedError("Azure Blob Storage backend not yet implemented")

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from Azure Blob Storage."""
        raise NotImplementedError("Azure Blob Storage backend not yet implemented")

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in Azure Blob Storage."""
        raise NotImplementedError("Azure Blob Storage backend not yet implemented")

    def get_file_size(self, file_path: str) -> int:
        """Get file size from Azure Blob Storage."""
        raise NotImplementedError("Azure Blob Storage backend not yet implemented")

    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy a file within Azure Blob Storage."""
        raise NotImplementedError("Azure Blob Storage backend not yet implemented")

    def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move a file within Azure Blob Storage."""
        raise NotImplementedError("Azure Blob Storage backend not yet implemented")


class GoogleCloudStorageBackend(StorageBackend):
    """Google Cloud Storage backend (stub for future implementation)."""

    def __init__(self,
                 bucket_name: str,
                 project_id: Optional[str] = None,
                 credentials_path: Optional[str] = None):
        """Initialize Google Cloud Storage backend.

        Args:
            bucket_name: GCS bucket name
            project_id: Google Cloud project ID
            credentials_path: Path to service account credentials JSON
        """
        self.bucket_name = bucket_name
        self.project_id = project_id

        # In production, initialize GCS client here
        # from google.cloud import storage
        # if credentials_path:
        #     self.storage_client = storage.Client.from_service_account_json(credentials_path)
        # else:
        #     self.storage_client = storage.Client(project=project_id)
        # self.bucket = self.storage_client.bucket(bucket_name)

    def save_file(self,
                 file_content: BinaryIO,
                 filename: str,
                 user_id: int,
                 metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """Save a file to Google Cloud Storage."""
        raise NotImplementedError("Google Cloud Storage backend not yet implemented")

    def get_file(self, file_path: str) -> BinaryIO:
        """Retrieve a file from Google Cloud Storage."""
        raise NotImplementedError("Google Cloud Storage backend not yet implemented")

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from Google Cloud Storage."""
        raise NotImplementedError("Google Cloud Storage backend not yet implemented")

    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in Google Cloud Storage."""
        raise NotImplementedError("Google Cloud Storage backend not yet implemented")

    def get_file_size(self, file_path: str) -> int:
        """Get file size from Google Cloud Storage."""
        raise NotImplementedError("Google Cloud Storage backend not yet implemented")

    def copy_file(self, source_path: str, dest_path: str) -> bool:
        """Copy a file within Google Cloud Storage."""
        raise NotImplementedError("Google Cloud Storage backend not yet implemented")

    def move_file(self, source_path: str, dest_path: str) -> bool:
        """Move a file within Google Cloud Storage."""
        raise NotImplementedError("Google Cloud Storage backend not yet implemented")


def get_storage_backend(backend_type: str = "local", **kwargs) -> StorageBackend:
    """Factory function to get a storage backend.

    Args:
        backend_type: Type of storage backend ('local', 's3', 'azure', 'gcs')
        **kwargs: Backend-specific configuration

    Returns:
        StorageBackend instance

    Raises:
        ValueError: If backend_type is not supported
    """
    backends = {
        'local': LocalStorageBackend,
        's3': S3StorageBackend,
        'azure': AzureBlobStorageBackend,
        'gcs': GoogleCloudStorageBackend,
    }

    backend_class = backends.get(backend_type.lower())
    if not backend_class:
        raise ValueError(f"Unsupported storage backend: {backend_type}")

    return backend_class(**kwargs)
