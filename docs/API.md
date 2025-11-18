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
```

## Authentication

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

**Response:**

```json
{
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
  ]
}
```

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
}
```

**Response:**

```json
{
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
}
```

## Rate Limiting

- **Free Tier**: 100 requests/hour
- **Pro Tier**: 1,000 requests/hour
- **Enterprise**: Custom limits

Rate limit headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    }
  }
}
```

### Common Error Codes

- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## SDK Examples

### Python

```python
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
```

### JavaScript

```javascript
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
