<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
# NEXUS Log Search API Documentation

## Overview

The NEXUS Log Search API provides RESTful endpoints for searching, filtering, and analyzing application logs. It's built with FastAPI and provides comprehensive log querying capabilities.
=======
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
=======
# NEXUS Scheduler API Documentation
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U

## Base URL

```
<<<<<<< HEAD
<<<<<<< HEAD
http://localhost:8000
=======
Production: https://api.nexus-platform.com/api/v1
Development: http://localhost:8000/api/v1
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
=======
# NEXUS Platform API Documentation

## Overview

The NEXUS Platform provides a comprehensive API for all 24 integrated modules. This document describes the API architecture, endpoints, authentication, and usage patterns.

## API Architecture

### Technology Stack

- **Framework**: FastAPI (future integration)
- **Authentication**: JWT-based authentication
- **Data Format**: JSON
- **API Style**: RESTful
- **Documentation**: OpenAPI 3.0 (Swagger)

### Base URL

```
Development: http://localhost:8501
Staging: https://staging-api.nexus-platform.com
Production: https://api.nexus-platform.com
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
=======
http://localhost:8000/api/v1
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
```

## Authentication

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms (API keys, OAuth, etc.).

## Endpoints

### 1. Root Endpoint

Get API information.

**Endpoint:** `GET /`
=======
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
=======
### JWT Token Authentication

All API requests require a valid JWT token in the Authorization header:

```http
Authorization: Bearer <your_jwt_token>
```

### Obtaining a Token

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "your_password"
}
```
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW

**Response:**

```json
{
<<<<<<< HEAD
<<<<<<< HEAD
  "service": "NEXUS Log Search API",
  "version": "1.0.0",
  "status": "running"
}
```

### 2. Health Check

Check API health status.

**Endpoint:** `GET /health`
=======
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai

**Response:**

```json
{
<<<<<<< HEAD
  "status": "healthy"
}
```

### 3. Search Logs (GET)

Search logs using query parameters.

**Endpoint:** `GET /search`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start_time | datetime | No | - | Start of time range (ISO 8601) |
| end_time | datetime | No | - | End of time range (ISO 8601) |
| level | string | No | - | Log level filter |
| logger_name | string | No | - | Logger name filter |
| request_id | string | No | - | Request ID filter |
| user_id | string | No | - | User ID filter |
| search_text | string | No | - | Text search in messages |
| error_type | string | No | - | Error type filter |
| limit | int | No | 100 | Max results (1-1000) |
| offset | int | No | 0 | Pagination offset |
| sort_order | string | No | desc | Sort order (asc/desc) |

**Examples:**

```bash
# Get all logs
curl "http://localhost:8000/search"

# Get errors only
curl "http://localhost:8000/search?level=ERROR"

# Search for specific user
curl "http://localhost:8000/search?user_id=user123&limit=50"

# Time range search
curl "http://localhost:8000/search?start_time=2025-01-18T00:00:00&end_time=2025-01-18T23:59:59"

# Combined filters
curl "http://localhost:8000/search?level=ERROR&search_text=database&limit=20"
```
=======
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai

**Response:**

```json
{
<<<<<<< HEAD
  "logs": [
    {
      "timestamp": "2025-01-18T10:30:45.123456",
      "level": "ERROR",
      "logger_name": "nexus.database",
      "message": "database_connection_failed",
      "app": "nexus",
      "request_id": "req-123",
      "user_id": "user456",
      "error_type": "ConnectionError",
      "error_message": "Failed to connect to database",
      "context": {
        "host": "db.example.com",
        "port": 5432
      }
    }
  ],
  "total_count": 1,
  "offset": 0,
  "limit": 100,
  "has_more": false
}
```

### 4. Search Logs (POST)

Search logs using JSON request body.

**Endpoint:** `POST /search`

**Request Body:**

```json
{
  "start_time": "2025-01-18T00:00:00",
  "end_time": "2025-01-18T23:59:59",
  "level": "ERROR",
  "logger_name": "nexus.api",
  "request_id": "req-123",
  "user_id": "user456",
  "search_text": "failed",
  "error_type": "ValueError",
  "limit": 50,
  "offset": 0,
  "sort_order": "desc"
}
```

All fields are optional.

**Examples:**

```bash
# Search for errors
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{"level": "ERROR", "limit": 100}'

# Search with multiple filters
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{
       "level": "ERROR",
       "search_text": "database",
       "user_id": "user123",
       "limit": 50
     }'

# Time range search
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{
       "start_time": "2025-01-18T00:00:00",
       "end_time": "2025-01-18T12:00:00",
       "limit": 100
     }'
```

**Response:** Same as GET /search

### 5. Log Statistics

Get aggregated log statistics.

**Endpoint:** `GET /stats`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| hours | int | No | 24 | Hours to analyze (1-168) |

**Examples:**

```bash
# Get stats for last 24 hours
curl "http://localhost:8000/stats"

# Get stats for last 7 days
curl "http://localhost:8000/stats?hours=168"

# Get stats for last hour
curl "http://localhost:8000/stats?hours=1"
=======
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
```

**Response:**

```json
{
<<<<<<< HEAD
  "total_logs": 1523,
  "error_count": 45,
  "warning_count": 123,
  "info_count": 1345,
  "debug_count": 10,
  "critical_count": 0,
  "time_range": {
    "start": "2025-01-17T10:00:00",
    "end": "2025-01-18T10:00:00"
  },
  "top_errors": [
    {
      "error_type": "ValueError",
      "count": 15
    },
    {
      "error_type": "ConnectionError",
      "count": 8
    },
    {
      "error_type": "TimeoutError",
      "count": 5
    }
  ],
  "logs_per_hour": [
    {
      "hour": "2025-01-17 10:00",
      "count": 45
    },
    {
      "hour": "2025-01-17 11:00",
      "count": 52
=======
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
    }
=======
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Core API Endpoints

### Health Check

```http
GET /api/v1/health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### User Management

#### Get Current User

```http
GET /api/v1/users/me
Authorization: Bearer <token>
```

**Response:**

```json
{
  "id": "user_123",
  "username": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Update User Profile

```http
PUT /api/v1/users/me
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "John Doe Updated",
  "preferences": {
    "theme": "dark",
    "language": "en"
  }
}
```

## Module-Specific APIs

### Word Processor API

#### Create Document

```http
POST /api/v1/documents
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My Document",
  "content": "Document content here...",
  "tags": ["work", "important"]
}
```

#### Get Document

```http
GET /api/v1/documents/{document_id}
Authorization: Bearer <token>
```

#### Update Document

```http
PUT /api/v1/documents/{document_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Updated Title",
  "content": "Updated content..."
}
```

#### Delete Document

```http
DELETE /api/v1/documents/{document_id}
Authorization: Bearer <token>
```

### Excel Sheets API

#### Create Spreadsheet

```http
POST /api/v1/spreadsheets
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Sales Data",
  "data": [
    ["Name", "Sales", "Region"],
    ["John", 1000, "East"],
    ["Jane", 1500, "West"]
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
  ]
}
```

<<<<<<< HEAD
<<<<<<< HEAD
## Data Models

### LogEntry

```python
{
  "timestamp": "datetime",           # Log timestamp (ISO 8601)
  "level": "string",                 # Log level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
  "logger_name": "string",           # Logger name
  "message": "string",               # Log message
  "app": "string",                   # Application name (default: "nexus")
  "request_id": "string | null",     # Request ID for correlation
  "user_id": "string | null",        # User identifier
  "error_type": "string | null",     # Error type if applicable
  "error_message": "string | null",  # Error message
  "traceback": "string | null",      # Stack trace for errors
  "context": "object | null",        # Additional context data
  "extra": "object | null"           # Extra fields
}
```

### LogSearchQuery

```python
{
  "start_time": "datetime | null",   # Start of time range
  "end_time": "datetime | null",     # End of time range
  "level": "string | null",          # Log level filter
  "logger_name": "string | null",    # Logger name filter
  "request_id": "string | null",     # Request ID filter
  "user_id": "string | null",        # User ID filter
  "search_text": "string | null",    # Text search
  "error_type": "string | null",     # Error type filter
  "limit": "int",                    # Max results (1-1000, default: 100)
  "offset": "int",                   # Pagination offset (default: 0)
  "sort_order": "string"             # Sort order (asc/desc, default: desc)
}
```

### LogSearchResponse

```python
{
  "logs": [LogEntry],                # Array of log entries
  "total_count": "int",              # Total matching logs
  "offset": "int",                   # Current offset
  "limit": "int",                    # Results per page
  "has_more": "bool"                 # More results available
}
```

### LogStats

```python
{
  "total_logs": "int",               # Total log count
  "error_count": "int",              # ERROR level count
  "warning_count": "int",            # WARNING level count
  "info_count": "int",               # INFO level count
  "debug_count": "int",              # DEBUG level count
  "critical_count": "int",           # CRITICAL level count
  "time_range": {
    "start": "datetime",             # Analysis start time
    "end": "datetime"                # Analysis end time
  },
  "top_errors": [
    {
      "error_type": "string",        # Error type
      "count": "int"                 # Occurrence count
    }
  ],
  "logs_per_hour": [
    {
      "hour": "string",              # Hour timestamp
      "count": "int"                 # Log count for hour
    }
  ]
=======
Currently, the API does not require authentication. This should be added in production.

## Endpoints

### Jobs

#### Create Job

Create a new scheduled job.

**Endpoint:** `POST /jobs/`

**Request Body:**
```json
{
  "name": "Daily Report",
  "description": "Generate daily analytics report",
  "job_type": "cron",
  "cron_expression": "0 9 * * 1-5",
  "interval_seconds": null,
  "scheduled_time": null,
  "calendar_rule": null,
  "task_name": "tasks.generate_report",
  "task_args": [],
  "task_kwargs": {"format": "pdf"},
  "timezone": "US/Eastern",
  "is_active": true,
  "max_retries": 3,
  "retry_delay": 60,
  "retry_backoff": true,
  "priority": 5,
  "tags": ["report", "analytics"],
  "metadata": {},
  "created_by": "admin"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "Daily Report",
  "job_type": "cron",
  "status": "pending",
  "is_active": true,
  "next_run_at": "2025-01-20T14:00:00Z",
  ...
}
```

#### List Jobs

Get all scheduled jobs with optional filtering.

**Endpoint:** `GET /jobs/`

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100, max: 1000)
- `is_active` (bool): Filter by active status
- `job_type` (string): Filter by job type (cron, interval, date, calendar)
- `tags` (string): Comma-separated tags

**Example:**
```
GET /jobs/?is_active=true&job_type=cron&limit=50
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "name": "Daily Report",
    ...
  }
]
```

#### Get Job

Get a specific job by ID.

**Endpoint:** `GET /jobs/{job_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Daily Report",
  ...
}
```

#### Update Job

Update an existing job.

**Endpoint:** `PUT /jobs/{job_id}`

**Request Body:**
```json
{
  "name": "Updated Job Name",
  "is_active": false,
  "priority": 7
}
```

**Response:** `200 OK`

#### Delete Job

Delete a job.

**Endpoint:** `DELETE /jobs/{job_id}`

**Response:** `204 No Content`

#### Execute Job

Manually execute a job immediately.

**Endpoint:** `POST /jobs/{job_id}/execute`

**Request Body (Optional):**
```json
{
  "task_args": [1, 2],
  "task_kwargs": {"override": true}
}
```

**Response:** `200 OK`
```json
{
  "message": "Job execution started",
  "task_id": "abc123-def456-ghi789"
}
```

#### Pause Job

Pause a job.

**Endpoint:** `POST /jobs/{job_id}/pause`

**Response:** `200 OK`
```json
{
  "message": "Job paused"
}
```

#### Resume Job

Resume a paused job.

**Endpoint:** `POST /jobs/{job_id}/resume`

**Response:** `200 OK`
```json
{
  "message": "Job resumed"
}
```

#### Get Job Executions

Get execution history for a specific job.

**Endpoint:** `GET /jobs/{job_id}/executions`

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 50, max: 500)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "job_id": 1,
    "status": "completed",
    "started_at": "2025-01-20T14:00:00Z",
    "completed_at": "2025-01-20T14:05:30Z",
    "duration_seconds": 330,
    ...
  }
]
```

### Statistics

#### Get Overview Stats

Get overall scheduler statistics.

**Endpoint:** `GET /jobs/stats/overview`

**Response:** `200 OK`
```json
{
  "total_jobs": 15,
  "active_jobs": 12,
  "paused_jobs": 3,
  "total_executions": 1543,
  "successful_executions": 1489,
  "failed_executions": 54,
  "running_executions": 2,
  "average_duration": 125.5,
  "last_24h_executions": 287
}
```

### Cron

#### Validate Cron Expression

Validate a cron expression and get next run times.

**Endpoint:** `POST /cron/validate`

**Request Body:**
```json
{
  "expression": "*/5 * * * *",
  "timezone": "UTC"
}
```

**Response:** `200 OK`
```json
{
  "is_valid": true,
  "description": "Every 5 minutes",
  "next_runs": [
    "2025-01-20T14:05:00Z",
    "2025-01-20T14:10:00Z",
    "2025-01-20T14:15:00Z",
    "2025-01-20T14:20:00Z",
    "2025-01-20T14:25:00Z"
  ],
  "error": null
}
```

#### Get Cron Presets

Get common cron expression presets.

**Endpoint:** `GET /cron/presets`

**Response:** `200 OK`
```json
{
  "every_minute": {
    "expression": "* * * * *",
    "description": "Every minute"
  },
  "hourly": {
    "expression": "0 * * * *",
    "description": "Every hour"
  },
  "daily_midnight": {
    "expression": "0 0 * * *",
    "description": "Daily at midnight"
  },
  ...
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
}
```

## Error Responses

<<<<<<< HEAD
All endpoints may return these error responses:

### 400 Bad Request

Invalid request parameters.

```json
{
  "detail": "Invalid parameter value"
=======
### 400 Bad Request
```json
{
  "detail": "Invalid request data"
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
}
```

### 404 Not Found
<<<<<<< HEAD

Endpoint not found.

```json
{
  "detail": "Not Found"
}
```

### 422 Validation Error

Request validation failed.

=======
```json
{
  "detail": "Job not found"
}
```

### 422 Unprocessable Entity
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
```json
{
  "detail": [
    {
<<<<<<< HEAD
      "loc": ["query", "limit"],
      "msg": "ensure this value is less than or equal to 1000",
      "type": "value_error"
=======
      "loc": ["body", "cron_expression"],
      "msg": "field required",
      "type": "value_error.missing"
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
    }
  ]
}
```

### 500 Internal Server Error
<<<<<<< HEAD

Server error occurred.

```json
{
  "detail": "Internal server error message"
}
=======
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
=======
#### Get Spreadsheet

```http
GET /api/v1/spreadsheets/{spreadsheet_id}
Authorization: Bearer <token>
```

### AI Assistant API

#### Generate Content

```http
POST /api/v1/ai/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "prompt": "Write a professional email about...",
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 1024
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
}
```

**Response:**

```json
{
<<<<<<< HEAD
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
=======
  "id": "gen_123",
  "content": "Generated content here...",
  "model": "claude-3-5-sonnet-20241022",
  "usage": {
    "input_tokens": 50,
    "output_tokens": 200
  }
}
```

#### Chat Completion

```http
POST /api/v1/ai/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "How can I improve this document?"}
  ],
  "context": {
    "document_id": "doc_123"
  }
}
```

### Analytics API

#### Get Dashboard Data

```http
GET /api/v1/analytics/dashboard
Authorization: Bearer <token>
```

**Response:**

```json
{
  "total_documents": 150,
  "total_projects": 25,
  "active_users": 42,
  "recent_activity": [...]
}
```

#### Generate Report

```http
POST /api/v1/analytics/reports
Authorization: Bearer <token>
Content-Type: application/json

{
  "report_type": "usage",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "format": "pdf"
}
```

### Project Management API

#### Create Project

```http
POST /api/v1/projects
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "New Project",
  "description": "Project description",
  "team_members": ["user_123", "user_456"],
  "deadline": "2024-12-31"
}
```

#### Get Project Tasks

```http
GET /api/v1/projects/{project_id}/tasks
Authorization: Bearer <token>
```

#### Create Task

```http
POST /api/v1/projects/{project_id}/tasks
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Task title",
  "description": "Task description",
  "assignee": "user_123",
  "priority": "high",
  "due_date": "2024-02-15"
}
```

## Webhooks

### Subscribe to Events

```http
POST /api/v1/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["document.created", "task.completed"],
  "secret": "webhook_secret_key"
}
```

### Webhook Event Format

```json
{
  "event": "document.created",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "document_id": "doc_123",
    "user_id": "user_123"
  },
  "signature": "sha256=..."
=======
```json
{
  "detail": "Internal server error"
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
}
```

## Rate Limiting

<<<<<<< HEAD
- **Free Tier**: 100 requests/hour
- **Pro Tier**: 1,000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
```

## Error Handling

### Error Response Format

<<<<<<< HEAD
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
=======
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
  }
}
```

<<<<<<< HEAD
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
```

## Pagination

<<<<<<< HEAD
Use `limit` and `offset` for pagination:

```bash
# First page (items 0-99)
curl "http://localhost:8000/search?limit=100&offset=0"

# Second page (items 100-199)
curl "http://localhost:8000/search?limit=100&offset=100"

# Third page (items 200-299)
curl "http://localhost:8000/search?limit=100&offset=200"
```

Check `has_more` in the response to determine if more results are available.

## Rate Limiting

Currently, no rate limiting is implemented. In production, implement appropriate rate limiting based on your requirements.

## CORS

Configure CORS for cross-origin requests if needed:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Client Examples
=======
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
=======
### Common Error Codes

- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## SDK Examples
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW

### Python

```python
<<<<<<< HEAD
import requests

<<<<<<< HEAD
# Search for errors
response = requests.post(
    "http://localhost:8000/search",
    json={
        "level": "ERROR",
        "limit": 50,
    }
)
logs = response.json()

# Get statistics
response = requests.get("http://localhost:8000/stats?hours=24")
stats = response.json()
print(f"Total errors: {stats['error_count']}")
=======
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
=======
from nexus_sdk import NexusClient

client = NexusClient(api_key="your_api_key")

# Create a document
document = client.documents.create(
    title="My Document",
    content="Document content"
)

# Use AI assistant
response = client.ai.generate(
    prompt="Write a summary of...",
    max_tokens=500
)
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
```

### JavaScript

```javascript
<<<<<<< HEAD
<<<<<<< HEAD
// Search for errors
fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    level: 'ERROR',
    limit: 50,
  }),
})
  .then(response => response.json())
  .then(data => console.log(data.logs));

// Get statistics
fetch('http://localhost:8000/stats?hours=24')
  .then(response => response.json())
  .then(stats => console.log(`Total errors: ${stats.error_count}`));
```

### cURL

```bash
# Search for errors
curl -X POST http://localhost:8000/search \
     -H "Content-Type: application/json" \
     -d '{"level": "ERROR", "limit": 50}'

# Get statistics
curl "http://localhost:8000/stats?hours=24"
```

## Performance Considerations

- The API reads log files directly for simplicity
- For large log files (>100MB), consider using a database backend
- Implement caching for frequently accessed queries
- Use appropriate indexes if using database storage
- Consider log archival for old logs

## Future Enhancements

- [ ] Database backend for better performance
- [ ] Real-time log streaming via WebSocket
- [ ] Advanced filtering with regex support
- [ ] Log aggregation and grouping
- [ ] Export logs to various formats (CSV, Excel)
- [ ] Authentication and authorization
- [ ] Rate limiting
- [ ] Metrics and monitoring integration
=======
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
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
=======
import { NexusClient } from '@nexus/sdk';

const client = new NexusClient({ apiKey: 'your_api_key' });

// Create a document
const document = await client.documents.create({
  title: 'My Document',
  content: 'Document content'
});

// Use AI assistant
const response = await client.ai.generate({
  prompt: 'Write a summary of...',
  maxTokens: 500
});
```

## Best Practices

1. **Always use HTTPS** in production
2. **Store API keys securely** in environment variables
3. **Implement exponential backoff** for retries
4. **Cache responses** when appropriate
5. **Use webhooks** instead of polling
6. **Validate input** on client side
7. **Handle rate limits** gracefully

## Changelog

### Version 1.0.0 (2024-01-01)
- Initial API release
- Core authentication endpoints
- Basic CRUD operations for all modules
- AI assistant integration
- Webhook support

## Support

For API support:
- Email: api-support@nexus-platform.com
- Documentation: https://docs.nexus-platform.com
- Status Page: https://status.nexus-platform.com
>>>>>>> origin/claude/nexus-platform-setup-01GgK8vgMUpRwMXvUmBp8eNW
=======
Currently, there are no rate limits. This should be implemented in production.

## Pagination

List endpoints support pagination via `skip` and `limit` query parameters.

**Example:**
```
GET /jobs/?skip=20&limit=10
```

## Filtering

Jobs can be filtered by:
- `is_active`: Boolean
- `job_type`: String (cron, interval, date, calendar)
- `tags`: Comma-separated string

**Example:**
```
GET /jobs/?is_active=true&job_type=cron&tags=report,analytics
```

## Sorting

Jobs are sorted by `created_at` in descending order (newest first).

## WebSocket Support

WebSocket support for real-time updates is planned for future releases.
>>>>>>> origin/claude/build-scheduler-module-01SggaZRDvso4oULkWNKGR2U
