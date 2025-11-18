# NEXUS Platform 🚀

**Unified AI-powered productivity platform** with integrated modules for API development, document editing, data analytics, and more.

Built with **Streamlit** & **Claude AI** ⚡

## Current Modules

### 📡 API Builder & Documentation (v1.0.0) - **PRODUCTION READY**

A comprehensive API development platform that rivals Postman, Swagger, and Stoplight.

**Key Features:**
- 🎨 Visual API Designer with drag-and-drop endpoint builder
- 🔌 Full CRUD endpoint management
- 🔐 Authentication (API Keys, JWT, OAuth2, Basic Auth, Custom)
- ⏱️ Advanced rate limiting & quota management (tiered plans)
- 📖 Auto-generated OpenAPI 3.0 / Swagger documentation
- 🧪 Built-in API testing framework with assertions
- 🎭 Mock server with delays & error scenarios
- 📦 API versioning with deprecation warnings & migration guides
- 📊 Request monitoring & analytics
- 💻 Code generation (Python, JavaScript, Java, cURL)
- 🌐 Interactive API explorer

**[→ Full API Builder Documentation](modules/api_builder/README.md)**

## Planned Modules

- 📊 Analytics & Dashboards
- 📝 Document Editor (Word)
- 📈 Spreadsheet Editor (Excel)
- 📽️ Presentation Editor (PowerPoint)
- 💬 Chat & Collaboration
- 📧 Email Management
- 📋 Project Management
- 🎨 Flowchart Designer
- 📅 Calendar & Scheduling
- 🗂️ File Manager

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd nexus-platform

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Launch NEXUS Platform

```bash
# Main platform launcher
streamlit run app.py
```

### Launch API Builder

```bash
# Streamlit UI
streamlit run modules/api_builder/streamlit_ui.py

# Or use the Python API
python examples/api_builder_example.py
```

### Using Python API

```python
from modules.api_builder import APIBuilder, HTTPMethod

# Create API Builder
builder = APIBuilder()

# Create an endpoint
endpoint = builder.create_endpoint(
    path="/api/users",
    method=HTTPMethod.GET,
    summary="Get all users"
)

# Add authentication
from modules.api_builder.auth import create_api_key_auth

auth = create_api_key_auth()
builder.add_auth_scheme(auth)

# Generate OpenAPI documentation
openapi_spec = builder.generate_openapi_spec(format="json")

# Export project
builder.export_project("my_api.json")
```

## Project Structure

```
nexus-platform/
├── app.py                      # Main platform launcher
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── modules/
│   └── api_builder/           # API Builder module
│       ├── __init__.py
│       ├── builder.py         # Core API builder engine
│       ├── endpoints.py       # Endpoint management
│       ├── auth.py            # Authentication schemes
│       ├── rate_limiting.py   # Rate limiting & quotas
│       ├── docs.py            # Documentation generation
│       ├── testing.py         # Testing framework
│       ├── mock.py            # Mock server
│       ├── versioning.py      # API versioning
│       ├── streamlit_ui.py    # Streamlit UI
│       └── README.md          # API Builder docs
├── tests/
│   └── api_builder/           # API Builder tests
│       ├── test_endpoints.py
│       ├── test_auth.py
│       └── test_builder.py
└── examples/
    └── api_builder_example.py # Complete example
```

## Features Comparison

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

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run API Builder tests
pytest tests/api_builder/ -v

# Run with coverage
pytest tests/ --cov=modules/api_builder
```

## Technology Stack

- **Frontend:** Streamlit
- **Backend:** Python 3.8+
- **AI Integration:** Claude AI
- **Standards:** OpenAPI 3.0, REST, GraphQL
- **Testing:** pytest

## Documentation

- **[API Builder Documentation](modules/api_builder/README.md)** - Complete guide
- **[Examples](examples/)** - Code examples and tutorials
- **[OpenAPI 3.0 Specification](https://swagger.io/specification/)** - Standard reference

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Part of the NEXUS platform.

## Roadmap

### Phase 1 (Current) ✅
- API Builder & Documentation Module

### Phase 2 (Next)
- Analytics & Dashboard Module
- Document Editor Module

### Phase 3 (Future)
- Spreadsheet Editor
- Presentation Editor
- Collaboration Tools

## Support

For issues and questions, please open an issue on the repository.

---

**Built with ❤️ by the NEXUS team**

*Powered by Streamlit & Claude AI*
