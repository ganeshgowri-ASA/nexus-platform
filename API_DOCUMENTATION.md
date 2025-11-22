# NEXUS Platform API Documentation

## Overview

The NEXUS Platform API is a production-ready FastAPI REST API providing comprehensive endpoints for enterprise productivity features including user management, document management, email, chat, project management, tasks, file storage, and AI integration.

## Features

### Core Features
- ✅ **FastAPI** with async/await support
- ✅ **Auto-generated OpenAPI documentation** (Swagger UI & ReDoc)
- ✅ **JWT Authentication** with secure token-based auth
- ✅ **Rate Limiting** (60 req/min, 1000 req/hour)
- ✅ **CORS Middleware** for cross-origin requests
- ✅ **Request Validation** using Pydantic models
- ✅ **Response Models** with automatic serialization
- ✅ **Comprehensive Error Handling** with detailed error responses
- ✅ **API Versioning** (/api/v1/)
- ✅ **Pagination Support** for list endpoints
- ✅ **Filtering & Sorting** capabilities
- ✅ **File Upload Endpoints** with size validation
- ✅ **WebSocket Support** (prepared for real-time chat)

### Modules

1. **Authentication** (`/api/v1/auth`)
   - User registration
   - Login (OAuth2 & JSON)
   - Token refresh
   - Password reset
   - Token verification

2. **Users** (`/api/v1/users`)
   - CRUD operations
   - User activation/deactivation
   - Profile management
   - Admin-only endpoints

3. **Documents** (`/api/v1/documents`)
   - Create, read, update, delete documents
   - Version history
   - Search and filtering
   - Public/private documents
   - Categories and tags

4. **Emails** (`/api/v1/emails`)
   - Send emails
   - List inbox/sent emails
   - Draft management
   - Read/unread tracking
   - Email filtering

5. **Chat** (`/api/v1/chat`)
   - Chat rooms (direct, group, channel)
   - Messages with threading
   - Real-time messaging (WebSocket ready)
   - Room participants management
   - Message editing/deletion

6. **Projects** (`/api/v1/projects`)
   - Project CRUD operations
   - Team member management
   - Project statistics
   - Status and priority tracking
   - Budget management

7. **Tasks** (`/api/v1/tasks`)
   - Task CRUD operations
   - Task assignment
   - Subtasks support
   - Comments and collaboration
   - Time tracking
   - Status management

8. **Files** (`/api/v1/files`)
   - File upload with validation
   - File download
   - Metadata management
   - Entity relationships
   - Search and filtering

9. **AI** (`/api/v1/ai`)
   - AI completions
   - Conversation management
   - Image generation
   - Embeddings
   - Usage statistics
   - Multiple model support

## Getting Started

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nexus-platform
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the server**
   ```bash
   # Development mode with auto-reload
   python -m api.main

   # Or using uvicorn directly
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Access Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Authentication

### Obtaining a Token

**Endpoint**: `POST /api/v1/auth/login`

**Request (OAuth2 Form)**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

**Request (JSON)**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "yourpassword"}'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Using the Token

Include the token in the Authorization header for authenticated requests:

```bash
curl -X GET "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login (OAuth2 form) | No |
| POST | `/api/v1/auth/token` | Login (JSON) | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| POST | `/api/v1/auth/logout` | Logout | Yes |
| POST | `/api/v1/auth/reset-password` | Reset password | Yes |
| GET | `/api/v1/auth/me` | Get current user | Yes |
| POST | `/api/v1/auth/verify-token` | Verify token | Yes |

### User Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/users` | List users (paginated) | Yes |
| GET | `/api/v1/users/{id}` | Get user by ID | Yes |
| POST | `/api/v1/users` | Create user (admin) | Yes (Admin) |
| PUT | `/api/v1/users/{id}` | Update user | Yes |
| DELETE | `/api/v1/users/{id}` | Delete user (admin) | Yes (Admin) |
| POST | `/api/v1/users/{id}/activate` | Activate user (admin) | Yes (Admin) |
| POST | `/api/v1/users/{id}/deactivate` | Deactivate user (admin) | Yes (Admin) |

### Document Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/documents` | List documents | Yes |
| GET | `/api/v1/documents/{id}` | Get document | Yes |
| POST | `/api/v1/documents` | Create document | Yes |
| PUT | `/api/v1/documents/{id}` | Update document | Yes |
| DELETE | `/api/v1/documents/{id}` | Delete document | Yes |
| POST | `/api/v1/documents/search` | Search documents | Yes |
| GET | `/api/v1/documents/{id}/versions` | Get version history | Yes |

### Email Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/emails` | List emails | Yes |
| GET | `/api/v1/emails/{id}` | Get email | Yes |
| POST | `/api/v1/emails/send` | Send email | Yes |
| POST | `/api/v1/emails/draft` | Save draft | Yes |
| POST | `/api/v1/emails/{id}/mark-read` | Mark as read | Yes |
| POST | `/api/v1/emails/{id}/mark-unread` | Mark as unread | Yes |
| DELETE | `/api/v1/emails/{id}` | Delete email | Yes |
| GET | `/api/v1/emails/inbox/unread-count` | Get unread count | Yes |

### Chat Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/chat/rooms` | List chat rooms | Yes |
| GET | `/api/v1/chat/rooms/{id}` | Get room | Yes |
| POST | `/api/v1/chat/rooms` | Create room | Yes |
| PUT | `/api/v1/chat/rooms/{id}` | Update room | Yes |
| DELETE | `/api/v1/chat/rooms/{id}` | Delete room | Yes |
| GET | `/api/v1/chat/rooms/{id}/participants` | Get participants | Yes |
| POST | `/api/v1/chat/rooms/{id}/join` | Join room | Yes |
| POST | `/api/v1/chat/rooms/{id}/leave` | Leave room | Yes |
| GET | `/api/v1/chat/rooms/{id}/messages` | List messages | Yes |
| POST | `/api/v1/chat/messages` | Send message | Yes |
| PUT | `/api/v1/chat/messages/{id}` | Edit message | Yes |
| DELETE | `/api/v1/chat/messages/{id}` | Delete message | Yes |
| WS | `/api/v1/chat/ws/{room_id}` | WebSocket connection | Yes |

### Project Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/projects` | List projects | Yes |
| GET | `/api/v1/projects/{id}` | Get project | Yes |
| POST | `/api/v1/projects` | Create project | Yes |
| PUT | `/api/v1/projects/{id}` | Update project | Yes |
| DELETE | `/api/v1/projects/{id}` | Delete project | Yes |
| GET | `/api/v1/projects/{id}/members` | Get team members | Yes |
| POST | `/api/v1/projects/{id}/members/{user_id}` | Add member | Yes |
| DELETE | `/api/v1/projects/{id}/members/{user_id}` | Remove member | Yes |
| GET | `/api/v1/projects/{id}/stats` | Get statistics | Yes |

### Task Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/tasks` | List tasks | Yes |
| GET | `/api/v1/tasks/{id}` | Get task | Yes |
| POST | `/api/v1/tasks` | Create task | Yes |
| PUT | `/api/v1/tasks/{id}` | Update task | Yes |
| DELETE | `/api/v1/tasks/{id}` | Delete task | Yes |
| POST | `/api/v1/tasks/{id}/assign/{user_id}` | Assign task | Yes |
| POST | `/api/v1/tasks/{id}/complete` | Mark complete | Yes |
| GET | `/api/v1/tasks/{id}/subtasks` | Get subtasks | Yes |
| GET | `/api/v1/tasks/{id}/comments` | Get comments | Yes |
| POST | `/api/v1/tasks/{id}/comments` | Add comment | Yes |

### File Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/files` | List files | Yes |
| GET | `/api/v1/files/{id}` | Get file metadata | Yes |
| POST | `/api/v1/files/upload` | Upload file | Yes |
| GET | `/api/v1/files/{id}/download` | Download file | Yes |
| PUT | `/api/v1/files/{id}` | Update metadata | Yes |
| DELETE | `/api/v1/files/{id}` | Delete file | Yes |
| GET | `/api/v1/files/{id}/download-url` | Get download URL | Yes |
| POST | `/api/v1/files/search` | Search files | Yes |

### AI Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/ai/completions` | Generate completion | Yes |
| GET | `/api/v1/ai/models` | List AI models | Yes |
| GET | `/api/v1/ai/conversations` | List conversations | Yes |
| POST | `/api/v1/ai/conversations` | Create conversation | Yes |
| GET | `/api/v1/ai/conversations/{id}` | Get conversation | Yes |
| DELETE | `/api/v1/ai/conversations/{id}` | Delete conversation | Yes |
| POST | `/api/v1/ai/images/generate` | Generate images | Yes |
| POST | `/api/v1/ai/embeddings` | Create embeddings | Yes |
| GET | `/api/v1/ai/usage/stats` | Get usage stats | Yes |

## Pagination

List endpoints support pagination with query parameters:

```bash
GET /api/v1/users?page=2&page_size=50
```

Parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

Response includes pagination metadata:
```json
{
  "items": [...],
  "total": 100,
  "page": 2,
  "page_size": 50,
  "total_pages": 2
}
```

## Filtering & Sorting

Many endpoints support filtering and sorting:

```bash
GET /api/v1/tasks?project_id=1&status=todo&priority=high&sort_by=due_date&sort_order=asc
```

Common parameters:
- `sort_by`: Field name to sort by
- `sort_order`: `asc` or `desc`
- Endpoint-specific filters (see API docs)

## Error Handling

The API returns standardized error responses:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 400,
  "path": "/api/v1/endpoint"
}
```

Common status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Too Many Requests (Rate Limit)
- `500` - Internal Server Error

## Rate Limiting

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1234567890
```

Default limits:
- 60 requests per minute
- 1000 requests per hour

## WebSocket Support

Real-time chat uses WebSocket connections:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws/1?token=YOUR_JWT_TOKEN');

ws.onmessage = (event) => {
  console.log('Message:', event.data);
};

ws.send(JSON.stringify({
  content: 'Hello, world!',
  message_type: 'text'
}));
```

## Development Notes

### Current Status

This API layer is **production-ready** with placeholder implementations. To complete the integration:

1. **Database Integration** - Connect to SQLAlchemy models (future session)
2. **Email Service** - Integrate SMTP or email service provider
3. **File Storage** - Implement local or cloud storage (S3, etc.)
4. **AI Integration** - Connect to OpenAI, Anthropic, or other AI providers
5. **WebSocket** - Complete connection management and broadcasting
6. **Caching** - Integrate Redis for caching and sessions

### TODO Items in Code

Search for `# TODO:` comments in the codebase for specific integration points.

## Security Considerations

1. **Change SECRET_KEY** in production
2. **Use HTTPS** in production
3. **Configure CORS** properly for your domain
4. **Enable rate limiting**
5. **Validate file uploads** (size, type, malware)
6. **Sanitize user inputs**
7. **Use environment variables** for sensitive data
8. **Enable Sentry** or similar for error tracking
9. **Regular security audits**
10. **Keep dependencies updated**

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Gunicorn + Uvicorn

```bash
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Environment Variables for Production

```bash
ENVIRONMENT=production
DEBUG=false
RELOAD=false
SECRET_KEY=<strong-random-secret-key>
ALLOWED_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@host:5432/db
ENABLE_SENTRY=true
SENTRY_DSN=<your-sentry-dsn>
```

## Support

For issues, questions, or contributions, please contact the NEXUS Platform team.

## License

Proprietary - NEXUS Platform
