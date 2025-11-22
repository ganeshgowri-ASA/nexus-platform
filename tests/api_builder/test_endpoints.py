"""
Tests for the endpoints module.
"""

import pytest
from modules.api_builder.endpoints import (
    Endpoint,
    EndpointManager,
    HTTPMethod,
    Parameter,
    ParameterType,
    DataType,
    RequestBody,
    Response,
)


class TestParameter:
    """Tests for Parameter class."""

    def test_parameter_creation(self):
        """Test creating a parameter."""
        param = Parameter(
            name="user_id",
            param_type=ParameterType.PATH,
            data_type=DataType.INTEGER,
            required=True,
            description="User ID",
        )

        assert param.name == "user_id"
        assert param.param_type == ParameterType.PATH
        assert param.data_type == DataType.INTEGER
        assert param.required is True

    def test_parameter_validation_success(self):
        """Test parameter validation with valid data."""
        param = Parameter(
            name="age",
            param_type=ParameterType.QUERY,
            data_type=DataType.INTEGER,
            minimum=0,
            maximum=120,
        )

        is_valid, error = param.validate(25)
        assert is_valid is True
        assert error is None

    def test_parameter_validation_failure(self):
        """Test parameter validation with invalid data."""
        param = Parameter(
            name="age",
            param_type=ParameterType.QUERY,
            data_type=DataType.INTEGER,
            minimum=0,
            maximum=120,
        )

        is_valid, error = param.validate(150)
        assert is_valid is False
        assert "at most 120" in error

    def test_parameter_to_dict(self):
        """Test converting parameter to dictionary."""
        param = Parameter(
            name="email",
            param_type=ParameterType.QUERY,
            data_type=DataType.STRING,
            pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
        )

        param_dict = param.to_dict()

        assert param_dict["name"] == "email"
        assert param_dict["in"] == "query"
        assert param_dict["type"] == "string"
        assert param_dict["pattern"] is not None


class TestEndpoint:
    """Tests for Endpoint class."""

    def test_endpoint_creation(self):
        """Test creating an endpoint."""
        endpoint = Endpoint(
            path="/api/users",
            method=HTTPMethod.GET,
            summary="Get all users",
            description="Returns a list of all users",
            tags=["users"],
        )

        assert endpoint.path == "/api/users"
        assert endpoint.method == HTTPMethod.GET
        assert endpoint.summary == "Get all users"
        assert "users" in endpoint.tags

    def test_endpoint_with_path_parameters(self):
        """Test endpoint with path parameters."""
        endpoint = Endpoint(
            path="/api/users/{user_id}",
            method=HTTPMethod.GET,
        )

        endpoint.parameters.append(
            Parameter(
                name="user_id",
                param_type=ParameterType.PATH,
                data_type=DataType.INTEGER,
                required=True,
            )
        )

        path_params = endpoint.get_path_parameters()
        assert len(path_params) == 1
        assert path_params[0].name == "user_id"

    def test_endpoint_path_validation_success(self):
        """Test valid endpoint path."""
        endpoint = Endpoint(
            path="/api/users/{user_id}",
            method=HTTPMethod.GET,
        )

        endpoint.parameters.append(
            Parameter(
                name="user_id",
                param_type=ParameterType.PATH,
                data_type=DataType.INTEGER,
                required=True,
            )
        )

        is_valid, error = endpoint.validate_path()
        assert is_valid is True
        assert error is None

    def test_endpoint_path_validation_failure(self):
        """Test invalid endpoint path."""
        endpoint = Endpoint(
            path="/api/users/{user_id}",
            method=HTTPMethod.GET,
        )

        # Missing path parameter definition
        is_valid, error = endpoint.validate_path()
        assert is_valid is False
        assert "not defined" in error

    def test_endpoint_to_dict(self):
        """Test converting endpoint to dictionary."""
        endpoint = Endpoint(
            path="/api/users",
            method=HTTPMethod.POST,
            summary="Create user",
        )

        endpoint_dict = endpoint.to_dict()

        assert endpoint_dict["path"] == "/api/users"
        assert endpoint_dict["method"] == "POST"
        assert endpoint_dict["summary"] == "Create user"
        assert "id" in endpoint_dict
        assert "responses" in endpoint_dict


class TestEndpointManager:
    """Tests for EndpointManager class."""

    def test_create_endpoint(self):
        """Test creating an endpoint."""
        manager = EndpointManager()

        endpoint = Endpoint(
            path="/api/users",
            method=HTTPMethod.GET,
        )

        created = manager.create(endpoint)

        assert created.id == endpoint.id
        assert len(manager.endpoints) == 1

    def test_create_duplicate_endpoint(self):
        """Test creating a duplicate endpoint."""
        manager = EndpointManager()

        endpoint1 = Endpoint(path="/api/users", method=HTTPMethod.GET)
        manager.create(endpoint1)

        endpoint2 = Endpoint(path="/api/users", method=HTTPMethod.GET)

        with pytest.raises(ValueError, match="already exists"):
            manager.create(endpoint2)

    def test_read_endpoint(self):
        """Test reading an endpoint."""
        manager = EndpointManager()

        endpoint = Endpoint(path="/api/users", method=HTTPMethod.GET)
        created = manager.create(endpoint)

        read_endpoint = manager.read(created.id)

        assert read_endpoint is not None
        assert read_endpoint.id == created.id

    def test_update_endpoint(self):
        """Test updating an endpoint."""
        manager = EndpointManager()

        endpoint = Endpoint(path="/api/users", method=HTTPMethod.GET)
        created = manager.create(endpoint)

        created.summary = "Updated summary"
        updated = manager.update(created.id, created)

        assert updated.summary == "Updated summary"

    def test_delete_endpoint(self):
        """Test deleting an endpoint."""
        manager = EndpointManager()

        endpoint = Endpoint(path="/api/users", method=HTTPMethod.GET)
        created = manager.create(endpoint)

        result = manager.delete(created.id)

        assert result is True
        assert len(manager.endpoints) == 0

    def test_list_endpoints(self):
        """Test listing endpoints."""
        manager = EndpointManager()

        manager.create(Endpoint(path="/api/users", method=HTTPMethod.GET))
        manager.create(Endpoint(path="/api/users", method=HTTPMethod.POST))
        manager.create(Endpoint(path="/api/posts", method=HTTPMethod.GET))

        all_endpoints = manager.list()
        assert len(all_endpoints) == 3

        get_endpoints = manager.list(method=HTTPMethod.GET)
        assert len(get_endpoints) == 2

    def test_search_endpoints(self):
        """Test searching endpoints."""
        manager = EndpointManager()

        manager.create(Endpoint(
            path="/api/users",
            method=HTTPMethod.GET,
            summary="Get users",
        ))
        manager.create(Endpoint(
            path="/api/posts",
            method=HTTPMethod.GET,
            summary="Get posts",
        ))

        results = manager.search("users")
        assert len(results) == 1
        assert results[0].path == "/api/users"

    def test_get_statistics(self):
        """Test getting endpoint statistics."""
        manager = EndpointManager()

        manager.create(Endpoint(
            path="/api/users",
            method=HTTPMethod.GET,
            tags=["users"],
        ))
        manager.create(Endpoint(
            path="/api/users",
            method=HTTPMethod.POST,
            tags=["users"],
        ))
        manager.create(Endpoint(
            path="/api/posts",
            method=HTTPMethod.GET,
            tags=["posts"],
            deprecated=True,
        ))

        stats = manager.get_statistics()

        assert stats["total"] == 3
        assert stats["by_method"]["GET"] == 2
        assert stats["by_method"]["POST"] == 1
        assert stats["by_tag"]["users"] == 2
        assert stats["deprecated"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
