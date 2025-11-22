"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from modules.speech_to_text.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/speech/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "supported_providers" in data


def test_list_providers(client):
    """Test list providers endpoint."""
    response = client.get("/api/v1/speech/providers")
    assert response.status_code == 200
    providers = response.json()
    assert "whisper" in providers


def test_get_provider_languages(client):
    """Test get provider languages endpoint."""
    response = client.get("/api/v1/speech/providers/whisper/languages")
    assert response.status_code == 200
    languages = response.json()
    assert "en" in languages


def test_get_invalid_provider_languages(client):
    """Test get languages for invalid provider."""
    response = client.get("/api/v1/speech/providers/invalid/languages")
    assert response.status_code == 404
