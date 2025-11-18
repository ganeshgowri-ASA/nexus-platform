# NEXUS Integration Hub

A production-ready integration platform for connecting NEXUS with 15+ third-party services.

## Features

### Core Features
- **Multi-Auth Support**: OAuth 2.0, API Key, JWT, Basic Auth, and custom authentication
- **Bidirectional Sync**: Two-way data synchronization with intelligent conflict resolution
- **Webhook Management**: Incoming and outgoing webhooks with signature validation and retry logic
- **Field Mapping**: Visual field mapper with transformation rules and AI-assisted suggestions
- **Rate Limiting**: Intelligent rate limiting with exponential backoff and throttling
- **Monitoring**: Real-time metrics, error tracking, and performance analytics
- **Message Queue**: Async processing with event bus and dead letter queue
- **RESTful API**: Complete FastAPI interface for programmatic control
- **UI Dashboard**: Beautiful Streamlit interface for visual management

### Pre-built Integrations (15+)

#### CRM
- **Salesforce**: Full CRM integration with contacts, accounts, and opportunities
- **HubSpot**: Marketing automation and CRM

#### Communication
- **Slack**: Team messaging and notifications
- **Zoom**: Video conferencing integration
- **Twilio**: SMS and voice communication

#### Email
- **Gmail**: Email integration with Google Workspace
- **SendGrid**: Transactional email delivery
- **Mailchimp**: Email marketing campaigns

#### Storage
- **Google Drive**: Cloud file storage
- **Dropbox**: File synchronization

#### Payment
- **Stripe**: Payment processing and subscriptions
- **PayPal**: Payment gateway integration

#### E-commerce
- **Shopify**: E-commerce platform integration

#### Automation
- **Zapier**: Workflow automation

#### Project Management
- **Jira**: Issue tracking and project management

## Installation

```bash
# Clone the repository
git clone https://github.com/nexus-platform/integration-hub.git

# Install dependencies
cd modules/integration_hub
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
alembic upgrade head

# Start Celery worker
celery -A tasks worker --loglevel=info

# Start API server
uvicorn api:router --reload

# Start UI dashboard
streamlit run ui.py
```

## Quick Start

### 1. Register an Integration

```python
from modules.integration_hub import IntegrationRegistry, AuthType

db = get_database_session()
registry = IntegrationRegistry(db)

# Register Salesforce integration
salesforce = registry.register_integration(
    name="Salesforce",
    slug="salesforce",
    provider="salesforce",
    auth_type=AuthType.OAUTH2,
    config={
        "authorization_url": "https://login.salesforce.com/services/oauth2/authorize",
        "token_url": "https://login.salesforce.com/services/oauth2/token",
        "api_base_url": "https://instance.salesforce.com/services/data/v57.0"
    },
    default_scopes=["api", "refresh_token"]
)
```

### 2. Create a Connection

```python
from modules.integration_hub import OAuthFlowManager

oauth_manager = OAuthFlowManager(db, encryption_key)

# Get authorization URL
auth_data = oauth_manager.get_authorization_url(
    integration_id=salesforce.id,
    redirect_uri="https://yourapp.com/oauth/callback"
)

# Redirect user to auth_data['url']
# After callback, exchange code for tokens

connection = await oauth_manager.handle_callback(
    code=authorization_code,
    state=state,
    user_id=current_user_id
)
```

### 3. Create a Sync Job

```python
from modules.integration_hub import SyncJob, SyncDirection

job = SyncJob(
    connection_id=connection.id,
    direction=SyncDirection.INBOUND,
    entity_type="contact",
    sync_config={"endpoint": "/contacts"},
    filters={"email": "*.@example.com"}
)

db.add(job)
db.commit()

# Execute sync
from modules.integration_hub.tasks import run_sync_job
run_sync_job.delay(job.id)
```

### 4. Create a Webhook

```python
from modules.integration_hub import WebhookManager

webhook_manager = WebhookManager(db)

webhook = webhook_manager.create_webhook(
    connection_id=connection.id,
    name="Sync Completed Notification",
    url="https://yourapp.com/webhooks/sync-completed",
    events=["sync.completed", "sync.failed"],
    is_incoming=False,
    secret="your_webhook_secret"
)
```

## API Usage

### List Integrations
```bash
GET /api/v1/integrations/
```

### Create Connection
```bash
POST /api/v1/integrations/connections/
{
  "integration_id": 1,
  "name": "My Salesforce Connection",
  "config": {},
  "scopes": ["api", "refresh_token"]
}
```

### Start Sync Job
```bash
POST /api/v1/integrations/sync-jobs/
{
  "connection_id": 1,
  "direction": "inbound",
  "entity_type": "contact",
  "sync_config": {"endpoint": "/contacts"}
}
```

### Get Metrics
```bash
GET /api/v1/integrations/metrics/dashboard
```

## Architecture

```
modules/integration_hub/
├── __init__.py              # Module initialization
├── models.py                # SQLAlchemy database models
├── schemas.py               # Pydantic validation schemas
├── connectors.py            # Base connector classes
├── oauth.py                 # OAuth 2.0 flow manager
├── webhooks.py              # Webhook management
├── sync.py                  # Data synchronization engine
├── mapping.py               # Field mapping and transformation
├── queue.py                 # Message queue and event bus
├── rate_limiting.py         # Rate limiting and throttling
├── monitoring.py            # Metrics and monitoring
├── registry.py              # Integration registry
├── api.py                   # FastAPI endpoints
├── tasks.py                 # Celery background tasks
├── ui.py                    # Streamlit dashboard
├── integrations/            # Pre-built integrations
│   ├── __init__.py
│   ├── salesforce.py
│   ├── hubspot.py
│   ├── slack.py
│   └── ...
└── tests/                   # Comprehensive test suite
    ├── test_connectors.py
    ├── test_sync.py
    └── ...
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/nexus

# Redis
REDIS_URL=redis://localhost:6379/0

# Encryption
ENCRYPTION_KEY=your-32-byte-encryption-key

# API
API_HOST=0.0.0.0
API_PORT=8000

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### Integration Configuration

Each integration requires specific configuration:

```python
# Salesforce
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret

# Stripe
STRIPE_API_KEY=your_api_key

# Slack
SLACK_CLIENT_ID=your_client_id
SLACK_CLIENT_SECRET=your_client_secret
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=modules/integration_hub --cov-report=html

# Run specific test file
pytest tests/test_connectors.py

# Run with verbose output
pytest -v
```

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "api:router", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/nexus
      - REDIS_URL=redis://redis:6379/0

  celery:
    build: .
    command: celery -A tasks worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@db/nexus
      - REDIS_URL=redis://redis:6379/0

  redis:
    image: redis:7-alpine

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_PASSWORD=pass
```

## Performance Optimization

1. **Enable Redis Caching**: Cache frequently accessed data
2. **Configure Connection Pooling**: Use SQLAlchemy connection pooling
3. **Implement Rate Limiting**: Prevent API quota exhaustion
4. **Use Async Operations**: Leverage async/await for I/O operations
5. **Batch Operations**: Process records in batches for better performance

## Security Best Practices

1. **Encrypt Credentials**: All credentials are encrypted at rest
2. **Validate Webhooks**: Use signature validation for incoming webhooks
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Audit Logging**: Track all integration operations
5. **RBAC**: Role-based access control for connections

## Troubleshooting

### Common Issues

**OAuth Token Expired**
```python
# Tokens are automatically refreshed
# If issues persist, manually trigger refresh:
from modules.integration_hub.oauth import OAuthFlowManager
oauth_manager = OAuthFlowManager(db, encryption_key)
await oauth_manager.refresh_token(connection_id)
```

**Rate Limit Exceeded**
```python
# Check remaining requests:
from modules.integration_hub.rate_limiting import RateLimiter
rate_limiter = RateLimiter(db)
remaining = rate_limiter.get_remaining_requests(connection_id)
```

**Sync Job Failed**
```python
# Check job logs:
logs = db.query(SyncLog).filter(SyncLog.sync_job_id == job_id).all()
for log in logs:
    print(f"{log.level}: {log.message}")
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Copyright © 2024 NEXUS Platform. All rights reserved.

## Support

- Documentation: https://docs.nexus-platform.com/integration-hub
- Issues: https://github.com/nexus-platform/integration-hub/issues
- Email: support@nexus-platform.com
