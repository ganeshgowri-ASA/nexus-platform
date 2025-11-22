# Knowledge Base API Documentation

## Base URL

```
https://api.nexus.com/api/kb
```

## Authentication

All API requests require an API key in the header:

```
X-API-Key: your-api-key
```

## Endpoints

### Articles

#### Create Article

```http
POST /articles
```

**Request Body:**
```json
{
  "title": "Getting Started Guide",
  "content": "<h1>Introduction</h1><p>Welcome...</p>",
  "author_id": "uuid",
  "summary": "Brief introduction to the platform",
  "category_id": "uuid",
  "tags": ["tutorial", "beginner"],
  "status": "draft",
  "access_level": "public",
  "language": "en"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "title": "Getting Started Guide",
  "slug": "getting-started-guide",
  "content": "...",
  "status": "draft",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### Get Article

```http
GET /articles/{article_id}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "title": "Getting Started Guide",
  "content": "...",
  "author": {
    "id": "uuid",
    "name": "John Doe"
  },
  "category": {...},
  "tags": [...],
  "view_count": 1234,
  "average_rating": 4.7
}
```

#### List Articles

```http
GET /articles?status=published&category_id=uuid&limit=20&offset=0
```

**Query Parameters:**
- `status` - Filter by status (draft, published, archived)
- `category_id` - Filter by category
- `author_id` - Filter by author
- `tags` - Filter by tags (comma-separated)
- `language` - Filter by language
- `search` - Text search query
- `limit` - Results per page (default: 20, max: 100)
- `offset` - Pagination offset

**Response:** `200 OK`
```json
{
  "articles": [...],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_more": true
}
```

### Search

#### Search KB

```http
POST /search
```

**Request Body:**
```json
{
  "query": "how to integrate API",
  "content_types": ["article", "tutorial"],
  "limit": 20
}
```

**Response:** `200 OK`
```json
{
  "results": [
    {
      "id": "uuid",
      "title": "API Integration Guide",
      "snippet": "Learn how to integrate...",
      "content_type": "article",
      "url": "/kb/article/api-integration-guide",
      "relevance_score": 0.95
    }
  ],
  "total": 10,
  "query": "how to integrate API"
}
```

#### Autocomplete

```http
GET /search/autocomplete?query=api
```

**Response:** `200 OK`
```json
{
  "suggestions": [
    "API Integration",
    "API Authentication",
    "API Rate Limits"
  ]
}
```

#### Question Answering

```http
POST /search/question
```

**Request Body:**
```json
{
  "question": "What is the API rate limit?"
}
```

**Response:** `200 OK`
```json
{
  "question": "What is the API rate limit?",
  "answer": "The API rate limit is 1000 requests per hour...",
  "sources": [
    {
      "id": "uuid",
      "title": "API Documentation",
      "url": "/kb/article/api-docs"
    }
  ],
  "confidence": 0.92
}
```

### Chatbot

#### Create Chat Session

```http
POST /chat/sessions
```

**Request Body:**
```json
{
  "user_id": "uuid"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "session_id": "session-uuid",
  "started_at": "2024-01-15T10:30:00Z"
}
```

#### Send Message

```http
POST /chat/sessions/{session_id}/messages
```

**Request Body:**
```json
{
  "message": "How do I reset my password?"
}
```

**Response:** `200 OK`
```json
{
  "message": "To reset your password, go to...",
  "suggested_articles": [
    {
      "id": "uuid",
      "title": "Password Reset Guide"
    }
  ]
}
```

### Analytics

#### Get Content Stats

```http
GET /analytics/content/{content_id}?days=30
```

**Response:** `200 OK`
```json
{
  "views": 5432,
  "unique_users": 2156,
  "average_rating": 4.7,
  "helpful_count": 1234,
  "period_days": 30
}
```

#### Get Popular Content

```http
GET /analytics/popular?days=7&limit=10
```

**Response:** `200 OK`
```json
{
  "content": [
    {
      "content_id": "uuid",
      "title": "Getting Started",
      "views": 5432,
      "type": "article"
    }
  ]
}
```

### Export

#### Export to PDF

```http
GET /export/article/{article_id}/pdf
```

**Response:** `200 OK`
- Content-Type: `application/pdf`
- Binary PDF file

#### Export to DOCX

```http
GET /export/article/{article_id}/docx
```

**Response:** `200 OK`
- Content-Type: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Binary DOCX file

## Rate Limiting

- **Default:** 60 requests per minute
- **Burst:** 100 requests per minute (short duration)

When rate limited, API returns:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request",
  "details": {
    "title": "Title is required"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid API key"
}
```

### 404 Not Found
```json
{
  "error": "Article not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

## Webhooks

Configure webhooks to receive notifications:

```json
{
  "event": "article.published",
  "data": {
    "id": "uuid",
    "title": "New Article",
    "url": "https://kb.nexus.com/article/new-article"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Available Events:**
- `article.published`
- `article.updated`
- `article.deleted`
- `comment.created`
- `rating.added`

## SDKs

### Python

```python
from nexus_kb import KnowledgeBaseClient

client = KnowledgeBaseClient(api_key="your-api-key")

# Search
results = client.search("how to get started")

# Create article
article = client.articles.create(
    title="My Article",
    content="...",
    author_id="uuid"
)
```

### JavaScript

```javascript
import { KnowledgeBaseClient } from '@nexus/kb-client';

const client = new KnowledgeBaseClient({
  apiKey: 'your-api-key'
});

// Search
const results = await client.search('how to get started');

// Create article
const article = await client.articles.create({
  title: 'My Article',
  content: '...'
});
```

## Best Practices

1. **Use pagination** for large result sets
2. **Cache responses** when possible
3. **Handle rate limits** gracefully
4. **Use webhooks** instead of polling
5. **Compress requests** with gzip
6. **Use batch operations** when available
