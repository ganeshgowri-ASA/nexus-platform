"""Tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from modules.scheduler.main import app

client = TestClient(app)


class TestRootEndpoints:
    """Test root endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NEXUS Scheduler API"
        assert data["version"] == "1.0.0"

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCronEndpoints:
    """Test cron validation endpoints"""

    def test_validate_cron(self):
        """Test cron validation"""
        response = client.post(
            "/api/v1/cron/validate",
            json={"expression": "*/5 * * * *", "timezone": "UTC"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_get_presets(self):
        """Test getting cron presets"""
        response = client.get("/api/v1/cron/presets")
        assert response.status_code == 200
        data = response.json()
        assert "hourly" in data
        assert "daily_midnight" in data


# Note: Job CRUD tests would require database setup
# These are simplified examples
class TestJobEndpoints:
    """Test job management endpoints"""

    @pytest.mark.skip(reason="Requires database setup")
    def test_create_job(self):
        """Test creating a job"""
        job_data = {
            "name": "Test Job",
            "description": "Test job description",
            "job_type": "cron",
            "cron_expression": "0 0 * * *",
            "task_name": "example.hello_world",
            "timezone": "UTC",
            "is_active": True,
            "max_retries": 3,
            "retry_delay": 60,
            "priority": 5
        }

        response = client.post("/api/v1/jobs/", json=job_data)
        # Would assert response.status_code == 201 with database
        pass
