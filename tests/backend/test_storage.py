"""
Unit tests for storage backend functionality.

Tests cover:
- Local storage backend operations
- S3 storage backend operations
- Storage manager functionality
- File upload/download/delete operations
- File hashing and deduplication
- Path generation
"""

import hashlib
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from io import BytesIO

from fastapi import UploadFile

from modules.documents.storage import (
    LocalStorageBackend,
    S3StorageBackend,
    StorageBackend,
    StorageManager,
)
from backend.core.exceptions import (
    FileNotFoundException,
    FileUploadException,
    FileDeleteException,
    StorageException,
)


@pytest.mark.unit
class TestLocalStorageBackend:
    """Test local filesystem storage backend."""

    @pytest.mark.asyncio
    async def test_init_creates_base_directory(self, temp_storage_path):
        """Test that initialization creates base directory."""
        storage_path = temp_storage_path / "test_storage"
        backend = LocalStorageBackend(str(storage_path))

        assert storage_path.exists()
        assert storage_path.is_dir()

    @pytest.mark.asyncio
    async def test_upload_file_success(self, temp_storage_path, sample_upload_file):
        """Test successful file upload."""
        backend = LocalStorageBackend(str(temp_storage_path))
        upload_file = sample_upload_file("test.txt", b"test content")

        result_path = await backend.upload_file(
            upload_file,
            "documents/test.txt",
            "text/plain"
        )

        assert result_path == "documents/test.txt"
        full_path = temp_storage_path / "documents/test.txt"
        assert full_path.exists()
        assert full_path.read_bytes() == b"test content"

    @pytest.mark.asyncio
    async def test_upload_file_creates_subdirectories(
        self, temp_storage_path, sample_upload_file
    ):
        """Test that upload creates necessary subdirectories."""
        backend = LocalStorageBackend(str(temp_storage_path))
        upload_file = sample_upload_file()

        await backend.upload_file(
            upload_file,
            "deep/nested/directory/file.txt"
        )

        full_path = temp_storage_path / "deep/nested/directory/file.txt"
        assert full_path.exists()

    @pytest.mark.asyncio
    async def test_upload_regular_file_object(self, temp_storage_path):
        """Test uploading regular file object (not UploadFile)."""
        backend = LocalStorageBackend(str(temp_storage_path))
        file_obj = BytesIO(b"regular file content")

        result_path = await backend.upload_file(
            file_obj,
            "regular_file.txt"
        )

        full_path = temp_storage_path / "regular_file.txt"
        assert full_path.exists()
        assert full_path.read_bytes() == b"regular file content"

    @pytest.mark.asyncio
    async def test_download_file_success(self, temp_storage_path):
        """Test successful file download."""
        backend = LocalStorageBackend(str(temp_storage_path))

        # Create test file
        test_file = temp_storage_path / "download_test.txt"
        test_file.write_bytes(b"download content")

        content = await backend.download_file("download_test.txt")

        assert content == b"download content"

    @pytest.mark.asyncio
    async def test_download_file_not_found(self, temp_storage_path):
        """Test downloading non-existent file raises exception."""
        backend = LocalStorageBackend(str(temp_storage_path))

        with pytest.raises(FileNotFoundException):
            await backend.download_file("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_delete_file_success(self, temp_storage_path):
        """Test successful file deletion."""
        backend = LocalStorageBackend(str(temp_storage_path))

        # Create test file
        test_file = temp_storage_path / "delete_test.txt"
        test_file.write_text("delete me")

        result = await backend.delete_file("delete_test.txt")

        assert result is True
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, temp_storage_path):
        """Test deleting non-existent file returns False."""
        backend = LocalStorageBackend(str(temp_storage_path))

        result = await backend.delete_file("nonexistent.txt")

        assert result is False

    @pytest.mark.asyncio
    async def test_file_exists_true(self, temp_storage_path):
        """Test file_exists returns True for existing file."""
        backend = LocalStorageBackend(str(temp_storage_path))

        test_file = temp_storage_path / "exists.txt"
        test_file.write_text("exists")

        exists = await backend.file_exists("exists.txt")

        assert exists is True

    @pytest.mark.asyncio
    async def test_file_exists_false(self, temp_storage_path):
        """Test file_exists returns False for non-existent file."""
        backend = LocalStorageBackend(str(temp_storage_path))

        exists = await backend.file_exists("nonexistent.txt")

        assert exists is False

    @pytest.mark.asyncio
    async def test_get_file_size(self, temp_storage_path):
        """Test getting file size."""
        backend = LocalStorageBackend(str(temp_storage_path))

        test_content = b"test content with specific size"
        test_file = temp_storage_path / "size_test.txt"
        test_file.write_bytes(test_content)

        size = await backend.get_file_size("size_test.txt")

        assert size == len(test_content)

    @pytest.mark.asyncio
    async def test_get_file_size_not_found(self, temp_storage_path):
        """Test getting size of non-existent file raises exception."""
        backend = LocalStorageBackend(str(temp_storage_path))

        with pytest.raises(FileNotFoundException):
            await backend.get_file_size("nonexistent.txt")

    @pytest.mark.asyncio
    async def test_list_files(self, temp_storage_path):
        """Test listing files in storage."""
        backend = LocalStorageBackend(str(temp_storage_path))

        # Create test files
        (temp_storage_path / "file1.txt").write_text("1")
        (temp_storage_path / "file2.txt").write_text("2")
        (temp_storage_path / "subdir").mkdir()
        (temp_storage_path / "subdir" / "file3.txt").write_text("3")

        files = await backend.list_files()

        assert len(files) == 3
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert str(Path("subdir/file3.txt")) in files

    @pytest.mark.asyncio
    async def test_list_files_with_prefix(self, temp_storage_path):
        """Test listing files with prefix filter."""
        backend = LocalStorageBackend(str(temp_storage_path))

        # Create test files
        subdir = temp_storage_path / "prefix"
        subdir.mkdir()
        (subdir / "file1.txt").write_text("1")
        (subdir / "file2.txt").write_text("2")
        (temp_storage_path / "other.txt").write_text("other")

        files = await backend.list_files("prefix")

        assert len(files) == 2
        assert all("prefix" in f for f in files)

    @pytest.mark.asyncio
    async def test_copy_file_success(self, temp_storage_path):
        """Test successful file copy."""
        backend = LocalStorageBackend(str(temp_storage_path))

        # Create source file
        source = temp_storage_path / "source.txt"
        source.write_text("copy me")

        result = await backend.copy_file("source.txt", "copy/destination.txt")

        assert result == "copy/destination.txt"
        dest = temp_storage_path / "copy/destination.txt"
        assert dest.exists()
        assert dest.read_text() == "copy me"
        assert source.exists()  # Source still exists

    @pytest.mark.asyncio
    async def test_copy_file_not_found(self, temp_storage_path):
        """Test copying non-existent file raises exception."""
        backend = LocalStorageBackend(str(temp_storage_path))

        with pytest.raises(FileNotFoundException):
            await backend.copy_file("nonexistent.txt", "destination.txt")


@pytest.mark.unit
class TestS3StorageBackend:
    """Test S3 storage backend."""

    @pytest.mark.asyncio
    async def test_init_requires_boto3(self):
        """Test that S3 backend requires boto3."""
        with patch("modules.documents.storage.boto3", None):
            with pytest.raises(StorageException, match="boto3 is required"):
                S3StorageBackend()

    @pytest.mark.asyncio
    @patch("modules.documents.storage.boto3")
    async def test_upload_file_success(self, mock_boto3, sample_upload_file):
        """Test successful S3 file upload."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        backend = S3StorageBackend()
        upload_file = sample_upload_file("test.txt", b"s3 content")

        result = await backend.upload_file(
            upload_file,
            "documents/test.txt",
            "text/plain"
        )

        assert result == "documents/test.txt"
        mock_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    @patch("modules.documents.storage.boto3")
    async def test_download_file_success(self, mock_boto3):
        """Test successful S3 file download."""
        mock_client = MagicMock()
        mock_response = {"Body": MagicMock(read=lambda: b"s3 content")}
        mock_client.get_object.return_value = mock_response
        mock_boto3.client.return_value = mock_client

        backend = S3StorageBackend()
        content = await backend.download_file("test.txt")

        assert content == b"s3 content"
        mock_client.get_object.assert_called_once()

    @pytest.mark.asyncio
    @patch("modules.documents.storage.boto3")
    async def test_delete_file_success(self, mock_boto3):
        """Test successful S3 file deletion."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        backend = S3StorageBackend()
        result = await backend.delete_file("test.txt")

        assert result is True
        mock_client.delete_object.assert_called_once()

    @pytest.mark.asyncio
    @patch("modules.documents.storage.boto3")
    async def test_file_exists_true(self, mock_boto3):
        """Test S3 file exists check."""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        backend = S3StorageBackend()
        exists = await backend.file_exists("test.txt")

        assert exists is True
        mock_client.head_object.assert_called_once()

    @pytest.mark.asyncio
    @patch("modules.documents.storage.boto3")
    async def test_list_files(self, mock_boto3):
        """Test listing S3 files."""
        mock_client = MagicMock()
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "file1.txt"},
                {"Key": "file2.txt"},
            ]
        }
        mock_boto3.client.return_value = mock_client

        backend = S3StorageBackend()
        files = await backend.list_files()

        assert len(files) == 2
        assert "file1.txt" in files


@pytest.mark.unit
class TestStorageManager:
    """Test storage manager functionality."""

    def test_init_with_custom_backend(self, mock_storage_backend):
        """Test initialization with custom backend."""
        manager = StorageManager(backend=mock_storage_backend)

        assert manager.backend == mock_storage_backend

    def test_init_with_auto_backend_selection(self, test_settings):
        """Test automatic backend selection."""
        with patch("modules.documents.storage.settings", test_settings):
            manager = StorageManager()

            assert isinstance(manager.backend, LocalStorageBackend)

    @pytest.mark.asyncio
    async def test_compute_file_hash_upload_file(self, sample_upload_file):
        """Test computing hash for UploadFile."""
        manager = StorageManager(backend=MagicMock())
        upload_file = sample_upload_file("test.txt", b"hash this content")

        file_hash = await manager.compute_file_hash(upload_file)

        expected_hash = hashlib.sha256(b"hash this content").hexdigest()
        assert file_hash == expected_hash

    @pytest.mark.asyncio
    async def test_compute_file_hash_regular_file(self):
        """Test computing hash for regular file object."""
        manager = StorageManager(backend=MagicMock())
        file_obj = BytesIO(b"hash this too")

        file_hash = await manager.compute_file_hash(file_obj)

        expected_hash = hashlib.sha256(b"hash this too").hexdigest()
        assert file_hash == expected_hash

    @pytest.mark.asyncio
    async def test_generate_unique_path_with_hash(self):
        """Test generating unique file path with hash."""
        manager = StorageManager(backend=MagicMock())

        path1 = await manager.generate_unique_path("test.txt", use_hash=True)
        path2 = await manager.generate_unique_path("test.txt", use_hash=True)

        # Paths should be different due to unique ID
        assert path1 != path2
        # Both should contain year/month structure
        assert "/documents/" in path1
        assert path1.endswith(".txt")

    @pytest.mark.asyncio
    async def test_generate_unique_path_without_hash(self):
        """Test generating file path without hash."""
        manager = StorageManager(backend=MagicMock())

        path = await manager.generate_unique_path("myfile.pdf", use_hash=False)

        assert path.endswith("myfile.pdf")
        assert "/documents/" in path

    @pytest.mark.asyncio
    async def test_generate_unique_path_custom_folder(self):
        """Test generating path with custom folder."""
        manager = StorageManager(backend=MagicMock())

        path = await manager.generate_unique_path(
            "test.txt",
            folder="invoices",
            use_hash=False
        )

        assert path.startswith("invoices/")

    @pytest.mark.asyncio
    async def test_save_file_success(self, sample_upload_file, mock_storage_backend):
        """Test successful file save with metadata."""
        manager = StorageManager(backend=mock_storage_backend)
        upload_file = sample_upload_file("save_test.txt", b"save this file")

        file_path, file_hash, file_size = await manager.save_file(
            upload_file,
            destination_path="test/save_test.txt",
            content_type="text/plain"
        )

        assert file_path == "test/save_test.txt"
        assert len(file_hash) == 64  # SHA-256 hex length
        assert file_size == len(b"save this file")
        mock_storage_backend.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_file_auto_path(self, sample_upload_file, mock_storage_backend):
        """Test saving file with auto-generated path."""
        manager = StorageManager(backend=mock_storage_backend)
        upload_file = sample_upload_file("auto.txt", b"auto path")

        file_path, file_hash, file_size = await manager.save_file(upload_file)

        assert file_path is not None
        assert "auto.txt" in file_path or ".txt" in file_path

    @pytest.mark.asyncio
    async def test_get_file(self, mock_storage_backend):
        """Test retrieving file."""
        manager = StorageManager(backend=mock_storage_backend)

        content = await manager.get_file("test/file.txt")

        assert content == b"test content"
        mock_storage_backend.download_file.assert_called_once_with("test/file.txt")

    @pytest.mark.asyncio
    async def test_delete_file(self, mock_storage_backend):
        """Test deleting file."""
        manager = StorageManager(backend=mock_storage_backend)

        result = await manager.delete_file("test/file.txt")

        assert result is True
        mock_storage_backend.delete_file.assert_called_once_with("test/file.txt")

    @pytest.mark.asyncio
    async def test_file_exists(self, mock_storage_backend):
        """Test checking file existence."""
        manager = StorageManager(backend=mock_storage_backend)

        exists = await manager.file_exists("test/file.txt")

        assert exists is True
        mock_storage_backend.file_exists.assert_called_once_with("test/file.txt")

    @pytest.mark.asyncio
    async def test_get_file_info(self, mock_storage_backend):
        """Test getting file information."""
        manager = StorageManager(backend=mock_storage_backend)

        info = await manager.get_file_info("test/file.txt")

        assert info["path"] == "test/file.txt"
        assert info["size"] == 1024
        assert info["exists"] is True


@pytest.mark.unit
class TestStorageErrors:
    """Test error handling in storage operations."""

    @pytest.mark.asyncio
    async def test_upload_error_handling(self, temp_storage_path):
        """Test upload error is properly wrapped."""
        backend = LocalStorageBackend(str(temp_storage_path))

        # Try to upload to invalid path
        with pytest.raises(FileUploadException):
            await backend.upload_file(
                None,  # Invalid file object
                "test.txt"
            )

    @pytest.mark.asyncio
    async def test_download_error_handling(self, temp_storage_path):
        """Test download error handling."""
        backend = LocalStorageBackend(str(temp_storage_path))

        # Create a directory instead of file
        (temp_storage_path / "not_a_file").mkdir()

        with pytest.raises(StorageException):
            await backend.download_file("not_a_file")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
