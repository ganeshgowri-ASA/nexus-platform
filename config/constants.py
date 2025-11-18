"""
Application constants for NEXUS Platform.

This module contains all constant values used throughout the application,
organized by domain.
"""
from enum import Enum


# Campaign Types
class CampaignType(str, Enum):
    """Campaign type enumeration."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SOCIAL = "social"
    MULTI_CHANNEL = "multi_channel"


# Campaign Status
class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


# Contact Status
class ContactStatus(str, Enum):
    """Contact subscription status."""
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


# Automation Status
class AutomationStatus(str, Enum):
    """Automation workflow status."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


# Trigger Types
class TriggerType(str, Enum):
    """Automation trigger types."""
    EVENT = "event"
    TIME = "time"
    MANUAL = "manual"
    BEHAVIORAL = "behavioral"
    CONDITIONAL = "conditional"


# Action Types
class ActionType(str, Enum):
    """Automation action types."""
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    UPDATE_FIELD = "update_field"
    ADD_TO_LIST = "add_to_list"
    REMOVE_FROM_LIST = "remove_from_list"
    UPDATE_SCORE = "update_score"
    WAIT = "wait"
    WEBHOOK = "webhook"
    AI_PERSONALIZE = "ai_personalize"


# Message Status
class MessageStatus(str, Enum):
    """Campaign message delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    UNSUBSCRIBED = "unsubscribed"


# Event Types
class EventType(str, Enum):
    """Event log types."""
    CAMPAIGN_CREATED = "campaign_created"
    CAMPAIGN_UPDATED = "campaign_updated"
    CAMPAIGN_SENT = "campaign_sent"
    CAMPAIGN_COMPLETED = "campaign_completed"
    CONTACT_CREATED = "contact_created"
    CONTACT_UPDATED = "contact_updated"
    CONTACT_SUBSCRIBED = "contact_subscribed"
    CONTACT_UNSUBSCRIBED = "contact_unsubscribed"
    AUTOMATION_CREATED = "automation_created"
    AUTOMATION_TRIGGERED = "automation_triggered"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    SMS_SENT = "sms_sent"
    WEBHOOK_TRIGGERED = "webhook_triggered"


# Lead Scoring Attributes
class LeadScoringAttribute(str, Enum):
    """Attributes used for lead scoring."""
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"
    LINK_CLICK = "link_click"
    FORM_SUBMISSION = "form_submission"
    PAGE_VISIT = "page_visit"
    DOWNLOAD = "download"
    PURCHASE = "purchase"
    ENGAGEMENT_TIME = "engagement_time"


# Default Lead Scoring Points
LEAD_SCORING_POINTS = {
    LeadScoringAttribute.EMAIL_OPEN: 5,
    LeadScoringAttribute.EMAIL_CLICK: 10,
    LeadScoringAttribute.LINK_CLICK: 15,
    LeadScoringAttribute.FORM_SUBMISSION: 25,
    LeadScoringAttribute.PAGE_VISIT: 3,
    LeadScoringAttribute.DOWNLOAD: 20,
    LeadScoringAttribute.PURCHASE: 100,
    LeadScoringAttribute.ENGAGEMENT_TIME: 1,  # per minute
}

# Lead Score Thresholds
LEAD_SCORE_COLD = 0
LEAD_SCORE_WARM = 50
LEAD_SCORE_HOT = 100

# Segmentation Operators
class SegmentOperator(str, Enum):
    """Operators for segment conditions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


# A/B Test Types
class ABTestType(str, Enum):
    """A/B test variation types."""
    SUBJECT_LINE = "subject_line"
    CONTENT = "content"
    SEND_TIME = "send_time"
    FROM_NAME = "from_name"
    CTA = "cta"


# Default Email Templates
DEFAULT_EMAIL_TEMPLATES = {
    "welcome": {
        "subject": "Welcome to {{company_name}}!",
        "body": """
            <h1>Welcome {{first_name}}!</h1>
            <p>We're excited to have you on board.</p>
            <p>Get started by exploring our platform features.</p>
            <a href="{{dashboard_url}}">Go to Dashboard</a>
        """
    },
    "newsletter": {
        "subject": "{{newsletter_title}}",
        "body": """
            <h1>{{newsletter_title}}</h1>
            <p>{{newsletter_content}}</p>
            <p>Best regards,<br>{{company_name}} Team</p>
        """
    },
    "promotional": {
        "subject": "Special Offer: {{offer_title}}",
        "body": """
            <h1>{{offer_title}}</h1>
            <p>{{offer_description}}</p>
            <p><strong>Use code: {{promo_code}}</strong></p>
            <a href="{{offer_url}}">Claim Your Offer</a>
        """
    },
}

# Rate Limiting
MAX_CAMPAIGNS_PER_USER = 100
MAX_CONTACTS_PER_WORKSPACE = 100000
MAX_AUTOMATIONS_PER_WORKSPACE = 50
MAX_EMAILS_PER_HOUR = 1000

# Batch Processing
DEFAULT_BATCH_SIZE = 100
MAX_BATCH_SIZE = 1000

# Cache TTL (in seconds)
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 1800  # 30 minutes
CACHE_TTL_LONG = 3600  # 1 hour

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# File Upload
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_TYPES = [".csv", ".xlsx", ".json"]

# API Versions
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"
