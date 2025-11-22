"""Email service module for NEXUS Platform.

This module provides comprehensive email functionality including:
- SMTP client for sending emails
- IMAP client for receiving emails
- Email parsing and content extraction
- Attachment handling
- Template system using Jinja2
- Email scheduling
- Email tracking
- Spam filtering
- Inbox synchronization
"""

from src.modules.email.service import EmailService

__all__ = ["EmailService"]
