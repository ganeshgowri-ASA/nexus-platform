"""
NEXUS Platform - API Client
"""
import os
from typing import Any, Dict, Optional, List
import requests
from requests.exceptions import RequestException


class APIClient:
    """Client for NEXUS Platform API."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (default from env)
        """
        self.base_url = base_url or os.getenv(
            "BACKEND_URL", "http://localhost:8000"
        )
        self.api_prefix = "/api/v1"
        self.timeout = 30

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Any:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json: JSON body

        Returns:
            Response data

        Raises:
            Exception: If request fails
        """
        url = f"{self.base_url}{self.api_prefix}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Any:
        """Make POST request."""
        return self._make_request("POST", endpoint, params=params, json=json)

    def put(
        self,
        endpoint: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Any:
        """Make PUT request."""
        return self._make_request("PUT", endpoint, params=params, json=json)

    def delete(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Make DELETE request."""
        return self._make_request("DELETE", endpoint, params=params)


class AttributionClient:
    """Client for Attribution API endpoints."""

    def __init__(self, api_client: Optional[APIClient] = None):
        """Initialize attribution client."""
        self.client = api_client or APIClient()

    # Channels
    def list_channels(self, active_only: bool = True) -> List[Dict]:
        """List all channels."""
        return self.client.get(
            "/attribution/channels",
            params={"active_only": active_only, "limit": 1000},
        )

    def create_channel(self, channel_data: Dict) -> Dict:
        """Create a new channel."""
        return self.client.post("/attribution/channels", json=channel_data)

    # Journeys
    def get_journey(self, journey_id: int) -> Dict:
        """Get journey by ID."""
        return self.client.get(f"/attribution/journeys/{journey_id}")

    def get_journey_visualization(
        self, journey_id: int, model_id: Optional[int] = None
    ) -> Dict:
        """Get journey visualization data."""
        params = {}
        if model_id:
            params["attribution_model_id"] = model_id
        return self.client.get(
            f"/attribution/journeys/{journey_id}/visualization", params=params
        )

    def get_conversion_paths(
        self, limit: int = 100, converted_only: bool = True
    ) -> List[Dict]:
        """Get common conversion paths."""
        return self.client.get(
            "/attribution/journeys/conversion-paths",
            params={"limit": limit, "converted_only": converted_only},
        )

    def get_journey_metrics(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict:
        """Get journey metrics."""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self.client.get("/attribution/journeys/metrics", params=params)

    # Attribution Models
    def list_models(self, active_only: bool = True) -> List[Dict]:
        """List all attribution models."""
        return self.client.get(
            "/attribution/models",
            params={"active_only": active_only, "limit": 1000},
        )

    def create_model(self, model_data: Dict) -> Dict:
        """Create attribution model."""
        return self.client.post("/attribution/models", json=model_data)

    # Attribution Calculation
    def calculate_attribution(self, journey_id: int, model_id: int) -> List[Dict]:
        """Calculate attribution for journey."""
        return self.client.post(
            f"/attribution/calculate/{journey_id}/{model_id}"
        )

    def calculate_bulk_attribution(self, request_data: Dict) -> Dict:
        """Calculate attribution for multiple journeys."""
        return self.client.post("/attribution/calculate/bulk", json=request_data)

    # AI Attribution
    def get_ai_insights(self, journey_ids: List[int], analysis_type: str) -> Dict:
        """Get AI insights."""
        return self.client.post(
            "/attribution/ai/insights",
            json={"journey_ids": journey_ids, "analysis_type": analysis_type},
        )

    def compare_models_ai(
        self, journey_ids: List[int], model_ids: List[int]
    ) -> Dict:
        """Compare models with AI analysis."""
        return self.client.post(
            "/attribution/ai/compare-models",
            json={"journey_ids": journey_ids, "model_ids": model_ids},
        )

    # Analytics
    def calculate_channel_roi(self, request_data: Dict) -> List[Dict]:
        """Calculate channel ROI."""
        return self.client.post("/attribution/analytics/channel-roi", json=request_data)

    def analyze_touchpoint_performance(
        self, group_by: str = "channel"
    ) -> List[Dict]:
        """Analyze touchpoint performance."""
        return self.client.get(
            "/attribution/analytics/touchpoint-performance",
            params={"group_by": group_by},
        )

    def compare_channels(
        self,
        channel_ids: List[int],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        model_id: Optional[int] = None,
    ) -> Dict:
        """Compare channels."""
        data = {"channel_ids": channel_ids}
        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date
        if model_id:
            data["attribution_model_id"] = model_id
        return self.client.post("/attribution/analytics/channel-comparison", json=data)

    def get_trends(
        self,
        metric: str,
        channel_id: Optional[int] = None,
        interval: str = "day",
    ) -> List[Dict]:
        """Get trend analysis."""
        params = {"metric": metric, "interval": interval}
        if channel_id:
            params["channel_id"] = channel_id
        return self.client.get("/attribution/analytics/trends", params=params)
