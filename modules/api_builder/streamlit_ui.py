"""
Streamlit UI for API Builder

Comprehensive visual interface for designing, testing, and documenting APIs.
"""

import streamlit as st
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    from .builder import APIBuilder, APIProject
    from .endpoints import (
        Endpoint,
        HTTPMethod,
        Parameter,
        ParameterType,
        DataType,
        RequestBody,
        Response,
    )
    from .auth import (
        create_api_key_auth,
        create_jwt_auth,
        create_basic_auth,
        create_oauth2_auth,
        APIKeyLocation,
    )
    from .rate_limiting import (
        RateLimitRule,
        RateLimitPeriod,
        ThrottleStrategy,
        create_free_plan,
        create_pro_plan,
        create_enterprise_plan,
    )
    from .versioning import (
        create_version,
        VersionStatus,
        VersioningStrategy,
    )
    from .testing import TestCase, TestCollection, AssertionType
    from .mock import create_success_scenario, create_error_scenario
except ImportError:
    # For standalone testing
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def init_session_state():
    """Initialize Streamlit session state."""
    if 'api_builder' not in st.session_state:
        project = APIProject(
            name="My API",
            description="Built with NEXUS API Builder",
            version="1.0.0",
            base_url="https://api.example.com",
        )
        st.session_state.api_builder = APIBuilder(project)

    if 'selected_endpoint_id' not in st.session_state:
        st.session_state.selected_endpoint_id = None

    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = "Dashboard"


def render_header():
    """Render the application header."""
    st.set_page_config(
        page_title="NEXUS API Builder",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🚀 NEXUS API Builder")
    st.markdown("**Professional API Development Platform** - Design, Test, Document, and Deploy")


def render_sidebar():
    """Render the sidebar with navigation."""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x60/4F46E5/FFFFFF?text=NEXUS+API", use_container_width=True)

        st.markdown("---")

        # Navigation
        selected = st.radio(
            "Navigation",
            [
                "📊 Dashboard",
                "🔌 Endpoints",
                "🔐 Authentication",
                "⏱️ Rate Limiting",
                "📖 Documentation",
                "🧪 Testing",
                "🎭 Mock Server",
                "📦 Versioning",
                "⚙️ Settings",
            ],
            label_visibility="collapsed"
        )

        st.session_state.selected_tab = selected.split(" ", 1)[1]

        st.markdown("---")

        # Project info
        builder = st.session_state.api_builder
        st.markdown("### Project Info")
        st.write(f"**Name:** {builder.project.name}")
        st.write(f"**Version:** {builder.project.version}")

        stats = builder.get_project_statistics()
        st.metric("Endpoints", stats['endpoints']['total'])
        st.metric("Versions", stats['versions']['total_versions'])


def render_dashboard():
    """Render the dashboard tab."""
    st.header("📊 Dashboard")

    builder = st.session_state.api_builder
    stats = builder.get_project_statistics()

    # Project overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Endpoints",
            stats['endpoints']['total'],
            help="Number of API endpoints defined"
        )

    with col2:
        st.metric(
            "Auth Schemes",
            stats['auth_schemes']['total'],
            help="Number of authentication schemes configured"
        )

    with col3:
        st.metric(
            "Test Cases",
            stats['tests']['total_tests'],
            help="Number of test cases created"
        )

    with col4:
        st.metric(
            "API Versions",
            stats['versions']['total_versions'],
            help="Number of API versions"
        )

    st.markdown("---")

    # Detailed statistics
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Endpoints by Method")
        by_method = stats['endpoints'].get('by_method', {})
        if by_method:
            for method, count in by_method.items():
                st.write(f"**{method}:** {count}")
        else:
            st.info("No endpoints defined yet")

    with col2:
        st.subheader("Endpoints by Tag")
        by_tag = stats['endpoints'].get('by_tag', {})
        if by_tag:
            for tag, count in list(by_tag.items())[:5]:
                st.write(f"**{tag}:** {count}")
        else:
            st.info("No tags used yet")

    # Quick actions
    st.markdown("---")
    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("➕ Create Endpoint", use_container_width=True):
            st.session_state.selected_tab = "Endpoints"
            st.rerun()

    with col2:
        if st.button("📄 Generate Docs", use_container_width=True):
            st.session_state.selected_tab = "Documentation"
            st.rerun()

    with col3:
        if st.button("🧪 Run Tests", use_container_width=True):
            st.session_state.selected_tab = "Testing"
            st.rerun()


def render_endpoints():
    """Render the endpoints management tab."""
    st.header("🔌 Endpoints")

    builder = st.session_state.api_builder

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 List", "➕ Create", "✏️ Edit"])

    with tab1:
        render_endpoint_list(builder)

    with tab2:
        render_endpoint_creator(builder)

    with tab3:
        render_endpoint_editor(builder)


def render_endpoint_list(builder: APIBuilder):
    """Render the endpoint list."""
    st.subheader("All Endpoints")

    endpoints = builder.list_endpoints()

    if not endpoints:
        st.info("No endpoints defined yet. Create your first endpoint!")
        return

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        method_filter = st.selectbox(
            "Filter by Method",
            ["All"] + [m.value for m in HTTPMethod]
        )

    with col2:
        search_query = st.text_input("Search", placeholder="Search endpoints...")

    # Filter endpoints
    filtered = endpoints
    if method_filter != "All":
        filtered = [e for e in filtered if e.method.value == method_filter]
    if search_query:
        filtered = builder.search_endpoints(search_query)

    # Display endpoints
    for endpoint in filtered:
        with st.expander(f"{endpoint.method.value} {endpoint.path}"):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**Summary:** {endpoint.summary or 'No summary'}")
                st.write(f"**Description:** {endpoint.description or 'No description'}")
                if endpoint.tags:
                    st.write(f"**Tags:** {', '.join(endpoint.tags)}")

            with col2:
                if st.button("Edit", key=f"edit_{endpoint.id}"):
                    st.session_state.selected_endpoint_id = endpoint.id
                    st.rerun()

                if st.button("Delete", key=f"delete_{endpoint.id}", type="secondary"):
                    builder.delete_endpoint(endpoint.id)
                    st.success("Endpoint deleted!")
                    st.rerun()

                if st.button("View Docs", key=f"docs_{endpoint.id}"):
                    docs = builder.get_endpoint_docs(endpoint.id)
                    st.json(docs)


def render_endpoint_creator(builder: APIBuilder):
    """Render the endpoint creation form."""
    st.subheader("Create New Endpoint")

    with st.form("create_endpoint_form"):
        col1, col2 = st.columns(2)

        with col1:
            path = st.text_input("Path*", placeholder="/api/users")
            method = st.selectbox("Method*", [m.value for m in HTTPMethod])
            summary = st.text_input("Summary", placeholder="Get all users")

        with col2:
            tags_input = st.text_input("Tags (comma-separated)", placeholder="users, public")
            description = st.text_area("Description", placeholder="Returns a list of all users")

        # Submit button
        submitted = st.form_submit_button("Create Endpoint", type="primary", use_container_width=True)

        if submitted:
            if not path:
                st.error("Path is required")
            else:
                try:
                    tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
                    endpoint = builder.create_endpoint(
                        path=path,
                        method=HTTPMethod(method),
                        summary=summary,
                        description=description,
                        tags=tags,
                    )
                    st.success(f"Endpoint created: {method} {path}")
                    st.session_state.selected_endpoint_id = endpoint.id
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


def render_endpoint_editor(builder: APIBuilder):
    """Render the endpoint editor."""
    st.subheader("Edit Endpoint")

    if not st.session_state.selected_endpoint_id:
        st.info("Select an endpoint from the list to edit")
        return

    endpoint = builder.get_endpoint(st.session_state.selected_endpoint_id)
    if not endpoint:
        st.error("Endpoint not found")
        return

    st.write(f"**Editing:** {endpoint.method.value} {endpoint.path}")

    # Basic info
    with st.expander("📝 Basic Information", expanded=True):
        summary = st.text_input("Summary", value=endpoint.summary)
        description = st.text_area("Description", value=endpoint.description)
        tags_str = ", ".join(endpoint.tags)
        tags_input = st.text_input("Tags (comma-separated)", value=tags_str)

        if st.button("Update Basic Info"):
            endpoint.summary = summary
            endpoint.description = description
            endpoint.tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
            builder.update_endpoint(endpoint.id, endpoint)
            st.success("Updated!")

    # Parameters
    with st.expander("🔧 Parameters"):
        render_parameter_editor(builder, endpoint)

    # Request body
    with st.expander("📦 Request Body"):
        render_request_body_editor(builder, endpoint)

    # Responses
    with st.expander("📤 Responses"):
        render_response_editor(builder, endpoint)


def render_parameter_editor(builder: APIBuilder, endpoint: Endpoint):
    """Render parameter editor."""
    st.subheader("Parameters")

    # Add new parameter
    with st.form("add_parameter"):
        col1, col2, col3 = st.columns(3)

        with col1:
            param_name = st.text_input("Name")
            param_type = st.selectbox("Type", [p.value for p in ParameterType])

        with col2:
            data_type = st.selectbox("Data Type", [d.value for d in DataType])
            required = st.checkbox("Required")

        with col3:
            description = st.text_input("Description")

        if st.form_submit_button("Add Parameter"):
            if param_name:
                param = Parameter(
                    name=param_name,
                    param_type=ParameterType(param_type),
                    data_type=DataType(data_type),
                    required=required,
                    description=description,
                )
                endpoint.parameters.append(param)
                builder.update_endpoint(endpoint.id, endpoint)
                st.success("Parameter added!")
                st.rerun()

    # List existing parameters
    if endpoint.parameters:
        st.write("**Existing Parameters:**")
        for i, param in enumerate(endpoint.parameters):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{param.name}** ({param.param_type.value}, {param.data_type.value}) - {param.description}")
            with col2:
                if st.button("Remove", key=f"remove_param_{i}"):
                    endpoint.parameters.pop(i)
                    builder.update_endpoint(endpoint.id, endpoint)
                    st.rerun()


def render_request_body_editor(builder: APIBuilder, endpoint: Endpoint):
    """Render request body editor."""
    st.subheader("Request Body")

    schema_json = st.text_area(
        "JSON Schema",
        value=json.dumps(endpoint.request_body.schema, indent=2) if endpoint.request_body else "{}",
        height=200,
    )

    content_type = st.text_input(
        "Content Type",
        value=endpoint.request_body.content_type if endpoint.request_body else "application/json"
    )

    if st.button("Update Request Body"):
        try:
            schema = json.loads(schema_json)
            endpoint.request_body = RequestBody(
                content_type=content_type,
                schema=schema,
            )
            builder.update_endpoint(endpoint.id, endpoint)
            st.success("Request body updated!")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")


def render_response_editor(builder: APIBuilder, endpoint: Endpoint):
    """Render response editor."""
    st.subheader("Responses")

    # Add new response
    with st.form("add_response"):
        col1, col2 = st.columns(2)

        with col1:
            status_code = st.number_input("Status Code", min_value=100, max_value=599, value=200)
            description = st.text_input("Description", value="Successful response")

        with col2:
            schema_json = st.text_area("Schema (JSON)", value="{}", height=100)

        if st.form_submit_button("Add Response"):
            try:
                schema = json.loads(schema_json)
                response = Response(
                    status_code=status_code,
                    description=description,
                    schema=schema,
                )
                endpoint.responses[status_code] = response
                builder.update_endpoint(endpoint.id, endpoint)
                st.success("Response added!")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")

    # List existing responses
    if endpoint.responses:
        st.write("**Existing Responses:**")
        for status_code, response in endpoint.responses.items():
            st.write(f"**{status_code}** - {response.description}")


def render_authentication():
    """Render the authentication tab."""
    st.header("🔐 Authentication")

    builder = st.session_state.api_builder

    tab1, tab2 = st.tabs(["📋 Schemes", "➕ Add Scheme"])

    with tab1:
        schemes = builder.auth_manager.list_schemes()
        if schemes:
            for scheme in schemes:
                with st.expander(f"{scheme.name} ({scheme.type.value})"):
                    st.write(f"**Type:** {scheme.type.value}")
                    st.write(f"**Description:** {scheme.description}")
                    st.write(f"**Enabled:** {scheme.enabled}")

                    if st.button(f"Remove {scheme.name}", key=f"remove_auth_{scheme.name}"):
                        builder.remove_auth_scheme(scheme.name)
                        st.success("Auth scheme removed!")
                        st.rerun()
        else:
            st.info("No authentication schemes configured")

    with tab2:
        st.subheader("Add Authentication Scheme")

        auth_type = st.selectbox(
            "Authentication Type",
            ["API Key", "JWT", "Basic Auth", "OAuth2"]
        )

        if auth_type == "API Key":
            name = st.text_input("Scheme Name", value="apiKey")
            location = st.selectbox("Location", [loc.value for loc in APIKeyLocation])
            param_name = st.text_input("Parameter Name", value="X-API-Key")

            if st.button("Add API Key Auth"):
                auth = create_api_key_auth(name, APIKeyLocation(location), param_name)
                builder.add_auth_scheme(auth)
                st.success("API Key authentication added!")
                st.rerun()

        elif auth_type == "JWT":
            name = st.text_input("Scheme Name", value="bearerAuth")
            expiration = st.number_input("Token Expiration (minutes)", value=60, min_value=1)

            if st.button("Add JWT Auth"):
                auth = create_jwt_auth(name, expiration)
                builder.add_auth_scheme(auth)
                st.success("JWT authentication added!")
                st.rerun()

        elif auth_type == "Basic Auth":
            name = st.text_input("Scheme Name", value="basicAuth")

            if st.button("Add Basic Auth"):
                auth = create_basic_auth(name)
                builder.add_auth_scheme(auth)
                st.success("Basic authentication added!")
                st.rerun()


def render_rate_limiting():
    """Render the rate limiting tab."""
    st.header("⏱️ Rate Limiting")

    builder = st.session_state.api_builder

    tab1, tab2, tab3 = st.tabs(["📋 Policies", "➕ Add Policy", "💎 Quota Plans"])

    with tab1:
        if builder.rate_limiter.policies:
            for name, policy in builder.rate_limiter.policies.items():
                with st.expander(f"{name}"):
                    st.write(f"**Max Requests:** {policy.rule.max_requests}")
                    st.write(f"**Period:** {policy.rule.period_value} {policy.rule.period.value}(s)")
                    st.write(f"**Strategy:** {policy.strategy.value}")
        else:
            st.info("No rate limiting policies configured")

    with tab2:
        st.subheader("Create Rate Limit Policy")

        name = st.text_input("Policy Name")
        max_requests = st.number_input("Max Requests", min_value=1, value=100)
        period = st.selectbox("Period", [p.value for p in RateLimitPeriod])
        strategy = st.selectbox("Strategy", [s.value for s in ThrottleStrategy])

        if st.button("Add Rate Limit"):
            if name:
                rule = RateLimitRule(
                    name=name,
                    max_requests=max_requests,
                    period=RateLimitPeriod(period),
                )
                builder.add_rate_limit(name, rule, ThrottleStrategy(strategy))
                st.success("Rate limit policy added!")
                st.rerun()

    with tab3:
        st.subheader("Quota Plans")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### Free Plan")
            free_plan = create_free_plan()
            st.write(f"**Daily:** {free_plan.daily_quota:,}")
            st.write(f"**Monthly:** {free_plan.monthly_quota:,}")
            st.write(f"**Price:** ${free_plan.price}")
            if st.button("Add Free Plan"):
                builder.rate_limiter.quota_manager.add_plan(free_plan)
                st.success("Free plan added!")

        with col2:
            st.markdown("### Pro Plan")
            pro_plan = create_pro_plan()
            st.write(f"**Daily:** {pro_plan.daily_quota:,}")
            st.write(f"**Monthly:** {pro_plan.monthly_quota:,}")
            st.write(f"**Price:** ${pro_plan.price}")
            if st.button("Add Pro Plan"):
                builder.rate_limiter.quota_manager.add_plan(pro_plan)
                st.success("Pro plan added!")

        with col3:
            st.markdown("### Enterprise Plan")
            enterprise_plan = create_enterprise_plan()
            st.write(f"**Daily:** Unlimited")
            st.write(f"**Monthly:** Unlimited")
            st.write(f"**Price:** ${enterprise_plan.price}")
            if st.button("Add Enterprise Plan"):
                builder.rate_limiter.quota_manager.add_plan(enterprise_plan)
                st.success("Enterprise plan added!")


def render_documentation():
    """Render the documentation tab."""
    st.header("📖 Documentation")

    builder = st.session_state.api_builder

    tab1, tab2, tab3 = st.tabs(["📄 OpenAPI", "📝 Markdown", "🔍 Explorer"])

    with tab1:
        st.subheader("OpenAPI Specification")

        format = st.radio("Format", ["JSON", "YAML"], horizontal=True)

        if st.button("Generate OpenAPI Spec"):
            try:
                if format == "JSON":
                    spec = builder.generate_openapi_spec("json")
                else:
                    spec = builder.generate_openapi_spec("yaml")

                st.code(spec, language="json" if format == "JSON" else "yaml")

                st.download_button(
                    "Download",
                    data=spec,
                    file_name=f"openapi.{'json' if format == 'JSON' else 'yaml'}",
                    mime="application/json" if format == "JSON" else "text/yaml",
                )
            except Exception as e:
                st.error(f"Error generating spec: {e}")

    with tab2:
        st.subheader("Markdown Documentation")

        if st.button("Generate Markdown Docs"):
            try:
                docs = builder.generate_markdown_docs()
                st.markdown(docs)

                st.download_button(
                    "Download",
                    data=docs,
                    file_name="api_documentation.md",
                    mime="text/markdown",
                )
            except Exception as e:
                st.error(f"Error generating docs: {e}")

    with tab3:
        st.subheader("Interactive API Explorer")
        st.info("Select an endpoint to explore and test")


def render_testing():
    """Render the testing tab."""
    st.header("🧪 Testing")

    builder = st.session_state.api_builder

    tab1, tab2, tab3 = st.tabs(["📋 Collections", "▶️ Run Tests", "📊 Results"])

    with tab1:
        st.subheader("Test Collections")

        if builder.api_tester.collections:
            for name, collection in builder.api_tester.collections.items():
                with st.expander(f"{name} ({len(collection.tests)} tests)"):
                    st.write(f"**Description:** {collection.description}")
                    st.write(f"**Tests:** {len(collection.tests)}")
        else:
            st.info("No test collections created yet")

    with tab2:
        st.subheader("Run Tests")

        if builder.api_tester.collections:
            collection_name = st.selectbox(
                "Select Collection",
                list(builder.api_tester.collections.keys())
            )

            use_mock = st.checkbox("Use Mock Server", value=True)

            if st.button("Run Tests"):
                with st.spinner("Running tests..."):
                    results = builder.run_tests(collection_name, use_mock)
                    st.success(f"Completed {len(results)} tests")

                    for result in results:
                        status = "✅" if result.passed else "❌"
                        st.write(f"{status} {result.test_name}")
        else:
            st.info("Create test collections first")

    with tab3:
        st.subheader("Test Statistics")

        stats = builder.get_test_statistics()

        if stats['total_tests'] > 0:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Tests", stats['total_tests'])
            with col2:
                st.metric("Passed", stats['passed_tests'])
            with col3:
                st.metric("Failed", stats['failed_tests'])

            st.progress(stats['pass_rate'] / 100)
            st.write(f"**Pass Rate:** {stats['pass_rate']:.1f}%")
        else:
            st.info("No test results yet")


def render_mock_server():
    """Render the mock server tab."""
    st.header("🎭 Mock Server")

    builder = st.session_state.api_builder

    tab1, tab2 = st.tabs(["📋 Scenarios", "🎯 Simulate"])

    with tab1:
        st.subheader("Mock Scenarios")

        endpoints = builder.list_endpoints()
        if endpoints:
            endpoint_options = {f"{e.method.value} {e.path}": e.id for e in endpoints}
            selected_endpoint = st.selectbox("Select Endpoint", list(endpoint_options.keys()))

            if selected_endpoint:
                endpoint_id = endpoint_options[selected_endpoint]

                col1, col2 = st.columns([3, 1])
                with col1:
                    scenario_name = st.text_input("Scenario Name", placeholder="success")
                with col2:
                    if st.button("Create Scenario"):
                        if scenario_name:
                            builder.create_mock_scenario(scenario_name, endpoint_id)
                            st.success("Mock scenario created!")
                            st.rerun()
        else:
            st.info("Create endpoints first")

    with tab2:
        st.subheader("Simulate Request")

        endpoints = builder.list_endpoints()
        if endpoints:
            endpoint_options = {f"{e.method.value} {e.path}": e.id for e in endpoints}
            selected_endpoint = st.selectbox("Endpoint", list(endpoint_options.keys()), key="sim_endpoint")

            if selected_endpoint and st.button("Simulate"):
                endpoint_id = endpoint_options[selected_endpoint]
                response = builder.simulate_request(endpoint_id)

                st.write("**Response:**")
                st.json(response)
        else:
            st.info("Create endpoints first")


def render_versioning():
    """Render the versioning tab."""
    st.header("📦 Versioning")

    builder = st.session_state.api_builder

    tab1, tab2, tab3 = st.tabs(["📋 Versions", "➕ Add Version", "🔄 Migration"])

    with tab1:
        versions = builder.list_versions()

        if versions:
            for version in versions:
                status_emoji = {
                    VersionStatus.DEVELOPMENT: "🚧",
                    VersionStatus.BETA: "🧪",
                    VersionStatus.STABLE: "✅",
                    VersionStatus.DEPRECATED: "⚠️",
                    VersionStatus.RETIRED: "🔒",
                }

                emoji = status_emoji.get(version.status, "📦")

                with st.expander(f"{emoji} v{version.version} ({version.status.value})"):
                    st.write(f"**Description:** {version.description}")
                    st.write(f"**Release Date:** {version.release_date.strftime('%Y-%m-%d')}")
                    if version.sunset_date:
                        st.write(f"**Sunset Date:** {version.sunset_date.strftime('%Y-%m-%d')}")
        else:
            st.info("No versions created yet")

    with tab2:
        st.subheader("Create Version")

        version = st.text_input("Version Number", placeholder="1.0.0")
        status = st.selectbox("Status", [s.value for s in VersionStatus])
        description = st.text_area("Description")

        if st.button("Create Version"):
            if version:
                api_version = create_version(version, VersionStatus(status), description)
                builder.add_version(api_version)
                st.success(f"Version {version} created!")
                st.rerun()

    with tab3:
        st.subheader("Migration Guide")

        versions = builder.list_versions()
        if len(versions) >= 2:
            version_list = [v.version for v in versions]

            col1, col2 = st.columns(2)
            with col1:
                from_version = st.selectbox("From Version", version_list)
            with col2:
                to_version = st.selectbox("To Version", version_list)

            if st.button("Generate Migration Guide"):
                guide = builder.generate_migration_guide(from_version, to_version)
                st.json(guide)
        else:
            st.info("Create at least 2 versions to generate migration guides")


def render_settings():
    """Render the settings tab."""
    st.header("⚙️ Settings")

    builder = st.session_state.api_builder

    tab1, tab2, tab3 = st.tabs(["📋 Project", "💾 Export/Import", "📊 Statistics"])

    with tab1:
        st.subheader("Project Settings")

        name = st.text_input("Project Name", value=builder.project.name)
        description = st.text_area("Description", value=builder.project.description)
        version = st.text_input("Version", value=builder.project.version)
        base_url = st.text_input("Base URL", value=builder.project.base_url)

        if st.button("Update Project"):
            builder.project.name = name
            builder.project.description = description
            builder.project.version = version
            builder.project.base_url = base_url
            builder.project.updated_at = datetime.now()
            st.success("Project updated!")

    with tab2:
        st.subheader("Export Project")

        if st.button("Export as JSON"):
            project_json = builder.export_project()
            st.download_button(
                "Download Project",
                data=project_json,
                file_name=f"{builder.project.name.replace(' ', '_')}.json",
                mime="application/json",
            )

        st.markdown("---")
        st.subheader("Import Project")

        uploaded_file = st.file_uploader("Choose a JSON file", type="json")
        if uploaded_file is not None:
            if st.button("Import"):
                try:
                    project_json = uploaded_file.read().decode()
                    builder.import_project(project_json)
                    st.success("Project imported successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")

    with tab3:
        st.subheader("Project Statistics")

        stats = builder.get_project_statistics()
        st.json(stats)


def main():
    """Main application entry point."""
    init_session_state()
    render_header()
    render_sidebar()

    # Route to appropriate tab
    tab = st.session_state.selected_tab

    if tab == "Dashboard":
        render_dashboard()
    elif tab == "Endpoints":
        render_endpoints()
    elif tab == "Authentication":
        render_authentication()
    elif tab == "Rate Limiting":
        render_rate_limiting()
    elif tab == "Documentation":
        render_documentation()
    elif tab == "Testing":
        render_testing()
    elif tab == "Mock Server":
        render_mock_server()
    elif tab == "Versioning":
        render_versioning()
    elif tab == "Settings":
        render_settings()


if __name__ == "__main__":
    main()
