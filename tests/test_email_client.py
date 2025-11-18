"""
Comprehensive Unit Tests for Email Client Module

Tests all components of the email client.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Import email client modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.email_client.client import EmailClient, EmailAccount, EmailMessage, AccountType
from modules.email_client.compose import EmailComposer, EmailTemplate, EmailSignature
from modules.email_client.parser import EmailParser
from modules.email_client.attachment_manager import AttachmentManager
from modules.email_client.search import EmailSearch, SearchFilter
from modules.email_client.rules import RulesEngine, EmailRule, RuleCondition, RuleAction, RuleConditionType, RuleActionType
from modules.email_client.contacts_integration import ContactsManager, Contact, ContactGroup
from modules.email_client.ai_assistant import AIEmailAssistant
from modules.email_client.security import SecurityManager


class TestEmailClient:
    """Test EmailClient core functionality."""

    @pytest.fixture
    async def client(self):
        """Create email client fixture."""
        client = EmailClient(enable_ai=False, enable_security=False)
        yield client
        await client.cleanup()

    @pytest.mark.asyncio
    async def test_add_account(self, client):
        """Test adding an email account."""
        account = EmailAccount(
            email_address="test@example.com",
            username="test@example.com",
            password="password123",
            imap_host="imap.example.com",
            smtp_host="smtp.example.com"
        )

        account_id = await client.add_account(account)

        assert account_id in client.accounts
        assert client.accounts[account_id].email_address == "test@example.com"

    @pytest.mark.asyncio
    async def test_remove_account(self, client):
        """Test removing an account."""
        account = EmailAccount(
            email_address="test@example.com",
            username="test",
            password="pass"
        )

        account_id = await client.add_account(account)
        await client.remove_account(account_id)

        assert account_id not in client.accounts

    @pytest.mark.asyncio
    async def test_unified_inbox(self, client):
        """Test unified inbox across accounts."""
        # Add two accounts
        account1 = EmailAccount(email_address="user1@example.com")
        account2 = EmailAccount(email_address="user2@example.com")

        await client.add_account(account1)
        await client.add_account(account2)

        messages = await client.get_unified_inbox()

        assert isinstance(messages, list)


class TestEmailComposer:
    """Test email composition functionality."""

    @pytest.fixture
    def composer(self):
        """Create composer fixture."""
        return EmailComposer()

    def test_create_message(self, composer):
        """Test creating a new message."""
        message = composer.create_message(
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
            subject="Test Subject",
            body="Test body",
            is_html=False
        )

        assert message['from_address'] == "sender@example.com"
        assert message['subject'] == "Test Subject"
        assert 'message_id' in message

    def test_create_reply(self, composer):
        """Test creating a reply."""
        original = {
            'message_id': '123',
            'from_address': 'sender@example.com',
            'to_addresses': ['recipient@example.com'],
            'subject': 'Original Subject',
            'body_text': 'Original body',
            'body_html': '<p>Original body</p>'
        }

        reply = composer.create_reply(original, "Reply body", is_html=False)

        assert reply['subject'].startswith("Re:")
        assert 'sender@example.com' in reply['to_addresses']

    def test_create_forward(self, composer):
        """Test creating a forward."""
        original = {
            'message_id': '123',
            'from_address': 'sender@example.com',
            'subject': 'Original Subject',
            'body_text': 'Original body',
            'attachments': [{'filename': 'test.pdf'}]
        }

        forward = composer.create_forward(
            original,
            to_addresses=['newrecipient@example.com'],
            body="Forwarding this"
        )

        assert forward['subject'].startswith("Fwd:")
        assert len(forward['attachments']) > 0

    def test_validate_email_address(self, composer):
        """Test email address validation."""
        assert composer.validate_email_address("user@example.com") == True
        assert composer.validate_email_address("invalid.email") == False
        assert composer.validate_email_address("user@") == False

    def test_validate_message(self, composer):
        """Test message validation."""
        valid_message = {
            'from_address': 'sender@example.com',
            'to_addresses': ['recipient@example.com'],
            'subject': 'Test',
            'body_text': 'Body'
        }

        errors = composer.validate_message(valid_message)
        assert len(errors) == 0

        invalid_message = {
            'from_address': 'invalid',
            'to_addresses': [],
            'subject': '',
            'body_text': ''
        }

        errors = composer.validate_message(invalid_message)
        assert len(errors) > 0

    def test_add_template(self, composer):
        """Test adding email template."""
        template = EmailTemplate(
            name="Test Template",
            subject="Hello {{name}}",
            body_html="<p>Hello {{name}}!</p>",
            variables=["name"]
        )

        template_id = composer.add_template(template)
        assert template_id in composer.templates

    def test_create_from_template(self, composer):
        """Test creating message from template."""
        template = EmailTemplate(
            name="Welcome",
            subject="Welcome {{name}}!",
            body_html="<p>Hi {{name}}, welcome to {{company}}!</p>",
            variables=["name", "company"]
        )

        composer.add_template(template)

        message = composer.create_from_template(
            template.template_id,
            variables={"name": "John", "company": "ACME"},
            to_addresses=["john@example.com"],
            from_address="hello@acme.com"
        )

        assert message is not None
        assert "John" in message['subject']
        assert "ACME" in message['body_html']

    def test_add_signature(self, composer):
        """Test adding signature."""
        signature = EmailSignature(
            name="My Signature",
            html_content="<p>Best regards,<br>John</p>",
            is_default=True
        )

        sig_id = composer.add_signature(signature)
        assert sig_id in composer.signatures

        default_sig = composer.get_default_signature()
        assert default_sig is not None
        assert default_sig.name == "My Signature"


class TestEmailParser:
    """Test email parsing functionality."""

    @pytest.fixture
    def parser(self):
        """Create parser fixture."""
        return EmailParser()

    def test_parse_simple_email(self, parser):
        """Test parsing a simple email."""
        raw_email = b"""From: sender@example.com
To: recipient@example.com
Subject: Test Email
Date: Mon, 1 Jan 2024 12:00:00 +0000

This is the email body.
"""

        parsed = parser.parse(raw_email)

        assert parsed['from_address'] == "sender@example.com"
        assert "recipient@example.com" in parsed['to_addresses']
        assert parsed['subject'] == "Test Email"
        assert "email body" in parsed['body_text']

    def test_extract_urls(self, parser):
        """Test URL extraction."""
        text = "Check out https://example.com and http://test.org for more info"
        urls = parser.extract_urls(text)

        assert len(urls) >= 2
        assert "https://example.com" in urls

    def test_extract_email_addresses(self, parser):
        """Test email address extraction."""
        text = "Contact us at support@example.com or sales@test.org"
        emails = parser.extract_email_addresses(text)

        assert len(emails) >= 2
        assert "support@example.com" in emails

    def test_get_text_preview(self, parser):
        """Test getting text preview."""
        message = {
            'body_text': "This is a very long email body that should be truncated to create a preview. " * 10
        }

        preview = parser.get_text_preview(message, length=50)

        assert len(preview) <= 53  # 50 + "..."
        assert preview.endswith("...")


class TestAttachmentManager:
    """Test attachment management."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create attachment manager fixture."""
        return AttachmentManager(storage_path=str(tmp_path / "attachments"))

    @pytest.mark.asyncio
    async def test_process_attachment(self, manager):
        """Test processing an attachment."""
        attachment_data = {
            'filename': 'test.txt',
            'content_type': 'text/plain',
            'data': b'Test file content'
        }

        attachment = await manager.process_attachment(attachment_data)

        assert attachment is not None
        assert attachment.filename == 'test.txt'
        assert attachment.size_bytes == len(b'Test file content')
        assert attachment.file_path is not None

    def test_format_file_size(self, manager):
        """Test file size formatting."""
        assert manager.format_file_size(500) == "500.00 B"
        assert "KB" in manager.format_file_size(1024)
        assert "MB" in manager.format_file_size(1024 * 1024)

    def test_get_file_icon(self, manager):
        """Test getting file icon."""
        assert manager.get_file_icon("document.pdf") == "file-pdf"
        assert manager.get_file_icon("image.jpg") == "file-image"
        assert manager.get_file_icon("unknown.xyz") == "file"

    @pytest.mark.asyncio
    async def test_attachment_size_limit(self, manager):
        """Test attachment size limit."""
        large_data = b'x' * (30 * 1024 * 1024)  # 30MB (exceeds default limit)

        attachment_data = {
            'filename': 'large.bin',
            'content_type': 'application/octet-stream',
            'data': large_data
        }

        attachment = await manager.process_attachment(attachment_data)

        # Should be rejected
        assert attachment is None


class TestEmailSearch:
    """Test search and filtering."""

    @pytest.fixture
    def search(self):
        """Create search fixture."""
        return EmailSearch()

    def test_apply_filter_unread(self, search):
        """Test filtering unread messages."""
        messages = [
            {'message_id': '1', 'is_read': False},
            {'message_id': '2', 'is_read': True},
            {'message_id': '3', 'is_read': False}
        ]

        filter = SearchFilter(is_read=False)
        filtered = search.apply_filter(messages, filter)

        assert len(filtered) == 2

    def test_apply_filter_date_range(self, search):
        """Test filtering by date range."""
        now = datetime.utcnow()

        messages = [
            {'message_id': '1', 'date': now - timedelta(days=1)},
            {'message_id': '2', 'date': now - timedelta(days=5)},
            {'message_id': '3', 'date': now - timedelta(days=10)}
        ]

        filter = SearchFilter(
            date_from=now - timedelta(days=7),
            date_to=now
        )

        filtered = search.apply_filter(messages, filter)

        assert len(filtered) == 2  # Only messages within last 7 days

    def test_save_filter(self, search):
        """Test saving search filter."""
        filter = SearchFilter(
            name="Important Unread",
            is_read=False,
            is_starred=True
        )

        filter_id = search.save_filter(filter)

        assert filter_id in search.saved_filters
        assert search.saved_filters[filter_id].name == "Important Unread"

    def test_smart_folders(self, search):
        """Test smart folders."""
        smart_folders = search.list_smart_folders()

        assert len(smart_folders) > 0
        assert any(sf.name == "Unread" for sf in smart_folders)

    def test_parse_search_query(self, search):
        """Test parsing search query."""
        query = "from:sender@example.com subject:meeting is:unread"

        filter = search.parse_search_query(query)

        assert filter.from_address == "sender@example.com"
        assert filter.subject_contains == "meeting"
        assert filter.is_read == False


class TestRulesEngine:
    """Test inbox rules and automation."""

    @pytest.fixture
    def rules_engine(self):
        """Create rules engine fixture."""
        return RulesEngine()

    @pytest.mark.asyncio
    async def test_apply_spam_rule(self, rules_engine):
        """Test spam filtering rule."""
        message = {
            'subject': 'Buy viagra now!',
            'body_text': 'Get cheap viagra',
            'is_spam': False,
            'folder': 'INBOX'
        }

        processed = await rules_engine.apply_rules(message)

        # Should be marked as spam and moved
        assert processed.get('is_spam') == True

    def test_add_rule(self, rules_engine):
        """Test adding a custom rule."""
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
                )
            ]
        )

        rule_id = rules_engine.add_rule(rule)

        assert rule_id in rules_engine.rules

    @pytest.mark.asyncio
    async def test_rule_execution(self, rules_engine):
        """Test rule execution."""
        rule = EmailRule(
            name="Star Important",
            conditions=[
                RuleCondition(
                    condition_type=RuleConditionType.FROM_CONTAINS,
                    value="boss@company.com"
                )
            ],
            actions=[
                RuleAction(
                    action_type=RuleActionType.MARK_AS_STARRED,
                    value=True
                )
            ]
        )

        rules_engine.add_rule(rule)

        message = {
            'from_address': 'boss@company.com',
            'subject': 'Meeting',
            'is_starred': False
        }

        processed = await rules_engine.apply_rules(message)

        assert processed.get('is_starred') == True


class TestContactsManager:
    """Test contacts management."""

    @pytest.fixture
    async def contacts_manager(self):
        """Create contacts manager fixture."""
        return ContactsManager()

    @pytest.mark.asyncio
    async def test_add_contact(self, contacts_manager):
        """Test adding a contact."""
        contact = Contact(
            email_address="john@example.com",
            display_name="John Doe",
            first_name="John",
            last_name="Doe",
            company="ACME Corp"
        )

        contact_id = await contacts_manager.add_contact(contact)

        assert contact_id in contacts_manager.contacts

    @pytest.mark.asyncio
    async def test_get_contact_by_email(self, contacts_manager):
        """Test getting contact by email."""
        contact = Contact(
            email_address="jane@example.com",
            display_name="Jane Smith"
        )

        await contacts_manager.add_contact(contact)

        found = await contacts_manager.get_contact_by_email("jane@example.com")

        assert found is not None
        assert found.display_name == "Jane Smith"

    @pytest.mark.asyncio
    async def test_search_contacts(self, contacts_manager):
        """Test searching contacts."""
        await contacts_manager.add_contact(Contact(
            email_address="alice@example.com",
            display_name="Alice Johnson",
            company="TechCorp"
        ))

        await contacts_manager.add_contact(Contact(
            email_address="bob@example.com",
            display_name="Bob Wilson",
            company="ACME"
        ))

        results = await contacts_manager.search_contacts("alice")

        assert len(results) >= 1
        assert any(c.display_name == "Alice Johnson" for c in results)

    @pytest.mark.asyncio
    async def test_autocomplete(self, contacts_manager):
        """Test autocomplete functionality."""
        await contacts_manager.add_contact(Contact(
            email_address="support@example.com",
            display_name="Support Team"
        ))

        suggestions = await contacts_manager.autocomplete("supp", limit=5)

        assert len(suggestions) > 0

    @pytest.mark.asyncio
    async def test_contact_groups(self, contacts_manager):
        """Test contact groups."""
        contact1 = Contact(email_address="user1@example.com")
        contact2 = Contact(email_address="user2@example.com")

        cid1 = await contacts_manager.add_contact(contact1)
        cid2 = await contacts_manager.add_contact(contact2)

        group = ContactGroup(
            name="Team",
            description="My team"
        )

        gid = await contacts_manager.create_group(group)

        await contacts_manager.add_to_group(cid1, gid)
        await contacts_manager.add_to_group(cid2, gid)

        group_contacts = await contacts_manager.get_group_contacts(gid)

        assert len(group_contacts) == 2


class TestAIAssistant:
    """Test AI email assistant."""

    @pytest.fixture
    async def ai_assistant(self):
        """Create AI assistant fixture."""
        return AIEmailAssistant()

    @pytest.mark.asyncio
    async def test_calculate_priority(self, ai_assistant):
        """Test priority calculation."""
        important_message = {
            'from_address': 'boss@company.com',
            'subject': 'URGENT: Meeting',
            'body_text': 'You need to attend this meeting.'
        }

        priority = await ai_assistant.calculate_priority(important_message)

        assert priority > 0.5  # Should be high priority

        unimportant_message = {
            'from_address': 'newsletter@example.com',
            'subject': 'Weekly digest',
            'body_text': 'Here is your weekly newsletter...'
        }

        priority = await ai_assistant.calculate_priority(unimportant_message)

        assert priority < 0.7  # Should be lower priority

    @pytest.mark.asyncio
    async def test_categorize_email(self, ai_assistant):
        """Test email categorization."""
        meeting_email = {
            'subject': 'Team Meeting Tomorrow',
            'body_text': 'Let\'s schedule a meeting for tomorrow at 2pm.'
        }

        category = await ai_assistant.categorize_email(meeting_email)

        assert category == 'Meetings'

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, ai_assistant):
        """Test sentiment analysis."""
        positive_message = {
            'body_text': 'Thank you so much! This is great work, I really appreciate it.'
        }

        sentiment = await ai_assistant.analyze_sentiment(positive_message)

        assert sentiment == 'positive'

        negative_message = {
            'body_text': 'Unfortunately, this is a problem. We have failed to meet the deadline.'
        }

        sentiment = await ai_assistant.analyze_sentiment(negative_message)

        assert sentiment == 'negative'

    @pytest.mark.asyncio
    async def test_summarize_email(self, ai_assistant):
        """Test email summarization."""
        message = {
            'body_text': """Hi team,

I wanted to give you an update on the project. We have completed phase 1 and are moving into phase 2.
The deadline is next Friday. Please review the attached documents and provide feedback by Wednesday.

Thanks,
John"""
        }

        summary = await ai_assistant.summarize_email(message)

        assert summary is not None
        assert len(summary.short_summary) > 0

    @pytest.mark.asyncio
    async def test_generate_smart_replies(self, ai_assistant):
        """Test smart reply generation."""
        message = {
            'from_address': 'colleague@company.com',
            'subject': 'Can you review this?',
            'body_text': 'Could you review the attached document and let me know your thoughts?'
        }

        replies = await ai_assistant.generate_smart_replies(message, count=3)

        assert len(replies) > 0
        assert all(hasattr(r, 'text') for r in replies)


class TestSecurityManager:
    """Test security features."""

    @pytest.fixture
    def security_manager(self):
        """Create security manager fixture."""
        return SecurityManager()

    @pytest.mark.asyncio
    async def test_spam_detection(self, security_manager):
        """Test spam detection."""
        spam_message = {
            'subject': 'GET VIAGRA NOW!!! LIMITED TIME OFFER!!!',
            'body_text': 'Click here to get viagra at cheap prices! Act now!',
            'from_address': 'spam@suspicious-domain123.com'
        }

        spam_result = await security_manager.detect_spam(spam_message)

        assert spam_result.is_spam == True
        assert spam_result.score > 0.5

        legitimate_message = {
            'subject': 'Project Update',
            'body_text': 'Here is the update on our project progress.',
            'from_address': 'colleague@company.com'
        }

        spam_result = await security_manager.detect_spam(legitimate_message)

        assert spam_result.is_spam == False

    def test_password_hashing(self, security_manager):
        """Test password hashing."""
        password = "my_secure_password"

        hashed = security_manager.hash_password(password)

        assert hashed != password
        assert security_manager.verify_password(password, hashed) == True
        assert security_manager.verify_password("wrong_password", hashed) == False

    def test_sanitize_html(self, security_manager):
        """Test HTML sanitization."""
        dangerous_html = """
        <p>Hello</p>
        <script>alert('XSS')</script>
        <p onclick="malicious()">Click me</p>
        """

        sanitized = security_manager.sanitize_html(dangerous_html)

        assert '<script>' not in sanitized
        assert 'onclick' not in sanitized
        assert '<p>Hello</p>' in sanitized

    @pytest.mark.asyncio
    async def test_virus_scanning(self, security_manager):
        """Test virus scanning."""
        # Safe data
        safe_data = b'This is safe text content'
        is_safe, threat = await security_manager.scan_for_virus(safe_data)
        assert is_safe == True

        # Executable signature
        exe_data = b'MZ\x90\x00' + b'\x00' * 100
        is_safe, threat = await security_manager.scan_for_virus(exe_data)
        assert is_safe == False


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
