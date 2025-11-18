"""
Tests for advertising module.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.advertising.models import Campaign, AdPlatform, CampaignObjective, BidStrategy
from modules.advertising.services.campaign_service import CampaignService
from modules.advertising.schemas import CampaignCreate


@pytest.mark.asyncio
async def test_create_campaign(db_session: AsyncSession):
    """Test creating a campaign."""
    campaign_data = CampaignCreate(
        name="Test Campaign",
        platform=AdPlatform.GOOGLE_ADS,
        objective=CampaignObjective.CONVERSION,
        budget_type="daily",
        daily_budget=100.0,
        currency="USD",
        bid_strategy=BidStrategy.MANUAL_CPC,
        bid_amount=1.50
    )

    campaign = await CampaignService.create_campaign(db_session, campaign_data)

    assert campaign.id is not None
    assert campaign.name == "Test Campaign"
    assert campaign.platform == AdPlatform.GOOGLE_ADS
    assert campaign.daily_budget == 100.0


@pytest.mark.asyncio
async def test_update_campaign_metrics(db_session: AsyncSession):
    """Test updating campaign metrics."""
    # Create campaign
    campaign_data = CampaignCreate(
        name="Metrics Test Campaign",
        platform=AdPlatform.FACEBOOK_ADS,
        objective=CampaignObjective.LEAD_GENERATION,
        budget_type="daily",
        daily_budget=200.0,
        currency="USD",
        bid_strategy=BidStrategy.TARGET_CPA,
        target_cpa=10.0
    )

    campaign = await CampaignService.create_campaign(db_session, campaign_data)

    # Update metrics
    metrics = {
        "impressions": 10000,
        "clicks": 500,
        "conversions": 25,
        "spent": 250.0,
        "revenue": 1250.0
    }

    updated_campaign = await CampaignService.update_campaign_metrics(
        db_session,
        campaign.id,
        metrics
    )

    assert updated_campaign.impressions == 10000
    assert updated_campaign.clicks == 500
    assert updated_campaign.conversions == 25
    assert updated_campaign.ctr == 5.0  # (500/10000) * 100
    assert updated_campaign.cpc == 0.5  # 250/500
    assert updated_campaign.roas == 5.0  # 1250/250


@pytest.mark.asyncio
async def test_pause_and_activate_campaign(db_session: AsyncSession):
    """Test pausing and activating a campaign."""
    # Create campaign
    campaign_data = CampaignCreate(
        name="Pause Test Campaign",
        platform=AdPlatform.LINKEDIN_ADS,
        objective=CampaignObjective.AWARENESS,
        budget_type="daily",
        daily_budget=150.0,
        currency="USD",
        bid_strategy=BidStrategy.AUTOMATED
    )

    campaign = await CampaignService.create_campaign(db_session, campaign_data)

    # Activate
    campaign = await CampaignService.activate_campaign(db_session, campaign.id)
    assert campaign.status.value == "active"

    # Pause
    campaign = await CampaignService.pause_campaign(db_session, campaign.id)
    assert campaign.status.value == "paused"


@pytest.mark.asyncio
async def test_campaign_api_endpoints(client: AsyncClient):
    """Test campaign API endpoints."""
    # Create campaign
    response = await client.post(
        "/api/advertising/campaigns/",
        json={
            "name": "API Test Campaign",
            "platform": "google_ads",
            "objective": "conversion",
            "budget_type": "daily",
            "daily_budget": 100.0,
            "currency": "USD",
            "bid_strategy": "manual_cpc",
            "bid_amount": 1.50
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "API Test Campaign"
    campaign_id = data["id"]

    # List campaigns
    response = await client.get("/api/advertising/campaigns/")
    assert response.status_code == 200
    assert len(response.json()) > 0

    # Get campaign
    response = await client.get(f"/api/advertising/campaigns/{campaign_id}")
    assert response.status_code == 200

    # Update campaign
    response = await client.patch(
        f"/api/advertising/campaigns/{campaign_id}",
        json={"daily_budget": 150.0}
    )
    assert response.status_code == 200
    assert response.json()["daily_budget"] == 150.0

    # Pause campaign
    response = await client.post(f"/api/advertising/campaigns/{campaign_id}/pause")
    assert response.status_code == 200
    assert response.json()["status"] == "paused"

    # Activate campaign
    response = await client.post(f"/api/advertising/campaigns/{campaign_id}/activate")
    assert response.status_code == 200
    assert response.json()["status"] == "active"
