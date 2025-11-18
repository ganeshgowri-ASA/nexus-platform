# NEXUS Platform - Multi-Channel Notification System

A comprehensive, production-ready notification system supporting multiple delivery channels with advanced features.

## Features

### Multi-Channel Support
- **Email**: SMTP, SendGrid, AWS SES
- **SMS**: Twilio, AWS SNS
- **Push Notifications**: Firebase Cloud Messaging (FCM), Apple Push Notification Service (APNs)
- **In-App**: Database-backed in-app notifications

### Core Capabilities
- ✅ Notification Templates with Jinja2 templating
- ✅ Notification Scheduling (immediate and delayed)
- ✅ Delivery Tracking and Analytics
- ✅ User Preferences Management
- ✅ One-Click Unsubscribe
- ✅ Webhook Support for provider events
- ✅ Bulk Notifications
- ✅ Priority Levels
- ✅ Retry Mechanism
- ✅ Email HTML/Plain Text support

## Architecture

```
nexus-platform/
├── backend/
│   ├── models/                    # Database models
│   │   ├── notification.py        # Notification records
│   │   ├── preference.py          # User preferences & unsubscribe
│   │   ├── template.py            # Notification templates
│   │   └── delivery.py            # Delivery tracking logs
│   ├── services/
│   │   └── notifications/
│   │       ├── providers/         # Channel providers
│   │       │   ├── email_provider.py
│   │       │   ├── sms_provider.py
│   │       │   ├── push_provider.py
│   │       │   └── in_app_provider.py
│   │       ├── notification_service.py  # Main service
│   │       ├── template_engine.py       # Template rendering
│   │       ├── scheduler.py             # Scheduling
│   │       ├── delivery_tracker.py      # Delivery tracking
│   │       └── unsubscribe_manager.py   # Preferences
│   ├── routers/
│   │   └── notifications.py       # API endpoints
│   ├── database.py                # Database config
│   └── main.py                    # FastAPI app
├── config/
│   └── settings.py                # Configuration
├── .env.example                   # Environment template
└── requirements.txt               # Dependencies
```

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd nexus-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# At minimum, configure one notification channel
```

### 3. Run the Server

```bash
# Start the API server
python backend/main.py

# Or using uvicorn directly
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

## Configuration Guide

### Email Configuration

#### SMTP (Gmail example)
```env
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
EMAIL_FROM=noreply@nexus.com
```

#### SendGrid
```env
EMAIL_BACKEND=sendgrid
SENDGRID_API_KEY=your-sendgrid-api-key
EMAIL_FROM=noreply@nexus.com
```

#### AWS SES
```env
EMAIL_BACKEND=ses
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
EMAIL_FROM=noreply@nexus.com
```

### SMS Configuration

#### Twilio
```env
SMS_BACKEND=twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890
```

#### AWS SNS
```env
SMS_BACKEND=sns
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
SNS_SENDER_ID=NEXUS
```

### Push Notification Configuration

#### Firebase Cloud Messaging (FCM)
```env
PUSH_BACKEND=fcm

# Option 1: Legacy Server Key
FCM_SERVER_KEY=your-server-key

# Option 2: Service Account (Recommended)
FCM_CREDENTIALS_PATH=/path/to/firebase-credentials.json
FCM_PROJECT_ID=your-project-id
```

#### Apple Push Notifications (APNs)
```env
PUSH_BACKEND=apns
APNS_CERTIFICATE_PATH=/path/to/cert.pem
APNS_KEY_ID=your-key-id
APNS_TEAM_ID=your-team-id
```

## Usage Examples

### Send Email Notification

```python
import requests

response = requests.post("http://localhost:8000/api/notifications/send", json={
    "user_id": "user123",
    "channel": "email",
    "recipient": "user@example.com",
    "title": "Welcome to NEXUS",
    "message": "Thank you for joining our platform!",
    "category": "onboarding",
    "priority": "normal"
})

print(response.json())
```

### Send SMS Notification

```python
response = requests.post("http://localhost:8000/api/notifications/send", json={
    "user_id": "user123",
    "channel": "sms",
    "recipient": "+1234567890",
    "title": "Verification Code",
    "message": "Your verification code is: 123456",
    "category": "security",
    "priority": "high"
})
```

### Send Push Notification

```python
response = requests.post("http://localhost:8000/api/notifications/send", json={
    "user_id": "user123",
    "channel": "push",
    "recipient": "device-token-here",
    "title": "New Message",
    "message": "You have a new message from John",
    "category": "messaging",
    "data": {
        "action_url": "/messages/123",
        "badge": 5
    }
})
```

### Send In-App Notification

```python
response = requests.post("http://localhost:8000/api/notifications/send", json={
    "user_id": "user123",
    "channel": "in_app",
    "recipient": "user123",
    "title": "Task Completed",
    "message": "Your export has finished processing",
    "category": "system",
    "data": {
        "action_url": "/downloads/export-123.csv"
    }
})
```

### Send with Template

```python
# First, create a template
template_response = requests.post("http://localhost:8000/api/notifications/templates", json={
    "name": "order_confirmation",
    "category": "transactional",
    "subject": "Order #{{ order_id }} Confirmed",
    "body": "Hello {{ customer_name }},\n\nYour order #{{ order_id }} for ${{ amount }} has been confirmed!",
    "html_body": "<h1>Order Confirmed</h1><p>Hello {{ customer_name }},</p><p>Your order #{{ order_id }} for ${{ amount }} has been confirmed!</p>",
    "variables": ["customer_name", "order_id", "amount"]
})

# Send using the template
response = requests.post("http://localhost:8000/api/notifications/send-template", json={
    "user_id": "user123",
    "channel": "email",
    "recipient": "user@example.com",
    "template_name": "order_confirmation",
    "template_vars": {
        "customer_name": "John Doe",
        "order_id": "12345",
        "amount": "99.99"
    }
})
```

### Schedule Notification

```python
from datetime import datetime, timedelta

# Schedule for 1 hour from now
scheduled_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()

response = requests.post("http://localhost:8000/api/notifications/send", json={
    "user_id": "user123",
    "channel": "email",
    "recipient": "user@example.com",
    "title": "Reminder",
    "message": "Your meeting starts in 15 minutes",
    "category": "reminder",
    "scheduled_at": scheduled_time
})
```

### Send Bulk Notifications

```python
response = requests.post("http://localhost:8000/api/notifications/send-bulk", json={
    "user_ids": ["user1", "user2", "user3"],
    "channel": "email",
    "title": "Important Announcement",
    "message": "We have an important update to share...",
    "category": "announcement"
})

print(f"Sent: {response.json()['sent']}, Failed: {response.json()['failed']}")
```

### Manage User Preferences

```python
# Get user preferences
preferences = requests.get(
    "http://localhost:8000/api/notifications/preferences/user123"
).json()

# Update preference
response = requests.put(
    "http://localhost:8000/api/notifications/preferences/user123",
    json={
        "category": "marketing",
        "channel": "email",
        "enabled": False  # Disable marketing emails
    }
)
```

### Get Delivery Analytics

```python
analytics = requests.get(
    "http://localhost:8000/api/notifications/analytics/delivery",
    params={
        "channel": "email",
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-01-31T23:59:59"
    }
).json()

print(f"Delivery Rate: {analytics['rates']['delivery_rate']}%")
print(f"Open Rate: {analytics['rates']['open_rate']}%")
print(f"Click Rate: {analytics['rates']['click_rate']}%")
```

## Database Schema

### Notifications Table
- `id`: Unique notification ID
- `user_id`: User identifier
- `channel`: Delivery channel (email, sms, push, in_app)
- `recipient`: Recipient identifier
- `title`: Notification title
- `message`: Notification message
- `status`: Current status (pending, scheduled, sent, failed, etc.)
- `priority`: Priority level
- `scheduled_at`: Scheduled send time
- `sent_at`: Actual send time
- `read`: Read status (for in-app)
- `category`: Notification category
- `template_id`: Associated template
- `created_at`, `updated_at`: Timestamps

### Notification Templates
- `id`: Template ID
- `name`: Unique template name
- `category`: Template category
- `subject`: Email subject template
- `body`: Message body template
- `html_body`: HTML email template
- `variables`: Required template variables
- `active`: Active status

### User Preferences
- `id`: Preference ID
- `user_id`: User identifier
- `category`: Notification category
- `channel`: Notification channel
- `enabled`: Whether enabled
- `settings`: Additional settings (JSON)

### Delivery Logs
- `id`: Log ID
- `notification_id`: Reference to notification
- `channel`: Delivery channel
- `status`: Delivery status
- `provider`: Provider used
- `provider_message_id`: Provider's message ID
- `sent_at`, `delivered_at`, `opened_at`, `clicked_at`: Timestamps
- `error_code`, `error_message`: Error details
- `processing_time_ms`: Processing time

## API Endpoints

### Notifications
- `POST /api/notifications/send` - Send notification
- `POST /api/notifications/send-bulk` - Send bulk notifications
- `POST /api/notifications/send-template` - Send with template
- `GET /api/notifications/user/{user_id}` - Get user notifications
- `POST /api/notifications/{id}/read` - Mark as read
- `GET /api/notifications/user/{user_id}/unread-count` - Get unread count

### Templates
- `POST /api/notifications/templates` - Create template
- `GET /api/notifications/templates` - List templates
- `GET /api/notifications/templates/{id}` - Get template

### Preferences
- `GET /api/notifications/preferences/{user_id}` - Get preferences
- `PUT /api/notifications/preferences/{user_id}` - Update preference

### Unsubscribe
- `POST /api/notifications/unsubscribe/{token}` - Process unsubscribe
- `GET /api/notifications/unsubscribe-url/{user_id}` - Generate unsubscribe URL

### Analytics
- `GET /api/notifications/analytics/delivery` - Delivery analytics

### Webhooks
- `POST /api/notifications/webhook/{provider}` - Handle provider webhooks

## Firebase Cloud Messaging Setup

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing
3. Enable Cloud Messaging

### 2. Get Credentials

#### Option A: Service Account (Recommended)
1. Go to Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save the JSON file
4. Set `FCM_CREDENTIALS_PATH` in .env

#### Option B: Server Key (Legacy)
1. Go to Project Settings → Cloud Messaging
2. Copy the Server Key
3. Set `FCM_SERVER_KEY` in .env

### 3. Client Integration

```javascript
// Web (JavaScript)
import { initializeApp } from "firebase/app";
import { getMessaging, getToken } from "firebase/messaging";

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// Get device token
const token = await getToken(messaging, {
  vapidKey: 'your-vapid-key'
});

// Send token to backend for user
await fetch('/api/notifications/register-device', {
  method: 'POST',
  body: JSON.stringify({ user_id: 'user123', device_token: token })
});
```

## Webhook Configuration

### SendGrid Email Events
Configure webhook URL: `https://your-domain.com/api/notifications/webhook/sendgrid`

Events: delivered, opened, clicked, bounced

### Twilio SMS Events
Configure Status Callback URL: `https://your-domain.com/api/notifications/webhook/twilio`

Events: delivered, failed

## Production Considerations

### Security
- Use HTTPS in production
- Configure CORS appropriately
- Secure webhook endpoints
- Use environment variables for secrets
- Implement rate limiting

### Performance
- Use connection pooling for database
- Implement caching for templates and preferences
- Use async workers for bulk notifications
- Set up message queue (Celery/Redis) for high volume

### Monitoring
- Set up error tracking (Sentry)
- Monitor delivery rates and failures
- Track API response times
- Set up alerting for failed deliveries

### Database
- Use PostgreSQL or MySQL for production
- Set up regular backups
- Implement database migrations with Alembic
- Add indexes for frequently queried fields

### Scaling
- Deploy with load balancer
- Use Redis for session/cache
- Consider microservices for each channel
- Implement circuit breakers for provider failures

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=backend tests/

# Test specific module
pytest tests/test_notifications.py
```

## Troubleshooting

### Email not sending
- Check SMTP credentials
- Verify firewall allows SMTP port
- Check email logs in delivery tracking
- Test with a simple SMTP client

### SMS not delivering
- Verify phone number format (E.164)
- Check Twilio/SNS account balance
- Ensure sender number is verified
- Check delivery logs for errors

### Push notifications not received
- Verify FCM credentials
- Check device token is valid
- Ensure app has notification permissions
- Test with FCM console

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]
- Email: support@nexus.com
