"""
Integration tests for Attribution API
"""
import pytest
from fastapi.testclient import TestClient

from backend.app.models.attribution import Journey, Channel, AttributionModel


class TestChannelEndpoints:
    """Test channel API endpoints."""

    def test_create_channel(self, client: TestClient):
        """Test creating a channel via API."""
        response = client.post(
            "/api/v1/attribution/channels",
            json={
                "name": "API Test Channel",
                "channel_type": "paid_search",
                "cost_per_click": 1.5,
                "monthly_budget": 5000.0,
                "is_active": True,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Channel"
        assert data["channel_type"] == "paid_search"
        assert "id" in data

    def test_get_channel(self, client: TestClient, test_channel: Channel):
        """Test getting a channel by ID."""
        response = client.get(f"/api/v1/attribution/channels/{test_channel.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_channel.id
        assert data["name"] == test_channel.name

    def test_list_channels(self, client: TestClient, test_channel: Channel):
        """Test listing channels."""
        response = client.get("/api/v1/attribution/channels")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert any(ch["id"] == test_channel.id for ch in data)


class TestJourneyEndpoints:
    """Test journey API endpoints."""

    def test_create_journey(self, client: TestClient):
        """Test creating a journey via API."""
        from datetime import datetime

        response = client.post(
            "/api/v1/attribution/journeys",
            json={
                "user_id": "api_test_user",
                "session_id": "api_test_session",
                "start_time": datetime.utcnow().isoformat(),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "api_test_user"
        assert "id" in data

    def test_get_journey(self, client: TestClient, test_journey: Journey):
        """Test getting a journey by ID."""
        response = client.get(f"/api/v1/attribution/journeys/{test_journey.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_journey.id
        assert data["user_id"] == test_journey.user_id

    def test_get_journey_visualization(
        self, client: TestClient, complete_test_journey: Journey
    ):
        """Test getting journey visualization."""
        response = client.get(
            f"/api/v1/attribution/journeys/{complete_test_journey.id}/visualization"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["journey_id"] == complete_test_journey.id
        assert "touchpoints" in data
        assert len(data["touchpoints"]) > 0


class TestTouchpointEndpoints:
    """Test touchpoint API endpoints."""

    def test_create_touchpoint(
        self, client: TestClient, test_journey: Journey, test_channel: Channel
    ):
        """Test creating a touchpoint via API."""
        from datetime import datetime

        response = client.post(
            "/api/v1/attribution/touchpoints",
            json={
                "journey_id": test_journey.id,
                "channel_id": test_channel.id,
                "touchpoint_type": "click",
                "timestamp": datetime.utcnow().isoformat(),
                "position_in_journey": 1,
                "engagement_score": 0.8,
                "cost": 2.0,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["journey_id"] == test_journey.id
        assert data["channel_id"] == test_channel.id


class TestConversionEndpoints:
    """Test conversion API endpoints."""

    def test_create_conversion(self, client: TestClient, test_journey: Journey):
        """Test creating a conversion via API."""
        from datetime import datetime

        response = client.post(
            "/api/v1/attribution/conversions",
            json={
                "journey_id": test_journey.id,
                "conversion_type": "purchase",
                "timestamp": datetime.utcnow().isoformat(),
                "revenue": 99.99,
                "quantity": 1,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["journey_id"] == test_journey.id
        assert data["revenue"] == 99.99


class TestAttributionModelEndpoints:
    """Test attribution model API endpoints."""

    def test_create_attribution_model(self, client: TestClient):
        """Test creating an attribution model via API."""
        response = client.post(
            "/api/v1/attribution/models",
            json={
                "name": "API Test Model",
                "model_type": "linear",
                "description": "Test linear model",
                "is_active": True,
                "is_default": False,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Model"
        assert data["model_type"] == "linear"

    def test_get_attribution_model(
        self, client: TestClient, test_attribution_model: AttributionModel
    ):
        """Test getting an attribution model by ID."""
        response = client.get(
            f"/api/v1/attribution/models/{test_attribution_model.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_attribution_model.id

    def test_list_attribution_models(
        self, client: TestClient, test_attribution_model: AttributionModel
    ):
        """Test listing attribution models."""
        response = client.get("/api/v1/attribution/models")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestAttributionCalculation:
    """Test attribution calculation endpoints."""

    def test_calculate_attribution(
        self,
        client: TestClient,
        complete_test_journey: Journey,
        test_attribution_model: AttributionModel,
    ):
        """Test calculating attribution for a journey."""
        response = client.post(
            f"/api/v1/attribution/calculate/"
            f"{complete_test_journey.id}/{test_attribution_model.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check result structure
        result = data[0]
        assert "journey_id" in result
        assert "attribution_model_id" in result
        assert "channel_id" in result
        assert "credit" in result
        assert "attributed_revenue" in result


class TestAnalyticsEndpoints:
    """Test analytics API endpoints."""

    def test_calculate_channel_roi(
        self, client: TestClient, test_channel: Channel
    ):
        """Test calculating channel ROI."""
        from datetime import datetime, timedelta

        start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        end_date = datetime.utcnow().isoformat()

        response = client.post(
            "/api/v1/attribution/analytics/channel-roi",
            json={
                "channel_ids": [test_channel.id],
                "start_date": start_date,
                "end_date": end_date,
                "attribution_model_id": None,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_analyze_touchpoint_performance(self, client: TestClient):
        """Test touchpoint performance analysis."""
        response = client.get(
            "/api/v1/attribution/analytics/touchpoint-performance",
            params={"group_by": "channel"},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestJourneyAnalysis:
    """Test journey analysis endpoints."""

    def test_get_journey_metrics(self, client: TestClient):
        """Test getting journey metrics."""
        response = client.get("/api/v1/attribution/journeys/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "total_journeys" in data
        assert "conversion_rate" in data

    def test_get_conversion_paths(self, client: TestClient):
        """Test getting conversion paths."""
        response = client.get(
            "/api/v1/attribution/journeys/conversion-paths",
            params={"limit": 100, "converted_only": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestCacheEndpoints:
    """Test cache management endpoints."""

    def test_check_cache_health(self, client: TestClient):
        """Test cache health check."""
        response = client.get("/api/v1/attribution/cache/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
