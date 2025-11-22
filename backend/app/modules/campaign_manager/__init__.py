"""
Campaign Manager Module for NEXUS Platform.

This module provides comprehensive campaign management capabilities including:
- Campaign planning and execution
- Budget management and allocation
- Creative asset library
- Multi-channel orchestration
- Team collaboration
- Timeline and milestone tracking
- Performance analytics
- AI-powered insights and optimization
"""

from app.modules.campaign_manager.router import router
from app.modules.campaign_manager.service import (
    CampaignService,
    ChannelService,
    AssetService,
    TeamService,
    MilestoneService,
    AnalyticsService,
)
from app.modules.campaign_manager.ai_service import AIService

__all__ = [
    "router",
    "CampaignService",
    "ChannelService",
    "AssetService",
    "TeamService",
    "MilestoneService",
    "AnalyticsService",
    "AIService",
]
