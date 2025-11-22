"""
Core API Builder Module

Main orchestrator that brings together all components: endpoints, authentication,
rate limiting, documentation, testing, mocking, and versioning.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime
import uuid

from .endpoints import (
    Endpoint,
    EndpointManager,
    HTTPMethod,
    Parameter,
    ParameterType,
    DataType,
    RequestBody,
    Response,
)
from .auth import AuthManager, AuthScheme
from .rate_limiting import RateLimiter, QuotaManager
from .docs import (
    OpenAPIGenerator,
    DocumentationGenerator,
    InteractiveExplorer,
    APIInfo,
    ServerInfo,
)
from .testing import APITester, TestCollection
from .mock import MockServer
from .versioning import (
    VersionManager,
    APIVersion,
    VersioningStrategy,
    VersionStatus,
)


@dataclass
class APIProject:
    """Represents a complete API project."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    base_url: str = "https://api.example.com"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "base_url": self.base_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata,
        }


class APIBuilder:
    """
    Main API Builder class that orchestrates all components.

    This is the primary interface for creating, managing, and testing APIs.
    """

    def __init__(self, project: Optional[APIProject] = None):
        self.project = project or APIProject(name="My API", description="API built with NEXUS")

        # Core components
        self.endpoint_manager = EndpointManager()
        self.auth_manager = AuthManager()
        self.rate_limiter = RateLimiter()
        self.version_manager = VersionManager()
        self.mock_server = MockServer()
        self.api_tester = APITester()

        # Documentation components
        self._init_documentation()

    def _init_documentation(self):
        """Initialize documentation components."""
        api_info = APIInfo(
            title=self.project.name,
            version=self.project.version,
            description=self.project.description,
        )

        servers = [ServerInfo(url=self.project.base_url)]

        self.openapi_generator = OpenAPIGenerator(api_info, servers)
        self.doc_generator = DocumentationGenerator(self.openapi_generator)
        self.api_explorer = InteractiveExplorer()

    # Endpoint Management Methods

    def create_endpoint(
        self,
        path: str,
        method: HTTPMethod,
        summary: str = "",
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> Endpoint:
        """Create a new API endpoint."""
        endpoint = Endpoint(
            path=path,
            method=method,
            summary=summary,
            description=description,
            tags=tags or [],
        )

        self.endpoint_manager.create(endpoint)
        self.project.updated_at = datetime.now()

        return endpoint

    def update_endpoint(self, endpoint_id: str, endpoint: Endpoint) -> Endpoint:
        """Update an existing endpoint."""
        updated = self.endpoint_manager.update(endpoint_id, endpoint)
        self.project.updated_at = datetime.now()
        return updated

    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete an endpoint."""
        result = self.endpoint_manager.delete(endpoint_id)
        if result:
            self.project.updated_at = datetime.now()
        return result

    def get_endpoint(self, endpoint_id: str) -> Optional[Endpoint]:
        """Get an endpoint by ID."""
        return self.endpoint_manager.read(endpoint_id)

    def list_endpoints(
        self,
        method: Optional[HTTPMethod] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Endpoint]:
        """List endpoints with optional filtering."""
        return self.endpoint_manager.list(method=method, tags=tags)

    def search_endpoints(self, query: str) -> List[Endpoint]:
        """Search endpoints."""
        return self.endpoint_manager.search(query)

    # Authentication Methods

    def add_auth_scheme(self, scheme: AuthScheme) -> None:
        """Add an authentication scheme."""
        self.auth_manager.add_scheme(scheme)
        self.project.updated_at = datetime.now()

    def remove_auth_scheme(self, scheme_name: str) -> bool:
        """Remove an authentication scheme."""
        result = self.auth_manager.remove_scheme(scheme_name)
        if result:
            self.project.updated_at = datetime.now()
        return result

    def set_global_auth(self, scheme_names: List[str]) -> None:
        """Set global authentication schemes."""
        self.auth_manager.set_global_schemes(scheme_names)
        self.project.updated_at = datetime.now()

    def authenticate(
        self,
        scheme_name: str,
        credentials: Dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        """Authenticate credentials."""
        return self.auth_manager.authenticate(scheme_name, credentials)

    # Rate Limiting Methods

    def add_rate_limit(
        self,
        name: str,
        rule: Any,  # RateLimitRule
        strategy: Any = None,  # ThrottleStrategy
    ) -> None:
        """Add a rate limit policy."""
        from .rate_limiting import ThrottleStrategy
        strategy = strategy or ThrottleStrategy.SLIDING_WINDOW
        self.rate_limiter.add_policy(name, rule, strategy)
        self.project.updated_at = datetime.now()

    def apply_rate_limit_to_endpoint(
        self,
        endpoint_id: str,
        policy_names: List[str],
    ) -> None:
        """Apply rate limiting to an endpoint."""
        self.rate_limiter.apply_to_endpoint(endpoint_id, policy_names)
        self.project.updated_at = datetime.now()

    def check_rate_limit(
        self,
        endpoint_id: str,
        identifier: str,
        user_id: Optional[str] = None,
    ) -> tuple[bool, List[Any], Optional[str]]:
        """Check rate limits for a request."""
        return self.rate_limiter.check_limits(endpoint_id, identifier, user_id)

    # Versioning Methods

    def add_version(self, version: APIVersion) -> None:
        """Add an API version."""
        self.version_manager.add_version(version)
        self.project.updated_at = datetime.now()

    def get_version(self, version: str) -> Optional[APIVersion]:
        """Get a specific version."""
        return self.version_manager.get_version(version)

    def list_versions(self) -> List[APIVersion]:
        """List all versions."""
        return list(self.version_manager.versions.values())

    def deprecate_version(
        self,
        version: str,
        message: str,
        sunset_days: int = 90,
        alternative: Optional[str] = None,
    ) -> None:
        """Deprecate a version."""
        api_version = self.version_manager.get_version(version)
        if api_version:
            api_version.mark_deprecated(message, sunset_days, alternative)
            self.project.updated_at = datetime.now()

    def generate_migration_guide(
        self,
        from_version: str,
        to_version: str,
    ) -> Dict[str, Any]:
        """Generate migration guide between versions."""
        return self.version_manager.generate_migration_guide(from_version, to_version)

    # Documentation Methods

    def generate_openapi_spec(
        self,
        format: str = "json",
    ) -> str:
        """Generate OpenAPI specification."""
        endpoints = list(self.endpoint_manager.endpoints.values())

        if format == "json":
            return self.openapi_generator.to_json(endpoints, self.auth_manager, self.project.tags)
        elif format == "yaml":
            return self.openapi_generator.to_yaml(endpoints, self.auth_manager, self.project.tags)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def generate_markdown_docs(self) -> str:
        """Generate Markdown documentation."""
        endpoints = list(self.endpoint_manager.endpoints.values())
        return self.doc_generator.generate_markdown(endpoints, self.project.base_url)

    def get_endpoint_docs(self, endpoint_id: str) -> Dict[str, Any]:
        """Get documentation for a specific endpoint."""
        endpoint = self.endpoint_manager.read(endpoint_id)
        if not endpoint:
            return {}

        return self.doc_generator.generate_endpoint_docs(endpoint, self.project.base_url)

    # Testing Methods

    def add_test_collection(self, collection: TestCollection) -> None:
        """Add a test collection."""
        self.api_tester.add_collection(collection)
        self.project.updated_at = datetime.now()

    def run_tests(
        self,
        collection_name: str,
        use_mock: bool = True,
    ) -> List[Any]:  # List[TestResult]
        """Run tests in a collection."""
        if use_mock:
            # Generate mock responses for tests
            collection = self.api_tester.collections.get(collection_name)
            if collection:
                mock_responses = {}
                for test in collection.tests:
                    endpoint = self.endpoint_manager.read(test.endpoint_id)
                    if endpoint:
                        # Use mock server to generate response
                        mock_response = self.mock_server.handle_request(
                            test.endpoint_id,
                            path_params=test.path_params,
                            query_params=test.query_params,
                            headers=test.headers,
                            body=test.body,
                        )
                        mock_responses[test.name] = mock_response

                return self.api_tester.run_collection(collection_name, mock_responses)

        return self.api_tester.run_collection(collection_name)

    def get_test_statistics(self) -> Dict[str, Any]:
        """Get testing statistics."""
        return self.api_tester.get_statistics()

    # Mock Server Methods

    def create_mock_scenario(
        self,
        name: str,
        endpoint_id: str,
    ) -> Any:  # MockScenario
        """Create a mock scenario for an endpoint."""
        endpoint = self.endpoint_manager.read(endpoint_id)
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} not found")

        scenario = self.mock_server.create_quick_scenario(name, endpoint_id, endpoint)
        self.project.updated_at = datetime.now()
        return scenario

    def add_mock_scenario(self, scenario: Any) -> None:
        """Add a custom mock scenario."""
        self.mock_server.add_scenario(scenario)
        self.project.updated_at = datetime.now()

    def simulate_request(
        self,
        endpoint_id: str,
        scenario_name: Optional[str] = None,
        path_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Simulate an API request using mock server."""
        return self.mock_server.handle_request(
            endpoint_id,
            scenario_name,
            path_params,
            query_params,
            headers,
            body,
        )

    # Project Management Methods

    def export_project(self, file_path: Optional[str] = None) -> str:
        """Export the entire project to JSON."""
        data = {
            "project": self.project.to_dict(),
            "endpoints": [e.to_dict() for e in self.endpoint_manager.endpoints.values()],
            "auth_schemes": {
                name: scheme.to_dict()
                for name, scheme in self.auth_manager.schemes.items()
            },
            "versions": [v.to_dict() for v in self.version_manager.versions.values()],
            "test_collections": [
                c.to_dict() for c in self.api_tester.collections.values()
            ],
            "mock_scenarios": json.loads(self.mock_server.export_scenarios()),
        }

        json_str = json.dumps(data, indent=2)

        if file_path:
            with open(file_path, 'w') as f:
                f.write(json_str)

        return json_str

    def import_project(self, json_str: str) -> None:
        """Import a project from JSON."""
        data = json.loads(json_str)

        # Import project info
        if "project" in data:
            project_data = data["project"]
            self.project = APIProject(
                id=project_data.get("id", str(uuid.uuid4())),
                name=project_data.get("name", ""),
                description=project_data.get("description", ""),
                version=project_data.get("version", "1.0.0"),
                base_url=project_data.get("base_url", ""),
                tags=project_data.get("tags", []),
                metadata=project_data.get("metadata", {}),
            )

        # Import endpoints
        if "endpoints" in data:
            for endpoint_data in data["endpoints"]:
                endpoint = Endpoint.from_dict(endpoint_data)
                try:
                    self.endpoint_manager.create(endpoint)
                except ValueError:
                    # Skip duplicates
                    pass

        # Import versions
        if "versions" in data:
            for version_data in data["versions"]:
                from .versioning import VersionStatus
                version = APIVersion(
                    version=version_data["version"],
                    status=VersionStatus(version_data["status"]),
                    description=version_data.get("description", ""),
                )
                self.version_manager.add_version(version)

        # Import test collections
        if "test_collections" in data:
            for collection_data in data["test_collections"]:
                collection = TestCollection.from_dict(collection_data)
                self.api_tester.add_collection(collection)

        # Import mock scenarios
        if "mock_scenarios" in data:
            self.mock_server.import_scenarios(json.dumps(data["mock_scenarios"]))

        # Reinitialize documentation
        self._init_documentation()

    def get_project_statistics(self) -> Dict[str, Any]:
        """Get comprehensive project statistics."""
        return {
            "project": {
                "name": self.project.name,
                "version": self.project.version,
                "created": self.project.created_at.isoformat(),
                "updated": self.project.updated_at.isoformat(),
            },
            "endpoints": self.endpoint_manager.get_statistics(),
            "auth_schemes": {
                "total": len(self.auth_manager.schemes),
                "schemes": list(self.auth_manager.schemes.keys()),
            },
            "versions": self.version_manager.get_statistics(),
            "tests": self.api_tester.get_statistics(),
            "mock_server": self.mock_server.get_statistics(),
        }

    # Quick Builder Methods

    @staticmethod
    def quick_endpoint(
        path: str,
        method: HTTPMethod = HTTPMethod.GET,
        summary: str = "",
    ) -> Endpoint:
        """Quickly create an endpoint (helper method)."""
        return Endpoint(
            path=path,
            method=method,
            summary=summary,
        )

    @staticmethod
    def quick_parameter(
        name: str,
        param_type: ParameterType,
        data_type: DataType = DataType.STRING,
        required: bool = False,
        description: str = "",
    ) -> Parameter:
        """Quickly create a parameter (helper method)."""
        return Parameter(
            name=name,
            param_type=param_type,
            data_type=data_type,
            required=required,
            description=description,
        )

    # Validation Methods

    def validate_project(self) -> tuple[bool, List[str]]:
        """Validate the entire project."""
        errors = []

        # Validate project info
        if not self.project.name:
            errors.append("Project name is required")

        if not self.project.version:
            errors.append("Project version is required")

        # Validate endpoints
        for endpoint in self.endpoint_manager.endpoints.values():
            is_valid, error = endpoint.validate_path()
            if not is_valid:
                errors.append(f"Endpoint {endpoint.path}: {error}")

        # Check for duplicate paths
        paths = {}
        for endpoint in self.endpoint_manager.endpoints.values():
            key = f"{endpoint.method.value}:{endpoint.path}"
            if key in paths:
                errors.append(f"Duplicate endpoint: {key}")
            paths[key] = endpoint.id

        return len(errors) == 0, errors

    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_project_statistics()
        return (
            f"APIBuilder(project='{self.project.name}', "
            f"endpoints={stats['endpoints']['total']}, "
            f"versions={stats['versions']['total_versions']})"
        )
