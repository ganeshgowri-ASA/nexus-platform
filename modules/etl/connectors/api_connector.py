"""REST API connector."""
from typing import Any, Dict, Optional, List
import pandas as pd
import httpx
from .base import BaseConnector
import json
from tenacity import retry, stop_after_attempt, wait_exponential


class APIConnector(BaseConnector):
    """Connector for REST APIs."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client: Optional[httpx.Client] = None
        self.base_url: Optional[str] = None

    def get_required_fields(self) -> list:
        """Get required configuration fields."""
        return ["base_url"]

    def connect(self) -> bool:
        """Establish API connection (create HTTP client)."""
        try:
            self.validate_config()
            self.base_url = self.config["base_url"]

            # Setup headers
            headers = self.config.get("headers", {})
            if "api_key" in self.config:
                headers["Authorization"] = f"Bearer {self.config['api_key']}"

            # Create HTTP client
            self.client = httpx.Client(
                base_url=self.base_url,
                headers=headers,
                timeout=self.config.get("timeout", 30.0),
                follow_redirects=True,
            )

            self.logger.info(f"Connected to API: {self.base_url}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to API: {e}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def extract(self, query: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Extract data from REST API."""
        try:
            if not self.client:
                raise RuntimeError("Not connected to API")

            # Get endpoint and parameters
            endpoint = query.get("endpoint") if query else self.config.get("endpoint", "")
            method = self.config.get("method", "GET").upper()
            params = self.config.get("params", {})
            data_path = self.config.get("data_path", None)  # Path to data in response

            # Merge query params
            if query and "params" in query:
                params.update(query["params"])

            # Handle pagination
            pagination = self.config.get("pagination", {})
            all_data = []

            if pagination.get("enabled", False):
                all_data = self._extract_with_pagination(endpoint, method, params, data_path, pagination)
            else:
                # Single request
                response = self._make_request(endpoint, method, params)
                data = self._extract_data_from_response(response.json(), data_path)
                all_data = data if isinstance(data, list) else [data]

            # Convert to DataFrame
            df = pd.DataFrame(all_data)

            # Apply filters
            if query:
                if "limit" in query:
                    df = df.head(query["limit"])
                if "columns" in query:
                    df = df[query["columns"]]

            self.logger.info(f"Extracted {len(df)} records from API")
            return df

        except Exception as e:
            self.logger.error(f"Error extracting data from API: {e}")
            raise

    def _make_request(self, endpoint: str, method: str, params: Dict = None, data: Dict = None) -> httpx.Response:
        """Make HTTP request."""
        if method == "GET":
            response = self.client.get(endpoint, params=params)
        elif method == "POST":
            response = self.client.post(endpoint, json=data, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response

    def _extract_with_pagination(
        self, endpoint: str, method: str, params: Dict, data_path: Optional[str], pagination_config: Dict
    ) -> List[Dict]:
        """Extract data with pagination support."""
        all_data = []
        page = pagination_config.get("start_page", 1)
        page_param = pagination_config.get("page_param", "page")
        limit_param = pagination_config.get("limit_param", "limit")
        max_pages = pagination_config.get("max_pages", 100)
        page_size = pagination_config.get("page_size", 100)

        params[limit_param] = page_size

        while page <= max_pages:
            params[page_param] = page

            try:
                response = self._make_request(endpoint, method, params)
                data = self._extract_data_from_response(response.json(), data_path)

                if not data or len(data) == 0:
                    break

                all_data.extend(data if isinstance(data, list) else [data])

                # Check if there are more pages
                if len(data) < page_size:
                    break

                page += 1

            except Exception as e:
                self.logger.warning(f"Error on page {page}: {e}")
                break

        return all_data

    def _extract_data_from_response(self, response: Dict, data_path: Optional[str]) -> Any:
        """Extract data from API response using path."""
        if not data_path:
            return response

        # Navigate through nested structure
        keys = data_path.split(".")
        result = response
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                raise ValueError(f"Invalid data path: {data_path}")
        return result

    def disconnect(self) -> None:
        """Close API connection."""
        if self.client:
            self.client.close()
        self.logger.info("Disconnected from API")

    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            if not self.client:
                return False

            # Try a simple request
            test_endpoint = self.config.get("test_endpoint", "/")
            response = self.client.get(test_endpoint)
            return response.status_code < 400

        except Exception:
            return False

    def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get API schema information (if available)."""
        try:
            # Try to get OpenAPI/Swagger schema
            schema_endpoints = ["/openapi.json", "/swagger.json", "/api/schema"]

            for endpoint in schema_endpoints:
                try:
                    response = self.client.get(endpoint)
                    if response.status_code == 200:
                        return response.json()
                except Exception:
                    continue

            return {"base_url": self.base_url, "endpoints": "Schema not available"}

        except Exception as e:
            self.logger.error(f"Error getting schema: {e}")
            return None
