"""
Unit tests for campaign service.

This module tests campaign service functionality.
"""
import pytest
from uuid import uuid4

from src.services.marketing.campaign_service import CampaignService
from src.schemas.marketing.campaign_schema import CampaignCreate
from config.constants import CampaignType, CampaignStatus


@pytest.mark.asyncio
async def test_create_campaign(test_db, test_workspace, test_user):
    """Test campaign creation."""
    service = CampaignService(test_db)

    campaign_data = CampaignCreate(
        name="Test Campaign",
        description="This is a test campaign",
        type=CampaignType.EMAIL,
        subject="Test Subject",
        content="<h1>Test Content</h1>",
        from_name="Test Sender",
        from_email="sender@example.com",
    )

    campaign = await service.create_campaign(
        campaign_data=campaign_data,
        workspace_id=test_workspace.id,
        user_id=test_user.id,
    )

    assert campaign.id is not None
    assert campaign.name == "Test Campaign"
    assert campaign.status == CampaignStatus.DRAFT
    assert campaign.workspace_id == test_workspace.id
    assert campaign.created_by == test_user.id


@pytest.mark.asyncio
async def test_get_campaign(test_db, test_workspace, test_user):
    """Test getting a campaign by ID."""
    service = CampaignService(test_db)

    # Create campaign
    campaign_data = CampaignCreate(
        name="Test Campaign",
        type=CampaignType.EMAIL,
        subject="Test Subject",
        content="<h1>Test Content</h1>",
    )

    created_campaign = await service.create_campaign(
        campaign_data=campaign_data,
        workspace_id=test_workspace.id,
        user_id=test_user.id,
    )

    # Get campaign
    retrieved_campaign = await service.get_campaign(
        campaign_id=created_campaign.id,
        workspace_id=test_workspace.id,
    )

    assert retrieved_campaign.id == created_campaign.id
    assert retrieved_campaign.name == created_campaign.name


@pytest.mark.asyncio
async def test_list_campaigns(test_db, test_workspace, test_user):
    """Test listing campaigns."""
    service = CampaignService(test_db)

    # Create multiple campaigns
    for i in range(3):
        campaign_data = CampaignCreate(
            name=f"Test Campaign {i}",
            type=CampaignType.EMAIL,
            subject=f"Test Subject {i}",
            content=f"<h1>Test Content {i}</h1>",
        )

        await service.create_campaign(
            campaign_data=campaign_data,
            workspace_id=test_workspace.id,
            user_id=test_user.id,
        )

    # List campaigns
    result = await service.list_campaigns(
        workspace_id=test_workspace.id,
        page=1,
        page_size=10,
    )

    assert len(result["campaigns"]) == 3
    assert result["total"] == 3
    assert result["page"] == 1


@pytest.mark.asyncio
async def test_get_campaign_metrics(test_db, test_workspace, test_user):
    """Test getting campaign metrics."""
    service = CampaignService(test_db)

    # Create campaign
    campaign_data = CampaignCreate(
        name="Test Campaign",
        type=CampaignType.EMAIL,
        subject="Test Subject",
        content="<h1>Test Content</h1>",
    )

    campaign = await service.create_campaign(
        campaign_data=campaign_data,
        workspace_id=test_workspace.id,
        user_id=test_user.id,
    )

    # Get metrics
    metrics = await service.get_campaign_metrics(
        campaign_id=campaign.id,
        workspace_id=test_workspace.id,
    )

    assert metrics.total_recipients == 0
    assert metrics.total_sent == 0
    assert metrics.open_rate == 0.0
    assert metrics.click_rate == 0.0
