# NEXUS Email Client Module

A world-class, full-featured email client with AI assistance for the NEXUS platform.

## Features

### 🌟 Core Features

- **Multi-Account Support**: Gmail, Outlook, Yahoo, IMAP/SMTP
- **Rich Email Composition**: HTML editor, attachments, templates, signatures
- **Advanced Search**: Full-text search, filters, smart folders
- **Inbox Rules**: Automation, auto-reply, filtering
- **AI Assistant**: Smart replies, summarization, priority sorting
- **Security**: PGP/S/MIME encryption, spam detection, phishing protection
- **Contacts**: Address book, groups, autocomplete
- **Beautiful UI**: Modern Streamlit interface

### 📧 Email Protocols

- **IMAP**: Full email synchronization
- **SMTP**: Reliable email sending
- **POP3**: Alternative protocol support
- **OAuth2**: Secure authentication

### 🤖 AI Features

- **Smart Replies**: AI-generated response suggestions
- **Email Summarization**: Automatic summary generation
- **Priority Inbox**: AI-based priority scoring
- **Sentiment Analysis**: Detect email tone
- **Category Detection**: Auto-categorize emails
- **Meeting Extraction**: Extract meeting info from emails
- **Phishing Detection**: AI-powered security

### 🔒 Security

- **PGP Encryption**: End-to-end encryption
- **S/MIME Support**: Certificate-based encryption
- **Spam Detection**: Advanced spam filtering
- **SPF/DKIM/DMARC**: Email authentication
- **Virus Scanning**: Attachment security
- **Content Filtering**: Remove dangerous content

## Installation

```bash
cd nexus-platform
pip install -r requirements.txt
```

## Quick Start

### 1. Basic Usage

```python
from modules.email_client import EmailClient, EmailAccount, AccountType

# Create email client
client = EmailClient()

# Add an account
account = EmailAccount(
    email_address="your@email.com",
    username="your@email.com",
    password="your_password",
    account_type=AccountType.GMAIL,
    imap_host="imap.gmail.com",
    smtp_host="smtp.gmail.com"
)

await client.add_account(account)

# Connect
await client.connect()

# Fetch messages
messages = await client.fetch_messages(folder="INBOX", limit=10)

# Send an email
from modules.email_client.compose import EmailComposer

composer = EmailComposer()
message = composer.create_message(
    from_address="your@email.com",
    to_addresses=["recipient@example.com"],
    subject="Hello from NEXUS!",
    body="<p>This is a test email.</p>",
    is_html=True
)

await client.send_message(message)
```

### 2. Using the Streamlit UI

```bash
streamlit run modules/email_client/streamlit_ui.py
```

This launches a beautiful Gmail-like interface with:
- Three-panel layout (folders, inbox, message view)
- Compose window
- Search functionality
- AI assistance panel

### 3. AI Features

```python
from modules.email_client.ai_assistant import AIEmailAssistant

ai_assistant = AIEmailAssistant()

# Get smart replies
replies = await ai_assistant.generate_smart_replies(message, count=3)
for reply in replies:
    print(f"{reply.text} (tone: {reply.tone}, confidence: {reply.confidence})")

# Summarize email
summary = await ai_assistant.summarize_email(message)
print(f"Summary: {summary.short_summary}")
print(f"Key points: {summary.key_points}")

# Calculate priority
priority = await ai_assistant.calculate_priority(message)
print(f"Priority score: {priority}")
```

### 4. Search and Filter

```python
from modules.email_client.search import EmailSearch, SearchFilter

search = EmailSearch()

# Simple search
results = await search.search(query="project update")

# Advanced filter
filter = SearchFilter(
    from_address="boss@company.com",
    is_read=False,
    has_attachments=True,
    date_from=datetime.now() - timedelta(days=7)
)

filtered_messages = search.apply_filter(messages, filter)

# Smart folders
unread = search.get_smart_folder_messages("unread", messages)
```

### 5. Inbox Rules

```python
from modules.email_client.rules import (
    RulesEngine, EmailRule, RuleCondition, RuleAction,
    RuleConditionType, RuleActionType
)

rules_engine = RulesEngine()

# Create a rule
rule = EmailRule(
    name="Archive Newsletters",
    conditions=[
        RuleCondition(
            condition_type=RuleConditionType.SUBJECT_CONTAINS,
            value="newsletter"
        )
    ],
    actions=[
        RuleAction(
            action_type=RuleActionType.MOVE_TO_FOLDER,
            value="Archive"
        ),
        RuleAction(
            action_type=RuleActionType.MARK_AS_READ,
            value=True
        )
    ]
)

rules_engine.add_rule(rule)

# Apply rules to a message
processed_message = await rules_engine.apply_rules(message)
```

### 6. Contacts Management

```python
from modules.email_client.contacts_integration import ContactsManager, Contact

contacts = ContactsManager()

# Add a contact
contact = Contact(
    email_address="john@example.com",
    display_name="John Doe",
    first_name="John",
    last_name="Doe",
    company="ACME Corp",
    phone_numbers=["+1234567890"]
)

await contacts.add_contact(contact)

# Search contacts
results = await contacts.search_contacts("john")

# Autocomplete
suggestions = await contacts.autocomplete("joh", limit=5)
```

### 7. Security Features

```python
from modules.email_client.security import SecurityManager

security = SecurityManager()

# Spam detection
spam_result = await security.detect_spam(message)
if spam_result.is_spam:
    print(f"Spam detected! Confidence: {spam_result.confidence}")
    print(f"Reasons: {spam_result.reasons}")

# Encrypt message (PGP)
encrypted = await security.encrypt_pgp(message, recipient_public_key)

# Check email security
security_check = await security.check_security(message)
print(f"SPF: {security_check.spf_result}")
print(f"DKIM: {security_check.dkim_result}")
```

## Configuration

### Email Account Presets

```python
from modules.email_client.client import GMAIL_CONFIG, OUTLOOK_CONFIG, YAHOO_CONFIG

# Gmail
gmail_account = EmailAccount(
    email_address="user@gmail.com",
    **GMAIL_CONFIG
)

# Outlook
outlook_account = EmailAccount(
    email_address="user@outlook.com",
    **OUTLOOK_CONFIG
)

# Yahoo
yahoo_account = EmailAccount(
    email_address="user@yahoo.com",
    **YAHOO_CONFIG
)
```

### OAuth2 Authentication

For Gmail, Outlook, and other OAuth2 providers:

```python
account = EmailAccount(
    email_address="user@gmail.com",
    oauth2_token="access_token_here",
    oauth2_refresh_token="refresh_token_here",
    **GMAIL_CONFIG
)
```

## Architecture

### Module Structure

```
modules/email_client/
├── __init__.py              # Module initialization
├── client.py                # Main email client
├── imap_handler.py          # IMAP protocol
├── smtp_handler.py          # SMTP protocol
├── pop3_handler.py          # POP3 protocol
├── compose.py               # Email composition
├── parser.py                # Email parsing
├── attachment_manager.py    # Attachment handling
├── search.py                # Search and filtering
├── rules.py                 # Inbox rules
├── contacts_integration.py  # Contacts management
├── ai_assistant.py          # AI features
├── security.py              # Security features
└── streamlit_ui.py          # Streamlit UI
```

### Key Classes

- **EmailClient**: Main orchestrator for all email operations
- **EmailComposer**: Email composition and templates
- **EmailParser**: Parse raw RFC822 emails
- **AttachmentManager**: Handle file attachments
- **EmailSearch**: Search and filtering engine
- **RulesEngine**: Inbox automation
- **ContactsManager**: Address book
- **AIEmailAssistant**: AI-powered features
- **SecurityManager**: Security and encryption

## Testing

Run the comprehensive test suite:

```bash
pytest tests/test_email_client.py -v
```

## Integration with NEXUS Platform

The email client integrates with other NEXUS modules:

```python
# Use with AI orchestrator
from modules.ai_orchestrator import AIOrchestrator

ai_orchestrator = AIOrchestrator()
ai_assistant = AIEmailAssistant(ai_model=ai_orchestrator)

# Use with file management
from modules.file_management import FileManager

file_manager = FileManager()
attachment_manager = AttachmentManager(storage_path=file_manager.get_path("email_attachments"))

# Use with database
from modules.database import DatabaseManager

db = DatabaseManager()
client = EmailClient(db_connection=db.get_connection())
```

## Best Practices

### 1. Account Management

```python
# Always use async/await
async def setup_email():
    client = EmailClient()
    account = EmailAccount(...)
    await client.add_account(account)
    await client.connect()

    try:
        # Do work
        messages = await client.fetch_messages()
    finally:
        await client.cleanup()
```

### 2. Error Handling

```python
try:
    await client.send_message(message)
except Exception as e:
    logger.error(f"Failed to send email: {e}")
    # Handle error
```

### 3. Resource Management

```python
# Use context manager (if implemented)
async with EmailClient() as client:
    await client.add_account(account)
    messages = await client.fetch_messages()
```

## Performance Tips

1. **Use connection pooling**: Keep connections alive for multiple operations
2. **Batch operations**: Fetch multiple messages at once
3. **Enable caching**: Cache frequently accessed data
4. **Use async operations**: All I/O operations are async
5. **Limit message fetching**: Use limit parameter to avoid fetching too many messages

## Security Recommendations

1. **Use OAuth2**: Prefer OAuth2 over password authentication
2. **Enable encryption**: Use PGP or S/MIME for sensitive emails
3. **Verify SPF/DKIM**: Check email authentication headers
4. **Scan attachments**: Always scan attachments for viruses
5. **Use SSL/TLS**: Always use encrypted connections

## Troubleshooting

### Connection Issues

```python
# Test connection
if await client.connect():
    print("Connected successfully")
else:
    print("Connection failed - check credentials and server settings")
```

### OAuth2 Token Refresh

```python
# Implement token refresh callback
async def refresh_oauth2_token(account):
    # Refresh logic here
    new_token = await get_new_token(account.oauth2_refresh_token)
    account.oauth2_token = new_token
    return account
```

### Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('modules.email_client')
logger.setLevel(logging.DEBUG)
```

## Contributing

Contributions are welcome! Please:

1. Add tests for new features
2. Follow the existing code style
3. Update documentation
4. Ensure all tests pass

## License

Part of the NEXUS Platform.

## Support

For issues and questions, please create an issue in the NEXUS repository.
