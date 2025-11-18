# NEXUS API Builder & Documentation Module 🚀

A comprehensive, production-ready API development platform that rivals Postman, Swagger, and Stoplight.

## Features

### 🎨 Visual API Designer
- Drag-and-drop endpoint builder
- REST/GraphQL support
- Request/response schema designer
- Interactive endpoint editor

### 🔌 Endpoint Management
- Full CRUD operations
- Path parameters, query parameters, headers
- Request body validation
- Response definitions
- Tag-based organization

### 🔐 Authentication
- **API Keys** - Header, query, or cookie-based
- **JWT** - Token creation and validation
- **Basic Auth** - Username/password authentication
- **OAuth2** - Full OAuth2 flow support
- **Custom** - Extensible authentication schemes

### ⏱️ Rate Limiting
- Multiple throttling strategies (fixed window, sliding window, token bucket)
- Request limits per second/minute/hour/day
- Quota management with tiered plans
- User-based rate limiting

### 📖 Documentation
- **Auto-generated OpenAPI 3.0** specification
- **Swagger/ReDoc** compatible
- **Interactive API explorer**
- **Code examples** in Python, JavaScript, Java, cURL
- **Markdown** documentation export

### 🧪 Testing
- Built-in API testing framework
- Test collections and suites
- Request/response validation
- Custom assertions
- Test result analytics

### 🎭 Mock Server
- Generate realistic mock responses
- Simulate network delays
- Error scenario testing
- Probabilistic responses
- Request logging

### 📦 Versioning
- API versioning (v1, v2, etc.)
- Deprecation warnings
- Migration guides
- Breaking change tracking
- Multiple versioning strategies

### 📊 Monitoring
- Request logging
- Performance metrics
- Error tracking
- Usage analytics

### 💻 Code Generation
- Client SDKs (Python, JavaScript, Java)
- Server stubs
- Type definitions

## Installation

```bash
pip install streamlit pyyaml
```

## Quick Start

### Using Python API

```python
from modules.api_builder import APIBuilder, HTTPMethod

# Create API Builder
builder = APIBuilder()

# Create an endpoint
endpoint = builder.create_endpoint(
    path="/api/users",
    method=HTTPMethod.GET,
    summary="Get all users",
    description="Returns a paginated list of users"
)

# Add parameters
from modules.api_builder import Parameter, ParameterType, DataType

builder.get_endpoint(endpoint.id).parameters.append(
    Parameter(
        name="page",
        param_type=ParameterType.QUERY,
        data_type=DataType.INTEGER,
        description="Page number",
        required=False,
        default=1
    )
)

# Add authentication
from modules.api_builder.auth import create_api_key_auth

auth = create_api_key_auth()
key = auth.generate_key("my-api")
builder.add_auth_scheme(auth)

# Generate OpenAPI documentation
openapi_spec = builder.generate_openapi_spec(format="json")
print(openapi_spec)

# Export project
builder.export_project("my_api_project.json")
```

### Using Streamlit UI

```bash
streamlit run modules/api_builder/streamlit_ui.py
```

## Architecture

```
modules/api_builder/
├── __init__.py           # Package exports
├── builder.py            # Core API Builder orchestrator
├── endpoints.py          # Endpoint management & CRUD
├── auth.py               # Authentication schemes
├── rate_limiting.py      # Rate limiting & throttling
├── docs.py               # OpenAPI/Swagger documentation
├── testing.py            # API testing framework
├── mock.py               # Mock server
├── versioning.py         # API versioning
└── streamlit_ui.py       # Streamlit UI interface
```

## Detailed Usage

### Creating Endpoints

```python
from modules.api_builder import (
    APIBuilder,
    HTTPMethod,
    Parameter,
    ParameterType,
    DataType,
    RequestBody,
    Response
)

builder = APIBuilder()

# Create POST endpoint with request body
endpoint = builder.create_endpoint(
    path="/api/users",
    method=HTTPMethod.POST,
    summary="Create a new user",
    tags=["users"]
)

# Define request body schema
endpoint.request_body = RequestBody(
    schema={
        "type": "object",
        "required": ["username", "email"],
        "properties": {
            "username": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "age": {"type": "integer", "minimum": 0}
        }
    }
)

# Define responses
endpoint.responses[201] = Response(
    status_code=201,
    description="User created successfully",
    schema={
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "username": {"type": "string"},
            "created_at": {"type": "string", "format": "date-time"}
        }
    }
)

builder.update_endpoint(endpoint.id, endpoint)
```

### Authentication

```python
from modules.api_builder.auth import (
    create_api_key_auth,
    create_jwt_auth,
    create_oauth2_auth
)

# API Key Authentication
api_key_auth = create_api_key_auth()
key = api_key_auth.generate_key("prod")
builder.add_auth_scheme(api_key_auth)

# JWT Authentication
jwt_auth = create_jwt_auth(expiration_minutes=60)
token = jwt_auth.create_token({"user_id": 123, "role": "admin"})
builder.add_auth_scheme(jwt_auth)

# Set global authentication
builder.set_global_auth(["apiKey"])
```

### Rate Limiting

```python
from modules.api_builder.rate_limiting import (
    RateLimitRule,
    RateLimitPeriod,
    ThrottleStrategy,
    create_free_plan,
    create_pro_plan
)

# Create rate limit policy
rule = RateLimitRule(
    name="api_limit",
    max_requests=100,
    period=RateLimitPeriod.MINUTE,
    description="100 requests per minute"
)

builder.add_rate_limit("api_limit", rule, ThrottleStrategy.SLIDING_WINDOW)

# Apply to endpoint
builder.apply_rate_limit_to_endpoint(endpoint.id, ["api_limit"])

# Add quota plans
free_plan = create_free_plan()
builder.rate_limiter.quota_manager.add_plan(free_plan)
```

### Testing

```python
from modules.api_builder.testing import (
    TestCase,
    TestCollection,
    AssertionType
)

# Create test collection
collection = TestCollection(
    name="User API Tests",
    description="Tests for user endpoints"
)

# Create test case
test = TestCase(
    name="Get user by ID",
    endpoint_id=endpoint.id,
    path_params={"user_id": 123},
    description="Test retrieving a user by ID"
)

# Add assertions
test.add_assertion(
    AssertionType.EQUALS,
    "status",
    200,
    "Status code should be 200"
)

test.add_assertion(
    AssertionType.HAS_KEY,
    "$.id",
    "id",
    "Response should have id field"
)

collection.add_test(test)
builder.add_test_collection(collection)

# Run tests
results = builder.run_tests("User API Tests", use_mock=True)

for result in results:
    print(f"{result.test_name}: {'PASS' if result.passed else 'FAIL'}")
```

### Mock Server

```python
from modules.api_builder.mock import (
    create_success_scenario,
    create_error_scenario
)

# Create mock scenarios
success_scenario = create_success_scenario(
    name="success",
    endpoint_id=endpoint.id,
    data={"id": 123, "username": "john_doe"}
)

error_scenario = create_error_scenario(
    name="not_found",
    endpoint_id=endpoint.id,
    status_code=404,
    message="User not found"
)

builder.add_mock_scenario(success_scenario)
builder.add_mock_scenario(error_scenario)

# Simulate request
response = builder.simulate_request(
    endpoint.id,
    scenario_name="success"
)

print(response)
```

### Versioning

```python
from modules.api_builder.versioning import (
    create_version,
    VersionStatus
)

# Create API versions
v1 = create_version("1.0.0", VersionStatus.STABLE)
v2 = create_version("2.0.0", VersionStatus.BETA)

builder.add_version(v1)
builder.add_version(v2)

# Deprecate old version
builder.deprecate_version(
    "1.0.0",
    message="Version 1.0.0 is deprecated. Please migrate to 2.0.0",
    sunset_days=90,
    alternative="2.0.0"
)

# Generate migration guide
guide = builder.generate_migration_guide("1.0.0", "2.0.0")
print(guide)
```

### Documentation Generation

```python
# Generate OpenAPI specification
openapi_json = builder.generate_openapi_spec(format="json")
openapi_yaml = builder.generate_openapi_spec(format="yaml")

# Generate Markdown documentation
markdown_docs = builder.generate_markdown_docs()

# Get endpoint-specific documentation
endpoint_docs = builder.get_endpoint_docs(endpoint.id)

# Documentation includes code examples in multiple languages
print(endpoint_docs["examples"]["python"])
print(endpoint_docs["examples"]["curl"])
print(endpoint_docs["examples"]["javascript"])
```

## Testing

Run the test suite:

```bash
pytest tests/api_builder/ -v
```

## Examples

See the `examples/` directory for complete examples:

- `basic_api.py` - Simple REST API
- `advanced_api.py` - Complex API with authentication and rate limiting
- `testing_example.py` - API testing workflow
- `documentation_example.py` - Documentation generation

## Comparison with Competitors

| Feature | NEXUS API Builder | Postman | Swagger | Stoplight |
|---------|------------------|---------|---------|-----------|
| Visual Designer | ✅ | ✅ | ❌ | ✅ |
| OpenAPI 3.0 | ✅ | ✅ | ✅ | ✅ |
| Mock Server | ✅ | ✅ | ❌ | ✅ |
| Testing | ✅ | ✅ | ❌ | ❌ |
| Rate Limiting | ✅ | ❌ | ❌ | ❌ |
| Versioning | ✅ | ❌ | ❌ | ✅ |
| Code Generation | ✅ | ✅ | ✅ | ✅ |
| Python API | ✅ | ❌ | ❌ | ❌ |
| Free & Open Source | ✅ | Limited | ✅ | Limited |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is part of the NEXUS platform.

## Support

For issues and questions, please open an issue on the repository.

---

**Built with ❤️ by the NEXUS team**
