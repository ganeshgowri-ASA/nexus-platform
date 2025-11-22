# NEXUS Webhooks Module

A comprehensive webhook management system for the NEXUS platform with event subscriptions, automatic delivery, retry logic, and security features.

## Features

- **Webhook Management**: Create, update, delete, and manage webhook endpoints
- **Event Subscriptions**: Subscribe webhooks to specific event types
- **Automatic Delivery**: Asynchronous webhook payload delivery using Celery
- **Retry Logic**: Exponential backoff retry mechanism for failed deliveries
- **Security**: HMAC-SHA256 signature verification for webhook authenticity
- **Delivery Logs**: Comprehensive logging and monitoring of all webhook deliveries
- **Streamlit UI**: User-friendly web interface for managing webhooks
- **REST API**: Full-featured FastAPI-based REST API

## Architecture

```
modules/webhooks/
├── api/                    # FastAPI endpoints
│   ├── webhooks.py        # Webhook CRUD operations
│   ├── events.py          # Event subscription & triggering
│   ├── deliveries.py      # Delivery monitoring
│   └── main.py            # FastAPI application
├── models/                # SQLAlchemy database models
│   ├── webhook.py         # Webhook model
│   ├── webhook_event.py   # Event subscription model
│   └── webhook_delivery.py # Delivery log model
├── services/              # Business logic
│   ├── webhook_service.py
│   ├── event_service.py
│   ├── delivery_service.py
│   └── signature_service.py
├── tasks/                 # Celery async tasks
│   ├── celery_app.py
│   └── delivery_tasks.py
├── ui/                    # Streamlit UI
│   └── app.py
└── config.py             # Configuration

```

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Relational database for storing webhooks and logs
- **Redis**: In-memory data store for Celery message broker
- **Celery**: Distributed task queue for async webhook delivery
- **SQLAlchemy**: SQL toolkit and ORM
- **Streamlit**: Web UI framework
- **HTTPX**: Modern HTTP client for sending webhooks
- **Pydantic**: Data validation using Python type annotations

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Using Docker (Recommended)

1. Clone the repository:
```bash
cd modules/webhooks
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Start all services:
```bash
make start
```

This will start:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- FastAPI API server (port 8000)
- Celery worker (background)
- Celery beat scheduler (background)
- Streamlit UI (port 8501)

### Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Initialize database:
```bash
make db-init
```

4. Start services separately:

```bash
# Terminal 1: API server
uvicorn modules.webhooks.api.main:app --reload

# Terminal 2: Celery worker
celery -A modules.webhooks.tasks.celery_app worker --loglevel=info

# Terminal 3: Celery beat
celery -A modules.webhooks.tasks.celery_app beat --loglevel=info

# Terminal 4: Streamlit UI
streamlit run modules/webhooks/ui/app.py
```

## Usage

### API Endpoints

Access the interactive API documentation at `http://localhost:8000/docs`

#### Webhooks

- `POST /api/v1/webhooks/` - Create a new webhook
- `GET /api/v1/webhooks/` - List all webhooks
- `GET /api/v1/webhooks/{id}` - Get webhook details
- `PATCH /api/v1/webhooks/{id}` - Update webhook
- `DELETE /api/v1/webhooks/{id}` - Delete webhook
- `POST /api/v1/webhooks/{id}/regenerate-secret` - Regenerate secret
- `GET /api/v1/webhooks/{id}/stats` - Get webhook statistics

#### Events

- `GET /api/v1/events/available` - List available event types
- `POST /api/v1/events/trigger` - Trigger an event
- `GET /api/v1/webhooks/{id}/events` - List event subscriptions
- `POST /api/v1/webhooks/{id}/events` - Add event subscription
- `DELETE /api/v1/webhooks/{id}/events/{event_type}` - Remove subscription

#### Deliveries

- `GET /api/v1/deliveries/` - List all deliveries
- `GET /api/v1/deliveries/{id}` - Get delivery details
- `POST /api/v1/deliveries/{id}/retry` - Retry failed delivery

### Streamlit UI

Access the web interface at `http://localhost:8501`

Features:
- Dashboard with statistics
- Create and manage webhooks
- Configure event subscriptions
- Monitor deliveries in real-time
- Manually trigger events for testing

### Example: Creating a Webhook

```python
import requests

# Create webhook
response = requests.post('http://localhost:8000/api/v1/webhooks/', json={
    "name": "My Webhook",
    "url": "https://example.com/webhook",
    "description": "Webhook for user events",
    "event_types": ["user.created", "user.updated"],
    "timeout": 30,
    "is_active": True
})

webhook = response.json()
print(f"Webhook ID: {webhook['id']}")
print(f"Secret: {webhook['secret']}")  # Save this for signature verification
```

### Example: Triggering an Event

```python
import requests

# Trigger event
response = requests.post('http://localhost:8000/api/v1/events/trigger', json={
    "event_type": "user.created",
    "event_id": "usr_12345",
    "payload": {
        "user_id": 12345,
        "email": "user@example.com",
        "name": "John Doe",
        "created_at": "2025-01-01T00:00:00Z"
    }
})

result = response.json()
print(f"Notified {result['webhooks_notified']} webhooks")
```

### Example: Verifying Webhook Signature (Receiver)

```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    """Verify webhook signature"""
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]

    return hmac.compare_digest(expected_signature, signature)

# In your webhook receiver endpoint
@app.post("/webhook")
def receive_webhook(request):
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.json()

    if not verify_webhook(payload, signature, 'your-webhook-secret'):
        return {"error": "Invalid signature"}, 401

    # Process the webhook
    print(f"Received event: {payload['event_type']}")
    return {"status": "success"}
```

## Event Types

The system supports the following event types:

- **User Events**: `user.created`, `user.updated`, `user.deleted`
- **Order Events**: `order.created`, `order.updated`, `order.completed`, `order.cancelled`
- **Payment Events**: `payment.completed`, `payment.failed`
- **Project Events**: `project.created`, `project.updated`, `project.completed`
- **Document Events**: `document.created`, `document.updated`, `document.shared`
- **Meeting Events**: `meeting.scheduled`, `meeting.started`, `meeting.ended`
- **Email Events**: `email.received`, `email.sent`
- **Task Events**: `task.created`, `task.completed`
- **Analytics Events**: `analytics.report_generated`

## Configuration

Key configuration options in `.env`:

```env
# Webhook timeout (seconds)
WEBHOOK_TIMEOUT=30

# Maximum retry attempts for failed deliveries
MAX_RETRY_ATTEMPTS=5

# Retry backoff factor (exponential)
RETRY_BACKOFF_FACTOR=2.0

# Initial retry delay (seconds)
INITIAL_RETRY_DELAY=60

# Log retention (days)
LOG_RETENTION_DAYS=30
```

## Retry Logic

Failed webhook deliveries are automatically retried with exponential backoff:

- Attempt 1: Immediate
- Attempt 2: After 60 seconds
- Attempt 3: After 120 seconds (60 × 2^1)
- Attempt 4: After 240 seconds (60 × 2^2)
- Attempt 5: After 480 seconds (60 × 2^3)

After max attempts, the delivery is marked as failed.

## Security

### HMAC Signature Verification

All webhook requests include an `X-Webhook-Signature` header with an HMAC-SHA256 signature:

```
X-Webhook-Signature: sha256=<hex_signature>
```

Receivers should verify this signature to ensure the webhook is authentic.

### Best Practices

1. **Keep secrets secure**: Never commit webhook secrets to version control
2. **Use HTTPS**: Only send webhooks to HTTPS endpoints in production
3. **Verify signatures**: Always verify the signature on the receiving end
4. **Rate limiting**: Implement rate limiting on webhook receivers
5. **Idempotency**: Handle duplicate deliveries gracefully using `event_id`

## Monitoring

### Delivery Status

Deliveries can have the following statuses:

- `pending`: Queued for delivery
- `sending`: Currently being sent
- `success`: Successfully delivered (2xx response)
- `failed`: Failed after all retries
- `retrying`: Waiting for next retry attempt

### Statistics

View webhook statistics including:

- Total deliveries
- Successful deliveries
- Failed deliveries
- Success rate
- Delivery trends

## Development

### Running Tests

```bash
make test
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Project Structure

```
modules/webhooks/
├── api/              # REST API endpoints
├── models/           # Database models
├── services/         # Business logic
├── tasks/            # Celery tasks
├── ui/               # Streamlit interface
├── tests/            # Test files
├── migrations/       # Database migrations
├── config.py         # Configuration
├── requirements.txt  # Python dependencies
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Troubleshooting

### Webhook not being delivered

1. Check webhook is active: `GET /api/v1/webhooks/{id}`
2. Check event subscription: `GET /api/v1/webhooks/{id}/events`
3. Check Celery worker is running: `docker-compose logs celery_worker`
4. Check delivery logs: `GET /api/v1/deliveries/?webhook_id={id}`

### Connection errors

1. Ensure PostgreSQL is running: `docker-compose ps postgres`
2. Ensure Redis is running: `docker-compose ps redis`
3. Check connection strings in `.env`

### Signature verification fails

1. Ensure you're using the correct webhook secret
2. Verify the payload hasn't been modified
3. Check the signature format (should be `sha256=<hex>`)

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This module is part of the NEXUS platform.

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: [API Docs](http://localhost:8000/docs)

---

Built with ❤️ for the NEXUS Platform
