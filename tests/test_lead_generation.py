<<<<<<< HEAD
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
=======
"""
Tests for lead generation module.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from modules.lead_generation.models import Lead, Form, LeadSource
from modules.lead_generation.services.lead_service import LeadService
from modules.lead_generation.services.form_service import FormService
from modules.lead_generation.schemas import LeadCreate, FormCreate


@pytest.mark.asyncio
async def test_create_lead(db_session: AsyncSession):
    """Test creating a lead."""
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
    lead_data = LeadCreate(
        email="test@example.com",
        first_name="Test",
        last_name="User",
<<<<<<< HEAD
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
=======
        company="Test Corp",
        source=LeadSource.FORM
    )

    lead = await LeadService.create_lead(db_session, lead_data)

    assert lead.id is not None
    assert lead.email == "test@example.com"
    assert lead.first_name == "Test"
    assert lead.status.value == "new"


@pytest.mark.asyncio
async def test_duplicate_lead_detection(db_session: AsyncSession):
    """Test duplicate lead detection."""
    lead_data = LeadCreate(
        email="duplicate@example.com",
        source=LeadSource.FORM
    )

    # Create first lead
    lead1 = await LeadService.create_lead(db_session, lead_data)
    assert lead1.is_duplicate is False

    # Create duplicate lead
    lead2 = await LeadService.create_lead(db_session, lead_data)
    assert lead2.is_duplicate is True
    assert lead2.duplicate_of == lead1.id


@pytest.mark.asyncio
async def test_create_form(db_session: AsyncSession):
    """Test creating a form."""
    form_data = FormCreate(
        name="Test Form",
        form_type="inline",
        fields=[
            {"name": "email", "type": "email", "required": True},
            {"name": "name", "type": "text", "required": True}
        ]
    )

    form = await FormService.create_form(db_session, form_data)

    assert form.id is not None
    assert form.name == "Test Form"
    assert len(form.fields) == 2
    assert form.is_active is True


@pytest.mark.asyncio
async def test_lead_scoring(db_session: AsyncSession):
    """Test lead scoring."""
    from modules.lead_generation.services.scoring_service import ScoringService

    # Create a lead
    lead_data = LeadCreate(
        email="score@example.com",
        first_name="John",
        last_name="Doe",
        company="Big Corp",
        job_title="CEO",
        phone="+1234567890",
        source=LeadSource.CHATBOT
    )

    lead = await LeadService.create_lead(db_session, lead_data)

    # Calculate score
    score = await ScoringService.calculate_lead_score(db_session, lead.id)

    assert score > 0
    assert lead.grade is not None


@pytest.mark.asyncio
async def test_lead_api_endpoints(client: AsyncClient):
    """Test lead API endpoints."""
    # Create lead
    response = await client.post(
        "/api/lead-generation/leads/",
        json={
            "email": "api@example.com",
            "first_name": "API",
            "last_name": "Test",
            "source": "form"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "api@example.com"
    lead_id = data["id"]

    # Get lead
    response = await client.get(f"/api/lead-generation/leads/{lead_id}")
    assert response.status_code == 200

    # Update lead
    response = await client.patch(
        f"/api/lead-generation/leads/{lead_id}",
        json={"status": "qualified"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "qualified"


@pytest.mark.asyncio
async def test_form_api_endpoints(client: AsyncClient):
    """Test form API endpoints."""
    # Create form
    response = await client.post(
        "/api/lead-generation/forms/",
        json={
            "name": "API Test Form",
            "form_type": "inline",
            "fields": [
                {"name": "email", "type": "email", "required": True}
            ]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "API Test Form"
    form_id = data["id"]

    # List forms
    response = await client.get("/api/lead-generation/forms/")
    assert response.status_code == 200
    assert len(response.json()) > 0

    # Get form
    response = await client.get(f"/api/lead-generation/forms/{form_id}")
    assert response.status_code == 200

    # Update form
    response = await client.patch(
        f"/api/lead-generation/forms/{form_id}",
        json={"is_active": False}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
>>>>>>> origin/claude/lead-gen-advertising-modules-013aKZjYzcLFmpKdzNMTj8Bi
