# NEXUS DMS API Documentation

Comprehensive API documentation for the NEXUS Document Management System.

## Table of Contents

- [Authentication](#authentication)
- [Documents API](#documents-api)
- [Folders API](#folders-api)
- [Permissions API](#permissions-api)
- [Search API](#search-api)
- [Versioning API](#versioning-api)
- [Workflow API](#workflow-api)
- [Share Links API](#share-links-api)
- [Error Handling](#error-handling)

## Base URL

```
Production: https://api.nexus-platform.com/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

All API endpoints require authentication using JWT Bearer tokens.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGc...token_here",
  "refresh_token": "eyJhbGc...refresh_token",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using Access Token

Include the access token in the Authorization header:

```http
Authorization: Bearer eyJhbGc...your_token_here
```

### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGc...refresh_token"
}
```

## Documents API

### Upload Document

Upload a new document to the system.

```http
POST /documents/upload
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: [binary file data]
title: "Document Title" (optional)
description: "Document description" (optional)
folder_id: 123 (optional)
tags: "tag1,tag2,tag3" (optional)
```

**Response:**

```json
{
  "id": 1,
  "title": "Document Title",
  "description": "Document description",
  "file_name": "document.pdf",
  "file_path": "documents/2025/01/document_abc123.pdf",
  "file_size": 1024567,
  "mime_type": "application/pdf",
  "file_hash": "abc123...",
  "status": "active",
  "owner_id": 1,
  "folder_id": 123,
  "is_public": false,
  "current_version": 1,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### Get Document

Retrieve document metadata.

```http
GET /documents/{document_id}
Authorization: Bearer {token}
```

**Response:**

```json
{
  "id": 1,
  "title": "Document Title",
  "description": "Document description",
  "file_name": "document.pdf",
  "file_size": 1024567,
  "mime_type": "application/pdf",
  "status": "active",
  "owner": {
    "id": 1,
    "username": "john_doe",
    "full_name": "John Doe"
  },
  "folder": {
    "id": 123,
    "name": "Projects",
    "path": "/Projects"
  },
  "tags": ["important", "project-x"],
  "permissions": ["view", "edit", "admin"],
  "view_count": 42,
  "download_count": 15,
  "current_version": 3,
  "is_locked": false,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-16T14:20:00Z"
}
```

### List Documents

List all documents accessible to the user.

```http
GET /documents?page=1&limit=20&status=active&folder_id=123
Authorization: Bearer {token}
```

**Query Parameters:**

- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (active, archived, deleted)
- `folder_id` (integer): Filter by folder
- `sort_by` (string): Sort field (created_at, title, size)
- `sort_order` (string): Sort direction (asc, desc)

**Response:**

```json
{
  "documents": [...],
  "total_count": 150,
  "page": 1,
  "limit": 20,
  "total_pages": 8
}
```

### Update Document

Update document metadata.

```http
PATCH /documents/{document_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "title": "Updated Title",
  "description": "Updated description",
  "status": "active",
  "tags": ["tag1", "tag2"]
}
```

### Download Document

Download document file.

```http
GET /documents/{document_id}/download
Authorization: Bearer {token}
```

**Response:** Binary file data with appropriate Content-Type header

### Delete Document

Delete a document (soft delete by default).

```http
DELETE /documents/{document_id}
Authorization: Bearer {token}
```

**Response:** `204 No Content`

## Folders API

### Create Folder

```http
POST /folders
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Folder Name",
  "description": "Folder description",
  "parent_id": 1,
  "color": "#FF5733",
  "is_public": false
}
```

### Get Folder

```http
GET /folders/{folder_id}
Authorization: Bearer {token}
```

### List Folders

```http
GET /folders?parent_id=1
Authorization: Bearer {token}
```

### Update Folder

```http
PATCH /folders/{folder_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Delete Folder

```http
DELETE /folders/{folder_id}
Authorization: Bearer {token}
```

## Permissions API

### Grant Permission

Grant access to a document for a specific user.

```http
POST /documents/{document_id}/permissions
Content-Type: application/json
Authorization: Bearer {token}

{
  "user_id": 123,
  "access_level": "edit",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Access Levels:**
- `view`: Read-only access
- `comment`: View and comment
- `edit`: View, comment, and edit
- `admin`: Full control

### List Permissions

```http
GET /documents/{document_id}/permissions
Authorization: Bearer {token}
```

### Revoke Permission

```http
DELETE /documents/{document_id}/permissions/{user_id}
Authorization: Bearer {token}
```

## Search API

### Search Documents

Full-text search with filters.

```http
GET /documents/search?query=contract&mime_type=application/pdf&created_after=2025-01-01
Authorization: Bearer {token}
```

**Query Parameters:**

- `query` (string): Search query
- `mime_type` (string): Filter by MIME type
- `status` (string): Filter by status
- `owner_id` (integer): Filter by owner
- `folder_id` (integer): Filter by folder
- `created_after` (date): Created after date
- `created_before` (date): Created before date
- `min_size` (integer): Minimum file size in bytes
- `max_size` (integer): Maximum file size in bytes
- `tags` (string): Comma-separated tags
- `sort_by` (string): Sort field
- `sort_order` (string): Sort direction
- `page` (integer): Page number
- `limit` (integer): Results per page

**Response:**

```json
{
  "documents": [...],
  "total_count": 42,
  "facets": {
    "mime_type": {
      "application/pdf": 25,
      "text/plain": 10,
      "image/png": 7
    },
    "status": {
      "active": 40,
      "archived": 2
    }
  },
  "query_time": 45.2,
  "page": 1,
  "limit": 20
}
```

### Save Search

```http
POST /search/saved
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Important Contracts",
  "query": {
    "query": "contract",
    "filters": {
      "mime_type": "application/pdf",
      "status": "active"
    }
  },
  "is_public": false
}
```

### Get Saved Searches

```http
GET /search/saved
Authorization: Bearer {token}
```

## Versioning API

### Create Version

Upload a new version of an existing document.

```http
POST /documents/{document_id}/versions
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: [binary file data]
change_summary: "Updated pricing information"
```

### List Versions

```http
GET /documents/{document_id}/versions
Authorization: Bearer {token}
```

**Response:**

```json
{
  "versions": [
    {
      "id": 3,
      "version_number": 3,
      "file_size": 1025000,
      "file_hash": "def456...",
      "change_summary": "Updated pricing",
      "created_by": {
        "id": 1,
        "username": "john_doe"
      },
      "created_at": "2025-01-16T10:00:00Z"
    },
    {
      "id": 2,
      "version_number": 2,
      "file_size": 1024500,
      "file_hash": "abc123...",
      "change_summary": "Fixed typos",
      "created_by": {
        "id": 1,
        "username": "john_doe"
      },
      "created_at": "2025-01-15T14:30:00Z"
    }
  ],
  "total_count": 3,
  "current_version": 3
}
```

### Get Version

```http
GET /documents/{document_id}/versions/{version_number}
Authorization: Bearer {token}
```

### Download Version

```http
GET /documents/{document_id}/versions/{version_number}/download
Authorization: Bearer {token}
```

### Compare Versions

```http
GET /documents/{document_id}/versions/compare?v1=1&v2=2
Authorization: Bearer {token}
```

**Response:**

```json
{
  "version1": {
    "number": 1,
    "size": 1024000,
    "created_at": "2025-01-15T10:00:00Z"
  },
  "version2": {
    "number": 2,
    "size": 1024500,
    "created_at": "2025-01-15T14:30:00Z"
  },
  "diff": ["diff line 1", "diff line 2"],
  "similarity": 0.95,
  "size_change": 500,
  "is_identical": false
}
```

### Rollback to Version

```http
POST /documents/{document_id}/versions/{version_number}/rollback
Authorization: Bearer {token}
```

## Workflow API

### Create Workflow Template

```http
POST /workflows/templates
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Review and Approve",
  "description": "Standard review workflow",
  "steps": [
    {
      "step_number": 1,
      "step_name": "Technical Review",
      "step_type": "review",
      "assignee_id": 123,
      "deadline_hours": 48,
      "is_required": true
    },
    {
      "step_number": 2,
      "step_name": "Manager Approval",
      "step_type": "approval",
      "assignee_id": 456,
      "deadline_hours": 24,
      "is_required": true
    }
  ]
}
```

### Start Workflow

```http
POST /documents/{document_id}/workflows
Content-Type: application/json
Authorization: Bearer {token}

{
  "template_id": 1,
  "priority": "high"
}
```

### Get Workflow Status

```http
GET /workflows/{workflow_id}
Authorization: Bearer {token}
```

### Approve Step

```http
POST /workflows/{workflow_id}/steps/{step_number}/approve
Content-Type: application/json
Authorization: Bearer {token}

{
  "comments": "Looks good, approved"
}
```

### Reject Step

```http
POST /workflows/{workflow_id}/steps/{step_number}/reject
Content-Type: application/json
Authorization: Bearer {token}

{
  "reason": "Needs more work on section 3"
}
```

### Get User Tasks

```http
GET /workflows/tasks/me?status=pending
Authorization: Bearer {token}
```

## Share Links API

### Create Share Link

Create a public or password-protected share link.

```http
POST /documents/{document_id}/share
Content-Type: application/json
Authorization: Bearer {token}

{
  "access_level": "view",
  "password": "secret123",
  "expires_in_days": 7,
  "max_downloads": 10
}
```

**Response:**

```json
{
  "id": 1,
  "token": "abc123xyz789",
  "url": "https://nexus.com/share/abc123xyz789",
  "access_level": "view",
  "expires_at": "2025-01-22T10:00:00Z",
  "max_downloads": 10,
  "download_count": 0,
  "created_at": "2025-01-15T10:00:00Z"
}
```

### Access Share Link

```http
GET /share/{token}?password=secret123
```

### List Share Links

```http
GET /documents/{document_id}/share
Authorization: Bearer {token}
```

### Revoke Share Link

```http
DELETE /share/{token}
Authorization: Bearer {token}
```

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "DOCUMENT_NOT_FOUND",
    "message": "Document with ID 123 not found",
    "details": {
      "document_id": 123
    },
    "timestamp": "2025-01-15T10:00:00Z"
  }
}
```

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `204 No Content`: Successful request with no response body
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `413 Payload Too Large`: File too large
- `415 Unsupported Media Type`: Invalid file type
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Common Error Codes

- `AUTHENTICATION_REQUIRED`: No authentication provided
- `INVALID_TOKEN`: Invalid or expired token
- `PERMISSION_DENIED`: Insufficient permissions
- `DOCUMENT_NOT_FOUND`: Document does not exist
- `FOLDER_NOT_FOUND`: Folder does not exist
- `USER_NOT_FOUND`: User does not exist
- `INVALID_FILE_TYPE`: File type not supported
- `FILE_TOO_LARGE`: File exceeds size limit
- `VALIDATION_ERROR`: Input validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `STORAGE_ERROR`: File storage error
- `VERSION_LIMIT_EXCEEDED`: Too many versions

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Authenticated requests**: 1000 requests per hour
- **Upload endpoints**: 100 requests per hour
- **Search endpoints**: 500 requests per hour

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705323600
```

## Pagination

Endpoints that return lists support pagination:

```http
GET /documents?page=2&limit=50
```

Pagination info is included in the response:

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 50,
    "total_count": 250,
    "total_pages": 5,
    "has_next": true,
    "has_previous": true
  }
}
```

## Webhooks

Subscribe to document events:

```http
POST /webhooks
Content-Type: application/json
Authorization: Bearer {token}

{
  "url": "https://your-app.com/webhook",
  "events": ["document.created", "document.updated", "document.deleted"],
  "secret": "webhook_secret_key"
}
```

### Webhook Events

- `document.created`: New document uploaded
- `document.updated`: Document metadata updated
- `document.deleted`: Document deleted
- `document.version.created`: New version created
- `workflow.started`: Workflow initiated
- `workflow.completed`: Workflow finished
- `permission.granted`: Permission granted
- `permission.revoked`: Permission revoked

## SDK Examples

### Python

```python
import requests

# Authenticate
response = requests.post(
    "https://api.nexus-platform.com/api/v1/auth/login",
    json={"email": "user@example.com", "password": "password"}
)
token = response.json()["access_token"]

# Upload document
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("document.pdf", "rb")}
data = {"title": "My Document"}

response = requests.post(
    "https://api.nexus-platform.com/api/v1/documents/upload",
    headers=headers,
    files=files,
    data=data
)
document = response.json()
```

### JavaScript

```javascript
// Authenticate
const loginResponse = await fetch('https://api.nexus-platform.com/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', password: 'password' })
});
const { access_token } = await loginResponse.json();

// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'My Document');

const uploadResponse = await fetch('https://api.nexus-platform.com/api/v1/documents/upload', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${access_token}` },
  body: formData
});
const document = await uploadResponse.json();
```

## Support

For API support and questions:

- Email: api-support@nexus-platform.com
- Documentation: https://docs.nexus-platform.com
- Status Page: https://status.nexus-platform.com
