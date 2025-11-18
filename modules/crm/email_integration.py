"""
CRM Email Integration Module - Email templates, tracking, sequences, and campaigns.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import hashlib


class EmailTemplateType(Enum):
    """Email template types."""
    COLD_OUTREACH = "cold_outreach"
    FOLLOW_UP = "follow_up"
    MEETING_REQUEST = "meeting_request"
    PROPOSAL = "proposal"
    THANK_YOU = "thank_you"
    NURTURE = "nurture"
    PROMOTIONAL = "promotional"
    NEWSLETTER = "newsletter"
    CUSTOM = "custom"


class EmailSequenceStatus(Enum):
    """Email sequence status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class CampaignStatus(Enum):
    """Campaign status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class EmailTemplate:
    """Email template entity."""
    id: str
    name: str
    template_type: EmailTemplateType
    subject: str
    body: str  # HTML or plain text

    # Personalization
    variables: List[str] = field(default_factory=list)  # e.g., {{first_name}}, {{company_name}}

    # Metadata
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Set[str] = field(default_factory=set)

    # Usage tracking
    times_used: int = 0
    last_used: Optional[datetime] = None

    # Performance metrics
    total_sent: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_replied: int = 0

    # Ownership
    created_by: Optional[str] = None
    is_shared: bool = False

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def open_rate(self) -> float:
        """Calculate open rate."""
        return (self.total_opened / self.total_sent * 100) if self.total_sent > 0 else 0.0

    @property
    def click_rate(self) -> float:
        """Calculate click rate."""
        return (self.total_clicked / self.total_sent * 100) if self.total_sent > 0 else 0.0

    @property
    def reply_rate(self) -> float:
        """Calculate reply rate."""
        return (self.total_replied / self.total_sent * 100) if self.total_sent > 0 else 0.0

    def render(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Render template with variables."""
        subject = self.subject
        body = self.body

        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, value)
            body = body.replace(placeholder, value)

        return {
            'subject': subject,
            'body': body,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'template_type': self.template_type.value,
            'subject': self.subject,
            'body': self.body,
            'variables': self.variables,
            'description': self.description,
            'category': self.category,
            'tags': list(self.tags),
            'times_used': self.times_used,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'total_sent': self.total_sent,
            'total_opened': self.total_opened,
            'total_clicked': self.total_clicked,
            'total_replied': self.total_replied,
            'open_rate': round(self.open_rate, 2),
            'click_rate': round(self.click_rate, 2),
            'reply_rate': round(self.reply_rate, 2),
            'created_by': self.created_by,
            'is_shared': self.is_shared,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


@dataclass
class EmailSequenceStep:
    """Step in an email sequence."""
    step_number: int
    template_id: str
    delay_days: int  # Days after previous step (0 for first step)
    subject: str
    body: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'step_number': self.step_number,
            'template_id': self.template_id,
            'delay_days': self.delay_days,
            'subject': self.subject,
            'body': self.body,
        }


@dataclass
class EmailSequence:
    """Email drip sequence."""
    id: str
    name: str
    description: Optional[str] = None
    status: EmailSequenceStatus = EmailSequenceStatus.DRAFT

    steps: List[EmailSequenceStep] = field(default_factory=list)

    # Enrollment criteria
    auto_enroll: bool = False
    stop_on_reply: bool = True

    # Performance
    total_enrolled: int = 0
    total_completed: int = 0
    total_replied: int = 0

    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'steps': [s.to_dict() for s in self.steps],
            'auto_enroll': self.auto_enroll,
            'stop_on_reply': self.stop_on_reply,
            'total_enrolled': self.total_enrolled,
            'total_completed': self.total_completed,
            'total_replied': self.total_replied,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


@dataclass
class EmailTracking:
    """Email tracking information."""
    email_id: str
    contact_id: str
    template_id: Optional[str] = None
    sequence_id: Optional[str] = None
    campaign_id: Optional[str] = None

    subject: str = ""
    sent_at: datetime = field(default_factory=datetime.now)

    # Engagement tracking
    opened: bool = False
    opened_at: Optional[datetime] = None
    open_count: int = 0

    clicked: bool = False
    clicked_at: Optional[datetime] = None
    click_count: int = 0

    replied: bool = False
    replied_at: Optional[datetime] = None

    bounced: bool = False
    unsubscribed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'email_id': self.email_id,
            'contact_id': self.contact_id,
            'template_id': self.template_id,
            'sequence_id': self.sequence_id,
            'campaign_id': self.campaign_id,
            'subject': self.subject,
            'sent_at': self.sent_at.isoformat(),
            'opened': self.opened,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'open_count': self.open_count,
            'clicked': self.clicked,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'click_count': self.click_count,
            'replied': self.replied,
            'replied_at': self.replied_at.isoformat() if self.replied_at else None,
            'bounced': self.bounced,
            'unsubscribed': self.unsubscribed,
        }


@dataclass
class EmailCampaign:
    """Email marketing campaign."""
    id: str
    name: str
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT

    # Content
    template_id: Optional[str] = None
    subject: str = ""
    body: str = ""

    # Targeting
    segment_ids: List[str] = field(default_factory=list)
    contact_ids: List[str] = field(default_factory=list)

    # Scheduling
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    # Performance
    total_recipients: int = 0
    total_sent: int = 0
    total_delivered: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_bounced: int = 0
    total_unsubscribed: int = 0

    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def delivery_rate(self) -> float:
        """Calculate delivery rate."""
        return (self.total_delivered / self.total_sent * 100) if self.total_sent > 0 else 0.0

    @property
    def open_rate(self) -> float:
        """Calculate open rate."""
        return (self.total_opened / self.total_delivered * 100) if self.total_delivered > 0 else 0.0

    @property
    def click_rate(self) -> float:
        """Calculate click rate."""
        return (self.total_clicked / self.total_delivered * 100) if self.total_delivered > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'template_id': self.template_id,
            'subject': self.subject,
            'body': self.body,
            'segment_ids': self.segment_ids,
            'contact_ids': self.contact_ids,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'total_recipients': self.total_recipients,
            'total_sent': self.total_sent,
            'total_delivered': self.total_delivered,
            'total_opened': self.total_opened,
            'total_clicked': self.total_clicked,
            'total_bounced': self.total_bounced,
            'total_unsubscribed': self.total_unsubscribed,
            'delivery_rate': round(self.delivery_rate, 2),
            'open_rate': round(self.open_rate, 2),
            'click_rate': round(self.click_rate, 2),
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class EmailIntegrationManager:
    """Manage email templates, sequences, campaigns, and tracking."""

    def __init__(self):
        """Initialize email integration manager."""
        self.templates: Dict[str, EmailTemplate] = {}
        self.sequences: Dict[str, EmailSequence] = {}
        self.campaigns: Dict[str, EmailCampaign] = {}
        self.tracking: Dict[str, EmailTracking] = {}  # email_id -> tracking

        self._contact_emails: Dict[str, List[str]] = {}  # contact_id -> [email_ids]

    # Template Management

    def create_template(self, template: EmailTemplate) -> EmailTemplate:
        """Create an email template."""
        # Extract variables from template
        template.variables = self._extract_variables(template.subject + " " + template.body)
        self.templates[template.id] = template
        return template

    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get a template by ID."""
        return self.templates.get(template_id)

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> Optional[EmailTemplate]:
        """Update a template."""
        template = self.templates.get(template_id)
        if not template:
            return None

        for key, value in updates.items():
            if hasattr(template, key):
                if key == 'template_type' and isinstance(value, str):
                    value = EmailTemplateType(value)
                setattr(template, key, value)

        # Re-extract variables if subject or body changed
        if 'subject' in updates or 'body' in updates:
            template.variables = self._extract_variables(template.subject + " " + template.body)

        template.updated_at = datetime.now()
        return template

    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    def list_templates(
        self,
        template_type: Optional[EmailTemplateType] = None,
        category: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> List[EmailTemplate]:
        """List email templates."""
        templates = list(self.templates.values())

        if template_type:
            templates = [t for t in templates if t.template_type == template_type]

        if category:
            templates = [t for t in templates if t.category == category]

        if created_by:
            templates = [t for t in templates if t.created_by == created_by]

        return sorted(templates, key=lambda t: t.updated_at, reverse=True)

    def _extract_variables(self, text: str) -> List[str]:
        """Extract template variables from text."""
        pattern = r'\{\{(\w+)\}\}'
        matches = re.findall(pattern, text)
        return list(set(matches))

    # Sequence Management

    def create_sequence(self, sequence: EmailSequence) -> EmailSequence:
        """Create an email sequence."""
        self.sequences[sequence.id] = sequence
        return sequence

    def get_sequence(self, sequence_id: str) -> Optional[EmailSequence]:
        """Get a sequence by ID."""
        return self.sequences.get(sequence_id)

    def update_sequence(self, sequence_id: str, updates: Dict[str, Any]) -> Optional[EmailSequence]:
        """Update a sequence."""
        sequence = self.sequences.get(sequence_id)
        if not sequence:
            return None

        for key, value in updates.items():
            if hasattr(sequence, key):
                if key == 'status' and isinstance(value, str):
                    value = EmailSequenceStatus(value)
                setattr(sequence, key, value)

        sequence.updated_at = datetime.now()
        return sequence

    def add_sequence_step(
        self,
        sequence_id: str,
        template_id: str,
        delay_days: int,
        subject: str,
        body: str
    ) -> Optional[EmailSequence]:
        """Add a step to a sequence."""
        sequence = self.sequences.get(sequence_id)
        if not sequence:
            return None

        step = EmailSequenceStep(
            step_number=len(sequence.steps) + 1,
            template_id=template_id,
            delay_days=delay_days,
            subject=subject,
            body=body,
        )
        sequence.steps.append(step)
        sequence.updated_at = datetime.now()
        return sequence

    # Campaign Management

    def create_campaign(self, campaign: EmailCampaign) -> EmailCampaign:
        """Create an email campaign."""
        self.campaigns[campaign.id] = campaign
        return campaign

    def get_campaign(self, campaign_id: str) -> Optional[EmailCampaign]:
        """Get a campaign by ID."""
        return self.campaigns.get(campaign_id)

    def update_campaign(self, campaign_id: str, updates: Dict[str, Any]) -> Optional[EmailCampaign]:
        """Update a campaign."""
        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return None

        for key, value in updates.items():
            if hasattr(campaign, key):
                if key == 'status' and isinstance(value, str):
                    value = CampaignStatus(value)
                setattr(campaign, key, value)

        campaign.updated_at = datetime.now()
        return campaign

    def schedule_campaign(
        self,
        campaign_id: str,
        scheduled_at: datetime
    ) -> Optional[EmailCampaign]:
        """Schedule a campaign."""
        return self.update_campaign(campaign_id, {
            'status': CampaignStatus.SCHEDULED,
            'scheduled_at': scheduled_at,
        })

    # Email Tracking

    def track_email_sent(
        self,
        email_id: str,
        contact_id: str,
        subject: str,
        template_id: Optional[str] = None,
        sequence_id: Optional[str] = None,
        campaign_id: Optional[str] = None
    ) -> EmailTracking:
        """Track a sent email."""
        tracking = EmailTracking(
            email_id=email_id,
            contact_id=contact_id,
            subject=subject,
            template_id=template_id,
            sequence_id=sequence_id,
            campaign_id=campaign_id,
        )
        self.tracking[email_id] = tracking

        # Update contact index
        if contact_id not in self._contact_emails:
            self._contact_emails[contact_id] = []
        self._contact_emails[contact_id].append(email_id)

        # Update template stats
        if template_id and template_id in self.templates:
            template = self.templates[template_id]
            template.total_sent += 1
            template.times_used += 1
            template.last_used = datetime.now()

        return tracking

    def track_email_opened(self, email_id: str) -> Optional[EmailTracking]:
        """Track email open."""
        tracking = self.tracking.get(email_id)
        if not tracking:
            return None

        if not tracking.opened:
            tracking.opened = True
            tracking.opened_at = datetime.now()

        tracking.open_count += 1

        # Update template stats
        if tracking.template_id and tracking.template_id in self.templates:
            template = self.templates[tracking.template_id]
            if tracking.open_count == 1:  # Only count unique opens
                template.total_opened += 1

        return tracking

    def track_email_clicked(self, email_id: str) -> Optional[EmailTracking]:
        """Track email click."""
        tracking = self.tracking.get(email_id)
        if not tracking:
            return None

        if not tracking.clicked:
            tracking.clicked = True
            tracking.clicked_at = datetime.now()

        tracking.click_count += 1

        # Update template stats
        if tracking.template_id and tracking.template_id in self.templates:
            template = self.templates[tracking.template_id]
            if tracking.click_count == 1:  # Only count unique clicks
                template.total_clicked += 1

        return tracking

    def track_email_replied(self, email_id: str) -> Optional[EmailTracking]:
        """Track email reply."""
        tracking = self.tracking.get(email_id)
        if not tracking:
            return None

        tracking.replied = True
        tracking.replied_at = datetime.now()

        # Update template stats
        if tracking.template_id and tracking.template_id in self.templates:
            template = self.templates[tracking.template_id]
            template.total_replied += 1

        return tracking

    def get_contact_email_history(self, contact_id: str) -> List[Dict[str, Any]]:
        """Get email history for a contact."""
        email_ids = self._contact_emails.get(contact_id, [])
        history = []

        for email_id in email_ids:
            if email_id in self.tracking:
                history.append(self.tracking[email_id].to_dict())

        # Sort by sent_at descending
        history.sort(key=lambda e: e['sent_at'], reverse=True)
        return history

    def get_engagement_stats(
        self,
        template_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get email engagement statistics."""
        emails = list(self.tracking.values())

        # Filter by template
        if template_id:
            emails = [e for e in emails if e.template_id == template_id]

        # Filter by campaign
        if campaign_id:
            emails = [e for e in emails if e.campaign_id == campaign_id]

        # Filter by date range
        if start_date:
            emails = [e for e in emails if e.sent_at >= start_date]
        if end_date:
            emails = [e for e in emails if e.sent_at <= end_date]

        total_sent = len(emails)
        total_opened = len([e for e in emails if e.opened])
        total_clicked = len([e for e in emails if e.clicked])
        total_replied = len([e for e in emails if e.replied])
        total_bounced = len([e for e in emails if e.bounced])

        return {
            'total_sent': total_sent,
            'total_opened': total_opened,
            'total_clicked': total_clicked,
            'total_replied': total_replied,
            'total_bounced': total_bounced,
            'open_rate': round((total_opened / total_sent * 100) if total_sent > 0 else 0, 2),
            'click_rate': round((total_clicked / total_sent * 100) if total_sent > 0 else 0, 2),
            'reply_rate': round((total_replied / total_sent * 100) if total_sent > 0 else 0, 2),
            'bounce_rate': round((total_bounced / total_sent * 100) if total_sent > 0 else 0, 2),
        }

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def get_statistics(self) -> Dict[str, Any]:
        """Get email integration statistics."""
        return {
            'total_templates': len(self.templates),
            'total_sequences': len(self.sequences),
            'total_campaigns': len(self.campaigns),
            'total_emails_tracked': len(self.tracking),
        }
