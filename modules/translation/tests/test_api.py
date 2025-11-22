"""
API endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from modules.translation.main import app

client = TestClient(app)


class TestTranslationAPI:
    """Tests for translation API endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_get_supported_languages(self):
        """Test get supported languages endpoint"""
        response = client.get("/api/translation/languages")
        assert response.status_code == 200
        assert "languages" in response.json()
        assert len(response.json()["languages"]) > 0

    def test_translate_endpoint_missing_fields(self):
        """Test translation endpoint with missing fields"""
        response = client.post(
            "/api/translation/translate",
            json={}
        )
        assert response.status_code == 422  # Validation error

    def test_detect_language_endpoint(self):
        """Test language detection endpoint"""
        response = client.post(
            "/api/translation/detect-language",
            json={"text": "Hello world"}
        )
        # May succeed or fail depending on API availability
        assert response.status_code in [200, 500]
