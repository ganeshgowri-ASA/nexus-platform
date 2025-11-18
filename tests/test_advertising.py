"""Tests for advertising module."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database import Base
from modules.advertising.ad_types import (
    CampaignCreate,
    CampaignStatus,
    AdPlatform,
)
from modules.advertising.campaigns import CampaignManager


@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.mark.asyncio
async def test_create_campaign(db_session):
    """Test campaign creation."""
    campaign_data = CampaignCreate(
        name="Test Campaign",
        objective="conversions",
        platform=AdPlatform.GOOGLE_ADS,
        daily_budget=100.0,
        start_date=datetime.utcnow(),
        status=CampaignStatus.DRAFT,
    )
    
    manager = CampaignManager(db_session)
    campaign = await manager.create_campaign(campaign_data)
    
    assert campaign.name == "Test Campaign"
    assert campaign.platform == AdPlatform.GOOGLE_ADS
    assert campaign.status == CampaignStatus.DRAFT


@pytest.mark.asyncio
async def test_list_campaigns(db_session):
    """Test listing campaigns."""
    # Create test campaigns
    for i in range(5):
        campaign_data = CampaignCreate(
            name=f"Campaign {i}",
            objective="traffic",
            platform=AdPlatform.FACEBOOK,
            daily_budget=50.0,
            start_date=datetime.utcnow(),
            status=CampaignStatus.ACTIVE,
        )
        manager = CampaignManager(db_session)
        await manager.create_campaign(campaign_data)
    
    # List campaigns
    campaigns = await manager.list_campaigns()
    
    assert len(campaigns) == 5


@pytest.mark.asyncio
async def test_update_campaign_status(db_session):
    """Test updating campaign status."""
    # Create campaign
    campaign_data = CampaignCreate(
        name="Test Campaign",
        objective="conversions",
        platform=AdPlatform.LINKEDIN,
        daily_budget=150.0,
        start_date=datetime.utcnow(),
        status=CampaignStatus.DRAFT,
    )
    
    manager = CampaignManager(db_session)
    campaign = await manager.create_campaign(campaign_data)
    
    # Update status
    updated = await manager.update_campaign_status(campaign.id, CampaignStatus.ACTIVE)
    
    assert updated.status == CampaignStatus.ACTIVE
