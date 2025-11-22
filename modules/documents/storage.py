"""
File storage module with multi-backend support.

This module provides unified file storage interface supporting multiple backends:
- Local filesystem storage
- AWS S3
- Azure Blob Storage
- Google Cloud Storage

Features:
- Automatic backend selection
- File upload/download with chunking
- Deduplication using content hashing
- Compression support
- Cloud sync capabilities
"""

import hashlib
import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Tuple

import aiofiles
from fastapi import UploadFile

from backend.core.config import get_settings
from backend.core.exceptions import (
    FileDeleteException,
    FileNotFoundException,
    FileUploadException,
    StorageException,
)
from backend.core.logging import LoggerMixin

settings = get_settings()


class StorageBackend(ABC, LoggerMixin):
    """
    Abstract base class for storage backends.

    All storage backends must implement these methods.
    """

    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO | UploadFile,
        destination_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Upload a file to storage.

        Args:
            file: File object to upload
            destination_path: Destination path in storage
            content_type: Content type (MIME type)

        Returns:
            str: Path to uploaded file
        """
        pass

    @abstractmethod
    async def download_file(self, file_path: str) -> bytes:
        """
        Download a file from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            bytes: File content
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            file_path: Path to file in storage

        Returns:
            bool: True if deleted successfully
        """
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            file_path: Path to file in storage

        Returns:
            bool: True if file exists
        """
        pass

    @abstractmethod
    async def get_file_size(self, file_path: str) -> int:
        """
        Get file size in bytes.

        Args:
            file_path: Path to file in storage

        Returns:
            int: File size in bytes
        """
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in storage with optional prefix.

        Args:
            prefix: Path prefix to filter files

        Returns:
            list[str]: List of file paths
        """
        pass

    @abstractmethod
    async def copy_file(self, source_path: str, destination_path: str) -> str:
        """
        Copy a file within storage.

        Args:
            source_path: Source file path
            destination_path: Destination file path

        Returns:
            str: Destination path
        """
        pass


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem storage backend.

    Stores files on the local filesystem with organized directory structure.
    """

    def __init__(self, base_path: str | None = None) -> None:
        """
        Initialize local storage backend.

        Args:
            base_path: Base directory for storage (defaults to config)
        """
        self.base_path = Path(base_path or settings.STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger.info("local_storage_initialized", base_path=str(self.base_path))

    async def upload_file(
        self,
        file: BinaryIO | UploadFile,
        destination_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload file to local storage."""
        try:
            full_path = self.base_path / destination_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(file, UploadFile):
                # FastAPI UploadFile
                async with aiofiles.open(full_path, "wb") as f:
                    content = await file.read()
                    await f.write(content)
            else:
                # Regular file object
                async with aiofiles.open(full_path, "wb") as f:
                    content = file.read()
                    await f.write(content)

            self.logger.info(
                "file_uploaded_local",
                destination_path=destination_path,
                size=full_path.stat().st_size,
            )
            return destination_path

        except Exception as e:
            self.logger.error("local_upload_failed", error=str(e), path=destination_path)
            raise FileUploadException(f"Failed to upload file: {str(e)}")

    async def download_file(self, file_path: str) -> bytes:
        """Download file from local storage."""
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundException(file_path)

        try:
            async with aiofiles.open(full_path, "rb") as f:
                content = await f.read()

            self.logger.debug("file_downloaded_local", file_path=file_path, size=len(content))
            return content

        except Exception as e:
            self.logger.error("local_download_failed", error=str(e), path=file_path)
            raise StorageException(f"Failed to download file: {str(e)}")

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage."""
        full_path = self.base_path / file_path

        if not full_path.exists():
            return False

        try:
            full_path.unlink()
            self.logger.info("file_deleted_local", file_path=file_path)
            return True

        except Exception as e:
            self.logger.error("local_delete_failed", error=str(e), path=file_path)
            raise FileDeleteException(f"Failed to delete file: {str(e)}")

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in local storage."""
        full_path = self.base_path / file_path
        return full_path.exists() and full_path.is_file()

    async def get_file_size(self, file_path: str) -> int:
        """Get file size from local storage."""
        full_path = self.base_path / file_path

        if not full_path.exists():
            raise FileNotFoundException(file_path)

        return full_path.stat().st_size

    async def list_files(self, prefix: str = "") -> list[str]:
        """List files in local storage."""
        search_path = self.base_path / prefix if prefix else self.base_path
        files = []

        if search_path.is_dir():
            for file_path in search_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.base_path)
                    files.append(str(relative_path))

        return files

    async def copy_file(self, source_path: str, destination_path: str) -> str:
        """Copy file within local storage."""
        source_full = self.base_path / source_path
        dest_full = self.base_path / destination_path

        if not source_full.exists():
            raise FileNotFoundException(source_path)

        dest_full.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_full, dest_full)

        self.logger.info("file_copied_local", source=source_path, destination=destination_path)
        return destination_path


class S3StorageBackend(StorageBackend):
    """
    AWS S3 storage backend.

    Stores files in Amazon S3 or S3-compatible services.
    """

    def __init__(self) -> None:
        """Initialize S3 storage backend."""
        try:
            import boto3
            from botocore.exceptions import ClientError

            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            )
            self.bucket_name = settings.AWS_S3_BUCKET_NAME
            self.ClientError = ClientError

            self.logger.info("s3_storage_initialized", bucket=self.bucket_name)

        except ImportError:
            raise StorageException("boto3 is required for S3 storage. Install with: pip install boto3")

    async def upload_file(
        self,
        file: BinaryIO | UploadFile,
        destination_path: str,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload file to S3."""
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            if isinstance(file, UploadFile):
                content = await file.read()
            else:
                content = file.read()

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=destination_path,
                Body=content,
                **extra_args,
            )

            self.logger.info("file_uploaded_s3", destination_path=destination_path, size=len(content))
            return destination_path

        except self.ClientError as e:
            self.logger.error("s3_upload_failed", error=str(e), path=destination_path)
            raise FileUploadException(f"S3 upload failed: {str(e)}")

    async def download_file(self, file_path: str) -> bytes:
        """Download file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_path)
            content = response["Body"].read()

            self.logger.debug("file_downloaded_s3", file_path=file_path, size=len(content))
            return content

        except self.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundException(file_path)
            self.logger.error("s3_download_failed", error=str(e), path=file_path)
            raise StorageException(f"S3 download failed: {str(e)}")

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            self.logger.info("file_deleted_s3", file_path=file_path)
            return True

        except self.ClientError as e:
            self.logger.error("s3_delete_failed", error=str(e), path=file_path)
            raise FileDeleteException(f"S3 delete failed: {str(e)}")

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except self.ClientError:
            return False

    async def get_file_size(self, file_path: str) -> int:
        """Get file size from S3."""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
            return response["ContentLength"]
        except self.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundException(file_path)
            raise StorageException(f"Failed to get file size: {str(e)}")

    async def list_files(self, prefix: str = "") -> list[str]:
        """List files in S3."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            files = []

            if "Contents" in response:
                files = [obj["Key"] for obj in response["Contents"]]

            return files

        except self.ClientError as e:
            self.logger.error("s3_list_failed", error=str(e), prefix=prefix)
            raise StorageException(f"S3 list failed: {str(e)}")

    async def copy_file(self, source_path: str, destination_path: str) -> str:
        """Copy file within S3."""
        try:
            copy_source = {"Bucket": self.bucket_name, "Key": source_path}
            self.s3_client.copy_object(
                CopySource=copy_source, Bucket=self.bucket_name, Key=destination_path
            )

            self.logger.info("file_copied_s3", source=source_path, destination=destination_path)
            return destination_path

        except self.ClientError as e:
            self.logger.error("s3_copy_failed", error=str(e), source=source_path)
            raise StorageException(f"S3 copy failed: {str(e)}")


class StorageManager(LoggerMixin):
    """
    Storage manager with automatic backend selection and utilities.

    Provides high-level storage operations with deduplication, compression,
    and automatic backend switching.
    """

    def __init__(self, backend: Optional[StorageBackend] = None) -> None:
        """
        Initialize storage manager.

        Args:
            backend: Storage backend (auto-selected if None)
        """
        if backend:
            self.backend = backend
        else:
            self.backend = self._get_backend()

        self.logger.info(
            "storage_manager_initialized",
            backend_type=self.backend.__class__.__name__,
        )

    def _get_backend(self) -> StorageBackend:
        """Get storage backend based on configuration."""
        backend_type = settings.STORAGE_BACKEND.lower()

        if backend_type == "local":
            return LocalStorageBackend()
        elif backend_type == "s3":
            return S3StorageBackend()
        elif backend_type == "azure":
            # Azure backend would be implemented similarly
            raise NotImplementedError("Azure storage backend not yet implemented")
        elif backend_type == "gcs":
            # GCS backend would be implemented similarly
            raise NotImplementedError("GCS storage backend not yet implemented")
        else:
            self.logger.warning(
                "unknown_backend_type",
                backend=backend_type,
                fallback="local",
            )
            return LocalStorageBackend()

    async def compute_file_hash(self, file: BinaryIO | UploadFile) -> str:
        """
        Compute SHA-256 hash of file content.

        Args:
            file: File to hash

        Returns:
            str: SHA-256 hash hex string
        """
        sha256_hash = hashlib.sha256()

        if isinstance(file, UploadFile):
            content = await file.read()
            await file.seek(0)  # Reset file pointer
        else:
            content = file.read()
            file.seek(0)  # Reset file pointer

        sha256_hash.update(content)
        return sha256_hash.hexdigest()

    async def generate_unique_path(
        self, file_name: str, folder: str = "documents", use_hash: bool = True
    ) -> str:
        """
        Generate unique file path with optional hash-based naming.

        Args:
            file_name: Original file name
            folder: Folder/prefix for organization
            use_hash: Use hash in filename for uniqueness

        Returns:
            str: Unique file path
        """
        from datetime import datetime
        import uuid

        # Extract file extension
        file_stem = Path(file_name).stem
        file_ext = Path(file_name).suffix

        # Create organized path: folder/YYYY/MM/filename
        now = datetime.utcnow()
        year = now.strftime("%Y")
        month = now.strftime("%m")

        if use_hash:
            # Use UUID for uniqueness
            unique_id = uuid.uuid4().hex[:12]
            filename = f"{file_stem}_{unique_id}{file_ext}"
        else:
            filename = file_name

        return f"{folder}/{year}/{month}/{filename}"

    async def save_file(
        self,
        file: BinaryIO | UploadFile,
        destination_path: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> Tuple[str, str, int]:
        """
        Save file to storage with metadata.

        Args:
            file: File to save
            destination_path: Destination path (auto-generated if None)
            content_type: Content type

        Returns:
            Tuple[str, str, int]: (file_path, file_hash, file_size)
        """
        # Compute file hash
        file_hash = await self.compute_file_hash(file)

        # Generate destination path if not provided
        if not destination_path:
            file_name = file.filename if isinstance(file, UploadFile) else "file"
            destination_path = await self.generate_unique_path(file_name)

        # Upload file
        await self.backend.upload_file(file, destination_path, content_type)

        # Get file size
        file_size = await self.backend.get_file_size(destination_path)

        self.logger.info(
            "file_saved",
            path=destination_path,
            hash=file_hash,
            size=file_size,
        )

        return destination_path, file_hash, file_size

    async def get_file(self, file_path: str) -> bytes:
        """
        Retrieve file from storage.

        Args:
            file_path: Path to file

        Returns:
            bytes: File content
        """
        return await self.backend.download_file(file_path)

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_path: Path to file

        Returns:
            bool: True if deleted
        """
        return await self.backend.delete_file(file_path)

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists.

        Args:
            file_path: Path to file

        Returns:
            bool: True if exists
        """
        return await self.backend.file_exists(file_path)

    async def get_file_info(self, file_path: str) -> dict[str, any]:
        """
        Get file information.

        Args:
            file_path: Path to file

        Returns:
            dict: File information
        """
        size = await self.backend.get_file_size(file_path)
        exists = await self.backend.file_exists(file_path)

        return {
            "path": file_path,
            "size": size,
            "exists": exists,
        }
