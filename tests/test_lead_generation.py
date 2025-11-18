"""Tests for lead generation module."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.database import Base
from modules.lead_generation.lead_types import LeadCreate, LeadStatus
from modules.lead_generation.capture import LeadCapture
from modules.lead_generation.scoring import LeadScoring
from modules.lead_generation.validation import LeadValidator


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
async def test_create_lead(db_session):
    """Test lead creation."""
    lead_data = LeadCreate(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        company="Test Company",
    )
    
    capture = LeadCapture(db_session)
    lead = await capture.capture_lead(lead_data)
    
    assert lead.email == "test@example.com"
    assert lead.first_name == "Test"
    assert lead.status == LeadStatus.NEW


@pytest.mark.asyncio
async def test_lead_validation(db_session):
    """Test lead validation."""
    validator = LeadValidator(db_session)
    
    # Valid lead
    valid_data = {
        "email": "test@example.com",
        "phone": "+1234567890",
    }
    result = await validator.validate_lead_data(valid_data)
    assert result["valid"] is True
    
    # Invalid email
    invalid_data = {
        "email": "invalid-email",
    }
    result = await validator.validate_lead_data(invalid_data)
    assert result["valid"] is False


@pytest.mark.asyncio
async def test_lead_scoring(db_session):
    """Test lead scoring."""
    # Create a lead first
    lead_data = LeadCreate(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        company="Test Company",
        job_title="CEO",
        phone="+1234567890",
    )
    
    capture = LeadCapture(db_session)
    lead = await capture.capture_lead(lead_data)
    
    # Calculate score
    scorer = LeadScoring(db_session)
    score = await scorer.calculate_score(lead.id)
    
    assert score > 0
    assert score <= 100
