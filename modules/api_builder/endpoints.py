"""
Endpoint Management Module

Handles CRUD operations, path parameters, query parameters, request bodies, and headers.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json
import re
from datetime import datetime
import uuid


class HTTPMethod(Enum):
    """HTTP methods supported by the API builder."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ParameterType(Enum):
    """Parameter types for API endpoints."""
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"


class DataType(Enum):
    """Data types for parameters and schemas."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"


@dataclass
class Parameter:
    """Represents an API parameter."""
    name: str
    param_type: ParameterType
    data_type: DataType
    required: bool = False
    description: str = ""
    default: Optional[Any] = None
    example: Optional[Any] = None
    enum: Optional[List[Any]] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None

    def validate(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a parameter value."""
        if value is None:
            if self.required:
                return False, f"Parameter '{self.name}' is required"
            return True, None

        # Type validation
        if self.data_type == DataType.STRING and not isinstance(value, str):
            return False, f"Parameter '{self.name}' must be a string"
        elif self.data_type == DataType.INTEGER and not isinstance(value, int):
            return False, f"Parameter '{self.name}' must be an integer"
        elif self.data_type == DataType.NUMBER and not isinstance(value, (int, float)):
            return False, f"Parameter '{self.name}' must be a number"
        elif self.data_type == DataType.BOOLEAN and not isinstance(value, bool):
            return False, f"Parameter '{self.name}' must be a boolean"
        elif self.data_type == DataType.ARRAY and not isinstance(value, list):
            return False, f"Parameter '{self.name}' must be an array"
        elif self.data_type == DataType.OBJECT and not isinstance(value, dict):
            return False, f"Parameter '{self.name}' must be an object"

        # Enum validation
        if self.enum and value not in self.enum:
            return False, f"Parameter '{self.name}' must be one of {self.enum}"

        # Pattern validation
        if self.pattern and isinstance(value, str):
            if not re.match(self.pattern, value):
                return False, f"Parameter '{self.name}' does not match pattern {self.pattern}"

        # Length validation
        if isinstance(value, str):
            if self.min_length and len(value) < self.min_length:
                return False, f"Parameter '{self.name}' must be at least {self.min_length} characters"
            if self.max_length and len(value) > self.max_length:
                return False, f"Parameter '{self.name}' must be at most {self.max_length} characters"

        # Range validation
        if isinstance(value, (int, float)):
            if self.minimum is not None and value < self.minimum:
                return False, f"Parameter '{self.name}' must be at least {self.minimum}"
            if self.maximum is not None and value > self.maximum:
                return False, f"Parameter '{self.name}' must be at most {self.maximum}"

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameter to dictionary."""
        return {
            "name": self.name,
            "in": self.param_type.value,
            "type": self.data_type.value,
            "required": self.required,
            "description": self.description,
            "default": self.default,
            "example": self.example,
            "enum": self.enum,
            "pattern": self.pattern,
            "minLength": self.min_length,
            "maxLength": self.max_length,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


@dataclass
class RequestBody:
    """Represents a request body schema."""
    content_type: str = "application/json"
    schema: Dict[str, Any] = field(default_factory=dict)
    required: bool = True
    description: str = ""
    examples: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert request body to dictionary."""
        return {
            "required": self.required,
            "description": self.description,
            "content": {
                self.content_type: {
                    "schema": self.schema,
                    "examples": self.examples,
                }
            }
        }


@dataclass
class Response:
    """Represents an API response."""
    status_code: int
    description: str = ""
    content_type: str = "application/json"
    schema: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, Parameter] = field(default_factory=dict)
    examples: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        result = {
            "description": self.description,
        }

        if self.schema or self.examples:
            result["content"] = {
                self.content_type: {
                    "schema": self.schema,
                    "examples": self.examples,
                }
            }

        if self.headers:
            result["headers"] = {
                name: param.to_dict() for name, param in self.headers.items()
            }

        return result


@dataclass
class Endpoint:
    """Represents an API endpoint."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    path: str = ""
    method: HTTPMethod = HTTPMethod.GET
    summary: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: Dict[int, Response] = field(default_factory=dict)
    deprecated: bool = False
    security: List[Dict[str, List[str]]] = field(default_factory=list)
    operation_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Initialize endpoint with defaults."""
        if not self.operation_id:
            self.operation_id = f"{self.method.value.lower()}_{self.path.replace('/', '_').strip('_')}"

        # Add default 200 response if no responses defined
        if not self.responses:
            self.responses[200] = Response(
                status_code=200,
                description="Successful response"
            )

    def get_path_parameters(self) -> List[Parameter]:
        """Get path parameters from endpoint."""
        return [p for p in self.parameters if p.param_type == ParameterType.PATH]

    def get_query_parameters(self) -> List[Parameter]:
        """Get query parameters from endpoint."""
        return [p for p in self.parameters if p.param_type == ParameterType.QUERY]

    def get_header_parameters(self) -> List[Parameter]:
        """Get header parameters from endpoint."""
        return [p for p in self.parameters if p.param_type == ParameterType.HEADER]

    def validate_path(self) -> tuple[bool, Optional[str]]:
        """Validate endpoint path."""
        if not self.path:
            return False, "Path cannot be empty"

        if not self.path.startswith('/'):
            return False, "Path must start with '/'"

        # Extract path parameters
        path_params = re.findall(r'\{([^}]+)\}', self.path)
        param_names = {p.name for p in self.get_path_parameters()}

        # Check if all path parameters are defined
        for param in path_params:
            if param not in param_names:
                return False, f"Path parameter '{param}' is not defined in parameters"

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        """Convert endpoint to dictionary."""
        result = {
            "id": self.id,
            "path": self.path,
            "method": self.method.value,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "operationId": self.operation_id,
            "deprecated": self.deprecated,
            "parameters": [p.to_dict() for p in self.parameters],
            "responses": {
                str(code): response.to_dict()
                for code, response in self.responses.items()
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if self.request_body:
            result["requestBody"] = self.request_body.to_dict()

        if self.security:
            result["security"] = self.security

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Endpoint':
        """Create endpoint from dictionary."""
        # Parse parameters
        parameters = []
        for param_data in data.get("parameters", []):
            parameters.append(Parameter(
                name=param_data["name"],
                param_type=ParameterType(param_data["in"]),
                data_type=DataType(param_data.get("type", "string")),
                required=param_data.get("required", False),
                description=param_data.get("description", ""),
                default=param_data.get("default"),
                example=param_data.get("example"),
                enum=param_data.get("enum"),
                pattern=param_data.get("pattern"),
                min_length=param_data.get("minLength"),
                max_length=param_data.get("maxLength"),
                minimum=param_data.get("minimum"),
                maximum=param_data.get("maximum"),
            ))

        # Parse request body
        request_body = None
        if "requestBody" in data:
            rb_data = data["requestBody"]
            content_type = list(rb_data.get("content", {}).keys())[0] if rb_data.get("content") else "application/json"
            content = rb_data.get("content", {}).get(content_type, {})
            request_body = RequestBody(
                content_type=content_type,
                schema=content.get("schema", {}),
                required=rb_data.get("required", True),
                description=rb_data.get("description", ""),
                examples=content.get("examples", {}),
            )

        # Parse responses
        responses = {}
        for code, resp_data in data.get("responses", {}).items():
            content_type = list(resp_data.get("content", {}).keys())[0] if resp_data.get("content") else "application/json"
            content = resp_data.get("content", {}).get(content_type, {})
            responses[int(code)] = Response(
                status_code=int(code),
                description=resp_data.get("description", ""),
                content_type=content_type,
                schema=content.get("schema", {}),
                examples=content.get("examples", {}),
            )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            path=data["path"],
            method=HTTPMethod(data["method"]),
            summary=data.get("summary", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            deprecated=data.get("deprecated", False),
            security=data.get("security", []),
            operation_id=data.get("operationId", ""),
        )


class EndpointManager:
    """Manages API endpoints with CRUD operations."""

    def __init__(self):
        self.endpoints: Dict[str, Endpoint] = {}

    def create(self, endpoint: Endpoint) -> Endpoint:
        """Create a new endpoint."""
        # Validate path
        is_valid, error = endpoint.validate_path()
        if not is_valid:
            raise ValueError(error)

        # Check for duplicates
        key = f"{endpoint.method.value}:{endpoint.path}"
        if key in [f"{e.method.value}:{e.path}" for e in self.endpoints.values()]:
            raise ValueError(f"Endpoint {endpoint.method.value} {endpoint.path} already exists")

        endpoint.created_at = datetime.now()
        endpoint.updated_at = datetime.now()
        self.endpoints[endpoint.id] = endpoint
        return endpoint

    def read(self, endpoint_id: str) -> Optional[Endpoint]:
        """Read an endpoint by ID."""
        return self.endpoints.get(endpoint_id)

    def update(self, endpoint_id: str, endpoint: Endpoint) -> Endpoint:
        """Update an existing endpoint."""
        if endpoint_id not in self.endpoints:
            raise ValueError(f"Endpoint {endpoint_id} not found")

        # Validate path
        is_valid, error = endpoint.validate_path()
        if not is_valid:
            raise ValueError(error)

        endpoint.id = endpoint_id
        endpoint.updated_at = datetime.now()
        self.endpoints[endpoint_id] = endpoint
        return endpoint

    def delete(self, endpoint_id: str) -> bool:
        """Delete an endpoint."""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            return True
        return False

    def list(
        self,
        method: Optional[HTTPMethod] = None,
        tags: Optional[List[str]] = None,
        deprecated: Optional[bool] = None,
    ) -> List[Endpoint]:
        """List endpoints with optional filtering."""
        results = list(self.endpoints.values())

        if method:
            results = [e for e in results if e.method == method]

        if tags:
            results = [e for e in results if any(tag in e.tags for tag in tags)]

        if deprecated is not None:
            results = [e for e in results if e.deprecated == deprecated]

        return results

    def search(self, query: str) -> List[Endpoint]:
        """Search endpoints by path, summary, or description."""
        query_lower = query.lower()
        results = []

        for endpoint in self.endpoints.values():
            if (query_lower in endpoint.path.lower() or
                query_lower in endpoint.summary.lower() or
                query_lower in endpoint.description.lower()):
                results.append(endpoint)

        return results

    def get_by_path(self, path: str, method: HTTPMethod) -> Optional[Endpoint]:
        """Get endpoint by path and method."""
        for endpoint in self.endpoints.values():
            if endpoint.path == path and endpoint.method == method:
                return endpoint
        return None

    def export_json(self) -> str:
        """Export all endpoints to JSON."""
        data = {
            "endpoints": [e.to_dict() for e in self.endpoints.values()]
        }
        return json.dumps(data, indent=2)

    def import_json(self, json_str: str) -> int:
        """Import endpoints from JSON."""
        data = json.loads(json_str)
        count = 0

        for endpoint_data in data.get("endpoints", []):
            endpoint = Endpoint.from_dict(endpoint_data)
            try:
                self.create(endpoint)
                count += 1
            except ValueError:
                # Skip duplicates
                continue

        return count

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about endpoints."""
        total = len(self.endpoints)
        by_method = {}
        by_tag = {}
        deprecated_count = 0

        for endpoint in self.endpoints.values():
            # Count by method
            method = endpoint.method.value
            by_method[method] = by_method.get(method, 0) + 1

            # Count by tag
            for tag in endpoint.tags:
                by_tag[tag] = by_tag.get(tag, 0) + 1

            # Count deprecated
            if endpoint.deprecated:
                deprecated_count += 1

        return {
            "total": total,
            "by_method": by_method,
            "by_tag": by_tag,
            "deprecated": deprecated_count,
        }
