"""Tests for email service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.modules.email.service import EmailService
from src.modules.email.models import EmailAccount, Email, EmailStatus, EmailPriority


class TestEmailService:
    """Test EmailService class."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def email_service(self, db_session):
        """Create EmailService instance."""
        return EmailService(db=db_session)

    def test_initialization(self, email_service):
        """Test service initialization."""
        assert email_service is not None
        assert email_service.attachment_handler is not None
        assert email_service.template_manager is not None
        assert email_service.scheduler is not None
        assert email_service.tracker is not None
        assert email_service.spam_filter is not None
        assert email_service.sync_service is not None

    @patch('src.modules.email.service.SMTPClient')
    def test_send_email(self, mock_smtp, email_service, db_session):
        """Test sending email."""
        # Setup mocks
        mock_account = Mock()
        mock_account.id = 1
        mock_account.email = "test@example.com"
        mock_account.name = "Test User"

        db_session.query.return_value.filter_by.return_value.first.return_value = mock_account
        db_session.add = Mock()
        db_session.flush = Mock()
        db_session.commit = Mock()

        mock_smtp_instance = Mock()
        mock_smtp_instance.send_email.return_value = "<message-id-123>"
        email_service.smtp_client = mock_smtp_instance
        email_service.account_id = 1

        # Send email
        result = email_service.send_email(
            to=["recipient@example.com"],
            subject="Test Email",
            body_text="This is a test email"
        )

        # Verify SMTP client was called
        assert mock_smtp_instance.send_email.called

    def test_create_account(self, email_service, db_session):
        """Test creating email account."""
        db_session.add = Mock()
        db_session.commit = Mock()
        db_session.refresh = Mock()

        account = email_service.create_account(
            email="test@example.com",
            name="Test User",
            smtp_host="smtp.example.com",
            smtp_port=587
        )

        assert db_session.add.called
        assert db_session.commit.called

    def test_get_inbox_stats(self, email_service, db_session):
        """Test getting inbox statistics."""
        email_service.account_id = 1

        # Mock query results
        mock_query = Mock()
        mock_query.filter_by.return_value.count.return_value = 10
        db_session.query.return_value = mock_query

        stats = email_service.get_inbox_stats()

        assert 'total' in stats
        assert 'unread' in stats
        assert 'spam' in stats
        assert 'sent' in stats


class TestSMTPClient:
    """Test SMTP client."""

    def test_smtp_initialization(self):
        """Test SMTP client initialization."""
        from src.modules.email.smtp_client import SMTPClient

        client = SMTPClient(
            host="smtp.example.com",
            port=587,
            username="test@example.com",
            password="password"
        )

        assert client.host == "smtp.example.com"
        assert client.port == 587
        assert client.username == "test@example.com"


class TestEmailParser:
    """Test email parser."""

    def test_decode_header_value(self):
        """Test decoding header values."""
        from src.modules.email.parser import EmailParser

        result = EmailParser.decode_header_value("Test Subject")
        assert result == "Test Subject"

    def test_extract_urls(self):
        """Test extracting URLs from text."""
        from src.modules.email.parser import EmailParser

        text = "Check out https://example.com and http://test.com"
        urls = EmailParser.extract_urls(text)

        assert len(urls) == 2
        assert "https://example.com" in urls
        assert "http://test.com" in urls


class TestSpamFilter:
    """Test spam filter."""

    def test_spam_filter_initialization(self):
        """Test spam filter initialization."""
        from src.modules.email.spam_filter import SpamFilter

        filter = SpamFilter()
        assert filter is not None
        assert filter.threshold > 0

    def test_check_spam_keywords(self):
        """Test spam keyword detection."""
        from src.modules.email.spam_filter import SpamFilter

        filter = SpamFilter(spam_keywords=["winner", "lottery"])

        score = filter._check_spam_keywords("You are a winner!")
        assert score > 0

        score = filter._check_spam_keywords("Normal email text")
        assert score == 0


class TestTemplateManager:
    """Test template manager."""

    def test_render_template_from_string(self):
        """Test rendering template from string."""
        from src.modules.email.template_manager import TemplateManager

        manager = TemplateManager()

        result = manager.render_template(
            "Hello {{ name }}!",
            {"name": "World"},
            from_string=True
        )

        assert result == "Hello World!"

    def test_custom_filters(self):
        """Test custom Jinja2 filters."""
        from src.modules.email.template_manager import TemplateManager

        manager = TemplateManager()

        # Test format_date filter
        result = manager.render_template(
            "{{ date | format_date('%Y-%m-%d') }}",
            {"date": datetime(2024, 1, 1)},
            from_string=True
        )

        assert "2024-01-01" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
