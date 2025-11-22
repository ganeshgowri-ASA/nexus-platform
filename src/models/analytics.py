"""
Analytics models for marketing automation.

This module contains models for tracking and analyzing campaign performance.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.core.database import Base


class CampaignAnalytics(Base):
    """
    Daily campaign analytics aggregation.

    Attributes:
        id: Analytics ID
        campaign_id: Associated campaign ID
        date: Analytics date
        sent_count: Messages sent
        delivered_count: Messages delivered
        opened_count: Messages opened
        clicked_count: Messages clicked
        bounced_count: Messages bounced
        unsubscribed_count: Unsubscribes
        open_rate: Open rate percentage
        click_rate: Click rate percentage
        bounce_rate: Bounce rate percentage
        conversion_count: Conversions
        conversion_rate: Conversion rate percentage
        revenue: Revenue generated
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "campaign_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Counts
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    bounced_count = Column(Integer, default=0)
    unsubscribed_count = Column(Integer, default=0)

    # Rates
    open_rate = Column(Float, default=0.0)
    click_rate = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)

    # Conversions
    conversion_count = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<CampaignAnalytics(campaign_id={self.campaign_id}, date={self.date})>"


class LinkClick(Base):
    """
    Link click tracking.

    Attributes:
        id: Click ID
        campaign_id: Associated campaign ID
        contact_id: Contact who clicked
        message_id: Associated message ID
        url: Clicked URL
        clicked_at: Click timestamp
        user_agent: User agent string
        ip_address: IP address
        metadata: Additional metadata (JSON)
        created_at: Creation timestamp
    """

    __tablename__ = "link_clicks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("campaign_messages.id"), index=True)
    url = Column(Text, nullable=False)
    clicked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_agent = Column(Text)
    ip_address = Column(String(45))
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<LinkClick(id={self.id}, url={self.url})>"


class Attribution(Base):
    """
    Multi-touch attribution tracking.

    Attributes:
        id: Attribution ID
        workspace_id: Associated workspace ID
        contact_id: Associated contact ID
        conversion_event: Conversion event type
        conversion_value: Conversion value/revenue
        touchpoints: Array of touchpoint data (JSON)
        attribution_model: Attribution model used
        converted_at: Conversion timestamp
        created_at: Creation timestamp
    """

    __tablename__ = "attributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=False, index=True)
    conversion_event = Column(String(100), nullable=False)
    conversion_value = Column(Float, default=0.0)
    touchpoints = Column(JSON, nullable=False)  # Array of campaign/channel interactions
    attribution_model = Column(String(50), default="last_touch")
    converted_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Attribution(id={self.id}, event={self.conversion_event})>"


class EventLog(Base):
    """
    System event logging for audit trail.

    Attributes:
        id: Event ID
        workspace_id: Associated workspace ID
        event_type: Event type
        entity_type: Entity type (campaign, automation, contact)
        entity_id: Entity ID
        user_id: User who triggered event
        event_data: Event data (JSON)
        ip_address: IP address
        user_agent: User agent
        created_at: Creation timestamp
    """

    __tablename__ = "event_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_data = Column(JSON, default={})
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<EventLog(id={self.id}, type={self.event_type})>"
