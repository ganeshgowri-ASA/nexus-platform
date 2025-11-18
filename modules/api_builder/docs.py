"""
Documentation Module

Auto-generates OpenAPI/Swagger documentation, provides interactive API explorer,
and generates code examples in multiple languages.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
import yaml
from datetime import datetime


@dataclass
class APIInfo:
    """API metadata information."""
    title: str
    version: str
    description: str = ""
    terms_of_service: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_url: str = ""
    license_name: str = ""
    license_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAPI info object."""
        info = {
            "title": self.title,
            "version": self.version,
        }

        if self.description:
            info["description"] = self.description
        if self.terms_of_service:
            info["termsOfService"] = self.terms_of_service

        contact = {}
        if self.contact_name:
            contact["name"] = self.contact_name
        if self.contact_email:
            contact["email"] = self.contact_email
        if self.contact_url:
            contact["url"] = self.contact_url
        if contact:
            info["contact"] = contact

        license_info = {}
        if self.license_name:
            license_info["name"] = self.license_name
        if self.license_url:
            license_info["url"] = self.license_url
        if license_info:
            info["license"] = license_info

        return info


@dataclass
class ServerInfo:
    """API server information."""
    url: str
    description: str = ""
    variables: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenAPI server object."""
        server = {"url": self.url}

        if self.description:
            server["description"] = self.description
        if self.variables:
            server["variables"] = self.variables

        return server


class OpenAPIGenerator:
    """Generates OpenAPI 3.0 specification."""

    def __init__(
        self,
        info: APIInfo,
        servers: Optional[List[ServerInfo]] = None,
    ):
        self.info = info
        self.servers = servers or []
        self.openapi_version = "3.0.3"

    def generate(
        self,
        endpoints: List[Any],  # List[Endpoint]
        auth_manager: Optional[Any] = None,  # AuthManager
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Generate OpenAPI specification."""
        spec = {
            "openapi": self.openapi_version,
            "info": self.info.to_dict(),
            "servers": [s.to_dict() for s in self.servers],
            "paths": self._generate_paths(endpoints),
        }

        if tags:
            spec["tags"] = tags

        # Add security schemes
        if auth_manager:
            security_schemes = auth_manager.to_openapi_security_schemes()
            if security_schemes:
                spec["components"] = {
                    "securitySchemes": security_schemes
                }

            # Add global security requirements
            security_requirements = auth_manager.get_security_requirements()
            if security_requirements:
                spec["security"] = security_requirements

        return spec

    def _generate_paths(self, endpoints: List[Any]) -> Dict[str, Any]:
        """Generate paths section of OpenAPI spec."""
        paths = {}

        for endpoint in endpoints:
            path = endpoint.path
            method = endpoint.method.value.lower()

            if path not in paths:
                paths[path] = {}

            paths[path][method] = self._generate_operation(endpoint)

        return paths

    def _generate_operation(self, endpoint: Any) -> Dict[str, Any]:
        """Generate operation object for an endpoint."""
        operation = {}

        if endpoint.summary:
            operation["summary"] = endpoint.summary
        if endpoint.description:
            operation["description"] = endpoint.description
        if endpoint.tags:
            operation["tags"] = endpoint.tags
        if endpoint.operation_id:
            operation["operationId"] = endpoint.operation_id
        if endpoint.deprecated:
            operation["deprecated"] = True

        # Parameters
        if endpoint.parameters:
            operation["parameters"] = [p.to_dict() for p in endpoint.parameters]

        # Request body
        if endpoint.request_body:
            operation["requestBody"] = endpoint.request_body.to_dict()

        # Responses
        operation["responses"] = {
            str(code): response.to_dict()
            for code, response in endpoint.responses.items()
        }

        # Security
        if endpoint.security:
            operation["security"] = endpoint.security

        return operation

    def to_json(
        self,
        endpoints: List[Any],
        auth_manager: Optional[Any] = None,
        tags: Optional[List[Dict[str, str]]] = None,
        indent: int = 2,
    ) -> str:
        """Generate OpenAPI spec as JSON string."""
        spec = self.generate(endpoints, auth_manager, tags)
        return json.dumps(spec, indent=indent)

    def to_yaml(
        self,
        endpoints: List[Any],
        auth_manager: Optional[Any] = None,
        tags: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Generate OpenAPI spec as YAML string."""
        spec = self.generate(endpoints, auth_manager, tags)
        return yaml.dump(spec, default_flow_style=False, sort_keys=False)


class CodeExampleGenerator:
    """Generates code examples in multiple languages."""

    @staticmethod
    def generate_curl(
        endpoint: Any,
        base_url: str = "https://api.example.com",
        auth_header: Optional[str] = None,
        body_example: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate cURL example."""
        method = endpoint.method.value
        path = endpoint.path
        url = f"{base_url}{path}"

        # Build curl command
        lines = [f"curl -X {method} '{url}'"]

        # Add headers
        if auth_header:
            lines.append(f"  -H '{auth_header}'")

        lines.append("  -H 'Content-Type: application/json'")

        # Add query parameters example
        query_params = endpoint.get_query_parameters()
        if query_params:
            params = "&".join([f"{p.name}={p.example or 'value'}" for p in query_params[:2]])
            lines[0] = f"curl -X {method} '{url}?{params}'"

        # Add body
        if endpoint.request_body and body_example:
            body_json = json.dumps(body_example, indent=2)
            lines.append(f"  -d '{body_json}'")

        return " \\\n".join(lines)

    @staticmethod
    def generate_python(
        endpoint: Any,
        base_url: str = "https://api.example.com",
        auth_header: Optional[str] = None,
        body_example: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate Python requests example."""
        method = endpoint.method.value.lower()
        path = endpoint.path
        url = f"{base_url}{path}"

        lines = ["import requests", "", f"url = '{url}'"]

        # Headers
        headers = {"Content-Type": "application/json"}
        if auth_header:
            key, value = auth_header.split(': ', 1)
            headers[key] = value

        lines.append(f"headers = {json.dumps(headers, indent=4)}")

        # Query parameters
        query_params = endpoint.get_query_parameters()
        if query_params:
            params = {p.name: p.example or "value" for p in query_params[:2]}
            lines.append(f"params = {json.dumps(params, indent=4)}")

        # Body
        if endpoint.request_body and body_example:
            lines.append(f"data = {json.dumps(body_example, indent=4)}")

        # Request
        request_line = f"response = requests.{method}(url, headers=headers"
        if query_params:
            request_line += ", params=params"
        if endpoint.request_body and body_example:
            request_line += ", json=data"
        request_line += ")"

        lines.append("")
        lines.append(request_line)
        lines.append("print(response.json())")

        return "\n".join(lines)

    @staticmethod
    def generate_javascript(
        endpoint: Any,
        base_url: str = "https://api.example.com",
        auth_header: Optional[str] = None,
        body_example: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate JavaScript fetch example."""
        method = endpoint.method.value
        path = endpoint.path
        url = f"{base_url}{path}"

        # Build fetch options
        options = {
            "method": method,
            "headers": {"Content-Type": "application/json"}
        }

        if auth_header:
            key, value = auth_header.split(': ', 1)
            options["headers"][key] = value

        if endpoint.request_body and body_example:
            options["body"] = "JSON.stringify(data)"

        lines = []

        # Query parameters
        query_params = endpoint.get_query_parameters()
        if query_params:
            params = {p.name: p.example or "value" for p in query_params[:2]}
            params_str = "&".join([f"{k}={v}" for k, v in params.items()])
            lines.append(f"const url = '{url}?{params_str}';")
        else:
            lines.append(f"const url = '{url}';")

        # Body data
        if endpoint.request_body and body_example:
            lines.append(f"const data = {json.dumps(body_example, indent=2)};")
            lines.append("")

        # Fetch call
        lines.append("fetch(url, {")
        lines.append(f"  method: '{method}',")
        lines.append("  headers: {")
        for key, value in options["headers"].items():
            lines.append(f"    '{key}': '{value}',")
        lines.append("  },")

        if endpoint.request_body and body_example:
            lines.append("  body: JSON.stringify(data)")

        lines.append("})")
        lines.append("  .then(response => response.json())")
        lines.append("  .then(data => console.log(data))")
        lines.append("  .catch(error => console.error('Error:', error));")

        return "\n".join(lines)

    @staticmethod
    def generate_java(
        endpoint: Any,
        base_url: str = "https://api.example.com",
        auth_header: Optional[str] = None,
        body_example: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate Java example using HttpClient."""
        method = endpoint.method.value
        path = endpoint.path
        url = f"{base_url}{path}"

        lines = [
            "import java.net.http.*;",
            "import java.net.URI;",
            "",
            "HttpClient client = HttpClient.newHttpClient();",
            "",
        ]

        # Build request
        request_lines = [
            f'HttpRequest request = HttpRequest.newBuilder()',
            f'    .uri(URI.create("{url}"))',
            f'    .header("Content-Type", "application/json")',
        ]

        if auth_header:
            key, value = auth_header.split(': ', 1)
            request_lines.append(f'    .header("{key}", "{value}")')

        if endpoint.request_body and body_example:
            body_json = json.dumps(body_example)
            request_lines.append(f'    .{method}(HttpRequest.BodyPublishers.ofString("{body_json}"))')
        else:
            request_lines.append(f'    .{method}(HttpRequest.BodyPublishers.noBody())')

        request_lines.append('    .build();')

        lines.extend(request_lines)
        lines.append("")
        lines.append("HttpResponse<String> response = client.send(request,")
        lines.append("    HttpResponse.BodyHandlers.ofString());")
        lines.append("System.out.println(response.body());")

        return "\n".join(lines)


class DocumentationGenerator:
    """Generates comprehensive API documentation."""

    def __init__(self, openapi_generator: OpenAPIGenerator):
        self.openapi_generator = openapi_generator
        self.code_generator = CodeExampleGenerator()

    def generate_endpoint_docs(
        self,
        endpoint: Any,
        base_url: str = "https://api.example.com",
    ) -> Dict[str, Any]:
        """Generate documentation for a single endpoint."""
        docs = {
            "endpoint": f"{endpoint.method.value} {endpoint.path}",
            "summary": endpoint.summary,
            "description": endpoint.description,
            "tags": endpoint.tags,
            "deprecated": endpoint.deprecated,
        }

        # Parameters
        if endpoint.parameters:
            docs["parameters"] = {
                "path": [p.to_dict() for p in endpoint.get_path_parameters()],
                "query": [p.to_dict() for p in endpoint.get_query_parameters()],
                "header": [p.to_dict() for p in endpoint.get_header_parameters()],
            }

        # Request body
        if endpoint.request_body:
            docs["request_body"] = endpoint.request_body.to_dict()

        # Responses
        docs["responses"] = {
            code: response.to_dict()
            for code, response in endpoint.responses.items()
        }

        # Code examples
        body_example = None
        if endpoint.request_body and endpoint.request_body.examples:
            body_example = list(endpoint.request_body.examples.values())[0]

        docs["examples"] = {
            "curl": self.code_generator.generate_curl(endpoint, base_url, body_example=body_example),
            "python": self.code_generator.generate_python(endpoint, base_url, body_example=body_example),
            "javascript": self.code_generator.generate_javascript(endpoint, base_url, body_example=body_example),
            "java": self.code_generator.generate_java(endpoint, base_url, body_example=body_example),
        }

        return docs

    def generate_markdown(
        self,
        endpoints: List[Any],
        base_url: str = "https://api.example.com",
    ) -> str:
        """Generate Markdown documentation."""
        lines = [
            f"# {self.openapi_generator.info.title}",
            "",
            self.openapi_generator.info.description,
            "",
            f"**Version:** {self.openapi_generator.info.version}",
            "",
        ]

        # Table of contents
        lines.append("## Table of Contents")
        lines.append("")

        for endpoint in endpoints:
            anchor = f"{endpoint.method.value.lower()}-{endpoint.path.replace('/', '-').strip('-')}"
            lines.append(f"- [{endpoint.method.value} {endpoint.path}](#{anchor})")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Endpoint details
        for endpoint in endpoints:
            lines.append(f"## {endpoint.method.value} {endpoint.path}")
            lines.append("")

            if endpoint.summary:
                lines.append(endpoint.summary)
                lines.append("")

            if endpoint.description:
                lines.append(endpoint.description)
                lines.append("")

            if endpoint.deprecated:
                lines.append("**⚠️ DEPRECATED**")
                lines.append("")

            # Parameters
            path_params = endpoint.get_path_parameters()
            if path_params:
                lines.append("### Path Parameters")
                lines.append("")
                lines.append("| Name | Type | Required | Description |")
                lines.append("|------|------|----------|-------------|")
                for param in path_params:
                    req = "Yes" if param.required else "No"
                    lines.append(f"| {param.name} | {param.data_type.value} | {req} | {param.description} |")
                lines.append("")

            query_params = endpoint.get_query_parameters()
            if query_params:
                lines.append("### Query Parameters")
                lines.append("")
                lines.append("| Name | Type | Required | Description |")
                lines.append("|------|------|----------|-------------|")
                for param in query_params:
                    req = "Yes" if param.required else "No"
                    lines.append(f"| {param.name} | {param.data_type.value} | {req} | {param.description} |")
                lines.append("")

            # Request body
            if endpoint.request_body:
                lines.append("### Request Body")
                lines.append("")
                lines.append(f"**Content-Type:** `{endpoint.request_body.content_type}`")
                lines.append("")

                if endpoint.request_body.schema:
                    lines.append("```json")
                    lines.append(json.dumps(endpoint.request_body.schema, indent=2))
                    lines.append("```")
                    lines.append("")

            # Responses
            lines.append("### Responses")
            lines.append("")

            for code, response in sorted(endpoint.responses.items()):
                lines.append(f"#### {code} - {response.description}")
                lines.append("")

                if response.schema:
                    lines.append("```json")
                    lines.append(json.dumps(response.schema, indent=2))
                    lines.append("```")
                    lines.append("")

            # Code examples
            lines.append("### Code Examples")
            lines.append("")

            body_example = None
            if endpoint.request_body and endpoint.request_body.examples:
                body_example = list(endpoint.request_body.examples.values())[0]

            lines.append("#### cURL")
            lines.append("```bash")
            lines.append(self.code_generator.generate_curl(endpoint, base_url, body_example=body_example))
            lines.append("```")
            lines.append("")

            lines.append("#### Python")
            lines.append("```python")
            lines.append(self.code_generator.generate_python(endpoint, base_url, body_example=body_example))
            lines.append("```")
            lines.append("")

            lines.append("#### JavaScript")
            lines.append("```javascript")
            lines.append(self.code_generator.generate_javascript(endpoint, base_url, body_example=body_example))
            lines.append("```")
            lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)


class InteractiveExplorer:
    """Provides interactive API exploration capabilities."""

    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def build_request(
        self,
        endpoint: Any,
        path_params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build a request for an endpoint."""
        # Replace path parameters
        path = endpoint.path
        if path_params:
            for key, value in path_params.items():
                path = path.replace(f"{{{key}}}", str(value))

        request = {
            "method": endpoint.method.value,
            "path": path,
            "query_params": query_params or {},
            "headers": headers or {},
            "body": body,
            "timestamp": datetime.now().isoformat(),
        }

        return request

    def validate_request(
        self,
        endpoint: Any,
        request: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        """Validate a request against endpoint requirements."""
        errors = []

        # Validate path parameters
        path_params_in_request = request.get("path_params", {})
        for param in endpoint.get_path_parameters():
            if param.required and param.name not in path_params_in_request:
                errors.append(f"Missing required path parameter: {param.name}")
            elif param.name in path_params_in_request:
                is_valid, error = param.validate(path_params_in_request[param.name])
                if not is_valid:
                    errors.append(error)

        # Validate query parameters
        query_params = request.get("query_params", {})
        for param in endpoint.get_query_parameters():
            if param.required and param.name not in query_params:
                errors.append(f"Missing required query parameter: {param.name}")
            elif param.name in query_params:
                is_valid, error = param.validate(query_params[param.name])
                if not is_valid:
                    errors.append(error)

        # Validate request body
        if endpoint.request_body and endpoint.request_body.required:
            if not request.get("body"):
                errors.append("Request body is required")

        return len(errors) == 0, errors

    def record_request(self, request: Dict[str, Any], response: Optional[Dict[str, Any]] = None) -> None:
        """Record a request in history."""
        self.history.append({
            "request": request,
            "response": response,
            "timestamp": datetime.now().isoformat(),
        })

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get request history."""
        return self.history[-limit:]

    def export_history(self) -> str:
        """Export history as JSON."""
        return json.dumps(self.history, indent=2)

    def clear_history(self) -> None:
        """Clear request history."""
        self.history = []
