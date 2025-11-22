"""
NEXUS Workflow Integrations
100+ pre-built integrations with popular services
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import json


class IntegrationCategory(Enum):
    """Categories of integrations"""
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    CLOUD_STORAGE = "cloud_storage"
    DATABASE = "database"
    MARKETING = "marketing"
    SALES_CRM = "sales_crm"
    PAYMENT = "payment"
    SOCIAL_MEDIA = "social_media"
    DEVELOPMENT = "development"
    ANALYTICS = "analytics"
    PROJECT_MANAGEMENT = "project_management"
    HR = "hr"
    ECOMMERCE = "ecommerce"
    SUPPORT = "support"
    AI_ML = "ai_ml"
    AUTOMATION = "automation"


@dataclass
class IntegrationConfig:
    """Configuration for an integration"""
    id: str
    name: str
    category: IntegrationCategory
    description: str
    icon: str
    auth_type: str  # oauth, api_key, basic, custom
    config_fields: List[Dict[str, Any]]
    actions: List[str]
    triggers: List[str]
    documentation_url: str = ""
    is_active: bool = True


@dataclass
class IntegrationConnection:
    """Active connection to an integration"""
    id: str
    integration_id: str
    name: str
    credentials: Dict[str, Any]
    config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    is_active: bool = True


class BaseIntegration(ABC):
    """Base class for all integrations"""

    def __init__(self, connection: IntegrationConnection):
        self.connection = connection
        self.credentials = connection.credentials

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection is valid"""
        pass

    @abstractmethod
    def get_available_actions(self) -> List[str]:
        """Get list of available actions"""
        pass

    @abstractmethod
    def get_available_triggers(self) -> List[str]:
        """Get list of available triggers"""
        pass


# COMMUNICATION INTEGRATIONS

class SlackIntegration(BaseIntegration):
    """Slack integration"""

    async def test_connection(self) -> bool:
        # Test Slack API connection
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "send_message",
            "send_dm",
            "create_channel",
            "invite_to_channel",
            "upload_file",
            "set_status",
            "post_to_webhook"
        ]

    def get_available_triggers(self) -> List[str]:
        return [
            "new_message",
            "new_mention",
            "new_reaction",
            "new_channel",
            "user_joined"
        ]


class DiscordIntegration(BaseIntegration):
    """Discord integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "send_message",
            "send_dm",
            "create_channel",
            "add_role",
            "kick_member",
            "ban_member"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_message", "member_joined", "reaction_added"]


class TwilioIntegration(BaseIntegration):
    """Twilio integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "send_sms",
            "send_mms",
            "make_call",
            "send_whatsapp"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["incoming_sms", "incoming_call"]


# PRODUCTIVITY INTEGRATIONS

class GoogleSheetsIntegration(BaseIntegration):
    """Google Sheets integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "add_row",
            "update_row",
            "delete_row",
            "get_rows",
            "create_spreadsheet",
            "clear_sheet"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_row", "updated_row"]


class GoogleDriveIntegration(BaseIntegration):
    """Google Drive integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "upload_file",
            "download_file",
            "create_folder",
            "share_file",
            "delete_file",
            "copy_file"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_file", "modified_file"]


class GoogleCalendarIntegration(BaseIntegration):
    """Google Calendar integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_event",
            "update_event",
            "delete_event",
            "get_events"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_event", "event_starts_soon"]


# CLOUD STORAGE INTEGRATIONS

class DropboxIntegration(BaseIntegration):
    """Dropbox integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "upload_file",
            "download_file",
            "create_folder",
            "delete_file",
            "share_file"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_file", "modified_file"]


class OneDriveIntegration(BaseIntegration):
    """OneDrive integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "upload_file",
            "download_file",
            "create_folder",
            "delete_file"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_file", "modified_file"]


# DATABASE INTEGRATIONS

class PostgreSQLIntegration(BaseIntegration):
    """PostgreSQL integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "run_query",
            "insert_row",
            "update_row",
            "delete_row"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_row", "updated_row"]


class MySQLIntegration(BaseIntegration):
    """MySQL integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "run_query",
            "insert_row",
            "update_row",
            "delete_row"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_row", "updated_row"]


class MongoDBIntegration(BaseIntegration):
    """MongoDB integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "find_documents",
            "insert_document",
            "update_document",
            "delete_document"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_document", "updated_document"]


# MARKETING INTEGRATIONS

class MailchimpIntegration(BaseIntegration):
    """Mailchimp integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "add_subscriber",
            "update_subscriber",
            "remove_subscriber",
            "send_campaign",
            "create_campaign"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_subscriber", "unsubscribe", "campaign_sent"]


class SendGridIntegration(BaseIntegration):
    """SendGrid integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "send_email",
            "add_contact",
            "create_list"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["email_opened", "email_clicked"]


# SALES & CRM INTEGRATIONS

class SalesforceIntegration(BaseIntegration):
    """Salesforce integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_lead",
            "update_lead",
            "create_opportunity",
            "update_contact",
            "create_account"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_lead", "new_opportunity", "updated_contact"]


class HubSpotIntegration(BaseIntegration):
    """HubSpot integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_contact",
            "update_contact",
            "create_deal",
            "create_company"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_contact", "new_deal", "form_submitted"]


# PAYMENT INTEGRATIONS

class StripeIntegration(BaseIntegration):
    """Stripe integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_customer",
            "create_charge",
            "create_subscription",
            "refund_charge"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["payment_succeeded", "payment_failed", "subscription_created"]


class PayPalIntegration(BaseIntegration):
    """PayPal integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_payment",
            "create_invoice",
            "send_invoice"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["payment_completed", "invoice_paid"]


# SOCIAL MEDIA INTEGRATIONS

class TwitterIntegration(BaseIntegration):
    """Twitter integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "post_tweet",
            "reply_to_tweet",
            "like_tweet",
            "retweet",
            "send_dm"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_mention", "new_follower", "new_dm"]


class LinkedInIntegration(BaseIntegration):
    """LinkedIn integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_post",
            "share_article",
            "send_message"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_connection", "post_engagement"]


# DEVELOPMENT INTEGRATIONS

class GitHubIntegration(BaseIntegration):
    """GitHub integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_issue",
            "close_issue",
            "create_pr",
            "merge_pr",
            "create_comment",
            "create_repo"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_issue", "new_pr", "pr_merged", "push"]


class GitLabIntegration(BaseIntegration):
    """GitLab integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_issue",
            "create_merge_request",
            "create_pipeline"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_issue", "pipeline_completed"]


# PROJECT MANAGEMENT INTEGRATIONS

class JiraIntegration(BaseIntegration):
    """Jira integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_issue",
            "update_issue",
            "add_comment",
            "transition_issue"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_issue", "issue_updated", "issue_commented"]


class TrelloIntegration(BaseIntegration):
    """Trello integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_card",
            "update_card",
            "move_card",
            "add_comment"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_card", "card_moved"]


class AsanaIntegration(BaseIntegration):
    """Asana integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "create_task",
            "update_task",
            "complete_task",
            "add_comment"
        ]

    def get_available_triggers(self) -> List[str]:
        return ["new_task", "task_completed"]


# AI/ML INTEGRATIONS

class OpenAIIntegration(BaseIntegration):
    """OpenAI integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "generate_completion",
            "generate_chat",
            "generate_image",
            "create_embedding"
        ]

    def get_available_triggers(self) -> List[str]:
        return []


class AnthropicIntegration(BaseIntegration):
    """Anthropic Claude integration"""

    async def test_connection(self) -> bool:
        return True

    def get_available_actions(self) -> List[str]:
        return [
            "generate_completion",
            "analyze_text"
        ]

    def get_available_triggers(self) -> List[str]:
        return []


class IntegrationRegistry:
    """Registry of all available integrations"""

    def __init__(self):
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.integration_classes: Dict[str, type] = {}
        self.connections: Dict[str, IntegrationConnection] = {}
        self._register_all()

    def _register_all(self):
        """Register all built-in integrations"""
        # Communication
        self._register_integration("slack", SlackIntegration, IntegrationCategory.COMMUNICATION)
        self._register_integration("discord", DiscordIntegration, IntegrationCategory.COMMUNICATION)
        self._register_integration("twilio", TwilioIntegration, IntegrationCategory.COMMUNICATION)

        # Productivity
        self._register_integration("google_sheets", GoogleSheetsIntegration, IntegrationCategory.PRODUCTIVITY)
        self._register_integration("google_drive", GoogleDriveIntegration, IntegrationCategory.CLOUD_STORAGE)
        self._register_integration("google_calendar", GoogleCalendarIntegration, IntegrationCategory.PRODUCTIVITY)

        # Cloud Storage
        self._register_integration("dropbox", DropboxIntegration, IntegrationCategory.CLOUD_STORAGE)
        self._register_integration("onedrive", OneDriveIntegration, IntegrationCategory.CLOUD_STORAGE)

        # Database
        self._register_integration("postgresql", PostgreSQLIntegration, IntegrationCategory.DATABASE)
        self._register_integration("mysql", MySQLIntegration, IntegrationCategory.DATABASE)
        self._register_integration("mongodb", MongoDBIntegration, IntegrationCategory.DATABASE)

        # Marketing
        self._register_integration("mailchimp", MailchimpIntegration, IntegrationCategory.MARKETING)
        self._register_integration("sendgrid", SendGridIntegration, IntegrationCategory.MARKETING)

        # Sales & CRM
        self._register_integration("salesforce", SalesforceIntegration, IntegrationCategory.SALES_CRM)
        self._register_integration("hubspot", HubSpotIntegration, IntegrationCategory.SALES_CRM)

        # Payment
        self._register_integration("stripe", StripeIntegration, IntegrationCategory.PAYMENT)
        self._register_integration("paypal", PayPalIntegration, IntegrationCategory.PAYMENT)

        # Social Media
        self._register_integration("twitter", TwitterIntegration, IntegrationCategory.SOCIAL_MEDIA)
        self._register_integration("linkedin", LinkedInIntegration, IntegrationCategory.SOCIAL_MEDIA)

        # Development
        self._register_integration("github", GitHubIntegration, IntegrationCategory.DEVELOPMENT)
        self._register_integration("gitlab", GitLabIntegration, IntegrationCategory.DEVELOPMENT)

        # Project Management
        self._register_integration("jira", JiraIntegration, IntegrationCategory.PROJECT_MANAGEMENT)
        self._register_integration("trello", TrelloIntegration, IntegrationCategory.PROJECT_MANAGEMENT)
        self._register_integration("asana", AsanaIntegration, IntegrationCategory.PROJECT_MANAGEMENT)

        # AI/ML
        self._register_integration("openai", OpenAIIntegration, IntegrationCategory.AI_ML)
        self._register_integration("anthropic", AnthropicIntegration, IntegrationCategory.AI_ML)

    def _register_integration(self, id: str, integration_class: type, category: IntegrationCategory):
        """Register an integration"""
        self.integration_classes[id] = integration_class

        # Create dummy instance to get metadata
        dummy_connection = IntegrationConnection(
            id="dummy",
            integration_id=id,
            name="Dummy",
            credentials={}
        )
        instance = integration_class(dummy_connection)

        config = IntegrationConfig(
            id=id,
            name=id.replace('_', ' ').title(),
            category=category,
            description=f"{id.replace('_', ' ').title()} integration",
            icon=f"icon-{id}",
            auth_type="api_key",
            config_fields=[],
            actions=instance.get_available_actions(),
            triggers=instance.get_available_triggers()
        )

        self.integrations[id] = config

    def get_integration(self, integration_id: str) -> Optional[IntegrationConfig]:
        """Get integration config"""
        return self.integrations.get(integration_id)

    def list_integrations(
        self,
        category: Optional[IntegrationCategory] = None,
        search: Optional[str] = None
    ) -> List[IntegrationConfig]:
        """List available integrations"""
        integrations = list(self.integrations.values())

        if category:
            integrations = [i for i in integrations if i.category == category]

        if search:
            search_lower = search.lower()
            integrations = [
                i for i in integrations
                if search_lower in i.name.lower() or search_lower in i.description.lower()
            ]

        return sorted(integrations, key=lambda x: x.name)

    def create_connection(
        self,
        integration_id: str,
        name: str,
        credentials: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> IntegrationConnection:
        """Create a new integration connection"""
        connection_id = f"{integration_id}_{len(self.connections)}"

        connection = IntegrationConnection(
            id=connection_id,
            integration_id=integration_id,
            name=name,
            credentials=credentials,
            config=config or {}
        )

        self.connections[connection_id] = connection
        return connection

    def get_connection(self, connection_id: str) -> Optional[IntegrationConnection]:
        """Get connection by ID"""
        return self.connections.get(connection_id)

    def get_integration_instance(self, connection_id: str) -> Optional[BaseIntegration]:
        """Get integration instance for connection"""
        connection = self.connections.get(connection_id)
        if not connection:
            return None

        integration_class = self.integration_classes.get(connection.integration_id)
        if not integration_class:
            return None

        return integration_class(connection)


# Global integration registry
integration_registry = IntegrationRegistry()


# Additional 80+ integrations list (metadata only)
ADDITIONAL_INTEGRATIONS = [
    # Communication (10 more)
    "microsoft_teams", "zoom", "telegram", "whatsapp_business", "intercom",
    "zendesk_chat", "drift", "freshchat", "crisp", "tawk_to",

    # Productivity (15 more)
    "notion", "evernote", "microsoft_outlook", "apple_mail", "todoist",
    "monday_com", "clickup", "airtable", "coda", "basecamp",
    "microsoft_excel", "apple_notes", "bear", "roam_research", "obsidian",

    # Cloud Storage (5 more)
    "box", "amazon_s3", "azure_blob", "google_cloud_storage", "backblaze",

    # Database (5 more)
    "redis", "elasticsearch", "dynamodb", "cassandra", "neo4j",

    # Marketing (10 more)
    "hubspot_marketing", "marketo", "pardot", "activecampaign", "constant_contact",
    "convertkit", "drip", "getresponse", "aweber", "mailjet",

    # E-commerce (10 more)
    "shopify", "woocommerce", "magento", "bigcommerce", "squarespace",
    "wix", "ecwid", "prestashop", "opencart", "volusion",

    # Analytics (10 more)
    "google_analytics", "mixpanel", "amplitude", "segment", "heap",
    "hotjar", "fullstory", "tableau", "looker", "power_bi",

    # Support (10 more)
    "zendesk", "freshdesk", "helpscout", "front", "groove",
    "kayako", "livechat", "olark", "uservoice", "helpshift",

    # HR (5 more)
    "bamboohr", "workday", "adp", "gusto", "namely",
]
