# NEXUS Email Service

A comprehensive email service module for the NEXUS Platform with support for sending, receiving, scheduling, tracking, and managing emails.

## Features

- **SMTP Client**: Send emails with attachments, HTML/text content, and custom headers
- **IMAP Client**: Receive and sync emails from IMAP servers
- **Email Parser**: Parse email messages, extract content, headers, and attachments
- **Attachment Handler**: Save, retrieve, and manage email attachments
- **Template System**: Create and use email templates with Jinja2
- **Email Scheduling**: Schedule emails to be sent at specific times
- **Email Tracking**: Track email opens, clicks, and engagement
- **Spam Filter**: Detect and filter spam emails
- **Inbox Sync**: Automatically synchronize inbox from IMAP servers

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with your email configuration:

```bash
# SMTP Configuration
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USERNAME=your-email@gmail.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_SMTP_USE_TLS=True

# IMAP Configuration
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USERNAME=your-email@gmail.com
EMAIL_IMAP_PASSWORD=your-app-password
EMAIL_IMAP_USE_SSL=True

# Email Settings
EMAIL_DEFAULT_SENDER=your-email@gmail.com
EMAIL_MAX_ATTACHMENT_SIZE_MB=25
EMAIL_SYNC_INTERVAL_MINUTES=5
EMAIL_BATCH_SIZE=50

# Database
DATABASE_URL=sqlite:///./nexus.db

# Tracking
EMAIL_TRACKING_ENABLED=True
```

## Quick Start

### Initialize Database

```python
from src.core.database import init_db

# Initialize database tables
init_db()
```

### Create Email Service

```python
from src.modules.email.service import EmailService

# Create service instance
service = EmailService()

# Create email account
account = service.create_account(
    email="your-email@gmail.com",
    name="Your Name",
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password",
    imap_host="imap.gmail.com",
    imap_port=993,
    imap_username="your-email@gmail.com",
    imap_password="your-app-password",
    is_default=True
)
```

### Send Email

```python
# Send simple email
email = service.send_email(
    to=["recipient@example.com"],
    subject="Hello from NEXUS",
    body_text="This is a plain text email.",
    body_html="<h1>Hello!</h1><p>This is an HTML email.</p>",
    account_id=account.id
)

# Send with attachments
email = service.send_email(
    to=["recipient@example.com"],
    subject="Documents",
    body_text="Please find attached documents.",
    attachments=["/path/to/file.pdf"],
    account_id=account.id
)

# Send with CC and BCC
email = service.send_email(
    to=["recipient@example.com"],
    cc=["cc@example.com"],
    bcc=["bcc@example.com"],
    subject="Meeting Notes",
    body_text="Here are the meeting notes.",
    account_id=account.id
)
```

### Use Email Templates

```python
# Create template
template = service.create_template(
    name="welcome",
    subject="Welcome to {{ app_name }}!",
    body_html="""
        <h1>Welcome, {{ user_name }}!</h1>
        <p>Thank you for joining {{ app_name }}.</p>
    """,
    body_text="Welcome, {{ user_name }}! Thank you for joining {{ app_name }}."
)

# Send using template
email = service.send_template_email(
    to=["newuser@example.com"],
    template_name="welcome",
    context={
        "user_name": "John Doe",
        "app_name": "NEXUS Platform"
    }
)
```

### Schedule Email

```python
from datetime import datetime, timedelta

# Schedule for later
send_time = datetime.utcnow() + timedelta(hours=2)

email = service.schedule_email(
    to=["recipient@example.com"],
    subject="Scheduled Email",
    body_text="This email was scheduled.",
    send_at=send_time,
    account_id=account.id
)

# Start scheduler
service.start_scheduler()
```

### Sync Inbox

```python
from datetime import datetime, timedelta

# Sync emails from last 7 days
since = datetime.utcnow() - timedelta(days=7)

stats = service.sync_inbox(
    folders=["INBOX"],
    since=since
)

print(f"Synced {stats['total_new']} new emails")
```

### Fetch and Read Emails

```python
# Fetch unread emails
emails = service.fetch_emails(unread_only=True, limit=10)

for email in emails:
    print(f"From: {email.from_address}")
    print(f"Subject: {email.subject}")
    print(f"Body: {email.body_text}")

    # Mark as read
    service.mark_as_read(email.id)
```

### Email Tracking

```python
# Send with tracking
email = service.send_email(
    to=["recipient@example.com"],
    subject="Tracked Email",
    body_html="<p>This email has tracking enabled.</p>",
    track_opens=True,
    track_clicks=True,
    account_id=account.id
)

# Get tracking stats
stats = service.get_email_stats(email.id)
print(f"Opens: {stats['opened_count']}")
print(f"Clicks: {stats['clicked_count']}")
```

### Inbox Statistics

```python
# Get inbox stats
stats = service.get_inbox_stats()

print(f"Total emails: {stats['total']}")
print(f"Unread: {stats['unread']}")
print(f"Spam: {stats['spam']}")
print(f"Sent: {stats['sent']}")
```

## Components

### 1. SMTP Client (`smtp_client.py`)

Handles sending emails via SMTP.

Features:
- TLS/SSL support
- Attachment handling
- Bulk sending
- Priority levels
- Custom headers

### 2. IMAP Client (`imap_client.py`)

Handles receiving emails via IMAP.

Features:
- Folder management
- Email search
- Mark as read/unread
- Delete and move emails
- Fetch by criteria

### 3. Email Parser (`parser.py`)

Parses email messages and extracts content.

Features:
- Header decoding
- Body extraction (text/HTML)
- Attachment detection
- URL extraction
- Email address parsing

### 4. Attachment Handler (`attachment_handler.py`)

Manages email attachments.

Features:
- Save attachments to disk
- File size validation
- Content type detection
- Cleanup old attachments
- Inline image support

### 5. Template Manager (`template_manager.py`)

Email template system using Jinja2.

Features:
- Template rendering
- Variable substitution
- Custom filters
- Database storage
- Default templates

### 6. Email Scheduler (`scheduler.py`)

Schedule email delivery.

Features:
- One-time scheduled emails
- Recurring emails
- Batch scheduling
- Pause/resume jobs
- Cron support

### 7. Email Tracker (`tracking.py`)

Track email engagement.

Features:
- Open tracking (pixel)
- Click tracking (links)
- Campaign statistics
- Engagement timeline
- Event export

### 8. Spam Filter (`spam_filter.py`)

Detect and filter spam.

Features:
- Keyword detection
- Link analysis
- Sender verification
- Attachment scanning
- Customizable threshold

### 9. Sync Service (`sync_service.py`)

Synchronize inbox from IMAP.

Features:
- Auto-sync all accounts
- Folder synchronization
- Incremental sync
- Spam detection on sync
- Attachment saving

### 10. Main Service (`service.py`)

Unified interface for all email operations.

## Database Models

- **EmailAccount**: Email account configuration
- **Email**: Email message
- **EmailAttachment**: Email attachment
- **EmailTemplate**: Email template
- **EmailTrackingEvent**: Tracking event

## Testing

Run tests:

```bash
pytest src/modules/email/tests/
```

Run with coverage:

```bash
pytest src/modules/email/tests/ --cov=src/modules/email
```

## Examples

See `examples/email_usage.py` for comprehensive usage examples.

## Security Notes

1. **Passwords**: Store email passwords securely. Use app-specific passwords for Gmail.
2. **Encryption**: Email passwords should be encrypted in production.
3. **Validation**: Email addresses are validated before sending.
4. **Attachments**: File size limits are enforced.
5. **Spam**: Spam filtering helps protect users.

## Gmail Configuration

For Gmail, you need to:

1. Enable 2-factor authentication
2. Generate an app-specific password
3. Use these settings:
   - SMTP: smtp.gmail.com:587 (TLS)
   - IMAP: imap.gmail.com:993 (SSL)

## Troubleshooting

### Connection Issues

- Check firewall settings
- Verify SMTP/IMAP ports are correct
- Ensure TLS/SSL settings match server requirements

### Authentication Failures

- Use app-specific passwords for Gmail
- Check username/password are correct
- Verify account has IMAP/SMTP enabled

### Attachment Issues

- Check file size limits
- Verify file paths are correct
- Ensure sufficient disk space

## License

Part of the NEXUS Platform project.

## Support

For issues or questions, please refer to the main NEXUS Platform documentation.
