"""
Testing Module

Built-in API testing framework with request builder, response validation, and test collections.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import re
import time
from datetime import datetime


class AssertionType(Enum):
    """Types of assertions."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    MATCHES_REGEX = "matches_regex"
    HAS_KEY = "has_key"
    HAS_LENGTH = "has_length"
    IS_TYPE = "is_type"


@dataclass
class Assertion:
    """Represents a test assertion."""
    assertion_type: AssertionType
    path: str  # JSONPath or response field
    expected: Any
    description: str = ""

    def evaluate(self, actual: Any) -> tuple[bool, Optional[str]]:
        """Evaluate the assertion."""
        try:
            if self.assertion_type == AssertionType.EQUALS:
                result = actual == self.expected
                error = None if result else f"Expected {self.expected}, got {actual}"

            elif self.assertion_type == AssertionType.NOT_EQUALS:
                result = actual != self.expected
                error = None if result else f"Expected not {self.expected}, but got {actual}"

            elif self.assertion_type == AssertionType.CONTAINS:
                result = self.expected in actual
                error = None if result else f"Expected {actual} to contain {self.expected}"

            elif self.assertion_type == AssertionType.NOT_CONTAINS:
                result = self.expected not in actual
                error = None if result else f"Expected {actual} to not contain {self.expected}"

            elif self.assertion_type == AssertionType.GREATER_THAN:
                result = actual > self.expected
                error = None if result else f"Expected {actual} > {self.expected}"

            elif self.assertion_type == AssertionType.LESS_THAN:
                result = actual < self.expected
                error = None if result else f"Expected {actual} < {self.expected}"

            elif self.assertion_type == AssertionType.MATCHES_REGEX:
                result = bool(re.match(self.expected, str(actual)))
                error = None if result else f"Expected {actual} to match pattern {self.expected}"

            elif self.assertion_type == AssertionType.HAS_KEY:
                result = self.expected in actual
                error = None if result else f"Expected key '{self.expected}' in {actual}"

            elif self.assertion_type == AssertionType.HAS_LENGTH:
                result = len(actual) == self.expected
                error = None if result else f"Expected length {self.expected}, got {len(actual)}"

            elif self.assertion_type == AssertionType.IS_TYPE:
                type_map = {
                    "string": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                }
                expected_type = type_map.get(self.expected, self.expected)
                result = isinstance(actual, expected_type)
                error = None if result else f"Expected type {self.expected}, got {type(actual).__name__}"

            else:
                result = False
                error = f"Unknown assertion type: {self.assertion_type}"

            return result, error

        except Exception as e:
            return False, f"Assertion error: {str(e)}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.assertion_type.value,
            "path": self.path,
            "expected": self.expected,
            "description": self.description,
        }


@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    endpoint_id: str
    description: str = ""
    path_params: Dict[str, Any] = field(default_factory=dict)
    query_params: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    assertions: List[Assertion] = field(default_factory=list)
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None
    timeout: int = 30  # seconds
    enabled: bool = True

    def add_assertion(
        self,
        assertion_type: AssertionType,
        path: str,
        expected: Any,
        description: str = "",
    ) -> None:
        """Add an assertion to the test case."""
        self.assertions.append(
            Assertion(
                assertion_type=assertion_type,
                path=path,
                expected=expected,
                description=description,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "endpoint_id": self.endpoint_id,
            "description": self.description,
            "path_params": self.path_params,
            "query_params": self.query_params,
            "headers": self.headers,
            "body": self.body,
            "assertions": [a.to_dict() for a in self.assertions],
            "timeout": self.timeout,
            "enabled": self.enabled,
        }


@dataclass
class TestResult:
    """Represents test execution result."""
    test_name: str
    passed: bool
    duration: float  # seconds
    assertions_passed: int
    assertions_failed: int
    errors: List[str] = field(default_factory=list)
    response_status: Optional[int] = None
    response_time: Optional[float] = None
    response_body: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "duration": self.duration,
            "assertions_passed": self.assertions_passed,
            "assertions_failed": self.assertions_failed,
            "errors": self.errors,
            "response_status": self.response_status,
            "response_time": self.response_time,
            "timestamp": self.timestamp.isoformat(),
        }


class ResponseValidator:
    """Validates API responses."""

    @staticmethod
    def validate_status_code(
        response_status: int,
        expected_status: int,
    ) -> tuple[bool, Optional[str]]:
        """Validate response status code."""
        if response_status == expected_status:
            return True, None
        return False, f"Expected status {expected_status}, got {response_status}"

    @staticmethod
    def validate_headers(
        response_headers: Dict[str, str],
        expected_headers: Dict[str, str],
    ) -> tuple[bool, List[str]]:
        """Validate response headers."""
        errors = []

        for key, expected_value in expected_headers.items():
            if key not in response_headers:
                errors.append(f"Missing header: {key}")
            elif response_headers[key] != expected_value:
                errors.append(f"Header {key}: expected {expected_value}, got {response_headers[key]}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_json_schema(
        response_body: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        """Validate response against JSON schema (simplified)."""
        errors = []

        def validate_field(path: str, value: Any, field_schema: Dict[str, Any]) -> None:
            # Check type
            expected_type = field_schema.get("type")
            if expected_type:
                type_map = {
                    "string": str,
                    "integer": int,
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "object": dict,
                }

                python_type = type_map.get(expected_type)
                if python_type and not isinstance(value, python_type):
                    errors.append(f"{path}: expected type {expected_type}, got {type(value).__name__}")

            # Check required fields for objects
            if isinstance(value, dict):
                required = field_schema.get("required", [])
                for req_field in required:
                    if req_field not in value:
                        errors.append(f"{path}: missing required field '{req_field}'")

                # Validate nested fields
                properties = field_schema.get("properties", {})
                for field_name, field_value in value.items():
                    if field_name in properties:
                        validate_field(
                            f"{path}.{field_name}",
                            field_value,
                            properties[field_name]
                        )

            # Check array items
            if isinstance(value, list):
                items_schema = field_schema.get("items")
                if items_schema:
                    for i, item in enumerate(value):
                        validate_field(f"{path}[{i}]", item, items_schema)

        validate_field("$", response_body, schema)

        return len(errors) == 0, errors

    @staticmethod
    def get_value_by_path(data: Any, path: str) -> Any:
        """Get value from data using JSONPath-like syntax."""
        if path == "$":
            return data

        # Simple implementation - supports basic paths like $.field.nested[0].value
        parts = path.split('.')
        current = data

        for part in parts:
            if part == "$":
                continue

            # Handle array indexing
            if '[' in part:
                field, index_part = part.split('[', 1)
                index = int(index_part.rstrip(']'))

                if field:
                    current = current[field]
                current = current[index]
            else:
                current = current[part]

        return current


class TestCollection:
    """A collection of test cases."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tests: List[TestCase] = []
        self.variables: Dict[str, Any] = {}  # Shared variables for tests

    def add_test(self, test: TestCase) -> None:
        """Add a test to the collection."""
        self.tests.append(test)

    def remove_test(self, test_name: str) -> bool:
        """Remove a test from the collection."""
        for i, test in enumerate(self.tests):
            if test.name == test_name:
                del self.tests[i]
                return True
        return False

    def set_variable(self, key: str, value: Any) -> None:
        """Set a collection variable."""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a collection variable."""
        return self.variables.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "tests": [t.to_dict() for t in self.tests],
            "variables": self.variables,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestCollection':
        """Create collection from dictionary."""
        collection = cls(data["name"], data.get("description", ""))
        collection.variables = data.get("variables", {})

        for test_data in data.get("tests", []):
            assertions = []
            for assertion_data in test_data.get("assertions", []):
                assertions.append(
                    Assertion(
                        assertion_type=AssertionType(assertion_data["type"]),
                        path=assertion_data["path"],
                        expected=assertion_data["expected"],
                        description=assertion_data.get("description", ""),
                    )
                )

            test = TestCase(
                name=test_data["name"],
                endpoint_id=test_data["endpoint_id"],
                description=test_data.get("description", ""),
                path_params=test_data.get("path_params", {}),
                query_params=test_data.get("query_params", {}),
                headers=test_data.get("headers", {}),
                body=test_data.get("body"),
                assertions=assertions,
                timeout=test_data.get("timeout", 30),
                enabled=test_data.get("enabled", True),
            )
            collection.add_test(test)

        return collection


class APITester:
    """Main API testing framework."""

    def __init__(self):
        self.collections: Dict[str, TestCollection] = {}
        self.results: List[TestResult] = []
        self.validator = ResponseValidator()

    def add_collection(self, collection: TestCollection) -> None:
        """Add a test collection."""
        self.collections[collection.name] = collection

    def run_test(
        self,
        test: TestCase,
        mock_response: Optional[Dict[str, Any]] = None,
    ) -> TestResult:
        """Run a single test case."""
        start_time = time.time()
        errors = []
        assertions_passed = 0
        assertions_failed = 0

        try:
            # Run setup if provided
            if test.setup:
                test.setup()

            # Simulate or make actual request
            # In production, this would make actual HTTP requests
            # For now, we'll use the mock response
            response = mock_response or {
                "status": 200,
                "headers": {},
                "body": {},
                "time": 0.1,
            }

            response_status = response.get("status", 200)
            response_body = response.get("body", {})
            response_time = response.get("time", 0.0)

            # Run assertions
            for assertion in test.assertions:
                try:
                    # Get value from response
                    if assertion.path.startswith("status"):
                        actual_value = response_status
                    elif assertion.path.startswith("headers"):
                        header_name = assertion.path.split('.')[-1]
                        actual_value = response.get("headers", {}).get(header_name)
                    elif assertion.path.startswith("time"):
                        actual_value = response_time
                    else:
                        # Extract from body
                        actual_value = self.validator.get_value_by_path(
                            response_body,
                            assertion.path
                        )

                    # Evaluate assertion
                    passed, error = assertion.evaluate(actual_value)

                    if passed:
                        assertions_passed += 1
                    else:
                        assertions_failed += 1
                        errors.append(error or "Assertion failed")

                except Exception as e:
                    assertions_failed += 1
                    errors.append(f"Assertion error: {str(e)}")

            # Run teardown if provided
            if test.teardown:
                test.teardown()

        except Exception as e:
            errors.append(f"Test execution error: {str(e)}")

        duration = time.time() - start_time
        passed = len(errors) == 0 and assertions_failed == 0

        result = TestResult(
            test_name=test.name,
            passed=passed,
            duration=duration,
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed,
            errors=errors,
            response_status=response.get("status") if mock_response else None,
            response_time=response.get("time") if mock_response else None,
            response_body=response.get("body") if mock_response else None,
        )

        self.results.append(result)
        return result

    def run_collection(
        self,
        collection_name: str,
        mock_responses: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[TestResult]:
        """Run all tests in a collection."""
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found")

        collection = self.collections[collection_name]
        results = []

        for test in collection.tests:
            if not test.enabled:
                continue

            mock_response = None
            if mock_responses and test.name in mock_responses:
                mock_response = mock_responses[test.name]

            result = self.run_test(test, mock_response)
            results.append(result)

        return results

    def run_all_collections(
        self,
        mock_responses: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
    ) -> Dict[str, List[TestResult]]:
        """Run all test collections."""
        all_results = {}

        for collection_name in self.collections:
            collection_mocks = None
            if mock_responses and collection_name in mock_responses:
                collection_mocks = mock_responses[collection_name]

            results = self.run_collection(collection_name, collection_mocks)
            all_results[collection_name] = results

        return all_results

    def get_statistics(self) -> Dict[str, Any]:
        """Get testing statistics."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests

        total_assertions = sum(r.assertions_passed + r.assertions_failed for r in self.results)
        passed_assertions = sum(r.assertions_passed for r in self.results)
        failed_assertions = sum(r.assertions_failed for r in self.results)

        avg_duration = sum(r.duration for r in self.results) / total_tests if total_tests > 0 else 0

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_assertions": total_assertions,
            "passed_assertions": passed_assertions,
            "failed_assertions": failed_assertions,
            "average_duration": avg_duration,
        }

    def export_results(self, format: str = "json") -> str:
        """Export test results."""
        data = {
            "results": [r.to_dict() for r in self.results],
            "statistics": self.get_statistics(),
            "timestamp": datetime.now().isoformat(),
        }

        if format == "json":
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def clear_results(self) -> None:
        """Clear test results."""
        self.results = []
