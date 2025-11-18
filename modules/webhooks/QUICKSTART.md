# Webhooks Module - Quick Start Guide

Get the NEXUS Webhooks module up and running in 5 minutes!

## Quick Start with Docker (Recommended)

### 1. Start Services

```bash
cd modules/webhooks
make start
```

This starts all required services:
- PostgreSQL database
- Redis
- FastAPI API server
- Celery worker & scheduler
- Streamlit UI

### 2. Access the Application

- **Streamlit UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

### 3. Create Your First Webhook

#### Option A: Using the UI (Easiest)

1. Go to http://localhost:8501
2. Navigate to "Webhooks" → "Create New"
3. Fill in the form:
   - Name: "My First Webhook"
   - URL: "https://webhook.site/unique-url" (get a test URL from webhook.site)
   - Select events: "user.created"
4. Click "Create Webhook"
5. **Save the secret** shown in the response!

#### Option B: Using the API

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Webhook",
    "url": "https://webhook.site/your-unique-url",
    "description": "Test webhook",
    "event_types": ["user.created"],
    "timeout": 30,
    "is_active": true
  }'
```

### 4. Trigger a Test Event

#### Using the UI:

1. Go to "Trigger Event"
2. Select event type: "user.created"
3. Enter a JSON payload:
```json
{
  "user_id": 123,
  "email": "test@example.com",
  "name": "Test User"
}
```
4. Click "Trigger Event"

#### Using the API:

```bash
curl -X POST "http://localhost:8000/api/v1/events/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user.created",
    "event_id": "evt_001",
    "payload": {
      "user_id": 123,
      "email": "test@example.com",
      "name": "Test User"
    }
  }'
```

### 5. Monitor Deliveries

- Go to "Deliveries" in the UI to see the delivery status
- Or check via API: http://localhost:8000/api/v1/deliveries/

## Testing Webhooks

### Get a Test Webhook URL

Use one of these free services to receive webhooks:

1. **webhook.site**: https://webhook.site
2. **requestbin**: https://requestbin.com
3. **webhook.test**: https://webhook.test

### Verify Signature on Receiver Side

When your webhook endpoint receives a request, verify the signature:

```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]

    # Generate expected signature
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    expected = hmac.new(
        secret.encode('utf-8'),
        payload_json.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

# In your Flask/FastAPI webhook receiver:
@app.post("/webhook")
def receive_webhook(request):
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.json()

    if not verify_webhook(payload, signature, 'your-webhook-secret'):
        return {"error": "Invalid signature"}, 401

    # Process webhook
    print(f"Event: {payload}")
    return {"status": "success"}
```

## Common Commands

```bash
# View logs
make logs

# Stop all services
make stop

# Restart services
make restart

# Clean up everything
make clean
```

## Available Event Types

Subscribe your webhooks to these events:

- `user.created`, `user.updated`, `user.deleted`
- `order.created`, `order.updated`, `order.completed`, `order.cancelled`
- `payment.completed`, `payment.failed`
- `project.created`, `project.updated`, `project.completed`
- `document.created`, `document.updated`, `document.shared`
- `meeting.scheduled`, `meeting.started`, `meeting.ended`
- `email.received`, `email.sent`
- `task.created`, `task.completed`
- `analytics.report_generated`

## Next Steps

1. **Read the full documentation**: See `README.md`
2. **Explore the API**: http://localhost:8000/docs
3. **Build integrations**: Use the API to integrate webhooks into your applications
4. **Configure production settings**: Edit `.env` for production use

## Troubleshooting

### Services won't start?

```bash
# Check Docker is running
docker ps

# Check logs
docker-compose logs
```

### Can't connect to API?

```bash
# Check if API is running
curl http://localhost:8000/health

# Check API logs
docker-compose logs api
```

### Webhooks not delivering?

1. Check Celery worker is running:
```bash
docker-compose logs celery_worker
```

2. Check delivery logs in the UI or API:
```bash
curl http://localhost:8000/api/v1/deliveries/
```

3. Verify webhook is active and subscribed to the event type

## Support

- Full documentation: `README.md`
- API docs: http://localhost:8000/docs
- GitHub Issues: [Report an issue]

---

Happy webhook-ing! 🎉
