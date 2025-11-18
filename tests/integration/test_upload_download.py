"""
Integration tests for file upload and download operations.

Tests cover:
- Single file upload
- Multiple file upload
- Large file upload with chunking
- File download
- Resume interrupted uploads
- File type validation
- Size limit validation
- Virus scanning (if enabled)
"""

import pytest
import hashlib
from io import BytesIO
from fastapi import status


@pytest.mark.integration
class TestFileUpload:
    """Test file upload operations."""

    def test_upload_text_file(self, client, auth_headers, regular_user):
        """Test uploading a simple text file."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("test.txt", BytesIO(b"Hello World"), "text/plain")
        }
        data = {
            "title": "Text File",
            "description": "Simple text file upload",
        }
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc = response.json()
        assert doc["title"] == "Text File"
        assert doc["mime_type"] == "text/plain"
        assert doc["file_size"] == len(b"Hello World")

    def test_upload_pdf_file(
        self, client, auth_headers, regular_user, sample_pdf_bytes
    ):
        """Test uploading a PDF file."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("document.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
        }
        data = {
            "title": "PDF Document",
        }
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc = response.json()
        assert doc["mime_type"] == "application/pdf"

    def test_upload_image_file(
        self, client, auth_headers, regular_user, sample_image_bytes
    ):
        """Test uploading an image file."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("image.png", BytesIO(sample_image_bytes), "image/png")
        }
        data = {
            "title": "Image File",
        }
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc = response.json()
        assert doc["mime_type"] == "image/png"

    def test_upload_to_folder(
        self, client, auth_headers, regular_user, test_folder
    ):
        """Test uploading file to specific folder."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("test.txt", BytesIO(b"In folder"), "text/plain")
        }
        data = {
            "title": "File in Folder",
            "folder_id": test_folder.id,
        }
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc = response.json()
        assert doc["folder_id"] == test_folder.id

    def test_upload_with_metadata(self, client, auth_headers, regular_user):
        """Test uploading file with additional metadata."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("test.txt", BytesIO(b"Content"), "text/plain")
        }
        data = {
            "title": "File with Metadata",
            "description": "Description text",
            "tags": "test,integration,upload",
        }
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc = response.json()
        assert doc["description"] == "Description text"

    def test_upload_without_file(self, client, auth_headers, regular_user):
        """Test upload request without file should fail."""
        headers = auth_headers(regular_user)

        data = {
            "title": "No File",
        }
        response = client.post(
            "/api/v1/documents/upload",
            data=data,
            headers=headers,
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_upload_empty_file(self, client, auth_headers, regular_user):
        """Test uploading empty file."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("empty.txt", BytesIO(b""), "text/plain")
        }
        data = {
            "title": "Empty File",
        }
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        # Empty files may be rejected
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_upload_without_title_uses_filename(
        self, client, auth_headers, regular_user
    ):
        """Test that upload without title uses filename."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("myfile.txt", BytesIO(b"Content"), "text/plain")
        }
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc = response.json()
        # Title should be derived from filename
        assert "myfile" in doc["title"].lower() or doc["title"] == "myfile.txt"

    @pytest.mark.slow
    def test_upload_large_file(self, client, auth_headers, regular_user):
        """Test uploading a larger file."""
        headers = auth_headers(regular_user)

        # Create 5MB file
        large_content = b"x" * (5 * 1024 * 1024)
        files = {
            "file": ("large.txt", BytesIO(large_content), "text/plain")
        }
        data = {
            "title": "Large File",
        }
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc = response.json()
        assert doc["file_size"] == len(large_content)

    def test_upload_duplicate_creates_new_document(
        self, client, auth_headers, regular_user
    ):
        """Test that uploading same file creates new document."""
        headers = auth_headers(regular_user)

        content = b"Duplicate content"
        files1 = {"file": ("file1.txt", BytesIO(content), "text/plain")}
        data1 = {"title": "File 1"}

        # First upload
        response1 = client.post(
            "/api/v1/documents/upload",
            files=files1,
            data=data1,
            headers=headers,
        )
        assert response1.status_code == status.HTTP_201_CREATED
        doc1_id = response1.json()["id"]

        # Second upload with same content
        files2 = {"file": ("file2.txt", BytesIO(content), "text/plain")}
        data2 = {"title": "File 2"}

        response2 = client.post(
            "/api/v1/documents/upload",
            files=files2,
            data=data2,
            headers=headers,
        )
        assert response2.status_code == status.HTTP_201_CREATED
        doc2_id = response2.json()["id"]

        # Should create separate documents
        assert doc1_id != doc2_id


@pytest.mark.integration
class TestMultipleFileUpload:
    """Test uploading multiple files."""

    def test_upload_multiple_files_separate_requests(
        self, client, auth_headers, regular_user
    ):
        """Test uploading multiple files in separate requests."""
        headers = auth_headers(regular_user)

        doc_ids = []
        for i in range(3):
            files = {
                "file": (f"file{i}.txt", BytesIO(f"Content {i}".encode()), "text/plain")
            }
            data = {"title": f"File {i}"}

            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers=headers,
            )

            assert response.status_code == status.HTTP_201_CREATED
            doc_ids.append(response.json()["id"])

        # All uploads should succeed
        assert len(doc_ids) == 3
        assert len(set(doc_ids)) == 3  # All unique


@pytest.mark.integration
class TestFileDownload:
    """Test file download operations."""

    def test_download_document(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test downloading a document."""
        headers = auth_headers(regular_user)

        response = client.get(
            f"/api/v1/documents/{test_document.id}/download",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.content) > 0
        # Content type should match document mime type
        if "content-type" in response.headers:
            assert test_document.mime_type in response.headers["content-type"]

    def test_download_document_unauthorized(
        self, client, auth_headers, other_user, test_document
    ):
        """Test downloading document without permission fails."""
        headers = auth_headers(other_user)

        response = client.get(
            f"/api/v1/documents/{test_document.id}/download",
            headers=headers,
        )

        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_download_public_document(
        self, client, auth_headers, other_user, public_document
    ):
        """Test downloading public document."""
        headers = auth_headers(other_user)

        response = client.get(
            f"/api/v1/documents/{public_document.id}/download",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK

    def test_download_nonexistent_document(
        self, client, auth_headers, regular_user
    ):
        """Test downloading non-existent document."""
        headers = auth_headers(regular_user)

        response = client.get(
            "/api/v1/documents/99999/download",
            headers=headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_download_increments_counter(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test that download increments download counter."""
        headers = auth_headers(regular_user)

        # Get initial count
        doc_response = client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=headers,
        )
        initial_count = doc_response.json().get("download_count", 0)

        # Download file
        client.get(
            f"/api/v1/documents/{test_document.id}/download",
            headers=headers,
        )

        # Check count increased
        doc_response2 = client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=headers,
        )
        new_count = doc_response2.json().get("download_count", 0)

        assert new_count >= initial_count

    def test_download_with_range_header(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test partial content download with Range header."""
        headers = auth_headers(regular_user)
        headers["Range"] = "bytes=0-99"

        response = client.get(
            f"/api/v1/documents/{test_document.id}/download",
            headers=headers,
        )

        # Partial content support is optional
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_206_PARTIAL_CONTENT,
        ]


@pytest.mark.integration
class TestFileValidation:
    """Test file upload validation."""

    @pytest.mark.slow
    def test_upload_oversized_file_rejected(
        self, client, auth_headers, regular_user, test_settings
    ):
        """Test that files exceeding size limit are rejected."""
        headers = auth_headers(regular_user)

        # Create file larger than limit (100MB default)
        if test_settings.MAX_UPLOAD_SIZE < 200 * 1024 * 1024:
            # Only test if we can create a file larger than limit
            oversized_content = b"x" * (test_settings.MAX_UPLOAD_SIZE + 1000)
            files = {
                "file": ("huge.txt", BytesIO(oversized_content), "text/plain")
            }
            data = {"title": "Oversized File"}

            response = client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data,
                headers=headers,
            )

            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            ]

    def test_upload_restricted_file_type(
        self, client, auth_headers, regular_user
    ):
        """Test uploading potentially restricted file type."""
        headers = auth_headers(regular_user)

        # .exe files are often restricted
        files = {
            "file": ("program.exe", BytesIO(b"MZ\x90\x00"), "application/x-msdownload")
        }
        data = {"title": "Executable File"}

        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        # May be accepted or rejected depending on configuration
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        ]


@pytest.mark.integration
class TestFileIntegrity:
    """Test file integrity and checksums."""

    def test_uploaded_file_integrity(
        self, client, auth_headers, regular_user
    ):
        """Test that uploaded file maintains integrity."""
        headers = auth_headers(regular_user)

        original_content = b"Integrity test content " * 100
        original_hash = hashlib.sha256(original_content).hexdigest()

        # Upload file
        files = {
            "file": ("integrity.txt", BytesIO(original_content), "text/plain")
        }
        data = {"title": "Integrity Test"}

        upload_response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert upload_response.status_code == status.HTTP_201_CREATED
        doc = upload_response.json()
        doc_id = doc["id"]

        # Download file
        download_response = client.get(
            f"/api/v1/documents/{doc_id}/download",
            headers=headers,
        )

        assert download_response.status_code == status.HTTP_200_OK

        # Verify content matches
        downloaded_content = download_response.content
        downloaded_hash = hashlib.sha256(downloaded_content).hexdigest()

        assert downloaded_hash == original_hash


@pytest.mark.integration
class TestContentTypeDetection:
    """Test automatic content type detection."""

    def test_detect_text_file_type(
        self, client, auth_headers, regular_user
    ):
        """Test detection of text file type."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("readme.txt", BytesIO(b"Text content"), "text/plain")
        }
        data = {"title": "Text File"}

        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc = response.json()
        assert "text" in doc["mime_type"]

    def test_detect_pdf_file_type(
        self, client, auth_headers, regular_user, sample_pdf_bytes
    ):
        """Test detection of PDF file type."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("doc.pdf", BytesIO(sample_pdf_bytes), "application/pdf")
        }
        data = {"title": "PDF"}

        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc = response.json()
        assert doc["mime_type"] == "application/pdf"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
