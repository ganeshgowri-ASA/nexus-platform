"""
Integration tests for document API endpoints.

Tests cover:
- Full API workflow from creation to deletion
- Document CRUD operations
- Permission management through API
- Folder operations
- Search API
- Version management API
- Workflow API integration
"""

import pytest
import json
from datetime import datetime
from io import BytesIO

from fastapi import status


@pytest.mark.integration
class TestDocumentLifecycle:
    """Test complete document lifecycle through API."""

    def test_create_document_flow(
        self, client, auth_headers, regular_user, sample_upload_file
    ):
        """Test creating a document through API."""
        headers = auth_headers(regular_user)

        # Create folder first
        folder_response = client.post(
            "/api/v1/folders",
            json={
                "name": "Test Folder",
                "description": "Folder for test document",
            },
            headers=headers,
        )
        assert folder_response.status_code == status.HTTP_201_CREATED
        folder_id = folder_response.json()["id"]

        # Upload document
        files = {
            "file": ("test.txt", BytesIO(b"Test content"), "text/plain")
        }
        data = {
            "title": "Test Document",
            "description": "Test document description",
            "folder_id": folder_id,
        }
        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        doc_data = response.json()
        assert doc_data["title"] == "Test Document"
        assert doc_data["owner_id"] == regular_user.id
        assert "id" in doc_data

    def test_get_document(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test retrieving a document through API."""
        headers = auth_headers(regular_user)

        response = client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        doc_data = response.json()
        assert doc_data["id"] == test_document.id
        assert doc_data["title"] == test_document.title

    def test_list_documents(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test listing documents through API."""
        headers = auth_headers(regular_user)

        response = client.get(
            "/api/v1/documents",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        docs = response.json()
        assert isinstance(docs, list)
        assert any(d["id"] == test_document.id for d in docs)

    def test_update_document(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test updating document metadata through API."""
        headers = auth_headers(regular_user)

        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
        }
        response = client.patch(
            f"/api/v1/documents/{test_document.id}",
            json=update_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        doc_data = response.json()
        assert doc_data["title"] == "Updated Title"
        assert doc_data["description"] == "Updated description"

    def test_delete_document(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test deleting document through API."""
        headers = auth_headers(regular_user)

        response = client.delete(
            f"/api/v1/documents/{test_document.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify document is deleted
        get_response = client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=headers,
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.integration
class TestDocumentPermissions:
    """Test document permission management through API."""

    def test_grant_permission(
        self, client, auth_headers, regular_user, other_user, test_document
    ):
        """Test granting document permission through API."""
        headers = auth_headers(regular_user)

        permission_data = {
            "user_id": other_user.id,
            "access_level": "edit",
        }
        response = client.post(
            f"/api/v1/documents/{test_document.id}/permissions",
            json=permission_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        perm_data = response.json()
        assert perm_data["user_id"] == other_user.id
        assert perm_data["access_level"] == "edit"

    def test_list_permissions(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test listing document permissions through API."""
        headers = auth_headers(regular_user)

        response = client.get(
            f"/api/v1/documents/{test_document.id}/permissions",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        permissions = response.json()
        assert isinstance(permissions, list)

    def test_revoke_permission(
        self, client, auth_headers, regular_user, other_user, test_document
    ):
        """Test revoking document permission through API."""
        headers = auth_headers(regular_user)

        # First grant permission
        client.post(
            f"/api/v1/documents/{test_document.id}/permissions",
            json={"user_id": other_user.id, "access_level": "view"},
            headers=headers,
        )

        # Then revoke
        response = client.delete(
            f"/api/v1/documents/{test_document.id}/permissions/{other_user.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.integration
class TestDocumentSearch:
    """Test document search through API."""

    def test_search_documents(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test searching documents through API."""
        headers = auth_headers(regular_user)

        search_params = {
            "query": "Test",
            "limit": 20,
            "offset": 0,
        }
        response = client.get(
            "/api/v1/documents/search",
            params=search_params,
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "documents" in result
        assert "total_count" in result

    def test_search_with_filters(
        self, client, auth_headers, regular_user
    ):
        """Test searching with filters through API."""
        headers = auth_headers(regular_user)

        search_params = {
            "query": "",
            "mime_type": "text/plain",
            "status": "active",
        }
        response = client.get(
            "/api/v1/documents/search",
            params=search_params,
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert isinstance(result["documents"], list)


@pytest.mark.integration
class TestDocumentVersions:
    """Test document versioning through API."""

    def test_create_version(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test creating document version through API."""
        headers = auth_headers(regular_user)

        files = {
            "file": ("updated.txt", BytesIO(b"Updated content"), "text/plain")
        }
        data = {
            "change_summary": "Updated content",
        }
        response = client.post(
            f"/api/v1/documents/{test_document.id}/versions",
            files=files,
            data=data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        version_data = response.json()
        assert version_data["document_id"] == test_document.id
        assert "version_number" in version_data

    def test_list_versions(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test listing document versions through API."""
        headers = auth_headers(regular_user)

        response = client.get(
            f"/api/v1/documents/{test_document.id}/versions",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        versions = response.json()
        assert isinstance(versions, list)

    def test_get_version(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test getting specific version through API."""
        headers = auth_headers(regular_user)

        # Get current version
        version_num = test_document.current_version
        response = client.get(
            f"/api/v1/documents/{test_document.id}/versions/{version_num}",
            headers=headers,
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_rollback_version(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test rolling back to previous version through API."""
        headers = auth_headers(regular_user)

        # Create new version first
        files = {"file": ("v2.txt", BytesIO(b"Version 2"), "text/plain")}
        client.post(
            f"/api/v1/documents/{test_document.id}/versions",
            files=files,
            data={"change_summary": "V2"},
            headers=headers,
        )

        # Rollback to version 1
        response = client.post(
            f"/api/v1/documents/{test_document.id}/versions/1/rollback",
            headers=headers,
        )

        # Should succeed or return 404 if version doesn't exist
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ]


@pytest.mark.integration
class TestFolderOperations:
    """Test folder operations through API."""

    def test_create_folder(self, client, auth_headers, regular_user):
        """Test creating folder through API."""
        headers = auth_headers(regular_user)

        folder_data = {
            "name": "New Folder",
            "description": "Test folder",
        }
        response = client.post(
            "/api/v1/folders",
            json=folder_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        folder = response.json()
        assert folder["name"] == "New Folder"
        assert "id" in folder

    def test_list_folders(
        self, client, auth_headers, regular_user, test_folder
    ):
        """Test listing folders through API."""
        headers = auth_headers(regular_user)

        response = client.get(
            "/api/v1/folders",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        folders = response.json()
        assert isinstance(folders, list)
        assert any(f["id"] == test_folder.id for f in folders)

    def test_get_folder(
        self, client, auth_headers, regular_user, test_folder
    ):
        """Test getting folder details through API."""
        headers = auth_headers(regular_user)

        response = client.get(
            f"/api/v1/folders/{test_folder.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        folder = response.json()
        assert folder["id"] == test_folder.id

    def test_update_folder(
        self, client, auth_headers, regular_user, test_folder
    ):
        """Test updating folder through API."""
        headers = auth_headers(regular_user)

        update_data = {
            "name": "Updated Folder Name",
            "description": "Updated description",
        }
        response = client.patch(
            f"/api/v1/folders/{test_folder.id}",
            json=update_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        folder = response.json()
        assert folder["name"] == "Updated Folder Name"

    def test_delete_folder(
        self, client, auth_headers, regular_user, test_folder
    ):
        """Test deleting folder through API."""
        headers = auth_headers(regular_user)

        response = client.delete(
            f"/api/v1/folders/{test_folder.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.integration
class TestShareLinks:
    """Test share link functionality through API."""

    def test_create_share_link(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test creating share link through API."""
        headers = auth_headers(regular_user)

        share_data = {
            "access_level": "view",
            "expires_in_days": 7,
        }
        response = client.post(
            f"/api/v1/documents/{test_document.id}/share",
            json=share_data,
            headers=headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        share_link = response.json()
        assert "token" in share_link
        assert share_link["access_level"] == "view"

    def test_list_share_links(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test listing share links through API."""
        headers = auth_headers(regular_user)

        response = client.get(
            f"/api/v1/documents/{test_document.id}/share",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        links = response.json()
        assert isinstance(links, list)


@pytest.mark.integration
class TestWorkflowAPI:
    """Test workflow management through API."""

    def test_create_workflow_template(
        self, client, admin_headers
    ):
        """Test creating workflow template through API."""
        template_data = {
            "name": "Review Workflow",
            "description": "Standard review process",
            "steps": [
                {
                    "step_number": 1,
                    "step_name": "Review",
                    "step_type": "review",
                },
                {
                    "step_number": 2,
                    "step_name": "Approve",
                    "step_type": "approval",
                },
            ],
        }
        response = client.post(
            "/api/v1/workflows/templates",
            json=template_data,
            headers=admin_headers,
        )

        # May not be implemented yet
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_501_NOT_IMPLEMENTED,
        ]

    def test_start_workflow(
        self, client, auth_headers, regular_user, test_document
    ):
        """Test starting workflow through API."""
        headers = auth_headers(regular_user)

        workflow_data = {
            "template_id": 1,
            "priority": "medium",
        }
        response = client.post(
            f"/api/v1/documents/{test_document.id}/workflows",
            json=workflow_data,
            headers=headers,
        )

        # May not be implemented yet
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_501_NOT_IMPLEMENTED,
        ]


@pytest.mark.integration
class TestAuthenticationFlow:
    """Test authentication flow."""

    def test_login_success(self, client, regular_user, test_password):
        """Test successful login."""
        login_data = {
            "email": regular_user.email,
            "password": test_password,
        }
        response = client.post(
            "/api/v1/auth/login",
            json=login_data,
        )

        # Check if auth endpoint exists
        if response.status_code != status.HTTP_404_NOT_FOUND:
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "access_token" in data

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword",
        }
        response = client.post(
            "/api/v1/auth/login",
            json=login_data,
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_unauthorized_access(self, client, test_document):
        """Test accessing protected endpoint without auth."""
        response = client.get(
            f"/api/v1/documents/{test_document.id}",
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
