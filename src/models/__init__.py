"""
Models package for NEXUS Platform.

This package contains all database models for the application.
"""
from src.models.base import User, Workspace
from src.models.campaign import Campaign, CampaignMessage, EmailTemplate, ABTest
from src.models.contact import Contact, ContactList, Tag, Segment, ContactEvent
from src.models.automation import (
    Automation,
    AutomationExecution,
    DripCampaign,
    DripEnrollment,
    WorkflowNode,
)
from src.models.analytics import (
    CampaignAnalytics,
    LinkClick,
    Attribution,
    EventLog,
)

__all__ = [
    # Base models
    "User",
    "Workspace",
    # Campaign models
    "Campaign",
    "CampaignMessage",
    "EmailTemplate",
    "ABTest",
    # Contact models
    "Contact",
    "ContactList",
    "Tag",
    "Segment",
    "ContactEvent",
    # Automation models
    "Automation",
    "AutomationExecution",
    "DripCampaign",
    "DripEnrollment",
    "WorkflowNode",
    # Analytics models
    "CampaignAnalytics",
    "LinkClick",
    "Attribution",
    "EventLog",
]
