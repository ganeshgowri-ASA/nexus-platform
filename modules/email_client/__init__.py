"""
NEXUS Email Client Module

A world-class, full-featured email client with AI assistance for the NEXUS platform.

Features:
- Multi-account support (Gmail, Outlook, Yahoo, IMAP/SMTP)
- Rich email composition with attachments
- Advanced search and filtering
- Inbox rules and automation
- AI-powered features (smart replies, summarization, priority sorting)
- PGP/S/MIME encryption
- Spam and phishing protection
- Calendar integration
- Beautiful Streamlit UI

Author: NEXUS Platform
Version: 1.0.0
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import EmailClient
    from .compose import EmailComposer
    from .search import EmailSearch
    from .ai_assistant import AIEmailAssistant

__version__ = "1.0.0"
__all__ = [
    "EmailClient",
    "EmailComposer",
    "EmailSearch",
    "AIEmailAssistant",
]


def get_email_client(*args, **kwargs) -> "EmailClient":
    """
    Factory function to create an EmailClient instance.

    Returns:
        EmailClient: Configured email client instance
    """
    from .client import EmailClient
    return EmailClient(*args, **kwargs)
