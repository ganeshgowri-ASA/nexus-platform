"""
API Testing Module

Provides APITestGenerator, EndpointTester, and ResponseValidator for API testing.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
import httpx
from jsonschema import validate, ValidationError
import time

logger = logging.getLogger(__name__)


class ResponseValidator:
    """
    HTTP response validator.

    Validates status codes, headers, body, and JSON schemas.
    """

    def __init__(self):
        """Initialize response validator."""
        self.logger = logging.getLogger(__name__)

    def validate_status_code(
        self,
        actual: int,
        expected: int,
    ) -> Dict[str, Any]:
        """Validate status code."""
        return {
            "valid": actual == expected,
            "actual": actual,
            "expected": expected,
            "message": f"Status code: {actual} {'==' if actual == expected else '!='} {expected}",
        }

    def validate_headers(
        self,
        headers: Dict[str, str],
        required_headers: List[str],
    ) -> Dict[str, Any]:
        """Validate required headers."""
        missing = [h for h in required_headers if h not in headers]

        return {
            "valid": len(missing) == 0,
            "missing_headers": missing,
            "message": f"Missing headers: {missing}" if missing else "All headers present",
        }

    def validate_json_schema(
        self,
        response_json: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate JSON against schema."""
        try:
            validate(instance=response_json, schema=schema)
            return {
                "valid": True,
                "message": "JSON schema valid",
            }
        except ValidationError as e:
            return {
                "valid": False,
                "error": str(e),
                "message": "JSON schema validation failed",
            }

    def validate_response_time(
        self,
        response_time_ms: float,
        max_time_ms: float,
    ) -> Dict[str, Any]:
        """Validate response time."""
        return {
            "valid": response_time_ms <= max_time_ms,
            "actual_ms": response_time_ms,
            "max_ms": max_time_ms,
            "message": f"Response time: {response_time_ms:.2f}ms {'<=' if response_time_ms <= max_time_ms else '>'} {max_time_ms}ms",
        }

    def validate_body_contains(
        self,
        body: str,
        expected_content: str,
    ) -> Dict[str, Any]:
        """Validate body contains content."""
        contains = expected_content in body

        return {
            "valid": contains,
            "message": f"Body {'contains' if contains else 'does not contain'} expected content",
        }


class EndpointTester:
    """
    HTTP endpoint tester.

    Tests individual API endpoints with various HTTP methods.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize endpoint tester.

        Args:
            base_url: Base URL for API
            timeout: Request timeout
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.validator = ResponseValidator()
        self.logger = logging.getLogger(__name__)

    async def test_endpoint(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        expected_status: int = 200,
        max_response_time_ms: float = 5000,
        validate_schema: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Test an API endpoint comprehensively.

        Args:
            method: HTTP method
            endpoint: Endpoint path
            headers: Request headers
            params: Query parameters
            json_data: JSON body
            data: Form data
            expected_status: Expected status code
            max_response_time_ms: Max response time
            validate_schema: JSON schema to validate

        Returns:
            Comprehensive test result
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        start_time = time.time()

        try:
            response = await self.client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=data,
            )

            response_time_ms = (time.time() - start_time) * 1000

            # Validate status code
            status_validation = self.validator.validate_status_code(
                response.status_code,
                expected_status,
            )

            # Validate response time
            time_validation = self.validator.validate_response_time(
                response_time_ms,
                max_response_time_ms,
            )

            # Parse response body
            try:
                response_json = response.json()
            except:
                response_json = None

            # Validate JSON schema if provided
            schema_validation = None
            if validate_schema and response_json:
                schema_validation = self.validator.validate_json_schema(
                    response_json,
                    validate_schema,
                )

            all_valid = status_validation["valid"] and time_validation["valid"]
            if schema_validation:
                all_valid = all_valid and schema_validation["valid"]

            result = {
                "success": all_valid,
                "method": method.upper(),
                "url": url,
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "headers": dict(response.headers),
                "response_body": response_json or response.text,
                "validations": {
                    "status": status_validation,
                    "response_time": time_validation,
                },
            }

            if schema_validation:
                result["validations"]["schema"] = schema_validation

            return result

        except Exception as e:
            self.logger.error(f"Endpoint test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": method.upper(),
                "url": url,
            }

    async def test_get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test GET endpoint."""
        return await self.test_endpoint("GET", endpoint, **kwargs)

    async def test_post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test POST endpoint."""
        return await self.test_endpoint("POST", endpoint, **kwargs)

    async def test_put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test PUT endpoint."""
        return await self.test_endpoint("PUT", endpoint, **kwargs)

    async def test_delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test DELETE endpoint."""
        return await self.test_endpoint("DELETE", endpoint, **kwargs)

    async def test_patch(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test PATCH endpoint."""
        return await self.test_endpoint("PATCH", endpoint, **kwargs)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.client.aclose()


class APITestGenerator:
    """
    API test generator.

    Generates API tests from OpenAPI/Swagger specifications.
    """

    def __init__(self, base_url: str):
        """
        Initialize API test generator.

        Args:
            base_url: Base API URL
        """
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        self.endpoint_tester = EndpointTester(base_url)

    async def generate_from_openapi(
        self,
        spec: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generate test cases from OpenAPI specification.

        Args:
            spec: OpenAPI spec dictionary

        Returns:
            List of generated test cases
        """
        test_cases = []

        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    test_case = self._generate_test_case(
                        path,
                        method,
                        operation,
                    )
                    test_cases.append(test_case)

        self.logger.info(f"Generated {len(test_cases)} test cases from OpenAPI spec")
        return test_cases

    def _generate_test_case(
        self,
        path: str,
        method: str,
        operation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate test case for an operation."""
        test_case = {
            "name": f"test_{method}_{path.replace('/', '_')}",
            "method": method,
            "endpoint": path,
            "description": operation.get("summary", ""),
            "parameters": operation.get("parameters", []),
            "request_body": operation.get("requestBody", {}),
            "responses": operation.get("responses", {}),
        }

        # Get expected successful status code
        if "200" in test_case["responses"]:
            test_case["expected_status"] = 200
        elif "201" in test_case["responses"]:
            test_case["expected_status"] = 201
        else:
            test_case["expected_status"] = 200

        return test_case

    async def run_generated_tests(
        self,
        test_cases: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run generated test cases.

        Args:
            test_cases: List of test cases

        Returns:
            Test execution results
        """
        results = []
        passed = 0
        failed = 0

        for test_case in test_cases:
            result = await self.endpoint_tester.test_endpoint(
                method=test_case["method"],
                endpoint=test_case["endpoint"],
                expected_status=test_case.get("expected_status", 200),
            )

            results.append({
                "test_case": test_case["name"],
                "result": result,
            })

            if result.get("success"):
                passed += 1
            else:
                failed += 1

        return {
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / len(test_cases) * 100) if test_cases else 0,
            "results": results,
        }

    async def cleanup(self) -> None:
        """Cleanup resources."""
        await self.endpoint_tester.cleanup()
