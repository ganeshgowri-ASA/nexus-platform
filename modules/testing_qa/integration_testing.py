"""
Integration Testing Module

Provides IntegrationTestRunner, APITester, and DatabaseTester for integration testing.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import pytest

logger = logging.getLogger(__name__)


class DatabaseTester:
    """
    Database integration tester.

    Tests database operations, queries, and migrations.
    """

    def __init__(self, database_url: str):
        """
        Initialize database tester.

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.engine = None
        self.session_factory = None
        self.logger = logging.getLogger(__name__)

    def connect(self) -> bool:
        """
        Connect to database.

        Returns:
            True if successful
        """
        try:
            self.engine = create_engine(self.database_url)
            self.session_factory = sessionmaker(bind=self.engine)
            self.logger.info("Connected to database")
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False

    def get_session(self) -> Session:
        """Get database session."""
        if not self.session_factory:
            self.connect()
        return self.session_factory()

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection.

        Returns:
            Test result
        """
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT 1"))
                return {
                    "success": True,
                    "message": "Database connection successful",
                    "result": result.scalar(),
                }
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def test_query(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Test a database query.

        Args:
            query: SQL query to test
            params: Query parameters

        Returns:
            Query result
        """
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                rows = result.fetchall()
                return {
                    "success": True,
                    "row_count": len(rows),
                    "rows": [dict(row._mapping) for row in rows],
                }
        except Exception as e:
            self.logger.error(f"Query test failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def test_transaction(self, operations: List[str]) -> Dict[str, Any]:
        """
        Test database transaction.

        Args:
            operations: List of SQL operations

        Returns:
            Transaction result
        """
        try:
            with self.get_session() as session:
                for operation in operations:
                    session.execute(text(operation))
                session.commit()
                return {
                    "success": True,
                    "operations_count": len(operations),
                }
        except Exception as e:
            self.logger.error(f"Transaction test failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def cleanup(self) -> None:
        """Cleanup database resources."""
        if self.engine:
            self.engine.dispose()


class APITester:
    """
    API integration tester.

    Tests HTTP endpoints, request/response handling, and API contracts.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize API tester.

        Args:
            base_url: Base URL for API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        self.logger = logging.getLogger(__name__)

    async def test_endpoint(
        self,
        method: str,
        endpoint: str,
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        json_data: Dict[str, Any] = None,
        expected_status: int = 200,
    ) -> Dict[str, Any]:
        """
        Test an API endpoint.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            headers: Request headers
            params: Query parameters
            json_data: JSON request body
            expected_status: Expected status code

        Returns:
            Test result
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = await self.client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=json_data,
            )

            result = {
                "success": response.status_code == expected_status,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "headers": dict(response.headers),
            }

            try:
                result["response_body"] = response.json()
            except:
                result["response_body"] = response.text

            if response.status_code != expected_status:
                result["error"] = f"Status code mismatch: {response.status_code} != {expected_status}"

            return result

        except Exception as e:
            self.logger.error(f"API test failed for {method} {url}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def test_get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test GET request."""
        return await self.test_endpoint("GET", endpoint, **kwargs)

    async def test_post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test POST request."""
        return await self.test_endpoint("POST", endpoint, **kwargs)

    async def test_put(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test PUT request."""
        return await self.test_endpoint("PUT", endpoint, **kwargs)

    async def test_delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Test DELETE request."""
        return await self.test_endpoint("DELETE", endpoint, **kwargs)

    async def test_response_schema(
        self,
        endpoint: str,
        method: str = "GET",
        expected_schema: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Test API response schema.

        Args:
            endpoint: API endpoint
            method: HTTP method
            expected_schema: Expected JSON schema

        Returns:
            Schema validation result
        """
        response = await self.test_endpoint(method, endpoint)

        if not response.get("success"):
            return response

        # Simple schema validation
        response_body = response.get("response_body", {})
        schema_valid = True
        errors = []

        if expected_schema:
            for key, expected_type in expected_schema.items():
                if key not in response_body:
                    errors.append(f"Missing key: {key}")
                    schema_valid = False
                elif not isinstance(response_body[key], expected_type):
                    errors.append(f"Type mismatch for {key}: expected {expected_type}, got {type(response_body[key])}")
                    schema_valid = False

        return {
            "success": schema_valid,
            "schema_valid": schema_valid,
            "errors": errors,
            "response": response_body,
        }

    async def cleanup(self) -> None:
        """Cleanup API client."""
        await self.client.aclose()


class IntegrationTestRunner:
    """
    Integration test runner.

    Coordinates integration tests across multiple components.
    """

    def __init__(
        self,
        database_url: str = None,
        api_base_url: str = None,
    ):
        """
        Initialize integration test runner.

        Args:
            database_url: Database connection URL
            api_base_url: API base URL
        """
        self.database_url = database_url
        self.api_base_url = api_base_url
        self.logger = logging.getLogger(__name__)
        self.db_tester = None
        self.api_tester = None

    async def setup(self) -> None:
        """Setup test environment."""
        if self.database_url:
            self.db_tester = DatabaseTester(self.database_url)
            self.db_tester.connect()

        if self.api_base_url:
            self.api_tester = APITester(self.api_base_url)

        self.logger.info("Integration test environment setup complete")

    async def teardown(self) -> None:
        """Teardown test environment."""
        if self.db_tester:
            self.db_tester.cleanup()

        if self.api_tester:
            await self.api_tester.cleanup()

        self.logger.info("Integration test environment teardown complete")

    async def run_integration_suite(
        self,
        test_cases: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run integration test suite.

        Args:
            test_cases: List of test case configurations

        Returns:
            Suite execution results
        """
        await self.setup()

        results = []
        passed = 0
        failed = 0

        try:
            for test_case in test_cases:
                test_type = test_case.get("type")
                result = None

                if test_type == "database":
                    result = await self._run_database_test(test_case)
                elif test_type == "api":
                    result = await self._run_api_test(test_case)
                elif test_type == "workflow":
                    result = await self._run_workflow_test(test_case)

                if result:
                    results.append(result)
                    if result.get("success"):
                        passed += 1
                    else:
                        failed += 1

        finally:
            await self.teardown()

        return {
            "total_tests": len(test_cases),
            "passed": passed,
            "failed": failed,
            "results": results,
        }

    async def _run_database_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run database test case."""
        if not self.db_tester:
            return {"success": False, "error": "Database tester not initialized"}

        operation = test_case.get("operation")

        if operation == "query":
            return await self.db_tester.test_query(
                test_case.get("query"),
                test_case.get("params"),
            )
        elif operation == "transaction":
            return await self.db_tester.test_transaction(
                test_case.get("operations"),
            )

        return {"success": False, "error": f"Unknown operation: {operation}"}

    async def _run_api_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run API test case."""
        if not self.api_tester:
            return {"success": False, "error": "API tester not initialized"}

        return await self.api_tester.test_endpoint(
            method=test_case.get("method", "GET"),
            endpoint=test_case.get("endpoint"),
            headers=test_case.get("headers"),
            json_data=test_case.get("json"),
            expected_status=test_case.get("expected_status", 200),
        )

    async def _run_workflow_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run workflow test case (multi-step)."""
        steps = test_case.get("steps", [])
        results = []

        for step in steps:
            step_type = step.get("type")
            result = None

            if step_type == "database":
                result = await self._run_database_test(step)
            elif step_type == "api":
                result = await self._run_api_test(step)

            results.append(result)

            # Stop on first failure if configured
            if not result.get("success") and test_case.get("stop_on_failure", True):
                break

        all_success = all(r.get("success") for r in results)

        return {
            "success": all_success,
            "steps_completed": len(results),
            "total_steps": len(steps),
            "step_results": results,
        }
