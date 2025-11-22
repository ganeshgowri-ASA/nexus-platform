"""
Lead Generation Module for NEXUS Platform.

This module provides comprehensive lead generation capabilities including:
- Form capture and landing pages
- Popups and chatbot lead capture
- Lead validation and enrichment
- Scoring and qualification
- Routing and nurturing
- Analytics and reporting
"""

from .lead_types import (
    Lead,
    LeadSource,
    LeadStatus,
    LeadScore,
    LeadActivity,
    Touchpoint,
    Conversion,
)

__all__ = [
    "Lead",
    "LeadSource",
    "LeadStatus",
    "LeadScore",
    "LeadActivity",
    "Touchpoint",
    "Conversion",
]
