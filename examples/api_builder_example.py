"""
Example: Building a Complete REST API with NEXUS API Builder

This example demonstrates how to create a full-featured API with authentication,
rate limiting, testing, and documentation.
"""

from modules.api_builder import (
    APIBuilder,
    APIProject,
    HTTPMethod,
    Parameter,
    ParameterType,
    DataType,
    RequestBody,
    Response,
)
from modules.api_builder.auth import create_api_key_auth, create_jwt_auth
from modules.api_builder.rate_limiting import (
    RateLimitRule,
    RateLimitPeriod,
    ThrottleStrategy,
    create_free_plan,
    create_pro_plan,
)
from modules.api_builder.versioning import create_version, VersionStatus
from modules.api_builder.testing import TestCase, TestCollection, AssertionType


def main():
    """Build a complete API example."""

    # Create API Builder with custom project
    project = APIProject(
        name="User Management API",
        description="A comprehensive user management REST API",
        version="1.0.0",
        base_url="https://api.example.com",
    )

    builder = APIBuilder(project)

    print("🚀 Building User Management API...")
    print()

    # 1. Create Endpoints
    print("📌 Creating endpoints...")

    # GET /api/users - List users
    list_users = builder.create_endpoint(
        path="/api/users",
        method=HTTPMethod.GET,
        summary="List all users",
        description="Returns a paginated list of all users",
        tags=["users"],
    )

    list_users.parameters.extend([
        Parameter(
            name="page",
            param_type=ParameterType.QUERY,
            data_type=DataType.INTEGER,
            description="Page number",
            default=1,
        ),
        Parameter(
            name="limit",
            param_type=ParameterType.QUERY,
            data_type=DataType.INTEGER,
            description="Items per page",
            default=10,
            maximum=100,
        ),
    ])

    # GET /api/users/{user_id} - Get user by ID
    get_user = builder.create_endpoint(
        path="/api/users/{user_id}",
        method=HTTPMethod.GET,
        summary="Get user by ID",
        description="Returns a single user by ID",
        tags=["users"],
    )

    get_user.parameters.append(
        Parameter(
            name="user_id",
            param_type=ParameterType.PATH,
            data_type=DataType.INTEGER,
            description="User ID",
            required=True,
        )
    )

    # POST /api/users - Create user
    create_user = builder.create_endpoint(
        path="/api/users",
        method=HTTPMethod.POST,
        summary="Create a new user",
        description="Creates a new user account",
        tags=["users"],
    )

    create_user.request_body = RequestBody(
        schema={
            "type": "object",
            "required": ["username", "email"],
            "properties": {
                "username": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 30,
                },
                "email": {
                    "type": "string",
                    "format": "email",
                },
                "full_name": {"type": "string"},
                "age": {
                    "type": "integer",
                    "minimum": 18,
                    "maximum": 120,
                },
            },
        },
        examples={
            "example1": {
                "username": "john_doe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "age": 30,
            }
        },
    )

    create_user.responses[201] = Response(
        status_code=201,
        description="User created successfully",
        schema={
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "email": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
            },
        },
    )

    builder.update_endpoint(list_users.id, list_users)
    builder.update_endpoint(get_user.id, get_user)
    builder.update_endpoint(create_user.id, create_user)

    print(f"✅ Created {len(builder.list_endpoints())} endpoints")
    print()

    # 2. Setup Authentication
    print("🔐 Setting up authentication...")

    # API Key auth
    api_key_auth = create_api_key_auth()
    key = api_key_auth.generate_key("prod")
    builder.add_auth_scheme(api_key_auth)
    print(f"   Generated API Key: {key}")

    # JWT auth
    jwt_auth = create_jwt_auth(expiration_minutes=60)
    builder.add_auth_scheme(jwt_auth)
    print("   Configured JWT authentication")

    builder.set_global_auth(["apiKey"])
    print("✅ Authentication configured")
    print()

    # 3. Setup Rate Limiting
    print("⏱️  Setting up rate limiting...")

    # Create rate limit rules
    standard_limit = RateLimitRule(
        name="standard_limit",
        max_requests=100,
        period=RateLimitPeriod.MINUTE,
        description="100 requests per minute",
    )

    builder.add_rate_limit("standard", standard_limit, ThrottleStrategy.SLIDING_WINDOW)

    # Apply to all endpoints
    for endpoint in builder.list_endpoints():
        builder.apply_rate_limit_to_endpoint(endpoint.id, ["standard"])

    # Add quota plans
    free_plan = create_free_plan()
    pro_plan = create_pro_plan()

    builder.rate_limiter.quota_manager.add_plan(free_plan)
    builder.rate_limiter.quota_manager.add_plan(pro_plan)

    print("✅ Rate limiting configured")
    print()

    # 4. Create API Versions
    print("📦 Setting up versioning...")

    v1 = create_version("1.0.0", VersionStatus.STABLE, "Initial stable release")
    v2 = create_version("2.0.0", VersionStatus.BETA, "Beta version with new features")

    builder.add_version(v1)
    builder.add_version(v2)

    print("✅ Created versions: 1.0.0 (stable), 2.0.0 (beta)")
    print()

    # 5. Create Mock Scenarios
    print("🎭 Creating mock scenarios...")

    for endpoint in builder.list_endpoints():
        builder.create_mock_scenario("success", endpoint.id)
        print(f"   Created mock for {endpoint.method.value} {endpoint.path}")

    print("✅ Mock scenarios created")
    print()

    # 6. Create Test Suite
    print("🧪 Creating test suite...")

    test_collection = TestCollection(
        name="User API Tests",
        description="Comprehensive tests for user API",
    )

    # Test: List users
    list_test = TestCase(
        name="List users",
        endpoint_id=list_users.id,
        query_params={"page": 1, "limit": 10},
    )
    list_test.add_assertion(AssertionType.EQUALS, "status", 200)
    test_collection.add_test(list_test)

    # Test: Get user by ID
    get_test = TestCase(
        name="Get user by ID",
        endpoint_id=get_user.id,
        path_params={"user_id": 123},
    )
    get_test.add_assertion(AssertionType.EQUALS, "status", 200)
    test_collection.add_test(get_test)

    # Test: Create user
    create_test = TestCase(
        name="Create user",
        endpoint_id=create_user.id,
        body={
            "username": "test_user",
            "email": "test@example.com",
            "age": 25,
        },
    )
    create_test.add_assertion(AssertionType.EQUALS, "status", 201)
    test_collection.add_test(create_test)

    builder.add_test_collection(test_collection)

    print(f"✅ Created test collection with {len(test_collection.tests)} tests")
    print()

    # 7. Run Tests
    print("▶️  Running tests...")

    results = builder.run_tests("User API Tests", use_mock=True)

    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"   {status} - {result.test_name}")

    test_stats = builder.get_test_statistics()
    print(f"\n   Pass Rate: {test_stats['pass_rate']:.1f}%")
    print()

    # 8. Generate Documentation
    print("📖 Generating documentation...")

    # OpenAPI specification
    openapi_spec = builder.generate_openapi_spec(format="json")
    with open("openapi.json", "w") as f:
        f.write(openapi_spec)
    print("   ✅ Generated OpenAPI spec: openapi.json")

    # Markdown documentation
    markdown_docs = builder.generate_markdown_docs()
    with open("API_DOCS.md", "w") as f:
        f.write(markdown_docs)
    print("   ✅ Generated Markdown docs: API_DOCS.md")

    print()

    # 9. Export Project
    print("💾 Exporting project...")

    project_export = builder.export_project("user_api_project.json")
    print("✅ Project exported to: user_api_project.json")
    print()

    # 10. Display Statistics
    print("📊 Project Statistics:")
    print("=" * 50)

    stats = builder.get_project_statistics()

    print(f"\n📌 Endpoints:")
    print(f"   Total: {stats['endpoints']['total']}")
    print(f"   By Method: {stats['endpoints']['by_method']}")

    print(f"\n🔐 Authentication:")
    print(f"   Schemes: {', '.join(stats['auth_schemes']['schemes'])}")

    print(f"\n📦 Versions:")
    print(f"   Total: {stats['versions']['total_versions']}")
    print(f"   Current: {stats['versions']['current_version']}")

    print(f"\n🧪 Tests:")
    print(f"   Total: {stats['tests']['total_tests']}")
    print(f"   Passed: {stats['tests']['passed_tests']}")
    print(f"   Failed: {stats['tests']['failed_tests']}")

    print(f"\n🎭 Mock Server:")
    print(f"   Scenarios: {stats['mock_server']['total_scenarios']}")

    print()
    print("=" * 50)
    print("✨ API Builder Example Complete!")
    print()
    print("Next steps:")
    print("1. Run the Streamlit UI: streamlit run modules/api_builder/streamlit_ui.py")
    print("2. Import the project: user_api_project.json")
    print("3. Explore the generated documentation")
    print("4. Run more tests and create additional endpoints")


if __name__ == "__main__":
    main()
