"""
Tests for the core API Builder.
"""

import pytest
import json
from modules.api_builder.builder import APIBuilder, APIProject
from modules.api_builder.endpoints import HTTPMethod, ParameterType, DataType
from modules.api_builder.auth import create_api_key_auth
from modules.api_builder.versioning import create_version, VersionStatus


class TestAPIBuilder:
    """Tests for APIBuilder class."""

    def test_create_api_builder(self):
        """Test creating an API builder."""
        builder = APIBuilder()

        assert builder.project is not None
        assert builder.endpoint_manager is not None
        assert builder.auth_manager is not None

    def test_create_endpoint(self):
        """Test creating an endpoint through builder."""
        builder = APIBuilder()

        endpoint = builder.create_endpoint(
            path="/api/users",
            method=HTTPMethod.GET,
            summary="Get all users",
            tags=["users"],
        )

        assert endpoint is not None
        assert endpoint.path == "/api/users"
        assert endpoint.method == HTTPMethod.GET

        # Verify it's in the manager
        retrieved = builder.get_endpoint(endpoint.id)
        assert retrieved is not None

    def test_list_endpoints(self):
        """Test listing endpoints."""
        builder = APIBuilder()

        builder.create_endpoint("/api/users", HTTPMethod.GET)
        builder.create_endpoint("/api/posts", HTTPMethod.GET)

        endpoints = builder.list_endpoints()

        assert len(endpoints) == 2

    def test_search_endpoints(self):
        """Test searching endpoints."""
        builder = APIBuilder()

        builder.create_endpoint("/api/users", HTTPMethod.GET, summary="Get users")
        builder.create_endpoint("/api/posts", HTTPMethod.GET, summary="Get posts")

        results = builder.search_endpoints("users")

        assert len(results) == 1
        assert results[0].path == "/api/users"

    def test_add_auth_scheme(self):
        """Test adding authentication scheme."""
        builder = APIBuilder()

        auth = create_api_key_auth()
        builder.add_auth_scheme(auth)

        scheme = builder.auth_manager.get_scheme("apiKey")

        assert scheme is not None

    def test_add_version(self):
        """Test adding an API version."""
        builder = APIBuilder()

        version = create_version("1.0.0", VersionStatus.STABLE)
        builder.add_version(version)

        retrieved = builder.get_version("1.0.0")

        assert retrieved is not None
        assert retrieved.version == "1.0.0"

    def test_generate_openapi_spec(self):
        """Test generating OpenAPI specification."""
        builder = APIBuilder()

        builder.create_endpoint("/api/users", HTTPMethod.GET, summary="Get users")

        spec_json = builder.generate_openapi_spec(format="json")

        assert spec_json is not None

        # Verify it's valid JSON
        spec = json.loads(spec_json)
        assert "openapi" in spec
        assert "paths" in spec
        assert "/api/users" in spec["paths"]

    def test_export_and_import_project(self):
        """Test exporting and importing a project."""
        builder = APIBuilder()

        # Create some data
        builder.project.name = "Test API"
        builder.create_endpoint("/api/users", HTTPMethod.GET)
        auth = create_api_key_auth()
        builder.add_auth_scheme(auth)

        # Export
        exported = builder.export_project()

        # Create new builder and import
        new_builder = APIBuilder()
        new_builder.import_project(exported)

        # Verify data
        assert new_builder.project.name == "Test API"
        assert len(new_builder.list_endpoints()) == 1
        assert new_builder.auth_manager.get_scheme("apiKey") is not None

    def test_validate_project(self):
        """Test project validation."""
        builder = APIBuilder()

        builder.project.name = "Test API"
        builder.create_endpoint("/api/users", HTTPMethod.GET)

        is_valid, errors = builder.validate_project()

        assert is_valid is True
        assert len(errors) == 0

    def test_get_project_statistics(self):
        """Test getting project statistics."""
        builder = APIBuilder()

        builder.create_endpoint("/api/users", HTTPMethod.GET)
        builder.create_endpoint("/api/posts", HTTPMethod.GET)

        stats = builder.get_project_statistics()

        assert stats["endpoints"]["total"] == 2
        assert stats["project"]["name"] is not None

    def test_create_mock_scenario(self):
        """Test creating a mock scenario."""
        builder = APIBuilder()

        endpoint = builder.create_endpoint("/api/users", HTTPMethod.GET)
        scenario = builder.create_mock_scenario("success", endpoint.id)

        assert scenario is not None
        assert scenario.name == "success"

    def test_simulate_request(self):
        """Test simulating an API request."""
        builder = APIBuilder()

        endpoint = builder.create_endpoint("/api/users", HTTPMethod.GET)
        builder.create_mock_scenario("success", endpoint.id)

        response = builder.simulate_request(endpoint.id)

        assert response is not None
        assert "status_code" in response
        assert "body" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
