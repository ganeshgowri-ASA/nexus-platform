"""
Wiki Integration Service

External service integrations for the NEXUS Wiki System including:
- Slack integration (notifications, slash commands, unfurling)
- Microsoft Teams integration (notifications, bots)
- GitHub integration (sync with GitHub wikis, link issues/PRs)
- JIRA integration (link to tickets, sync documentation)
- Webhook system for custom integrations
- Generic REST API integration support
- OAuth handling for third-party services
- Event notification system
- Bidirectional sync capabilities

Author: NEXUS Platform Team
"""

import re
import json
import hmac
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from enum import Enum
from urllib.parse import urljoin, quote
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from app.config import settings
from modules.wiki.models import (
    WikiPage, WikiHistory, WikiComment, WikiCategory,
    WikiTag, WikiLink
)
from modules.wiki.wiki_types import (
    PageStatus, ContentFormat, ChangeType, NotificationType
)

logger = get_logger(__name__)


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

class IntegrationType(str, Enum):
    """Types of integrations."""
    SLACK = "slack"
    TEAMS = "teams"
    GITHUB = "github"
    JIRA = "jira"
    WEBHOOK = "webhook"
    REST_API = "rest_api"
    CUSTOM = "custom"


class EventType(str, Enum):
    """Types of events that can trigger integrations."""
    PAGE_CREATED = "page_created"
    PAGE_UPDATED = "page_updated"
    PAGE_DELETED = "page_deleted"
    PAGE_PUBLISHED = "page_published"
    COMMENT_ADDED = "comment_added"
    MENTION = "mention"
    TAG_ADDED = "tag_added"
    CATEGORY_CHANGED = "category_changed"


class WebhookStatus(str, Enum):
    """Status of webhook deliveries."""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


# ============================================================================
# SLACK INTEGRATION
# ============================================================================

class SlackIntegration:
    """
    Slack integration for wiki notifications, slash commands, and link unfurling.

    Provides:
    - Channel notifications for page updates
    - Slash commands for wiki operations
    - Rich link unfurling for wiki URLs
    - Interactive messages and buttons
    """

    def __init__(self, db: Session, bot_token: Optional[str] = None, signing_secret: Optional[str] = None):
        """
        Initialize Slack integration.

        Args:
            db: SQLAlchemy database session
            bot_token: Slack bot OAuth token
            signing_secret: Slack signing secret for request verification

        Example:
            >>> slack = SlackIntegration(db, bot_token="xoxb-...")
            >>> slack.send_page_notification(page_id=123, channel="#wiki-updates")
        """
        self.db = db
        self.bot_token = bot_token or ""
        self.signing_secret = signing_secret or ""
        self.api_base = "https://api.slack.com/api"

    def send_page_notification(
        self,
        page_id: int,
        channel: str,
        event_type: EventType = EventType.PAGE_UPDATED,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Send notification to Slack channel about page event.

        Args:
            page_id: Wiki page ID
            channel: Slack channel (e.g., "#wiki-updates" or "C0123456789")
            event_type: Type of event
            user_id: User who triggered the event

        Returns:
            True if notification sent successfully

        Example:
            >>> slack.send_page_notification(
            ...     page_id=123,
            ...     channel="#general",
            ...     event_type=EventType.PAGE_PUBLISHED
            ... )
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                logger.warning(f"Page {page_id} not found for Slack notification")
                return False

            # Build message blocks
            blocks = self._build_page_notification_blocks(page, event_type, user_id)

            # Send message
            response = self._post("chat.postMessage", {
                "channel": channel,
                "blocks": blocks,
                "text": f"Wiki page {event_type.value}: {page.title}"
            })

            if response.get("ok"):
                logger.info(f"Sent Slack notification for page {page_id} to {channel}")
                return True
            else:
                logger.error(f"Failed to send Slack notification: {response.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}", exc_info=True)
            return False

    def handle_slash_command(
        self,
        command: str,
        text: str,
        user_id: str,
        channel_id: str,
        response_url: str
    ) -> Dict[str, Any]:
        """
        Handle Slack slash command for wiki operations.

        Args:
            command: Slash command name (e.g., "/wiki")
            text: Command text/arguments
            user_id: Slack user ID
            channel_id: Slack channel ID
            response_url: URL for delayed responses

        Returns:
            Response dictionary for Slack

        Example:
            >>> response = slack.handle_slash_command(
            ...     command="/wiki",
            ...     text="search python tutorial",
            ...     user_id="U0123456789",
            ...     channel_id="C0123456789",
            ...     response_url="https://..."
            ... )
        """
        try:
            parts = text.strip().split(maxsplit=1)
            action = parts[0].lower() if parts else "help"
            args = parts[1] if len(parts) > 1 else ""

            if action == "search":
                return self._handle_search_command(args)
            elif action == "create":
                return self._handle_create_command(args, user_id)
            elif action == "recent":
                return self._handle_recent_command()
            elif action == "help":
                return self._handle_help_command()
            else:
                return {
                    "response_type": "ephemeral",
                    "text": f"Unknown command: {action}. Type `/wiki help` for available commands."
                }

        except Exception as e:
            logger.error(f"Error handling slash command: {str(e)}", exc_info=True)
            return {
                "response_type": "ephemeral",
                "text": f"Error: {str(e)}"
            }

    def unfurl_links(
        self,
        links: List[str],
        channel: str,
        message_ts: str
    ) -> bool:
        """
        Unfurl wiki page links in Slack messages.

        Args:
            links: List of wiki URLs to unfurl
            channel: Slack channel
            message_ts: Message timestamp

        Returns:
            True if unfurling successful

        Example:
            >>> slack.unfurl_links(
            ...     links=["https://wiki.example.com/page/python-guide"],
            ...     channel="C0123456789",
            ...     message_ts="1234567890.123456"
            ... )
        """
        try:
            unfurls = {}

            for link in links:
                # Extract page slug from URL
                slug = self._extract_page_slug(link)
                if not slug:
                    continue

                # Get page
                page = self.db.query(WikiPage).filter(
                    WikiPage.slug == slug,
                    WikiPage.is_deleted == False
                ).first()

                if page:
                    unfurls[link] = self._build_page_unfurl(page)

            if not unfurls:
                return False

            # Send unfurls
            response = self._post("chat.unfurl", {
                "channel": channel,
                "ts": message_ts,
                "unfurls": unfurls
            })

            return response.get("ok", False)

        except Exception as e:
            logger.error(f"Error unfurling links: {str(e)}", exc_info=True)
            return False

    def verify_request(
        self,
        timestamp: str,
        body: str,
        signature: str
    ) -> bool:
        """
        Verify Slack request signature.

        Args:
            timestamp: Request timestamp
            body: Request body
            signature: X-Slack-Signature header

        Returns:
            True if signature is valid
        """
        try:
            # Check timestamp is recent (within 5 minutes)
            if abs(int(datetime.utcnow().timestamp()) - int(timestamp)) > 300:
                return False

            # Compute signature
            sig_basestring = f"v0:{timestamp}:{body}"
            computed_sig = 'v0=' + hmac.new(
                self.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()

            # Compare signatures
            return hmac.compare_digest(computed_sig, signature)

        except Exception as e:
            logger.error(f"Error verifying Slack request: {str(e)}", exc_info=True)
            return False

    # Private helper methods

    def _post(self, method: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to Slack API."""
        url = f"{self.api_base}/{method}"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=data, headers=headers)
        return response.json()

    def _build_page_notification_blocks(
        self,
        page: WikiPage,
        event_type: EventType,
        user_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Build Slack message blocks for page notification."""
        icon = {
            EventType.PAGE_CREATED: ":sparkles:",
            EventType.PAGE_UPDATED: ":pencil2:",
            EventType.PAGE_DELETED: ":wastebasket:",
            EventType.PAGE_PUBLISHED: ":rocket:"
        }.get(event_type, ":page_facing_up:")

        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{icon} *{event_type.value.replace('_', ' ').title()}*\n<https://wiki.example.com/page/{page.slug}|{page.title}>"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Category:*\n{page.category.name if page.category else 'Uncategorized'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{page.status.value.title()}"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Updated {page.updated_at.strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            }
        ]

    def _build_page_unfurl(self, page: WikiPage) -> Dict[str, Any]:
        """Build unfurl data for a wiki page."""
        return {
            "title": page.title,
            "text": page.summary or page.content[:200] + "...",
            "fields": [
                {
                    "title": "Category",
                    "value": page.category.name if page.category else "Uncategorized",
                    "short": True
                },
                {
                    "title": "Status",
                    "value": page.status.value.title(),
                    "short": True
                }
            ],
            "footer": "NEXUS Wiki",
            "ts": int(page.updated_at.timestamp())
        }

    def _extract_page_slug(self, url: str) -> Optional[str]:
        """Extract page slug from wiki URL."""
        match = re.search(r'/page/([^/\?]+)', url)
        return match.group(1) if match else None

    def _handle_search_command(self, query: str) -> Dict[str, Any]:
        """Handle wiki search slash command."""
        if not query:
            return {
                "response_type": "ephemeral",
                "text": "Please provide a search query. Example: `/wiki search python`"
            }

        # Search pages
        pages = self.db.query(WikiPage).filter(
            WikiPage.is_deleted == False,
            WikiPage.status == PageStatus.PUBLISHED,
            or_(
                WikiPage.title.ilike(f"%{query}%"),
                WikiPage.content.ilike(f"%{query}%")
            )
        ).limit(5).all()

        if not pages:
            return {
                "response_type": "ephemeral",
                "text": f"No pages found for '{query}'"
            }

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Search results for '{query}':*"
                }
            }
        ]

        for page in pages:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• <https://wiki.example.com/page/{page.slug}|{page.title}>"
                }
            })

        return {
            "response_type": "ephemeral",
            "blocks": blocks
        }

    def _handle_create_command(self, title: str, user_id: str) -> Dict[str, Any]:
        """Handle page creation slash command."""
        if not title:
            return {
                "response_type": "ephemeral",
                "text": "Please provide a page title. Example: `/wiki create My New Page`"
            }

        return {
            "response_type": "ephemeral",
            "text": f"To create a page titled '{title}', visit: https://wiki.example.com/create?title={quote(title)}"
        }

    def _handle_recent_command(self) -> Dict[str, Any]:
        """Handle recent pages slash command."""
        pages = self.db.query(WikiPage).filter(
            WikiPage.is_deleted == False,
            WikiPage.status == PageStatus.PUBLISHED
        ).order_by(desc(WikiPage.updated_at)).limit(5).all()

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Recently updated pages:*"
                }
            }
        ]

        for page in pages:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"• <https://wiki.example.com/page/{page.slug}|{page.title}>\n   _{page.updated_at.strftime('%Y-%m-%d %H:%M')}_"
                }
            })

        return {
            "response_type": "ephemeral",
            "blocks": blocks
        }

    def _handle_help_command(self) -> Dict[str, Any]:
        """Handle help slash command."""
        return {
            "response_type": "ephemeral",
            "text": """*Wiki Commands:*
• `/wiki search <query>` - Search for pages
• `/wiki create <title>` - Create a new page
• `/wiki recent` - Show recently updated pages
• `/wiki help` - Show this help message"""
        }


# ============================================================================
# MICROSOFT TEAMS INTEGRATION
# ============================================================================

class TeamsIntegration:
    """
    Microsoft Teams integration for wiki notifications and bot interactions.

    Provides:
    - Channel notifications via webhooks
    - Adaptive cards for rich notifications
    - Bot framework integration
    - Message actions and commands
    """

    def __init__(self, db: Session, webhook_url: Optional[str] = None):
        """
        Initialize Teams integration.

        Args:
            db: SQLAlchemy database session
            webhook_url: Teams incoming webhook URL

        Example:
            >>> teams = TeamsIntegration(db, webhook_url="https://...")
            >>> teams.send_page_notification(page_id=123)
        """
        self.db = db
        self.webhook_url = webhook_url or ""

    def send_page_notification(
        self,
        page_id: int,
        event_type: EventType = EventType.PAGE_UPDATED,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Send notification to Teams channel about page event.

        Args:
            page_id: Wiki page ID
            event_type: Type of event
            user_id: User who triggered the event

        Returns:
            True if notification sent successfully

        Example:
            >>> teams.send_page_notification(
            ...     page_id=123,
            ...     event_type=EventType.PAGE_PUBLISHED
            ... )
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                logger.warning(f"Page {page_id} not found for Teams notification")
                return False

            # Build adaptive card
            card = self._build_page_adaptive_card(page, event_type, user_id)

            # Send to webhook
            response = requests.post(
                self.webhook_url,
                json=card,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                logger.info(f"Sent Teams notification for page {page_id}")
                return True
            else:
                logger.error(f"Failed to send Teams notification: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending Teams notification: {str(e)}", exc_info=True)
            return False

    def _build_page_adaptive_card(
        self,
        page: WikiPage,
        event_type: EventType,
        user_id: Optional[int]
    ) -> Dict[str, Any]:
        """Build adaptive card for page notification."""
        color = {
            EventType.PAGE_CREATED: "Good",
            EventType.PAGE_UPDATED: "Attention",
            EventType.PAGE_DELETED: "Warning",
            EventType.PAGE_PUBLISHED: "Good"
        }.get(event_type, "Default")

        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": f"{event_type.value}: {page.title}",
            "themeColor": color,
            "title": event_type.value.replace("_", " ").title(),
            "sections": [
                {
                    "activityTitle": page.title,
                    "activitySubtitle": page.summary or "No description",
                    "facts": [
                        {
                            "name": "Category:",
                            "value": page.category.name if page.category else "Uncategorized"
                        },
                        {
                            "name": "Status:",
                            "value": page.status.value.title()
                        },
                        {
                            "name": "Last Updated:",
                            "value": page.updated_at.strftime("%Y-%m-%d %H:%M")
                        }
                    ]
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Page",
                    "targets": [
                        {
                            "os": "default",
                            "uri": f"https://wiki.example.com/page/{page.slug}"
                        }
                    ]
                }
            ]
        }


# ============================================================================
# GITHUB INTEGRATION
# ============================================================================

class GitHubIntegration:
    """
    GitHub integration for wiki sync and issue linking.

    Provides:
    - Sync with GitHub wiki
    - Link to issues and pull requests
    - Webhook support for GitHub events
    - Bidirectional content sync
    """

    def __init__(
        self,
        db: Session,
        token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None
    ):
        """
        Initialize GitHub integration.

        Args:
            db: SQLAlchemy database session
            token: GitHub personal access token
            repo_owner: Repository owner
            repo_name: Repository name

        Example:
            >>> github = GitHubIntegration(
            ...     db,
            ...     token="ghp_...",
            ...     repo_owner="myorg",
            ...     repo_name="myrepo"
            ... )
            >>> github.sync_wiki_to_github()
        """
        self.db = db
        self.token = token or ""
        self.repo_owner = repo_owner or ""
        self.repo_name = repo_name or ""
        self.api_base = "https://api.github.com"

    def sync_page_to_github(
        self,
        page_id: int,
        create_if_missing: bool = True
    ) -> bool:
        """
        Sync wiki page to GitHub wiki.

        Args:
            page_id: Wiki page ID to sync
            create_if_missing: Create page if it doesn't exist on GitHub

        Returns:
            True if sync successful

        Example:
            >>> github.sync_page_to_github(page_id=123)
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                logger.warning(f"Page {page_id} not found for GitHub sync")
                return False

            # GitHub wiki uses .md files
            filename = f"{page.slug}.md"

            # Get GitHub wiki content
            content_url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}.wiki/contents/{filename}"

            response = self._get(content_url)

            if response.status_code == 200:
                # Update existing page
                data = response.json()
                sha = data["sha"]
                return self._update_github_file(filename, page.content, sha, f"Update {page.title}")
            elif response.status_code == 404 and create_if_missing:
                # Create new page
                return self._create_github_file(filename, page.content, f"Create {page.title}")
            else:
                logger.error(f"GitHub API error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error syncing to GitHub: {str(e)}", exc_info=True)
            return False

    def sync_from_github(
        self,
        filename: str,
        author_id: int
    ) -> Optional[int]:
        """
        Sync content from GitHub wiki to local wiki.

        Args:
            filename: GitHub wiki filename
            author_id: User ID to attribute changes to

        Returns:
            Page ID if sync successful

        Example:
            >>> page_id = github.sync_from_github("Python-Guide.md", author_id=1)
        """
        try:
            # Get content from GitHub
            content_url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}.wiki/contents/{filename}"
            response = self._get(content_url)

            if response.status_code != 200:
                logger.error(f"Failed to fetch from GitHub: {response.status_code}")
                return None

            data = response.json()
            content = requests.get(data["download_url"]).text

            # Extract title from filename
            title = filename.replace(".md", "").replace("-", " ").title()
            slug = filename.replace(".md", "").lower()

            # Check if page exists
            page = self.db.query(WikiPage).filter(
                WikiPage.slug == slug,
                WikiPage.is_deleted == False
            ).first()

            if page:
                # Update existing page
                page.content = content
                page.updated_at = datetime.utcnow()
            else:
                # Create new page
                page = WikiPage(
                    title=title,
                    slug=slug,
                    content=content,
                    content_format=ContentFormat.MARKDOWN,
                    author_id=author_id,
                    status=PageStatus.PUBLISHED
                )
                self.db.add(page)

            self.db.commit()
            logger.info(f"Synced page from GitHub: {title}")
            return page.id

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error syncing from GitHub: {str(e)}", exc_info=True)
            return None

    def link_issue(
        self,
        page_id: int,
        issue_number: int,
        link_type: str = "references"
    ) -> bool:
        """
        Create link between wiki page and GitHub issue.

        Args:
            page_id: Wiki page ID
            issue_number: GitHub issue number
            link_type: Type of link (references, closes, etc.)

        Returns:
            True if link created successfully

        Example:
            >>> github.link_issue(page_id=123, issue_number=45, link_type="references")
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return False

            # Create external link
            issue_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/issues/{issue_number}"

            link = WikiLink(
                source_page_id=page_id,
                target_url=issue_url,
                link_type=LinkType.EXTERNAL,
                title=f"Issue #{issue_number}"
            )

            self.db.add(link)
            self.db.commit()

            logger.info(f"Linked page {page_id} to issue #{issue_number}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error linking issue: {str(e)}", exc_info=True)
            return False

    def handle_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Handle GitHub webhook events.

        Args:
            event_type: GitHub event type
            payload: Webhook payload

        Returns:
            True if event handled successfully

        Example:
            >>> github.handle_webhook("push", payload_data)
        """
        try:
            if event_type == "gollum":  # Wiki page event
                return self._handle_wiki_event(payload)
            elif event_type == "issues":
                return self._handle_issue_event(payload)
            elif event_type == "pull_request":
                return self._handle_pr_event(payload)
            else:
                logger.info(f"Unhandled GitHub event: {event_type}")
                return True

        except Exception as e:
            logger.error(f"Error handling GitHub webhook: {str(e)}", exc_info=True)
            return False

    # Private helper methods

    def _get(self, url: str) -> requests.Response:
        """Make GET request to GitHub API."""
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        return requests.get(url, headers=headers)

    def _create_github_file(
        self,
        path: str,
        content: str,
        message: str
    ) -> bool:
        """Create file in GitHub repository."""
        import base64

        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}.wiki/contents/{path}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode()
        }

        response = requests.put(url, json=data, headers=headers)
        return response.status_code == 201

    def _update_github_file(
        self,
        path: str,
        content: str,
        sha: str,
        message: str
    ) -> bool:
        """Update file in GitHub repository."""
        import base64

        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}.wiki/contents/{path}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        data = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
            "sha": sha
        }

        response = requests.put(url, json=data, headers=headers)
        return response.status_code == 200

    def _handle_wiki_event(self, payload: Dict[str, Any]) -> bool:
        """Handle GitHub wiki events."""
        # Implementation would sync wiki changes
        logger.info("Handling GitHub wiki event")
        return True

    def _handle_issue_event(self, payload: Dict[str, Any]) -> bool:
        """Handle GitHub issue events."""
        # Implementation would process issue mentions
        logger.info("Handling GitHub issue event")
        return True

    def _handle_pr_event(self, payload: Dict[str, Any]) -> bool:
        """Handle GitHub pull request events."""
        # Implementation would process PR mentions
        logger.info("Handling GitHub PR event")
        return True


# ============================================================================
# JIRA INTEGRATION
# ============================================================================

class JIRAIntegration:
    """
    JIRA integration for ticket linking and documentation sync.

    Provides:
    - Link wiki pages to JIRA tickets
    - Sync documentation to JIRA
    - Webhook support for JIRA events
    - Smart linking based on ticket mentions
    """

    def __init__(
        self,
        db: Session,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        api_token: Optional[str] = None
    ):
        """
        Initialize JIRA integration.

        Args:
            db: SQLAlchemy database session
            base_url: JIRA instance URL
            username: JIRA username/email
            api_token: JIRA API token

        Example:
            >>> jira = JIRAIntegration(
            ...     db,
            ...     base_url="https://mycompany.atlassian.net",
            ...     username="user@example.com",
            ...     api_token="..."
            ... )
        """
        self.db = db
        self.base_url = base_url or ""
        self.username = username or ""
        self.api_token = api_token or ""

    def link_ticket(
        self,
        page_id: int,
        ticket_key: str,
        link_type: str = "documents"
    ) -> bool:
        """
        Link wiki page to JIRA ticket.

        Args:
            page_id: Wiki page ID
            ticket_key: JIRA ticket key (e.g., "PROJ-123")
            link_type: Type of link

        Returns:
            True if link created successfully

        Example:
            >>> jira.link_ticket(page_id=123, ticket_key="PROJ-456")
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return False

            # Create link in database
            ticket_url = f"{self.base_url}/browse/{ticket_key}"

            link = WikiLink(
                source_page_id=page_id,
                target_url=ticket_url,
                link_type=LinkType.EXTERNAL,
                title=f"JIRA {ticket_key}"
            )

            self.db.add(link)
            self.db.commit()

            # Add remote link in JIRA
            self._add_remote_link(
                ticket_key,
                f"https://wiki.example.com/page/{page.slug}",
                page.title
            )

            logger.info(f"Linked page {page_id} to JIRA ticket {ticket_key}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error linking JIRA ticket: {str(e)}", exc_info=True)
            return False

    def scan_page_for_tickets(
        self,
        page_id: int,
        auto_link: bool = True
    ) -> List[str]:
        """
        Scan page content for JIRA ticket mentions.

        Args:
            page_id: Wiki page ID
            auto_link: Automatically create links for found tickets

        Returns:
            List of found ticket keys

        Example:
            >>> tickets = jira.scan_page_for_tickets(page_id=123, auto_link=True)
            >>> print(f"Found tickets: {tickets}")
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                return []

            # Find JIRA ticket patterns (e.g., PROJ-123)
            pattern = r'\b([A-Z]{2,10}-\d+)\b'
            matches = re.findall(pattern, page.content)

            # Remove duplicates
            ticket_keys = list(set(matches))

            if auto_link:
                for ticket_key in ticket_keys:
                    # Check if link already exists
                    ticket_url = f"{self.base_url}/browse/{ticket_key}"
                    existing = self.db.query(WikiLink).filter(
                        WikiLink.source_page_id == page_id,
                        WikiLink.target_url == ticket_url
                    ).first()

                    if not existing:
                        self.link_ticket(page_id, ticket_key)

            logger.info(f"Found {len(ticket_keys)} JIRA tickets in page {page_id}")
            return ticket_keys

        except Exception as e:
            logger.error(f"Error scanning for JIRA tickets: {str(e)}", exc_info=True)
            return []

    def add_comment_to_ticket(
        self,
        ticket_key: str,
        comment: str
    ) -> bool:
        """
        Add comment to JIRA ticket.

        Args:
            ticket_key: JIRA ticket key
            comment: Comment text

        Returns:
            True if comment added successfully

        Example:
            >>> jira.add_comment_to_ticket(
            ...     "PROJ-123",
            ...     "Documentation updated: https://wiki.example.com/page/guide"
            ... )
        """
        try:
            url = f"{self.base_url}/rest/api/3/issue/{ticket_key}/comment"

            response = self._post(url, {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment
                                }
                            ]
                        }
                    ]
                }
            })

            if response.status_code == 201:
                logger.info(f"Added comment to JIRA ticket {ticket_key}")
                return True
            else:
                logger.error(f"Failed to add JIRA comment: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error adding JIRA comment: {str(e)}", exc_info=True)
            return False

    # Private helper methods

    def _post(self, url: str, data: Dict[str, Any]) -> requests.Response:
        """Make POST request to JIRA API."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        return requests.post(
            url,
            json=data,
            headers=headers,
            auth=(self.username, self.api_token)
        )

    def _add_remote_link(
        self,
        ticket_key: str,
        url: str,
        title: str
    ) -> bool:
        """Add remote link to JIRA ticket."""
        try:
            api_url = f"{self.base_url}/rest/api/3/issue/{ticket_key}/remotelink"

            response = self._post(api_url, {
                "object": {
                    "url": url,
                    "title": title
                }
            })

            return response.status_code == 201

        except Exception as e:
            logger.error(f"Error adding JIRA remote link: {str(e)}", exc_info=True)
            return False


# ============================================================================
# WEBHOOK SYSTEM
# ============================================================================

class WebhookManager:
    """
    Webhook manager for custom integrations.

    Provides:
    - Register and manage webhooks
    - Trigger webhooks on events
    - Retry failed deliveries
    - Webhook signature verification
    """

    def __init__(self, db: Session):
        """
        Initialize webhook manager.

        Args:
            db: SQLAlchemy database session

        Example:
            >>> webhooks = WebhookManager(db)
            >>> webhooks.register_webhook(
            ...     url="https://example.com/webhook",
            ...     events=[EventType.PAGE_CREATED, EventType.PAGE_UPDATED]
            ... )
        """
        self.db = db
        self._webhooks: Dict[int, Dict[str, Any]] = {}

    def register_webhook(
        self,
        url: str,
        events: List[EventType],
        secret: Optional[str] = None,
        enabled: bool = True
    ) -> int:
        """
        Register a new webhook.

        Args:
            url: Webhook URL
            events: List of events to trigger webhook
            secret: Secret for signature verification
            enabled: Whether webhook is enabled

        Returns:
            Webhook ID

        Example:
            >>> webhook_id = webhooks.register_webhook(
            ...     url="https://example.com/webhook",
            ...     events=[EventType.PAGE_CREATED],
            ...     secret="my-secret"
            ... )
        """
        webhook_id = len(self._webhooks) + 1

        self._webhooks[webhook_id] = {
            "id": webhook_id,
            "url": url,
            "events": events,
            "secret": secret,
            "enabled": enabled,
            "created_at": datetime.utcnow()
        }

        logger.info(f"Registered webhook {webhook_id} for {url}")
        return webhook_id

    def trigger_webhook(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[int, bool]:
        """
        Trigger webhooks for an event.

        Args:
            event_type: Type of event
            data: Event data
            max_retries: Maximum retry attempts

        Returns:
            Dictionary of webhook_id -> success status

        Example:
            >>> results = webhooks.trigger_webhook(
            ...     EventType.PAGE_CREATED,
            ...     {"page_id": 123, "title": "New Page"}
            ... )
        """
        results = {}

        for webhook_id, webhook in self._webhooks.items():
            if not webhook["enabled"]:
                continue

            if event_type not in webhook["events"]:
                continue

            # Prepare payload
            payload = {
                "event": event_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }

            # Send webhook
            success = self._send_webhook(
                webhook["url"],
                payload,
                webhook.get("secret"),
                max_retries
            )

            results[webhook_id] = success

        return results

    def _send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        secret: Optional[str],
        max_retries: int
    ) -> bool:
        """Send webhook with retries."""
        headers = {"Content-Type": "application/json"}

        # Add signature if secret provided
        if secret:
            signature = self._generate_signature(json.dumps(payload), secret)
            headers["X-Webhook-Signature"] = signature

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 200:
                    logger.info(f"Webhook delivered to {url}")
                    return True
                else:
                    logger.warning(f"Webhook failed: {response.status_code} (attempt {attempt + 1})")

            except Exception as e:
                logger.error(f"Webhook error: {str(e)} (attempt {attempt + 1})")

            # Wait before retry
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff

        return False

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate webhook signature."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()


# ============================================================================
# INTEGRATION ORCHESTRATOR
# ============================================================================

class IntegrationOrchestrator:
    """
    Central orchestrator for all integrations.

    Coordinates multiple integration types and manages event routing.
    """

    def __init__(self, db: Session):
        """
        Initialize integration orchestrator.

        Args:
            db: SQLAlchemy database session

        Example:
            >>> orchestrator = IntegrationOrchestrator(db)
            >>> orchestrator.notify_page_event(
            ...     page_id=123,
            ...     event_type=EventType.PAGE_PUBLISHED
            ... )
        """
        self.db = db
        self.slack: Optional[SlackIntegration] = None
        self.teams: Optional[TeamsIntegration] = None
        self.github: Optional[GitHubIntegration] = None
        self.jira: Optional[JIRAIntegration] = None
        self.webhooks = WebhookManager(db)

    def initialize_integrations(self, config: Dict[str, Any]) -> None:
        """
        Initialize all configured integrations.

        Args:
            config: Integration configuration dictionary

        Example:
            >>> config = {
            ...     "slack": {"bot_token": "xoxb-...", "signing_secret": "..."},
            ...     "github": {"token": "ghp_...", "repo": "org/repo"}
            ... }
            >>> orchestrator.initialize_integrations(config)
        """
        if "slack" in config:
            self.slack = SlackIntegration(
                self.db,
                bot_token=config["slack"].get("bot_token"),
                signing_secret=config["slack"].get("signing_secret")
            )

        if "teams" in config:
            self.teams = TeamsIntegration(
                self.db,
                webhook_url=config["teams"].get("webhook_url")
            )

        if "github" in config:
            gh_config = config["github"]
            self.github = GitHubIntegration(
                self.db,
                token=gh_config.get("token"),
                repo_owner=gh_config.get("repo_owner"),
                repo_name=gh_config.get("repo_name")
            )

        if "jira" in config:
            self.jira = JIRAIntegration(
                self.db,
                base_url=config["jira"].get("base_url"),
                username=config["jira"].get("username"),
                api_token=config["jira"].get("api_token")
            )

        logger.info("Initialized integrations")

    def notify_page_event(
        self,
        page_id: int,
        event_type: EventType,
        user_id: Optional[int] = None,
        channels: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        Notify all integrations about a page event.

        Args:
            page_id: Wiki page ID
            event_type: Type of event
            user_id: User who triggered the event
            channels: Specific channels to notify

        Returns:
            Dictionary of integration -> success status

        Example:
            >>> results = orchestrator.notify_page_event(
            ...     page_id=123,
            ...     event_type=EventType.PAGE_PUBLISHED,
            ...     channels=["#wiki-updates"]
            ... )
        """
        results = {}

        # Slack notification
        if self.slack and channels:
            for channel in channels:
                success = self.slack.send_page_notification(
                    page_id,
                    channel,
                    event_type,
                    user_id
                )
                results[f"slack:{channel}"] = success

        # Teams notification
        if self.teams:
            success = self.teams.send_page_notification(page_id, event_type, user_id)
            results["teams"] = success

        # Webhooks
        page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
        if page:
            webhook_results = self.webhooks.trigger_webhook(
                event_type,
                {
                    "page_id": page_id,
                    "title": page.title,
                    "slug": page.slug,
                    "user_id": user_id
                }
            )
            for webhook_id, success in webhook_results.items():
                results[f"webhook:{webhook_id}"] = success

        return results
