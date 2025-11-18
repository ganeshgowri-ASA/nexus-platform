"""Integration tests for A/B testing API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestExperimentAPI:
    """Test suite for Experiment API endpoints."""

    async def test_create_experiment(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
    ):
        """Test creating a new experiment."""
        response = await client.post(
            "/api/v1/experiments/",
            json=sample_experiment_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_experiment_data["name"]
        assert data["type"] == sample_experiment_data["type"]
        assert data["status"] == "draft"
        assert "id" in data

    async def test_list_experiments(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
    ):
        """Test listing experiments."""
        # Create an experiment first
        await client.post("/api/v1/experiments/", json=sample_experiment_data)

        # List experiments
        response = await client.get("/api/v1/experiments/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_get_experiment(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
    ):
        """Test getting a specific experiment."""
        # Create experiment
        create_response = await client.post(
            "/api/v1/experiments/",
            json=sample_experiment_data,
        )
        experiment_id = create_response.json()["id"]

        # Get experiment
        response = await client.get(f"/api/v1/experiments/{experiment_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == experiment_id
        assert data["name"] == sample_experiment_data["name"]

    async def test_get_nonexistent_experiment(self, client: AsyncClient):
        """Test getting a nonexistent experiment."""
        response = await client.get("/api/v1/experiments/99999")

        assert response.status_code == 404

    async def test_update_experiment(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
    ):
        """Test updating an experiment."""
        # Create experiment
        create_response = await client.post(
            "/api/v1/experiments/",
            json=sample_experiment_data,
        )
        experiment_id = create_response.json()["id"]

        # Update experiment
        update_data = {"name": "Updated Name", "description": "Updated description"}
        response = await client.patch(
            f"/api/v1/experiments/{experiment_id}",
            json=update_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

    async def test_start_experiment_without_variants(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
    ):
        """Test starting experiment without variants (should fail)."""
        # Create experiment
        create_response = await client.post(
            "/api/v1/experiments/",
            json=sample_experiment_data,
        )
        experiment_id = create_response.json()["id"]

        # Try to start without variants
        response = await client.post(f"/api/v1/experiments/{experiment_id}/start")

        assert response.status_code == 400

    async def test_experiment_stats(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
    ):
        """Test getting experiment statistics."""
        # Create experiment
        create_response = await client.post(
            "/api/v1/experiments/",
            json=sample_experiment_data,
        )
        experiment_id = create_response.json()["id"]

        # Get stats
        response = await client.get(f"/api/v1/experiments/{experiment_id}/stats")

        assert response.status_code == 200
        data = response.json()
        assert "experiment_id" in data
        assert "total_participants" in data
        assert "variant_stats" in data


@pytest.mark.asyncio
class TestVariantAPI:
    """Test suite for Variant API endpoints."""

    async def test_create_variant(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
        sample_variant_data: dict,
    ):
        """Test creating a variant."""
        # Create experiment first
        exp_response = await client.post(
            "/api/v1/experiments/",
            json=sample_experiment_data,
        )
        experiment_id = exp_response.json()["id"]

        # Create variant
        sample_variant_data["experiment_id"] = experiment_id
        response = await client.post("/api/v1/variants/", json=sample_variant_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_variant_data["name"]
        assert data["experiment_id"] == experiment_id

    async def test_list_variants(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
        sample_variant_data: dict,
    ):
        """Test listing variants for an experiment."""
        # Create experiment
        exp_response = await client.post(
            "/api/v1/experiments/",
            json=sample_experiment_data,
        )
        experiment_id = exp_response.json()["id"]

        # Create variant
        sample_variant_data["experiment_id"] = experiment_id
        await client.post("/api/v1/variants/", json=sample_variant_data)

        # List variants
        response = await client.get(f"/api/v1/variants/experiment/{experiment_id}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


@pytest.mark.asyncio
class TestMetricsAPI:
    """Test suite for Metrics API endpoints."""

    async def test_create_metric(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
        sample_metric_data: dict,
    ):
        """Test creating a metric."""
        # Create experiment first
        exp_response = await client.post(
            "/api/v1/experiments/",
            json=sample_experiment_data,
        )
        experiment_id = exp_response.json()["id"]

        # Create metric
        sample_metric_data["experiment_id"] = experiment_id
        response = await client.post("/api/v1/metrics/", json=sample_metric_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_metric_data["name"]
        assert data["experiment_id"] == experiment_id

    async def test_track_event(
        self,
        client: AsyncClient,
        sample_experiment_data: dict,
        sample_variant_data: dict,
        sample_metric_data: dict,
    ):
        """Test tracking a metric event."""
        # Create experiment
        exp_response = await client.post(
            "/api/v1/experiments/",
            json=sample_experiment_data,
        )
        experiment_id = exp_response.json()["id"]

        # Create variant
        sample_variant_data["experiment_id"] = experiment_id
        var_response = await client.post("/api/v1/variants/", json=sample_variant_data)
        variant_id = var_response.json()["id"]

        # Create metric
        sample_metric_data["experiment_id"] = experiment_id
        metric_response = await client.post("/api/v1/metrics/", json=sample_metric_data)
        metric_id = metric_response.json()["id"]

        # Track event
        event_data = {
            "metric_id": metric_id,
            "participant_id": "test_user_123",
            "variant_id": variant_id,
            "value": 1.0,
        }
        response = await client.post("/api/v1/metrics/events", json=event_data)

        assert response.status_code == 201
        data = response.json()
        assert data["metric_id"] == metric_id
        assert data["participant_id"] == event_data["participant_id"]
        assert data["value"] == event_data["value"]


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ab-testing"

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
