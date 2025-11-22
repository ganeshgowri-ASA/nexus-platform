"""
Mock Server Module

Generate mock responses, simulate delays, and error scenarios for API testing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import random
import time
from datetime import datetime


class MockResponseType(Enum):
    """Types of mock responses."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RANDOM = "random"


@dataclass
class MockResponse:
    """Represents a mock API response."""
    status_code: int
    body: Dict[str, Any]
    headers: Dict[str, str] = field(default_factory=dict)
    delay_ms: int = 0  # Simulated delay in milliseconds
    probability: float = 1.0  # Probability of this response being selected (0.0 - 1.0)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status_code": self.status_code,
            "body": self.body,
            "headers": self.headers,
            "delay_ms": self.delay_ms,
            "probability": self.probability,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockResponse':
        """Create from dictionary."""
        return cls(
            status_code=data["status_code"],
            body=data["body"],
            headers=data.get("headers", {}),
            delay_ms=data.get("delay_ms", 0),
            probability=data.get("probability", 1.0),
            description=data.get("description", ""),
        )


@dataclass
class MockScenario:
    """Represents a mock scenario with multiple possible responses."""
    name: str
    endpoint_id: str
    responses: List[MockResponse] = field(default_factory=list)
    enabled: bool = True
    description: str = ""

    def add_response(
        self,
        status_code: int,
        body: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        delay_ms: int = 0,
        probability: float = 1.0,
        description: str = "",
    ) -> MockResponse:
        """Add a mock response to the scenario."""
        response = MockResponse(
            status_code=status_code,
            body=body,
            headers=headers or {},
            delay_ms=delay_ms,
            probability=probability,
            description=description,
        )
        self.responses.append(response)
        return response

    def get_response(self) -> Optional[MockResponse]:
        """Get a response based on probabilities."""
        if not self.responses:
            return None

        # Normalize probabilities
        total_prob = sum(r.probability for r in self.responses)
        if total_prob == 0:
            return random.choice(self.responses)

        # Select based on probability
        rand = random.random() * total_prob
        cumulative = 0

        for response in self.responses:
            cumulative += response.probability
            if rand <= cumulative:
                return response

        return self.responses[-1]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "endpoint_id": self.endpoint_id,
            "responses": [r.to_dict() for r in self.responses],
            "enabled": self.enabled,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockScenario':
        """Create from dictionary."""
        scenario = cls(
            name=data["name"],
            endpoint_id=data["endpoint_id"],
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )

        for response_data in data.get("responses", []):
            scenario.responses.append(MockResponse.from_dict(response_data))

        return scenario


class MockDataGenerator:
    """Generates mock data for responses."""

    @staticmethod
    def generate_from_schema(schema: Dict[str, Any]) -> Any:
        """Generate mock data based on JSON schema."""
        data_type = schema.get("type", "object")

        if data_type == "string":
            enum = schema.get("enum")
            if enum:
                return random.choice(enum)

            pattern = schema.get("pattern")
            if pattern:
                return f"string-{random.randint(1000, 9999)}"

            example = schema.get("example")
            if example:
                return example

            return f"string-{random.randint(1000, 9999)}"

        elif data_type == "integer":
            minimum = schema.get("minimum", 0)
            maximum = schema.get("maximum", 100)
            return random.randint(minimum, maximum)

        elif data_type == "number":
            minimum = schema.get("minimum", 0.0)
            maximum = schema.get("maximum", 100.0)
            return round(random.uniform(minimum, maximum), 2)

        elif data_type == "boolean":
            return random.choice([True, False])

        elif data_type == "array":
            items_schema = schema.get("items", {})
            min_items = schema.get("minItems", 1)
            max_items = schema.get("maxItems", 5)
            count = random.randint(min_items, max_items)

            return [
                MockDataGenerator.generate_from_schema(items_schema)
                for _ in range(count)
            ]

        elif data_type == "object":
            result = {}
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            # Generate required fields
            for field_name in required:
                if field_name in properties:
                    result[field_name] = MockDataGenerator.generate_from_schema(
                        properties[field_name]
                    )

            # Optionally generate other fields
            for field_name, field_schema in properties.items():
                if field_name not in result and random.random() > 0.3:
                    result[field_name] = MockDataGenerator.generate_from_schema(
                        field_schema
                    )

            return result

        return None

    @staticmethod
    def generate_error_response(
        status_code: int,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a standard error response."""
        error_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
        }

        return {
            "error": {
                "code": status_code,
                "message": message or error_messages.get(status_code, "Error"),
                "timestamp": datetime.now().isoformat(),
            }
        }

    @staticmethod
    def generate_success_response(
        data: Any,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a standard success response."""
        response = {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        if meta:
            response["meta"] = meta

        return response

    @staticmethod
    def generate_paginated_response(
        items: List[Any],
        page: int = 1,
        per_page: int = 10,
        total: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate a paginated response."""
        if total is None:
            total = len(items)

        start = (page - 1) * per_page
        end = start + per_page
        page_items = items[start:end]

        return {
            "success": True,
            "data": page_items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
                "has_next": end < total,
                "has_prev": page > 1,
            },
            "timestamp": datetime.now().isoformat(),
        }


class MockServer:
    """Mock server for simulating API responses."""

    def __init__(self):
        self.scenarios: Dict[str, MockScenario] = {}
        self.request_log: List[Dict[str, Any]] = []
        self.global_delay_ms: int = 0
        self.error_rate: float = 0.0  # Probability of random errors (0.0 - 1.0)

    def add_scenario(self, scenario: MockScenario) -> None:
        """Add a mock scenario."""
        key = f"{scenario.endpoint_id}:{scenario.name}"
        self.scenarios[key] = scenario

    def remove_scenario(self, endpoint_id: str, scenario_name: str) -> bool:
        """Remove a mock scenario."""
        key = f"{endpoint_id}:{scenario_name}"
        if key in self.scenarios:
            del self.scenarios[key]
            return True
        return False

    def get_scenarios(self, endpoint_id: str) -> List[MockScenario]:
        """Get all scenarios for an endpoint."""
        return [
            scenario for key, scenario in self.scenarios.items()
            if scenario.endpoint_id == endpoint_id
        ]

    def create_quick_scenario(
        self,
        name: str,
        endpoint_id: str,
        endpoint: Any,  # Endpoint object
    ) -> MockScenario:
        """Quickly create a scenario from endpoint definition."""
        scenario = MockScenario(
            name=name,
            endpoint_id=endpoint_id,
            description=f"Auto-generated scenario for {endpoint.path}",
        )

        # Generate responses based on endpoint definition
        for status_code, response_def in endpoint.responses.items():
            body = {}

            if response_def.schema:
                body = MockDataGenerator.generate_from_schema(response_def.schema)
            else:
                # Generate default response
                if 200 <= status_code < 300:
                    body = MockDataGenerator.generate_success_response(
                        {"message": "Success"}
                    )
                else:
                    body = MockDataGenerator.generate_error_response(status_code)

            scenario.add_response(
                status_code=status_code,
                body=body,
                headers={"Content-Type": "application/json"},
                delay_ms=random.randint(50, 200),
                probability=1.0 if status_code == 200 else 0.1,
                description=response_def.description,
            )

        self.add_scenario(scenario)
        return scenario

    def handle_request(
        self,
        endpoint_id: str,
        scenario_name: Optional[str] = None,
        path_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle a mock request."""
        start_time = time.time()

        # Log request
        request_log = {
            "endpoint_id": endpoint_id,
            "scenario_name": scenario_name,
            "path_params": path_params,
            "query_params": query_params,
            "headers": headers,
            "body": body,
            "timestamp": datetime.now().isoformat(),
        }

        # Check for random error
        if self.error_rate > 0 and random.random() < self.error_rate:
            error_codes = [500, 502, 503]
            status_code = random.choice(error_codes)
            response = {
                "status_code": status_code,
                "body": MockDataGenerator.generate_error_response(status_code),
                "headers": {"Content-Type": "application/json"},
                "delay_ms": 0,
            }

            request_log["response"] = response
            self.request_log.append(request_log)

            # Apply global delay
            if self.global_delay_ms > 0:
                time.sleep(self.global_delay_ms / 1000.0)

            return response

        # Find scenario
        scenario = None
        if scenario_name:
            key = f"{endpoint_id}:{scenario_name}"
            scenario = self.scenarios.get(key)
        else:
            # Use first available scenario for endpoint
            scenarios = self.get_scenarios(endpoint_id)
            scenario = scenarios[0] if scenarios else None

        if not scenario or not scenario.enabled:
            # Return 404 if no scenario found
            response = {
                "status_code": 404,
                "body": MockDataGenerator.generate_error_response(
                    404, "Mock scenario not found"
                ),
                "headers": {"Content-Type": "application/json"},
                "delay_ms": 0,
            }

            request_log["response"] = response
            self.request_log.append(request_log)
            return response

        # Get mock response from scenario
        mock_response = scenario.get_response()
        if not mock_response:
            # Return 500 if no response configured
            response = {
                "status_code": 500,
                "body": MockDataGenerator.generate_error_response(
                    500, "No mock response configured"
                ),
                "headers": {"Content-Type": "application/json"},
                "delay_ms": 0,
            }

            request_log["response"] = response
            self.request_log.append(request_log)
            return response

        # Apply delays
        total_delay = self.global_delay_ms + mock_response.delay_ms
        if total_delay > 0:
            time.sleep(total_delay / 1000.0)

        # Build response
        response_time = (time.time() - start_time) * 1000  # Convert to ms

        response = {
            "status_code": mock_response.status_code,
            "body": mock_response.body,
            "headers": {
                **mock_response.headers,
                "X-Mock-Server": "true",
                "X-Response-Time-Ms": str(int(response_time)),
            },
            "delay_ms": total_delay,
            "time": response_time / 1000.0,  # Convert to seconds
        }

        request_log["response"] = response
        self.request_log.append(request_log)

        return response

    def set_global_delay(self, delay_ms: int) -> None:
        """Set global delay for all responses."""
        self.global_delay_ms = max(0, delay_ms)

    def set_error_rate(self, error_rate: float) -> None:
        """Set probability of random errors (0.0 - 1.0)."""
        self.error_rate = max(0.0, min(1.0, error_rate))

    def get_request_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent request log."""
        return self.request_log[-limit:]

    def clear_request_log(self) -> None:
        """Clear request log."""
        self.request_log = []

    def export_scenarios(self) -> str:
        """Export all scenarios to JSON."""
        data = {
            "scenarios": [s.to_dict() for s in self.scenarios.values()],
            "config": {
                "global_delay_ms": self.global_delay_ms,
                "error_rate": self.error_rate,
            }
        }
        return json.dumps(data, indent=2)

    def import_scenarios(self, json_str: str) -> int:
        """Import scenarios from JSON."""
        data = json.loads(json_str)
        count = 0

        for scenario_data in data.get("scenarios", []):
            scenario = MockScenario.from_dict(scenario_data)
            self.add_scenario(scenario)
            count += 1

        config = data.get("config", {})
        if "global_delay_ms" in config:
            self.set_global_delay(config["global_delay_ms"])
        if "error_rate" in config:
            self.set_error_rate(config["error_rate"])

        return count

    def get_statistics(self) -> Dict[str, Any]:
        """Get mock server statistics."""
        total_requests = len(self.request_log)

        status_codes = {}
        for log in self.request_log:
            response = log.get("response", {})
            status = response.get("status_code")
            if status:
                status_codes[status] = status_codes.get(status, 0) + 1

        return {
            "total_requests": total_requests,
            "total_scenarios": len(self.scenarios),
            "status_codes": status_codes,
            "global_delay_ms": self.global_delay_ms,
            "error_rate": self.error_rate,
        }


# Utility functions for creating common mock scenarios

def create_success_scenario(
    name: str,
    endpoint_id: str,
    data: Any,
    delay_ms: int = 100,
) -> MockScenario:
    """Create a simple success scenario."""
    scenario = MockScenario(
        name=name,
        endpoint_id=endpoint_id,
        description="Success scenario",
    )

    scenario.add_response(
        status_code=200,
        body=MockDataGenerator.generate_success_response(data),
        headers={"Content-Type": "application/json"},
        delay_ms=delay_ms,
    )

    return scenario


def create_error_scenario(
    name: str,
    endpoint_id: str,
    status_code: int = 500,
    message: Optional[str] = None,
    delay_ms: int = 100,
) -> MockScenario:
    """Create a simple error scenario."""
    scenario = MockScenario(
        name=name,
        endpoint_id=endpoint_id,
        description=f"Error scenario ({status_code})",
    )

    scenario.add_response(
        status_code=status_code,
        body=MockDataGenerator.generate_error_response(status_code, message),
        headers={"Content-Type": "application/json"},
        delay_ms=delay_ms,
    )

    return scenario


def create_timeout_scenario(
    name: str,
    endpoint_id: str,
    delay_ms: int = 30000,
) -> MockScenario:
    """Create a timeout scenario."""
    scenario = MockScenario(
        name=name,
        endpoint_id=endpoint_id,
        description="Timeout scenario",
    )

    scenario.add_response(
        status_code=504,
        body=MockDataGenerator.generate_error_response(504, "Gateway Timeout"),
        headers={"Content-Type": "application/json"},
        delay_ms=delay_ms,
    )

    return scenario
